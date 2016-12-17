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
from datetime import datetime
import logging

from django.conf import settings
from django.contrib.admin.utils import quote
from django.contrib.auth.models import AbstractUser, Group
from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType
from django.core.exceptions import PermissionDenied
from django.core.urlresolvers import NoReverseMatch, reverse
from django.db import models, DEFAULT_DB_ALIAS, connections, transaction
from django.db.models.signals import pre_delete
from django.dispatch.dispatcher import receiver
from django.utils import timezone
from django.utils.translation import ugettext_lazy as _
from django.utils.text import capfirst



logger = logging.getLogger(__name__)


class HierarchyModel(models.Model):
  lft = models.PositiveIntegerField(db_index=True, editable=False, null=True, blank=True)
  rght = models.PositiveIntegerField(null=True, editable=False, blank=True)
  lvl = models.PositiveIntegerField(null=True, editable=False, blank=True)
  # Translators: Translation included with Django
  name = models.CharField(_('name'), max_length=300, primary_key=True,
                          help_text=_('Unique identifier'))
  owner = models.ForeignKey('self', verbose_name=_('owner'), null=True, blank=True,
                            related_name='xchildren', help_text=_('Hierarchical parent'))

  def save(self, *args, **kwargs):
    # Trigger recalculation of the hieracrhy.
    # TODO this triggers the recalculation in too many cases, including a lot
    # of changes which don't require it. Alternative solution is to use the
    # pre-save signal which has more information.
    self.lft = None
    self.rght = None
    self.lvl = None

    # Call the real save() method
    super(HierarchyModel, self).save(*args, **kwargs)

  def delete(self, *args, **kwargs):
    try:
      # Update an arbitrary other object to trigger recalculation of the hierarchy
      obj = self.__class__.objects.using(self._state.db).exclude(pk=self.pk)[0]
      obj.lft = None
      obj.rght = None
      obj.lvl = None
      obj.save(
        update_fields=['lft', 'rght', 'lvl'],
        using=self._state.db
        )
    except:
      # Failure can happen when eg we delete the last record
      pass
    # Call the real delete() method
    super(HierarchyModel, self).delete(*args, **kwargs)

  class Meta:
    abstract = True

  @classmethod
  def rebuildHierarchy(cls, database=DEFAULT_DB_ALIAS):

    # Verify whether we need to rebuild or not.
    # We search for the first record whose lft field is null.
    if len(cls.objects.using(database).filter(lft__isnull=True)[:1]) == 0:
      return

    nodes = {}
    children = {}
    updates = []

    def tagChildren(me, left, level):
      right = left + 1
      # Get all children of this node
      for i in children.get(me, []):
        # Recursive execution of this function for each child of this node
        right = tagChildren(i, right, level + 1)

      # After processing the children of this node now know its left and right values
      updates.append( (left, right, level, me) )

      # Remove from node list (to mark as processed)
      del nodes[me]

      # Return the right value of this node + 1
      return right + 1

    # Load all nodes in memory
    for i in cls.objects.using(database).values('name', 'owner'):
      if i['name'] == i['owner']:
        logging.error("Data error: '%s' points to itself as owner" % i['name'])
        nodes[i['name']] = None
      else:
        nodes[i['name']] = i['owner']
        if i['owner']:
          if not i['owner'] in children:
            children[i['owner']] = set()
          children[i['owner']].add(i['name'])
    keys = sorted(nodes.items())

    # Loop over nodes without parent
    cnt = 1
    for i, j in keys:
      if j is None:
        cnt = tagChildren(i, cnt, 0)

    if nodes:
      # If the nodes dictionary isn't empty, it is an indication of an
      # invalid hierarchy.
      # There are loops in your hierarchy, ie parent-chains not ending
      # at a top-level node without parent.
      bad = nodes.copy()
      updated = True
      while updated:
        updated = False
        for i in bad.keys():
          ok = True
          for j, k in bad.items():
            if k == i:
              ok = False
              break
          if ok:
            # If none of the bad keys points to me as a parent, I am unguilty
            del bad[i]
            updated = True
      logging.error("Data error: Hierarchy loops among %s" % sorted(bad.keys()))
      for i, j in sorted(bad.items()):
        nodes[i] = None

      # Continue loop over nodes without parent
      keys = sorted(nodes.items())
      for i, j in keys:
        if j is None:
          cnt = tagChildren(i, cnt, 0)

    # Write all results to the database
    with transaction.atomic(using=database):
      connections[database].cursor().executemany(
        'update %s set lft=%%s, rght=%%s, lvl=%%s where name = %%s' % connections[database].ops.quote_name(cls._meta.db_table),
        updates
        )


class MultiDBManager(models.Manager):
  def get_queryset(self):
    from freppledb.common.middleware import _thread_locals
    req = getattr(_thread_locals, 'request', None)
    if req:
      return super(MultiDBManager, self).get_queryset().using(getattr(req, 'database', DEFAULT_DB_ALIAS))
    else:
      return super(MultiDBManager, self).get_queryset().using(DEFAULT_DB_ALIAS)


class AuditModel(models.Model):
  '''
  This is an abstract base model.
  It implements the capability to maintain:
    - the date of the last modification of the record.
    - a string intended to describe the source system that supplied the record
  '''
  # Database fields
  source = models.CharField(_('source'), db_index=True, max_length=300, null=True, blank=True)
  lastmodified = models.DateTimeField(_('last modified'), editable=False, db_index=True, default=timezone.now)

  objects = MultiDBManager()  # The default manager.

  def save(self, *args, **kwargs):
    # Update the field with every change
    self.lastmodified = datetime.now()

    # Call the real save() method
    super(AuditModel, self).save(*args, **kwargs)

  class Meta:
    abstract = True


class Parameter(AuditModel):
  # Database fields
  # Translators: Translation included with Django
  name = models.CharField(_('name'), max_length=60, primary_key=True)
  value = models.CharField(_('value'), max_length=1000, null=True, blank=True)
  description = models.CharField(_('description'), max_length=1000, null=True, blank=True)

  def __str__(self):
    return self.name

  class Meta(AuditModel.Meta):
    db_table = 'common_parameter'
    verbose_name = _('parameter')
    verbose_name_plural = _('parameters')

  @staticmethod
  def getValue(key, database=DEFAULT_DB_ALIAS, default=None):
    try:
      return Parameter.objects.using(database).get(pk=key).value
    except:
      return default


class Scenario(models.Model):
  scenarioStatus = (
    ('free', _('free')),
    ('in use', _('in use')),
    ('busy', _('busy')),
  )

  # Database fields
  # Translators: Translation included with Django
  name = models.CharField(_('name'), max_length=300, primary_key=True)
  description = models.CharField(_('description'), max_length=500, null=True, blank=True)
  status = models.CharField(
    _('status'), max_length=10,
    null=False, blank=False, choices=scenarioStatus
    )
  lastrefresh = models.DateTimeField(_('last refreshed'), null=True, editable=False)

  def __str__(self):
    return self.name

  @staticmethod
  def syncWithSettings():
    try:
      # Bring the scenario table in sync with settings.databases
      with transaction.atomic(savepoint=False):
        dbs = [ i for i, j in settings.DATABASES.items() if j['NAME'] ]
        for sc in Scenario.objects.all():
          if sc.name not in dbs:
            sc.delete()
        scs = [sc.name for sc in Scenario.objects.all()]
        for db in dbs:
          if db not in scs:
            if db == DEFAULT_DB_ALIAS:
              Scenario(name=db, status="In use", description='Production').save()
            else:
              Scenario(name=db, status="Free").save()
    except:
      # Failures are acceptable - eg when the default database has not been intialized yet
      pass

  def __lt__ (self, other):
    # Default database is always first in the list
    if self.name == DEFAULT_DB_ALIAS:
      return True
    elif other.name == DEFAULT_DB_ALIAS:
      return False
    # Other databases are sorted by their description
    return (self.description or self.name) < (other.description or other.name)

  class Meta:
    db_table = "common_scenario"
    permissions = (
        ("copy_scenario", "Can copy a scenario"),
        ("release_scenario", "Can release a scenario"),
       )
    verbose_name_plural = _('scenarios')
    verbose_name = _('scenario')
    ordering = ['name']


class Wizard(models.Model):
  # Database fields
  # Translators: Translation included with Django
  name = models.CharField(_('name'), max_length=300, primary_key=True)
  sequenceorder = models.IntegerField(_('progress'), help_text=_('Model completion level'))
  url_doc = models.URLField(_('documentation URL'), max_length=500, null=True, blank=True)
  url_internaldoc = models.URLField(_('wizard URL'), max_length=500, null=True, blank=True)
  owner = models.ForeignKey('self', verbose_name=_('owner'), null=True, blank=True,
                            related_name='xchildren', help_text=_('Hierarchical parent'))
  status = models.BooleanField(blank=True, default=True)

  def __str__(self):
    return self.name

  class Meta:
    db_table = "common_wizard"
    ordering = ['sequenceorder']


class User(AbstractUser):
  languageList = tuple( [ ('auto', _('Detect automatically')), ] + list(settings.LANGUAGES) )
  language = models.CharField(
    _('language'), max_length=10, choices=languageList,
    default='auto'
    )
  theme = models.CharField(
    _('theme'), max_length=20, default=settings.DEFAULT_THEME,
    choices=[ (i, capfirst(i)) for i in settings.THEMES ]
    )
  pagesize = models.PositiveIntegerField(_('page size'), default=settings.DEFAULT_PAGESIZE)
  horizonbuckets = models.CharField(max_length=300, blank=True, null=True)
  horizonstart = models.DateTimeField(blank=True, null=True)
  horizonend = models.DateTimeField(blank=True, null=True)
  horizontype = models.BooleanField(blank=True, default=True)
  horizonlength = models.IntegerField(blank=True, default=6, null=True)
  horizonunit = models.CharField(
    blank=True, max_length=5, default='month', null=True,
    choices=(("day", "day"), ("week", "week"), ("month", "month"))
    )
  lastmodified = models.DateTimeField(
    _('last modified'), auto_now=True, null=True, blank=True,
    editable=False, db_index=True
    )


  def save(self, force_insert=False, force_update=False, using=DEFAULT_DB_ALIAS, update_fields=None):
    '''
    Every change to a user model is saved to all active scenarios.

    The is_superuser and is_active fields can be different in each scenario.
    All other fields are expected to be identical in each database.

    Because of the logic in this method creating users directly in the
    database tables is NOT a good idea!
    '''
    # We want to automatically give access to the django admin to all users
    self.is_staff = True

    scenarios = [ i['name'] for i in Scenario.objects.filter(status='In use').values('name') ]

    # The same id of a new user MUST be identical in all databases.
    # We manipulate the sequences, and correct if required.
    newuser = False
    tmp_is_active = self.is_active
    tmp_is_superuser = self.is_superuser
    if self.id is None:
      newuser = True
      self.id = 0
      cur_seq = {}
      for db in scenarios:
        cursor = connections[db].cursor()
        cursor.execute("select nextval('common_user_id_seq')")
        cur_seq[db] = cursor.fetchone()[0]
        if cur_seq[db] > self.id:
          self.id = cur_seq[db]
      for db in scenarios:
        if cur_seq[db] != self.id:
          cursor = connections[db].cursor()
          cursor.execute("select setval('common_user_id_seq', %s)", [self.id - 1])
      self.is_active = False
      self.is_superuser = False

    # Save only specific fields which we want to have identical across
    # all scenario databases.
    if not update_fields:
      update_fields2 = [
        'username', 'password', 'last_login', 'first_name', 'last_name',
        'email', 'date_joined', 'language', 'theme', 'pagesize',
        'horizonbuckets', 'horizonstart', 'horizonend', 'horizonunit',
        'lastmodified', 'is_staff'
        ]
    else:
      # Important is NOT to save the is_active and is_superuser fields.
      update_fields2 = update_fields[:]  # Copy!
      if 'is_active' in update_fields2:
        update_fields2.remove('is_active')
      if 'is_superuser' in update_fields:
        update_fields2.remove('is_superuser')
    if update_fields2 or newuser:
      for db in scenarios:
        if db == using:
          continue
        try:
          with transaction.atomic(using=db, savepoint=True):
            super(User, self).save(
              force_insert=force_insert,
              force_update=force_update,
              using=db,
              update_fields=update_fields2 if not newuser else None
              )
        except:
          with transaction.atomic(using=db, savepoint=False):
            newuser = True
            self.is_active = False
            self.is_superuser = False
            super(User, self).save(
              force_insert=force_insert,
              force_update=force_update,
              using=db
              )
            if settings.DEFAULT_USER_GROUP:
                  grp = Group.objects.all().using(db).get_or_create(name=settings.DEFAULT_USER_GROUP)[0]
                  self.groups.add(grp.id)

    # Continue with the regular save, as if nothing happened.
    self.is_active = tmp_is_active
    self.is_superuser = tmp_is_superuser
    usr = super(User, self).save(
      force_insert=force_insert,
      force_update=force_update,
      using=using,
      update_fields=update_fields
      )
    if settings.DEFAULT_USER_GROUP and newuser:
      grp = Group.objects.all().using(using).get_or_create(name=settings.DEFAULT_USER_GROUP)[0]
      self.groups.add(grp.id)
    return usr


  def joined_age(self):
    '''
    Returns the number of days since the user joined
    '''
    if self.date_joined.year == 2000:
      # This is the user join date from the demo database.
      # We'll consider that a new user.
      self.date_joined = self.last_login
      self.save()
    return (datetime.now() - self.date_joined).total_seconds() / 86400


  class Meta:
    db_table = "common_user"
    # Translators: Translation included with Django
    verbose_name = _('user')
    # Translators: Translation included with Django
    verbose_name_plural = _('users')


@receiver(pre_delete, sender=User)
def delete_user(sender, instance, **kwargs):
  raise PermissionDenied


class Comment(models.Model):
  id = models.AutoField(_('identifier'), primary_key=True)
  content_type = models.ForeignKey(
    # Translators: Translation included with Django
    ContentType, verbose_name=_('content type'),
    related_name="content_type_set_for_%(class)s"
    )
  # Translators: Translation included with Django
  object_pk = models.TextField(_('object id'))
  content_object = GenericForeignKey(ct_field="content_type", fk_field="object_pk")
  comment = models.TextField(_('comment'), max_length=3000)
  # Translators: Translation included with Django
  user = models.ForeignKey(User, verbose_name=_('user'), blank=True, null=True, editable=False)
  lastmodified = models.DateTimeField(_('last modified'), default=timezone.now, editable=False)

  class Meta:
      db_table = "common_comment"
      ordering = ('id',)
      verbose_name = _('comment')
      verbose_name_plural = _('comments')

  def __str__(self):
      return "%s: %s..." % (self.object_pk, self.comment[:50])

  def get_admin_url(self):
    """
    Returns the admin URL to edit the object represented by this comment.
    """
    if self.content_type and self.object_pk:
      url_name = 'data:%s_%s_change' % (self.content_type.app_label, self.content_type.model)
      try:
        return reverse(url_name, args=(quote(self.object_pk),))
      except NoReverseMatch:
        try:
          url_name = 'admin:%s_%s_change' % (self.content_type.app_label, self.content_type.model)
          return reverse(url_name, args=(quote(self.object_pk),))
        except NoReverseMatch:
          pass
    return None


class Bucket(AuditModel):
  # Create some dummy string for common bucket names to force them to be translated.
  extra_strings = ( _('day'), _('week'), _('month'), _('quarter'), _('year') )

  # Database fields
  # Translators: Translation included with Django
  name = models.CharField(_('name'), max_length=300, primary_key=True)
  description = models.CharField(_('description'), max_length=500, null=True, blank=True)
  level = models.IntegerField(_('level'), help_text=_('Higher values indicate more granular time buckets'))

  def __str__(self):
    return str(self.name)

  class Meta:
    verbose_name = _('bucket')
    verbose_name_plural = _('buckets')
    db_table = 'common_bucket'


class BucketDetail(AuditModel):
  # Database fields
  id = models.AutoField(_('identifier'), primary_key=True)
  bucket = models.ForeignKey(Bucket, verbose_name=_('bucket'), db_index=True)
  # Translators: Translation included with Django
  name = models.CharField(_('name'), max_length=300, db_index=True)
  startdate = models.DateTimeField(_('start date'))
  enddate = models.DateTimeField(_('end date'))

  def __str__(self):
    return "%s %s" % (self.bucket.name or "", self.startdate)

  class Meta:
    verbose_name = _('bucket date')
    verbose_name_plural = _('bucket dates')
    db_table = 'common_bucketdetail'
    unique_together = (('bucket', 'startdate'),)
    ordering = ['bucket', 'startdate']
