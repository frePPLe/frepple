#
# Copyright (C) 2007-2012 by Johan De Taeye, frePPLe bvba
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

# file : $URL$
# revision : $LastChangedRevision$  $LastChangedBy$
# date : $LastChangedDate$

from datetime import timedelta, datetime

from django.db import models, DEFAULT_DB_ALIAS, connections, transaction
from django.contrib.auth.models import User
from django.contrib.contenttypes import generic
from django.contrib.contenttypes.models import ContentType
from django.db.models import signals
from django.utils.translation import ugettext_lazy as _
from django.conf import settings 


class HierarchyModel(models.Model):
  lft = models.PositiveIntegerField(db_index = True, editable=False, null=True, blank=True)
  rght = models.PositiveIntegerField(null=True, editable=False, blank=True)
  level = models.PositiveIntegerField(null=True, editable=False, blank=True)
  name = models.CharField(_('name'), max_length=settings.NAMESIZE, primary_key=True,
    help_text=_('Unique identifier'))
  owner = models.ForeignKey('self', verbose_name=_('owner'), null=True, blank=True, related_name='xchildren',
    help_text=_('Hierarchical parent'))

  def save(self, *args, **kwargs):
    # Trigger recalculation of the hieracrhy
    self.lft = None
    self.rght = None
    self.level = None

    # Call the real save() method
    super(HierarchyModel, self).save(*args, **kwargs)

  class Meta:
    abstract = True

  @classmethod
  def rebuildHierarchy(cls, database = DEFAULT_DB_ALIAS):

    # Verify whether we need to rebuild or not.
    # We search for the first record whose lft field is null.
    if len(cls.objects.using(database).filter(lft__isnull=True)[:1]) == 0:
      return

    tmp_debug = settings.DEBUG
    settings.DEBUG = False
    nodes = {}
    transaction.enter_transaction_management(using=database)
    transaction.managed(True, using=database)
    cursor = connections[database].cursor()

    def tagChildren(me, left, level):
      right = left + 1
      # get all children of this node
      for i, j in keys:
        if j == me:
          # Recursive execution of this function for each child of this node
          right = tagChildren(i, right, level + 1)

      # After processing the children of this node now know its left and right values
      cursor.execute(
        'update %s set lft=%d, rght=%d, level=%d where name = %%s' % (cls._meta.db_table, left, right, level),
        [me]
        )

      # Return the right value of this node + 1
      return right + 1

    # Load all nodes in memory
    for i in cls.objects.using(database).values('name','owner'):
      nodes[i['name']] = i['owner']
    keys = sorted(nodes.items())

    # Loop over nodes without parent
    cnt = 1
    for i, j in keys:
      if j == None:
        cnt = tagChildren(i,cnt,0)
    transaction.commit(using=database)
    settings.DEBUG = tmp_debug
    transaction.leave_transaction_management(using=database)


class AuditModel(models.Model):
  '''
  This is an abstract base model.
  It implements the capability to maintain the date of the last modification of the record.
  '''
  # Database fields
  lastmodified = models.DateTimeField(_('last modified'), editable=False, db_index=True, default=datetime.now())

  def save(self, *args, **kwargs):
    # Update the field with every change
    self.lastmodified = datetime.now()

    # Call the real save() method
    super(AuditModel, self).save(*args, **kwargs)

  class Meta:
    abstract = True
    
    
class Parameter(AuditModel):
  # Database fields
  name = models.CharField(_('name'), max_length=settings.NAMESIZE, primary_key=True)
  value = models.CharField(_('value'), max_length=settings.NAMESIZE, null=True, blank=True)
  description = models.CharField(_('description'), max_length=settings.DESCRIPTIONSIZE, null=True, blank=True)

  def __unicode__(self): return self.name

  class Meta(AuditModel.Meta):
    db_table = 'common_parameter'
    verbose_name = _('parameter')
    verbose_name_plural = _('parameters')

    
# TODO The bucket preference is not really generic. Different models could
#      have separate bucket definitions.
class Preferences(models.Model):
  csvOutputType = (
    ('table',_('Table')),
    ('list',_('List')),
  )
  languageList = tuple( [ ('auto',_('Detect automatically')), ] + list(settings.LANGUAGES) )
  user = models.ForeignKey(User, verbose_name=_('user'), primary_key=True)
  buckets = models.CharField(_('buckets'), max_length=settings.NAMESIZE, blank=True, null=True)
  startdate = models.DateTimeField(_('start date'), blank=True, null=True)
  enddate = models.DateTimeField(_('end date'), blank=True, null=True)
  language = models.CharField(_('language'), max_length=10, choices=languageList,
    default='auto')
  theme = models.CharField(_('theme'), max_length=20, default=settings.DEFAULT_THEME, 
    choices=settings.THEMES)
  pagesize = models.PositiveIntegerField(_('page size'), default=settings.DEFAULT_PAGESIZE)
  lastmodified = models.DateTimeField(_('last modified'), auto_now=True, editable=False, db_index=True)

  class Meta:
      db_table = "common_preference"


def CreatePreferenceModel(instance, **kwargs):
  '''Create a preference model for a new user.'''
  pref, created = Preferences.objects.get_or_create(user=instance)
  if created:
    try:
      pref.startdate = datetime.strptime(Parameter.objects.get(name="currentdate").value, "%Y-%m-%d %H:%M:%S")
    except:
      pref.startdate = datetime.now()
    pref.enddate = pref.startdate + timedelta(365)
    pref.save()

# This signal will make sure a preference model is created when a user is added.
# The preference model is automatically deleted again when the user is deleted.
signals.post_save.connect(CreatePreferenceModel, sender=User)


class Comment(models.Model):
  id = models.AutoField(_('identifier'), primary_key=True)
  content_type = models.ForeignKey(ContentType,
          verbose_name=_('content type'),
          related_name="content_type_set_for_%(class)s")
  object_pk = models.TextField(_('object ID'))
  content_object = generic.GenericForeignKey(ct_field="content_type", fk_field="object_pk")
  comment = models.TextField(_('comment'), max_length=settings.COMMENT_MAX_LENGTH)
  user = models.ForeignKey(User, verbose_name=_('user'), blank=True, null=True, editable=False)
  lastmodified = models.DateTimeField(_('last modified'), default=datetime.now(), editable=False)
  
  class Meta:
      db_table = "common_comment"
      ordering = ('id',)
      verbose_name = _('comment')
      verbose_name_plural = _('comments')

  def __unicode__(self):
      return "%s: %s..." % (self.object_pk, self.comment[:50])


class Bucket(AuditModel):
  # Create some dummy string for common bucket names to force them to be translated.
  extra_strings = ( _('day'), _('week'), _('month'), _('quarter'), _('year'), _('telescope') )

  # Database fields
  name = models.CharField(_('name'), max_length=settings.NAMESIZE, primary_key=True)
  description = models.CharField(_('description'), max_length=settings.DESCRIPTIONSIZE, null=True, blank=True)

  def __unicode__(self): return str(self.name)

  class Meta:
    verbose_name = _('bucket')
    verbose_name_plural = _('buckets')
    db_table = 'common_bucket'


class BucketDetail(AuditModel):
  # Database fields
  id = models.AutoField(_('identifier'), primary_key=True)
  bucket = models.ForeignKey(Bucket, verbose_name=_('bucket'), db_index=True)
  name = models.CharField(_('name'), max_length=settings.NAMESIZE)
  startdate = models.DateTimeField(_('start date'))
  enddate = models.DateTimeField(_('end date'))

  def __unicode__(self): return u"%s %s" % (self.bucket.name or "", self.startdate)

  class Meta:
    verbose_name = _('bucket date')
    verbose_name_plural = _('bucket dates')
    db_table = 'common_bucketdetail'
    unique_together = (('bucket', 'startdate'),)
    ordering = ['bucket','startdate']

