#
# Copyright (C) 2007-2011 by Johan De Taeye, frePPLe bvba
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
from django.db.models import signals
from django.utils.translation import ugettext_lazy as _
from django.conf import settings

from freppledb.input.models import Parameter


# TODO The bucket preference is not really generic. Different models could
#      have seperate bucket definitions.
class Preferences(models.Model):
  csvOutputType = (
    ('table',_('Table')),
    ('list',_('List')),
  )
  languageList = tuple( [ ('auto',_('Detect automatically')), ] + list(settings.LANGUAGES) )
  user = models.ForeignKey(User, verbose_name=_('user'), primary_key=True)
  buckets = models.CharField(_('buckets'), max_length=settings.NAMESIZE, blank=True, null=True)
  startdate = models.DateField(_('start date'), blank=True, null=True)
  enddate = models.DateField(_('end date'), blank=True, null=True)
  language = models.CharField(_('language'), max_length=10, choices=languageList,
    default='auto')
  theme = models.CharField(_('theme'), max_length=10, default=settings.DEFAULT_THEME, 
    choices=settings.THEMES)
  pagesize = models.PositiveIntegerField(_('page size'), default=settings.DEFAULT_PAGESIZE)
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
