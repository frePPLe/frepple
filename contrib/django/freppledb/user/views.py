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
# email : jdetaeye@users.sourceforge.net

from django.shortcuts import render_to_response
from django.contrib.auth.decorators import login_required
from django.template import RequestContext
from django import newforms as forms
from freppledb.user.models import Preferences

class PreferencesForm(forms.Form):
  buckets = forms.ChoiceField(initial='Month', choices=Preferences.buckettype, help_text="Default bucket size for reports")
  startdate = forms.DateField(required=False,
    help_text="Start date for filtering report data",
    widget=forms.TextInput(attrs={'class':"vDateField"}),
    )
  enddate = forms.DateField(required=False,
    help_text="End date for filtering report data",
    widget=forms.TextInput(attrs={'class':"vDateField"}),
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
        pref.save()
        request.user.message_set.create(message='Successfully updated preferences')
      except:
        request.user.message_set.create(message='Failure updating preferences')
  else:
    pref = request.user.get_profile()
    form = PreferencesForm({'buckets': pref.buckets, 'startdate': pref.startdate, 'enddate': pref.enddate})
  return render_to_response('user/preferences.html', {
     'title': 'Edit my preferences',
     'form': form,
     'reset_crumbs': True,
     },
     context_instance=RequestContext(request))