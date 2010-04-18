#
# Copyright (C) 2007-2010 by Johan De Taeye
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
# Foundation Inc., 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301 USA
#

# file : $URL$
# revision : $LastChangedRevision$  $LastChangedBy$
# date : $LastChangedDate$

from datetime import timedelta, datetime

from django.db import models
from django.contrib.auth.models import User
from django.dispatch import dispatcher
from django.db.models import signals
from django.utils.translation import ugettext_lazy as _
from django.conf import settings

from input.models import Parameter


class Preferences(models.Model):
  buckettype = (
    ('standard',_('Standard')),
    ('day',_('Day')),
    ('week',_('Week')),
    ('month',_('Month')),
    ('quarter',_('Quarter')),
    ('year',_('Year')),
  )
  csvOutputType = (
    ('table',_('Table')),
    ('list',_('List')),
  )
  csvDelimiter = (
    ('comma',_('comma ","')),
    ('semicolon',_('semicolon ";"')),
  )
  languageList = tuple( [ ('auto',_('Detect automatically')), ] + list(settings.LANGUAGES) )
  user = models.ForeignKey(User, verbose_name=_('user'), unique=True)
  buckets = models.CharField(_('buckets'), max_length=10, choices=buckettype,
    default='standard')
  startdate = models.DateField(_('startdate'), blank=True, null=True)
  enddate = models.DateField(_('enddate'), blank=True, null=True)
  csvdelimiter = models.CharField(_('CSV delimiter'), max_length=10, choices=csvDelimiter,
    default='comma')
  language = models.CharField(_('language'), max_length=10, choices=csvDelimiter,
    default='auto')
  lastmodified = models.DateTimeField(_('last modified'), auto_now=True, editable=False, db_index=True)


def CreatePreferenceModel(instance, **kwargs):
  '''Create a preference model for a new user.'''
  pref, created = Preferences.objects.get_or_create(user=instance)
  if created:
    try:
      pref.startdate = datetime.strptime(Parameter.objects.get(name="currentdate").value, "%Y-%m-%d %H:%M:%S").date()
    except: 
      pref.startdate = datetime.now().date()
    pref.enddate = pref.startdate + timedelta(365)
    pref.save()

# This signal will make sure a preference model is created when a user is added.
# The preference model is automatically deleted again when the user is deleted.
signals.post_save.connect(CreatePreferenceModel, sender=User)
