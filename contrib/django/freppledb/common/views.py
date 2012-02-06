#
# Copyright (C) 2007-2012 by Johan De Taeye, frePPLe bvba
#
# This library is free software; you can redistribute it and/or modify it
# under the terms of the GNU Lesser General Public License as published
# by the Free Software Foundation; either version 2.1 of the License, or
# (at your option) any later version.
#
# This library is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU Lesser
# General Public License for more details.
#
# You should have received a copy of the GNU Lesser General Public
# License along with this library; if not, write to the Free Software
# Foundation Inc., 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301, USA
#

# file : $URL$
# revision : $LastChangedRevision$  $LastChangedBy$
# date : $LastChangedDate$

from django.shortcuts import render_to_response
from django.views.decorators.csrf import csrf_protect
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.template import RequestContext
from django import forms
from django.utils.encoding import force_unicode
from django.utils.translation import ugettext_lazy as _
from django.contrib.auth.models import User, Group
from django.contrib.admin.models import LogEntry
from django.contrib.syndication.views import Feed
from django.utils import translation
from django.conf import settings

from freppledb.common.models import Preferences
from freppledb.common.report import GridReport, GridFieldText, GridFieldBool, GridFieldInteger
from freppledb.input.models import Bucket


class PreferencesForm(forms.Form):
  language = forms.ChoiceField(label = _("language"),
    initial="auto",
    choices=Preferences.languageList,
    help_text=_("Language of the user interface"),
    )
  buckets = forms.ModelChoiceField(queryset=Bucket.objects.all().values_list('name', flat=True),
    label=_("Buckets"),
    required=False,
    help_text=_("Time bucket size for reports"),
    )
  startdate = forms.DateField(label = _("report start date"),
    required=False,
    help_text=_("Start date for filtering report data"),
    widget=forms.TextInput(attrs={'class':"vDateField"}),
    )
  enddate = forms.DateField(label = _("report end date"),
    required=False,
    help_text=_("End date for filtering report data"),
    widget=forms.TextInput(attrs={'class':"vDateField"}),
    )
  pagesize = forms.IntegerField(label = _('page size'),
    required=False,
    initial=100,
    min_value=25,
    help_text = _('Number of records to fetch in a single page from the server'),                            
    )
  theme = forms.ChoiceField(label = _('theme'),
    required=False,
    choices=settings.THEMES,
    help_text=_('Theme for the user interface'),
    )

@login_required
@csrf_protect
def preferences(request):
  if request.method == 'POST':
    form = PreferencesForm(request.POST)
    if form.is_valid():
      try:
        pref = Preferences.objects.get(user=request.user)
        newdata = form.cleaned_data
        pref.buckets = newdata['buckets']
        pref.startdate = newdata['startdate']
        pref.enddate = newdata['enddate']
        pref.language = newdata['language']
        pref.theme = newdata['theme']
        pref.pagesize = newdata['pagesize']
        pref.save()
        # Switch to the new theme and language immediately
        request.theme = newdata['theme']
        if translation.get_language() != newdata['language']:
          translation.activate(newdata['language'])
          request.LANGUAGE_CODE = translation.get_language()
        messages.add_message(request, messages.INFO, force_unicode(_('Successfully updated preferences')))
      except:
        messages.add_message(request, messages.ERROR, force_unicode(_('Failure updating preferences')))
  else:
    pref = request.user.get_profile()
    form = PreferencesForm({
      'buckets': pref.buckets,
      'startdate': pref.startdate,
      'enddate': pref.enddate,
      'language': pref.language,
      'theme': pref.theme,
      'pagesize': pref.pagesize,
      })
  return render_to_response('common/preferences.html', {
     'title': _('Edit my preferences'),
     'form': form,
     },
     context_instance=RequestContext(request))


class UserList(GridReport):
  '''
  A list report to show users.
  '''
  template = 'auth/userlist.html'
  title = _("User List")
  basequeryset = User.objects.all()
  model = User
  frozenColumns = 1

  rows = (
    GridFieldInteger('id', title=_('identifier'), key=True, formatter='user'),          
    GridFieldText('username', title=_('username')),          
    GridFieldText('email', title=_('E-mail'), formatter='email', width=200),          
    GridFieldText('first_name', title=_('first_name')),          
    GridFieldText('last_name', title=_('last name')),          
    GridFieldBool('is_staff', title=_('staff status')),          
    )


class GroupList(GridReport):
  '''
  A list report to show groups.
  '''
  template = 'auth/grouplist.html'
  title = _("Group List")
  basequeryset = Group.objects.all()
  model = Group
  frozenColumns = 0
  rows = (
    GridFieldInteger('id', title=_('identifier'), key=True, formatter='group'),          
    GridFieldText('name', title=_('name'), key=True, width=200),          
    )

 
class RSSFeed(Feed):
  title = _("frePPLe recent changes")

  def __call__(self, request, *args, **kwargs):
    # HTTP auth check inspired by http://djangosnippets.org/snippets/243/
    self.link = "%s/rss/" % request.prefix
    self.request = request
    return super(RSSFeed, self).__call__(request, *args, **kwargs)

  def items(self):
    return LogEntry.objects.all().using(self.request.database).order_by('-action_time')[:50]

  def item_title(self, action):
    if action.is_addition():
      return _("Added %(name)s \"%(object)s\".") % {'name': action.content_type.name, 'object': action.object_repr}
    elif action.is_change():
      return _("Changed %(name)s \"%(object)s\".") % {'name': action.content_type.name, 'object': action.object_repr}
    elif action.is_deletion():
      return _("Deleted %(name)s \"%(object)s\".") % {'name': action.content_type.name, 'object': action.object_repr}

  def author_name(self, action):
    if action and action.user:
      return action.user.get_full_name
    else:
      return ''

  def item_categories(self, action):
    return ( action.content_type.name, )

  def item_pubdate(self, action):
    return action.action_time

  def item_description(self, action):
    return action.change_message
    
  def item_link(self, action):
    if action.is_deletion(): return ''
    return action.get_admin_url() and ("%s/admin/%s" % (self.request.prefix, action.get_admin_url())) or ''
