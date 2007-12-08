#
# Copyright (C) 2007 by Johan De Taeye
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
# Foundation Inc., 59 Temple Place, Suite 330, Boston, MA 02111-1307, USA
#

# file : $URL$
# revision : $LastChangedRevision$  $LastChangedBy$
# date : $LastChangedDate$

from django.shortcuts import render_to_response
from django.contrib.auth.decorators import login_required
from django.template import RequestContext
from django import newforms as forms
from django.utils.translation import ugettext_lazy as _

from user.models import Preferences


class PreferencesForm(forms.Form):
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
  csvformat = forms.ChoiceField(label = _("CSV output format"),
    initial = _('Table'),
    choices=Preferences.csvOutputType,
    help_text = _("Exporting CSV data as a table or a list"),
    )

@login_required
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
        pref.csvformat = newdata['csvformat']
        pref.save()
        request.user.message_set.create(message='Successfully updated preferences')
      except:
        request.user.message_set.create(message='Failure updating preferences')
  else:
    pref = request.user.get_profile()
    form = PreferencesForm({
      'buckets': pref.buckets,
      'startdate': pref.startdate,
      'enddate': pref.enddate,
      'csvformat': pref.csvformat
      })
  return render_to_response('user/preferences.html', {
     'title': _('Edit my preferences'),
     'form': form,
     'reset_crumbs': True,
     },
     context_instance=RequestContext(request))