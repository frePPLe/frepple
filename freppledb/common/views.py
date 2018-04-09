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

import json

from django.shortcuts import render
from django.contrib import messages
from django.contrib.auth import update_session_auth_hash
from django.contrib.auth.password_validation import validate_password, get_password_validators, password_validators_help_text_html
from django.contrib.auth.decorators import login_required
from django.contrib.admin.views.decorators import staff_member_required
from django.contrib.contenttypes.models import ContentType
from django.core.urlresolvers import reverse, resolve
from django.template import loader, TemplateDoesNotExist
from django import forms
from django.utils.encoding import force_text
from django.utils.translation import ugettext_lazy as _
from django.utils.text import capfirst
from django.contrib.auth.models import Group
from django.utils import translation
from django.conf import settings
from django.http import Http404, HttpResponseRedirect, HttpResponse, HttpResponseServerError, HttpResponseNotFound
from django.views.decorators.csrf import csrf_protect
from django.views.decorators.debug import sensitive_variables

from freppledb.common.models import User, Parameter, Comment, Bucket, BucketDetail
from freppledb.common.report import GridReport, GridFieldLastModified, GridFieldText
from freppledb.common.report import GridFieldBool, GridFieldDateTime, GridFieldInteger
from freppledb.common.report import getCurrency

from freppledb.admin import data_site
from freppledb import VERSION

import logging
logger = logging.getLogger(__name__)


@staff_member_required
def AboutView(request):
  return HttpResponse(
     content=json.dumps({'version': VERSION, 'apps': settings.INSTALLED_APPS }),
     content_type='application/json; charset=%s' % settings.DEFAULT_CHARSET
     )


@staff_member_required
def cockpit(request):
  return render(request, 'index.html',
    context= {
      'title': _('cockpit'),
      'bucketnames': Bucket.objects.order_by('-level').values_list('name', flat=True),
      'currency': json.dumps(getCurrency())
      }
    )


def handler404(request):
  '''
  Custom error handler which redirects to the main page rather than displaying the 404 page.
  '''
  messages.add_message(
    request, messages.ERROR,
    #. Translators: Translation included with Django
    force_text(_('Page not found') + ": " + request.prefix + request.get_full_path())
    )
  return HttpResponseRedirect(request.prefix + "/")


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
  return HttpResponseServerError(template.render({}, request))


###############################################
@login_required
@csrf_protect
def wizard(request):
  return render(request, 'common/wizard.html',
    context = {
      'title': _('Path to unlock features'),
      'hasForecast': 'freppledb.forecast' in settings.INSTALLED_APPS,
      'hasIP': 'freppledb.inventoryplanning' in settings.INSTALLED_APPS,
      }
    )


class PreferencesForm(forms.Form):
  language = forms.ChoiceField(
    label=_("language"),
    initial="auto",
    choices=User.languageList
    )
  pagesize = forms.IntegerField(
    label=_('Page size'),
    required=False,
    initial=100
    )
  theme = forms.ChoiceField(
    label=_('Theme'),
    required=False,
    choices=[ (i, capfirst(i)) for i in settings.THEMES ],
    )
  cur_password = forms.CharField(
    #. Translators: Translation included with Django
    label = _("Change password"),
    required=False,
    #. Translators: Translation included with Django
    help_text=_('Old password'),
    widget = forms.PasswordInput()
    )
  new_password1 = forms.CharField(
    label = "",
    required=False,
    #. Translators: Translation included with Django
    help_text=password_validators_help_text_html(get_password_validators(settings.AUTH_PASSWORD_VALIDATORS)),
    widget = forms.PasswordInput()
    )
  new_password2 = forms.CharField(
    label = "",
    required = False,
    #. Translators: Translation included with Django
    help_text = _('New password confirmation'),
    widget = forms.PasswordInput()
    )

  def __init__(self, *args, **kwargs):
    super(PreferencesForm, self).__init__(*args, **kwargs)
    if len(settings.THEMES) == 1:  #If there is only one theme make this choice unavailable
      self.fields.pop('theme')

  def clean(self):
    newdata = super(PreferencesForm, self).clean()
    if newdata.get('pagesize',0) > 10000:
      raise forms.ValidationError("Maximum page size is 10000.")
    if newdata.get('pagesize',25) < 25:
      raise forms.ValidationError("Minimum page size is 25.")
    if newdata['cur_password']:
      if not self.user.check_password(newdata['cur_password']):
        #. Translators: Translation included with Django
        raise forms.ValidationError(_("Your old password was entered incorrectly. Please enter it again."))
      # Validate_password raises a ValidationError
      validate_password(newdata['new_password1'], self.user, get_password_validators(settings. AUTH_PASSWORD_VALIDATORS))
      if newdata['new_password1'] != newdata['new_password2']:
        #. Translators: Translation included with Django
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
  LANGUAGE = User.languageList[0][1]
  for l in User.languageList:
    if l[0] == request.user.language:
      LANGUAGE = l[1]
  return render(request, 'common/preferences.html',
    context = {
      'title': _('My preferences'),
      'form': form,
      'THEMES': settings.THEMES,
      'LANGUAGE': LANGUAGE
      }
    )


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
    return HttpResponseServerError('Only post requests allowed')
  form = HorizonForm(request.POST)
  if not form.is_valid():
    return HttpResponseServerError('Invalid form data')
  try:
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


@login_required
@csrf_protect
def saveSettings(request):
  if request.method != 'POST' or not request.is_ajax():
    raise Http404('Only ajax post requests allowed')
  try:
    data = json.loads(request.body.decode(request.encoding))
    for key, value in data.items():
      request.user.setPreference(key, value, database=request.database)
    return HttpResponse(content="OK")
  except Exception as e:
    logger.error("Error saving report settings: %s" % e)
    return HttpResponseServerError('Error saving report settings')


class UserList(GridReport):
  '''
  A list report to show users.
  '''
  #. Translators: Translation included with Django
  title = _("users")
  basequeryset = User.objects.all()
  model = User
  frozenColumns = 2
  permissions = (("change_user", "Can change user"),)
  help_url = 'user-guide/user-interface/getting-around/user-permissions-and-roles.html'

  rows = (
    #. Translators: Translation included with Django
    GridFieldInteger('id', title=_('id'), key=True, formatter='admin', extra='"role":"common/user"'),
    #. Translators: Translation included with Django
    GridFieldText('username', title=_('username')),
    #. Translators: Translation included with Django
    GridFieldText('email', title=_('email address'), formatter='email', width=200),
    #. Translators: Translation included with Django
    GridFieldText('first_name', title=_('first name')),
    #. Translators: Translation included with Django
    GridFieldText('last_name', title=_('last name')),
    #. Translators: Translation included with Django
    GridFieldBool('is_active', title=_('active')),
    #. Translators: Translation included with Django
    GridFieldBool('is_superuser', title=_('superuser status'), width=120),
    #. Translators: Translation included with Django
    GridFieldDateTime('date_joined', title=_('date joined'), editable=False),
    #. Translators: Translation included with Django
    GridFieldDateTime('last_login', title=_('last login'), editable=False)
    )


class GroupList(GridReport):
  '''
  A list report to show groups.
  '''
  #. Translators: Translation included with Django
  title = _("groups")
  basequeryset = Group.objects.all()
  model = Group
  frozenColumns = 1
  permissions = (("change_group", "Can change group"),)
  help_url = 'user-guide/user-interface/getting-around/user-permissions-and-roles.html'

  rows = (
    GridFieldInteger('id', title=_('identifier'), key=True, formatter='detail', extra='"role":"auth/group"'),
    #. Translators: Translation included with Django
    GridFieldText('name', title=_('name'), width=200),
    )


class ParameterList(GridReport):
  '''
  A list report to show all configurable parameters.
  '''
  title = _("parameters")
  basequeryset = Parameter.objects.all()
  model = Parameter
  adminsite = 'admin'
  frozenColumns = 1
  help_url = 'user-guide/model-reference/parameters.html'

  rows = (
    #. Translators: Translation included with Django
    GridFieldText('name', title=_('name'), key=True, formatter='detail', extra='"role":"common/parameter"'),
    GridFieldText('value', title=_('value')),
    GridFieldText('description', title=_('description'), formatter='longstring'),
    GridFieldText('source', title=_('source')),
    GridFieldLastModified('lastmodified'),
    )


class CommentList(GridReport):
  '''
  A list report to display all comments.
  '''
  template = 'common/commentlist.html'
  title = _('comments')
  basequeryset = Comment.objects.all()
  model = Comment
  editable = False
  multiselect = False
  frozenColumns = 0
  help_url = 'user-guide/user-interface/getting-around/comments.html'

  rows = (
    GridFieldInteger('id', title=_('identifier'), key=True),
    GridFieldLastModified('lastmodified'),
    #. Translators: Translation included with Django
    GridFieldText('user', title=_('user'), field_name='user__username', editable=False, align='center', width=80),
    GridFieldText('model', title=_('model'), field_name='content_type__model', editable=False, align='center'),
    GridFieldText('object_pk', title=_('object id'), field_name='object_pk', editable=False, align='center', extra='"formatter":"objectfmt"'),
    GridFieldText('comment', title=_('comment'), width=400, editable=False, align='center'),
    GridFieldText('app', title="app", hidden=True, field_name='content_type__app_label')
    )


class BucketList(GridReport):
  '''
  A list report to show dates.
  '''
  title = _("buckets")
  basequeryset = Bucket.objects.all()
  model = Bucket
  frozenColumns = 1
  help_url = 'user-guide/model-reference/buckets.html'
  rows = (
    #. Translators: Translation included with Django
    GridFieldText('name', title=_('name'), key=True, formatter='detail', extra='"role":"common/bucket"'),
    GridFieldText('description', title=_('description')),
    GridFieldInteger('level', title=_('level')),
    GridFieldText('source', title=_('source')),
    GridFieldLastModified('lastmodified'),
    )


class BucketDetailList(GridReport):
  '''
  A list report to show dates.
  '''
  title = _("bucket dates")
  basequeryset = BucketDetail.objects.all()
  model = BucketDetail
  frozenColumns = 2
  help_url = 'user-guide/model-reference/buckets.html'
  default_sort = (2, 'asc', 1, 'asc')
  rows = (
    GridFieldInteger('id', title=_('identifier'), key=True, hidden=True),
    GridFieldText('bucket', title=_('bucket'), field_name='bucket__name', formatter='detail', extra='"role":"common/bucket"'),
    GridFieldDateTime('startdate', title=_('start date')),
    GridFieldDateTime('enddate', title=_('end date')),
    #. Translators: Translation included with Django
    GridFieldText('name', title=_('name')),
    GridFieldText('source', title=_('source')),
    GridFieldLastModified('lastmodified'),
    )


@staff_member_required
def detail(request, app, model, object_id):
  # Find the object type
  ct = ContentType.objects.get(app_label=app, model=model)
  admn = data_site._registry[ct.model_class()]
  if not hasattr(admn, 'tabs'):
    return HttpResponseNotFound('Object type not found')

  # Find the tab we need to open
  lasttab = request.session.get('lasttab')
  newtab = None
  for tab in admn.tabs:
    if lasttab == tab['name'] or not lasttab:
      perms = tab.get('permissions')
      if perms:
        if isinstance(perms, str):
          # A single permission is given
          if not request.user.has_perm(perms):
            continue
        else:
          # A list or tuple of permissions is given
          ok = True
          for p in perms:
            if not request.user.has_perm(p):
              ok = False
              break
          if not ok:
            continue
      newtab = tab
      break
  if not newtab:
    newtab = admn.tabs[0]

  # Convert a view name into a function when accessed the first time
  viewfunc = newtab.get('viewfunc', None)
  if not viewfunc:
    url = reverse(newtab['view'], args=("dummy",))
    newtab['viewfunc'] = resolve(url).func

  # Open the tab
  return newtab['viewfunc'](request, object_id)


def csrf_failure(request, reason):
  # Redirect to login page
  logger.error("CSRF failure detected")
  return HttpResponseRedirect(request.prefix + "/")
