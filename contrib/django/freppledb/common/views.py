#
# Copyright (C) 2007-2013 by frePPLe bvba
#
# This library is free software; you can redistribute it and/or modify it
# under the terms of the GNU Affero General Public License as published
# by the Free Software Foundation; either version 3 of the License, or
# (at your option) any later version.
#
# This library is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU Affero
# General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public
# License along with this program.  If not, see <http://www.gnu.org/licenses/>.
#

from django.shortcuts import render_to_response
from django.contrib import messages
from django.contrib.auth import update_session_auth_hash
from django.contrib.auth.decorators import login_required
from django.contrib.admin.utils import unquote, quote
from django.contrib.admin.views.decorators import staff_member_required
from django.contrib.contenttypes.models import ContentType
from django.template import RequestContext, loader, TemplateDoesNotExist
from django import forms
from django.utils.encoding import force_text
from django.utils.translation import ugettext_lazy as _
from django.utils.text import capfirst
from django.contrib.auth.models import Group
from django.utils import translation
from django.conf import settings
from django.http import Http404, HttpResponseRedirect, HttpResponse, HttpResponseServerError
from django.views.decorators.csrf import csrf_protect
from django.views.decorators.debug import sensitive_variables

from freppledb.common.models import User, Parameter, Comment, Bucket, BucketDetail
from freppledb.common.report import GridReport, GridFieldLastModified, GridFieldText
from freppledb.common.report import GridFieldBool, GridFieldDateTime, GridFieldInteger


import logging
logger = logging.getLogger(__name__)


def handler404(request):
  '''
  Custom error handler which redirects to the main page rather than displaying the 404 page.
  '''
  messages.add_message(
    request, messages.ERROR,
    force_text(_('Page not found') + ": " + request.prefix + request.get_full_path())
    )
  return HttpResponseRedirect(request.prefix + "/admin/")


def handler500(request):
  '''
  Custom error handler.
  The only difference with the default Django handler is that we passes more context
  to the error template.
  '''
  try:
    template = loader.get_template("500.html")
  except TemplateDoesNotExist:
    return HttpResponseServerError('<h1>Server Error (500)</h1>', content_type='text/html')
  return HttpResponseServerError(template.render(RequestContext(request)))


class PreferencesForm(forms.Form):
  language = forms.ChoiceField(
    label=_("Language"),
    initial="auto",
    choices=User.languageList,
    help_text=_("Language of the user interface"),
    )
  pagesize = forms.IntegerField(
    label=_('Page size'),
    required=False,
    initial=100,
    min_value=25,
    help_text=_('Number of records to display in a single page'),
    )
  
  theme = forms.ChoiceField(
    label=_('Theme'),
    required=False,
    choices=[ (i, capfirst(i)) for i in settings.THEMES ],
    help_text=_('Theme for the user interface'),
    )
  cur_password = forms.CharField(
    label = _("Change password"),
    required=False,
    help_text=_('Old password'),
    widget = forms.PasswordInput()
    )
  new_password1 = forms.CharField(
    label = "",
    required=False,
    help_text=_('New password'),
    widget = forms.PasswordInput()
    )
  new_password2 = forms.CharField(
    label = "",
    required = False,
    help_text = _('New password confirmation'),
    widget = forms.PasswordInput()
    )
  
  def __init__(self, *args, **kwargs):
    super(PreferencesForm, self).__init__(*args, **kwargs) 
    if len(settings.THEMES) == 1:  #If there is only one theme make this choice unavailable
      self.fields.pop('theme')
    
  def clean(self):
    newdata = super(PreferencesForm, self).clean()
    if newdata['cur_password']:
      if not self.user.check_password(newdata['cur_password']):
        raise forms.ValidationError(_("Your old password was entered incorrectly. Please enter it again."))
      if newdata['new_password1'] != newdata['new_password2']:
        raise forms.ValidationError("The two password fields didn't match.")


@sensitive_variables('newdata')
@login_required
@csrf_protect
def preferences(request):
  if request.method == 'POST':
    form = PreferencesForm(request.POST)
    form.user = request.user
    if form.is_valid():
      try:
        newdata = form.cleaned_data
        request.user.language = newdata['language']
        if 'theme' in newdata:
          request.user.theme = newdata['theme']
        request.user.pagesize = newdata['pagesize']
        if newdata['cur_password']:
          request.user.set_password(newdata["new_password1"])
          # Updating the password logs out all other sessions for the user
          # except the current one if
          # django.contrib.auth.middleware.SessionAuthenticationMiddleware
          # is enabled.
          update_session_auth_hash(request, form.user)
        request.user.save()
        # Switch to the new theme and language immediately
        if 'theme' in newdata:
          request.theme = newdata['theme']
        if newdata['language'] == 'auto':
          newdata['language'] = translation.get_language_from_request(request)
        if translation.get_language() != newdata['language']:
          translation.activate(newdata['language'])
          request.LANGUAGE_CODE = translation.get_language()
        messages.add_message(request, messages.INFO, force_text(_('Successfully updated preferences')))
      except Exception as e:
        logger.error("Failure updating preferences: %s" % e)
        messages.add_message(request, messages.ERROR, force_text(_('Failure updating preferences')))
  else:
    pref = request.user
    form = PreferencesForm({
      'language': pref.language,
      'theme': pref.theme,
      'pagesize': pref.pagesize,
      })
  return render_to_response('common/preferences.html', {
     'title': _('My preferences'),
     'form': form,
     },
     context_instance=RequestContext(request))


class HorizonForm(forms.Form):
  horizonbuckets = forms.ModelChoiceField(queryset=Bucket.objects.all().values_list('name', flat=True))
  horizonstart = forms.DateField(required=False)
  horizonend = forms.DateField(required=False)
  horizontype = forms.ChoiceField(choices=(("1", "1"), ("0", "0")))
  horizonlength = forms.IntegerField(required=False, min_value=1)
  horizonunit = forms.ChoiceField(choices=(("day", "day"), ("week", "week"), ("month", "month")))


@login_required
@csrf_protect
def horizon(request):
  if request.method != 'POST':
    raise Http404('Only post requests allowed')
  form = HorizonForm(request.POST)
  if not form.is_valid():
    raise Http404('Invalid form data')
  try:
    request.user.horizonstart = form.cleaned_data['horizonstart']
    request.user.horizonbuckets = form.cleaned_data['horizonbuckets']
    request.user.horizonstart = form.cleaned_data['horizonstart']
    request.user.horizonend = form.cleaned_data['horizonend']
    request.user.horizontype = form.cleaned_data['horizontype'] == '1'
    request.user.horizonlength = form.cleaned_data['horizonlength']
    request.user.horizonunit = form.cleaned_data['horizonunit']
    request.user.save()
    return HttpResponse(content="OK")
  except Exception as e:
    logger.error("Error saving horizon settings: %s" % e)
    raise Http404('Error saving horizon settings')


class UserList(GridReport):
  '''
  A list report to show users.
  '''
  template = 'common/userlist.html'
  title = _("User List")
  basequeryset = User.objects.all()
  model = User
  adminsite = 'admin'
  frozenColumns = 2
  multiselect = False

  rows = (
    GridFieldInteger('id', title=_('id'), key=True, formatter='user'),
    GridFieldText('username', title=_('username')),
    GridFieldText('email', title=_('email address'), formatter='email', width=200),
    GridFieldText('first_name', title=_('first name')),
    GridFieldText('last_name', title=_('last name')),
    GridFieldBool('is_active', title=_('active')),
    GridFieldBool('is_superuser', title=_('superuser status'), width=120),
    GridFieldDateTime('date_joined', title=_('date joined'), editable=False),
    GridFieldDateTime('last_login', title=_('last login'), editable=False)
    )


class GroupList(GridReport):
  '''
  A list report to show groups.
  '''
  template = 'auth/grouplist.html'
  title = _("Group List")
  basequeryset = Group.objects.all()
  model = Group
  adminsite = 'admin'
  frozenColumns = 0
  multiselect = False
  rows = (
    GridFieldInteger('id', title=_('identifier'), key=True, formatter='group'),
    GridFieldText('name', title=_('name'), key=True, width=200),
    )


class ParameterList(GridReport):
  '''
  A list report to show all configurable parameters.
  '''
  template = 'common/parameterlist.html'
  title = _("Parameter List")
  basequeryset = Parameter.objects.all()
  model = Parameter
  adminsite = 'admin'
  frozenColumns = 1

  rows = (
    GridFieldText('name', title=_('name'), key=True, formatter='parameter'),
    GridFieldText('value', title=_('value')),
    GridFieldText('description', title=_('description')),
    GridFieldText('source', title=_('source')),
    GridFieldLastModified('lastmodified'),
    )


@staff_member_required
@csrf_protect
def Comments(request, app, model, object_id):
  try:
    modeltype = ContentType.objects.using(request.database).get(app_label=app, model=model)
    modeltype._state.db = request.database
    object_id = unquote(object_id)
    modelinstance = modeltype.get_object_for_this_type(pk=object_id)
    comments = Comment.objects.using(request.database) \
      .filter(content_type__pk=modeltype.id, object_pk=object_id) \
      .order_by('-id')
  except:
    raise Http404('Object not found')
  if request.method == 'POST':
    if request.user.has_perm("common.add_comment"):
      comment = request.POST['comment']
      if comment:
        Comment(
             content_object=modelinstance,
             user=request.user,
             comment=comment
             ).save(using=request.database)
    return HttpResponseRedirect('%s/comments/%s/%s/%s/' % (request.prefix, app, model, object_id))
  else:
    return render_to_response('common/comments.html', {
      'title': capfirst(force_text(modelinstance._meta.verbose_name) + " " + object_id),
      'model': model,
      'object_id': quote(object_id),
      'active_tab': 'comments',
      'comments': comments
      },
      context_instance=RequestContext(request))


class CommentList(GridReport):
  '''
  A list report to display all comments.
  '''
  template = 'common/commentlist.html'
  title = _('Comments')
  basequeryset = Comment.objects.all()
  model = Comment
  adminsite = 'admin'
  editable = False
  multiselect = False
  frozenColumns = 0

  rows = (
    GridFieldInteger('id', title=_('identifier'), key=True),
    GridFieldLastModified('lastmodified'),
    GridFieldText('user', title=_('user'), field_name='user__username', editable=False, align='center', width=80),
    GridFieldText('content_type', title=_('type'), field_name='content_type__model', editable=False, align='center'),
    GridFieldText('object_pk', title=_('object ID'), field_name='object_pk', editable=False, align='center', extra='formatter:objectfmt'),
    GridFieldText('comment', title=_('comment'), editable=False, align='center'),
    )


class BucketList(GridReport):
  '''
  A list report to show dates.
  '''
  template = 'common/bucketlist.html'
  title = _("Bucket List")
  basequeryset = Bucket.objects.all()
  model = Bucket
  adminsite = 'admin'
  frozenColumns = 1
  rows = (
    GridFieldText('name', title=_('name'), key=True, formatter="bucket"),
    GridFieldText('description', title=_('description')),
    GridFieldInteger('level', title=_('level')),
    GridFieldText('source', title=_('source')),
    GridFieldLastModified('lastmodified'),
    )


class BucketDetailList(GridReport):
  '''
  A list report to show dates.
  '''
  template = 'common/bucketlist.html'
  title = _("Bucket Detail List")
  basequeryset = BucketDetail.objects.all()
  model = BucketDetail
  adminsite = 'admin'
  frozenColumns = 2
  rows = (
    GridFieldText('bucket', title=_('bucket'), field_name='bucket__name', formatter="bucket"),
    GridFieldDateTime('startdate', title=_('start date')),
    GridFieldDateTime('enddate', title=_('end date')),
    GridFieldText('name', title=_('name')),
    GridFieldText('source', title=_('source')),
    GridFieldLastModified('lastmodified'),
    )
