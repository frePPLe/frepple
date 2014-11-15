#
# Copyright (C) 2007-2013 by Johan De Taeye, frePPLe bvba
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
from django.db import models, transaction, DEFAULT_DB_ALIAS
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.utils.translation import ugettext_lazy as _
from django.conf import settings

from freppledb.common.models import User

import logging
logger = logging.getLogger(__name__)


class Task(models.Model):
  '''
  Expected status values are:
    - 'Waiting'
    - 'Done'
    - 'Failed'
    - 'Canceled'
    - 'DD%', where DD represents the percentage completed
  Other values are okay, but the above have translations.
  '''
  # Database fields
  id = models.AutoField(_('identifier'), primary_key=True, editable=False)
  name = models.CharField(_('name'), max_length=20, db_index=True, editable=False)
  submitted = models.DateTimeField(_('submitted'), editable=False)
  started = models.DateTimeField(_('started'), blank=True, null=True, editable=False)
  finished = models.DateTimeField(_('submitted'), blank=True, null=True, editable=False)
  arguments = models.TextField(_('arguments'), max_length=200, null=True, editable=False)
  status = models.CharField(_('status'), max_length=20, editable=False)
  message = models.TextField(_('message'), max_length=200, null=True, editable=False)
  user = models.ForeignKey(User, verbose_name=_('user'), blank=True, null=True, editable=False)

  def __str__(self):
    return "%s - %s - %s" % (self.id, self.name, self.status)

  class Meta:
    db_table = "execute_log"
    verbose_name_plural = _('tasks')
    verbose_name = _('task')

  @staticmethod
  def submitTask():
    # Add record to the database
    # Check if a worker is present. If not launch one.
    return 1


class Scenario(models.Model):
  scenarioStatus = (
    ('free', _('Free')),
    ('in use', _('In use')),
    ('busy', _('Busy')),
  )

  # Database fields
  name = models.CharField(_('name'), max_length=settings.NAMESIZE, primary_key=True)
  description = models.CharField(_('description'), max_length=settings.DESCRIPTIONSIZE, null=True, blank=True)
  status = models.CharField(
    _('status'), max_length=10,
    null=False, blank=False, choices=scenarioStatus
    )
  lastrefresh = models.DateTimeField(_('last refreshed'), null=True, editable=False)

  def __str__(self):
    return self.name

  @staticmethod
  def syncWithSettings():
    ac = transaction.get_autocommit()
    transaction.set_autocommit(False)
    try:
      # Bring the scenario table in sync with settings.databases
      dbs = [ i for i, j in settings.DATABASES.items() if j['NAME'] ]
      for sc in Scenario.objects.all():
        if sc.name not in dbs:
          sc.delete()
      scs = [sc.name for sc in Scenario.objects.all()]
      for db in dbs:
        if db not in scs:
          if db == DEFAULT_DB_ALIAS:
            Scenario(name=db, status="In use", description='Production database').save()
          else:
            Scenario(name=db, status="Free").save()
      transaction.commit()
    except Exception as e:
      logger.error("Error synchronizing the scenario table with the settings: %s" % e)
      transaction.rollback()
    finally:
      transaction.set_autocommit(ac)

  class Meta:
    db_table = "execute_scenario"
    permissions = (
        ("copy_scenario", "Can copy a scenario"),
        ("release_scenario", "Can release a scenario"),
       )
    verbose_name_plural = _('scenarios')
    verbose_name = _('scenario')
    ordering = ['name']


@receiver(post_save, sender=User)
def sync_handler(sender, **kwargs):
  if not kwargs.get('created', False) or kwargs.get('using', DEFAULT_DB_ALIAS) != DEFAULT_DB_ALIAS:
    return
  # A new user is created in the default database.
  # We create the same user in all scenarios that are in use. Otherwise the user can't create
  # comments or edit objects in these what-if scenarios.
  for sc in Scenario.objects.all().filter(status='In use'):
    kwargs['instance'].save(using=sc.name)
