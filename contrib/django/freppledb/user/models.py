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

from django.db import models
from django.contrib.auth.models import User
from django.dispatch import dispatcher
from django.db.models import signals
from datetime import date

from freppledb.input.models import Plan


class Preferences(models.Model):
    buckettype = (
      ('default','Default'),
      ('day','Day'),
      ('week','Week'),
      ('month','Month'),
      ('quarter','Quarter'),
      ('year','Year'),
    )
    user = models.ForeignKey(User, unique=True, edit_inline=models.TABULAR,
      num_in_admin=1,min_num_in_admin=1, max_num_in_admin=1, num_extra_on_change=0)
    buckets = models.CharField(maxlength=10, choices=buckettype, default='default')
    startdate = models.DateField(blank=True, null=True)
    enddate = models.DateField(blank=True, null=True)
    dummy = models.SmallIntegerField(editable=False, core=True, default=1)


def CreatePreferenceModel(instance):
    '''Create a preference model for a new user.'''
    pref, created = Preferences.objects.get_or_create(user=instance)
    if created:
      try: pref.startdate = Plan.objects.all()[0].currentdate.date()
      except: pass  # No real problem when this fails
      pref.save()

# This signal will make sure a preference model is created when a user is added.
# The preference model is automatically deleted again when the user is deleted.
dispatcher.connect(CreatePreferenceModel, signal=signals.post_save, sender=User)
