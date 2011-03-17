#
# Copyright (C) 2007-2010 by Johan De Taeye, frePPLe bvba
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

from freppledb.common.models import Preferences
from freppledb.common.report import ListReport, FilterText, FilterBool

from django.contrib.auth.models import User, Group


class PreferencesForm(forms.Form):
  language = forms.ChoiceField(label = _("Language"),
    initial="auto",
    choices=Preferences.languageList,
    help_text=_("Language of the user interface"),
    )
  buckets = forms.ChoiceField(label = _("Buckets"),
    initial=_('Default'),
    choices=Preferences.buckettype,
    help_text=_("Bucket size for reports"),
    )
  startdate = forms.DateField(label = _("Report start date"),
    required=False,
    help_text=_("Start date for filtering report data"),
    widget=forms.TextInput(attrs={'class':"vDateField"}),
    )
  enddate = forms.DateField(label = _("Report end date"),
    required=False,
    help_text=_("End date for filtering report data"),
    widget=forms.TextInput(attrs={'class':"vDateField"}),
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
        pref.save()
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
      })
  return render_to_response('common/preferences.html', {
     'title': _('Edit my preferences'),
     'form': form,
     'reset_crumbs': True,
     },
     context_instance=RequestContext(request))


class UserList(ListReport):
  '''
  A list report to show users.
  '''
  template = 'auth/userlist.html'
  title = _("User List")
  basequeryset = User.objects.all()
  model = User
  frozenColumns = 1

  rows = (
    ('username', {
      'title': _('username'),
      'filter': FilterText(),
      }),
    ('email', {
      'title': _('E-mail'),
      'filter': FilterText(),
      }),
    ('first_name', {
      'title': _('first name'),
      'filter': FilterText(),
      }),
    ('last_name', {
      'title': _('last name'),
      'filter': FilterText(),
      }),
    ('is_staff', {
      'title': _('staff status'),
      'filter': FilterBool(),
      }),
    )


class GroupList(ListReport):
  '''
  A list report to show groups.
  '''
  template = 'auth/grouplist.html'
  title = _("Group List")
  basequeryset = Group.objects.all()
  model = Group
  frozenColumns = 0

  rows = (
    ('name', {
      'title': _('name'),
      'filter': FilterText(),
      }),
    )
