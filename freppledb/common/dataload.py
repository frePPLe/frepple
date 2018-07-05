#
# Copyright (C) 2017 by frePPLe bvba
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

from datetime import timedelta, datetime
from decimal import Decimal
from logging import INFO, ERROR, WARNING, DEBUG

from django import forms
from django.contrib.admin.models import LogEntry, CHANGE, ADDITION
from django.contrib.contenttypes.models import ContentType
from django.core.validators import EMPTY_VALUES
from django.db import DEFAULT_DB_ALIAS
from django.db.models.fields import IntegerField, AutoField, DurationField, BooleanField, DecimalField
from django.db.models.fields import DateField, DateTimeField, TimeField, CharField, NOT_PROVIDED
from django.db.models.fields.related import RelatedField
from django.forms.models import modelform_factory
from django.utils import translation
from django.utils.translation import ugettext_lazy as _
from django.utils.encoding import force_text
from django.utils.text import get_text_list


def parseExcelWorksheet(model, data, user=None, database=DEFAULT_DB_ALIAS, ping=False):

  class MappedRow:
    '''
    A row of data is made to behave as a dictionary.
    For instance the following data:
       headers: ['field1', 'field2', 'field3']
       data: [val1, val2, val3]
    behaves like:
      {'field1': val1, 'field2': val2, 'field3': val3}
    but it's faster because we don't actually build the dictionary.
    '''
    def __init__(self, headers=[]):
      self.headers = {}
      self.data = []
      colnum = 0
      self.numHeaders = 0
      for col in headers:
        if col:
          self.headers[col.name] = (colnum, col)
          self.numHeaders += 1
        colnum += 1

    def setData(self, data):
      self.data = data

    def empty(self):
      for i in self.data:
        if i.value:
          return False
      return True

    def __getitem__(self, key):
      tmp = self.headers.get(key)
      if tmp:
        idx = tmp[0]
        field = tmp[1]
      else:
        idx = None
        field = None
      data = self.data[idx].value if idx is not None and idx < len(self.data) else None
      if isinstance(field, (IntegerField, AutoField)):
        if isinstance(data, (Decimal, float, int)):
          data = int(data)
      elif isinstance(field, DecimalField):
        if isinstance(data, (Decimal, float)):
          data = round(data, 8)
      elif isinstance(field, DurationField):
        if isinstance(data, float):
          data = "%.6f" % data
        else:
          data = str(data) if data is not None else None
      elif isinstance(field, (DateField, DateTimeField)) and isinstance(data, datetime):
        # Rounding to second
        if data.microsecond < 500000:
          data = data.replace(microsecond=0)
        else:
          data = data.replace(microsecond=0) + timedelta(seconds=1)
      elif isinstance(field, TimeField) and isinstance(data, datetime):
        data = "%s:%s:%s" % (data.hour, data.minute, data.second)
      elif isinstance(field, RelatedField) and not isinstance(data, str) and isinstance(field.target_field, CharField) and data is not None:
        data = str(data)
      elif isinstance(data, str):
        data = data.strip()
      return data

    def get(self, key, default=NOT_PROVIDED):
      try:
        return self.__getitem__(key)
      except KeyError as e:
        if default != NOT_PROVIDED:
          return default
        raise e

    def __len__(self):
      return self.numHeaders

    def __contains__(self, key):
      return key in self.headers

    def has_key(self, key):
      return key in self.headers

    def keys(self):
      return self.headers.keys()

    def values(self):
      return [ i.value for i in self.data ]

    def items(self):
      return { col: self.__getitem__(col) for col in self.headers.keys() }

    __setitem__ = None
    __delitem__ = None


  if hasattr(model, 'parseData'):
    # Some models have their own special uploading logic
    return model.parseData(data, MappedRow, user, database, ping)
  else:
    return _parseData(model, data, MappedRow, user, database, ping)


def parseCSVdata(model, data, user=None, database=DEFAULT_DB_ALIAS, ping=False):
  '''
  This method:
    - reads CSV data from an input iterator
    - creates or updates the database records
    - yields a list of data validation errors

  The data must follow the following format:
    - the first row contains a header, listing all field names
    - a first character # marks a comment line
    - empty rows are skipped
  '''

  class MappedRow:
    '''
    A row of data is made to behave as a dictionary.
    For instance the following data:
       headers: ['field1', 'field2', 'field3']
       data: [val1, val2, val3]
    behaves like:
      {'field1': val1, 'field2': val2, 'field3': val3}
    but it's faster because we don't actually build the dictionary.
    '''
    def __init__(self, headers=[]):
      self.headers = {}
      self.data = []
      colnum = 0
      self.numHeaders = 0
      for col in headers:
        if col:
          self.headers[col.name] = (colnum, col)
          self.numHeaders += 1
        colnum += 1

    def setData(self, data):
      self.data = data

    def empty(self):
      for i in self.data:
        if i:
          return False
      return True

    def __getitem__(self, key):
      try:
        idx = self.headers.get(key)
        if idx is None or idx[0] >= len(self.data):
          return None
        val = self.data[idx[0]]
        if isinstance(idx[1], BooleanField) and val == '0':
          # Argh... bool('0') returns True.
          return False
        else:
          return val
      except KeyError as e:
        raise e

    def get(self, key, default=NOT_PROVIDED):
      try:
        return self.__getitem__(key)
      except KeyError as e:
        if default != NOT_PROVIDED:
          return default
        raise e

    def __len__(self):
      return self.numHeaders

    def __contains__(self, key):
      return key in self.headers

    def has_key(self, key):
      return key in self.headers

    def keys(self):
      return self.headers.keys()

    def values(self):
      return self.data

    def items(self):
      return { col: self.data[idx[0]] for col, idx in self.headers.items() }

    __setitem__ = None
    __delitem__ = None

  if hasattr(model, 'parseData'):
    # Some models have their own special uploading logic
    return model.parseData(data, MappedRow, user, database, ping)
  else:
    return _parseData(model, data, MappedRow, user, database, ping)


def _parseData(model, data, rowmapper, user, database, ping):

  selfReferencing = []

  def formfieldCallback(f):
    #global selfReferencing
    if isinstance(f, RelatedField):
      tmp = BulkForeignKeyFormField(field=f, using=database)
      if f.remote_field.model == model:
        selfReferencing.append(tmp)
      return tmp
    else:
      return f.formfield(localize=True)

  # Initialize
  headers = []
  rownumber = 0
  pingcounter = 0
  changed = 0
  added = 0
  content_type_id = ContentType.objects.get_for_model(model).pk
  admin_log = []

  errors = 0
  warnings = 0
  has_pk_field = False
  rowWrapper = rowmapper()
  for row in data:

    rownumber += 1
    rowWrapper.setData(row)

    # Case 1: The first line is read as a header line
    if rownumber == 1:

      # Collect required fields
      required_fields = set()
      for i in model._meta.fields:
        if not i.blank and i.default == NOT_PROVIDED and not isinstance(i, AutoField):
          required_fields.add(i.name)

      # Validate all columns
      for col in rowWrapper.values():
        col = str(col).strip().strip('#').lower() if col else ""
        if col == "":
          headers.append(None)
          continue
        ok = False
        for i in model._meta.fields:
          # Try with translated field names
          if col == i.name.lower() \
            or col == i.verbose_name.lower() \
            or col == ("%s - %s" % (model.__name__, i.verbose_name)).lower():
              if i.editable is True:
                headers.append(i)
              else:
                headers.append(None)
              required_fields.discard(i.name)
              ok = True
              break
          if translation.get_language() != 'en':
            # Try with English field names
            with translation.override('en'):
              if col == i.name.lower() \
                or col == i.verbose_name.lower() \
                or col == ("%s - %s" % (model.__name__, i.verbose_name)).lower():
                  if i.editable is True:
                    headers.append(i)
                  else:
                    headers.append(None)
                  required_fields.discard(i.name)
                  ok = True
                  break
        if not ok:
          headers.append(None)
          warnings += 1
          yield (
            WARNING, None, None, None,
            force_text(_('Skipping unknown field %(column)s' % {'column': col}))
            )
        if col == model._meta.pk.name.lower() or \
           col == model._meta.pk.verbose_name.lower():
          has_pk_field = True
      if required_fields:
        # We are missing some required fields
        errors += 1
        #. Translators: Translation included with django
        yield (
          ERROR, None, None, None,
          force_text(_('Some keys were missing: %(keys)s' % {'keys': ', '.join(required_fields)}))
          )
      # Abort when there are errors
      if errors:
        raise NameError("Can't proceed")

      # Create a form class that will be used to validate the data
      fields = [i.name for i in headers if i]
      UploadForm = modelform_factory(
        model,
        fields=tuple(fields),
        formfield_callback=formfieldCallback
        )
      rowWrapper = rowmapper(headers)

      # Get natural keys for the class
      natural_key = None
      if hasattr(model.objects, 'get_by_natural_key'):
        if model._meta.unique_together:
          natural_key = model._meta.unique_together[0]
        elif hasattr(model, 'natural_key'):
          natural_key = model.natural_key

    # Case 2: Skip empty rows
    elif rowWrapper.empty():
      continue

    # Case 3: Process a data row
    else:
      try:
        # Step 1: Send a ping-alive message to make the upload interruptable
        if ping:
          pingcounter += 1
          if pingcounter >= 100:
            pingcounter = 0
            yield (DEBUG, rownumber, None, None, None)

        # Step 2: Fill the form with data, either updating an existing
        # instance or creating a new one.
        if has_pk_field:
          # A primary key is part of the input fields
          try:
            # Try to find an existing record with the same primary key
            it = model.objects.using(database).only(*fields).get(pk=rowWrapper[model._meta.pk.name])
            form = UploadForm(rowWrapper, instance=it)
          except model.DoesNotExist:
            form = UploadForm(rowWrapper)
            it = None
        elif natural_key:
          # A natural key exists for this model
          try:
            # Build the natural key
            key = []
            for x in natural_key:
              key.append(rowWrapper.get(x, None))
            # Try to find an existing record using the natural key
            it = model.objects.get_by_natural_key(*key)
            form = UploadForm(rowWrapper, instance=it)
          except model.DoesNotExist:
            form = UploadForm(rowWrapper)
            it = None
          except model.MultipleObjectsReturned:
            yield (
              ERROR, rownumber, None, None,
              force_text(_('Key fields not unique'))
              )
            continue
        else:
          # No primary key required for this model
          form = UploadForm(rowWrapper)
          it = None

        # Step 3: Validate the form and model, and save to the database
        if form.has_changed():
          if form.is_valid():
            # Save the form
            obj = form.save(commit=False)
            if it:
              changed += 1
              obj.save(using=database, force_update=True)
            else:
              added += 1
              obj.save(using=database, force_insert=True)
              # Add the new object in the cache of available keys
              for x in selfReferencing:
                if x.cache is not None and obj.pk not in x.cache:
                  x.cache[obj.pk] = obj
            if user:
              admin_log.append(
                LogEntry(
                  user_id=user.id,
                  content_type_id=content_type_id,
                  object_id=obj.pk,
                  object_repr=force_text(obj),
                  action_flag=it and CHANGE or ADDITION,
                  #. Translators: Translation included with Django
                  change_message='Changed %s.' % get_text_list(form.changed_data, 'and')
                ))
              if len(admin_log) > 100:
                LogEntry.objects.all().using(database).bulk_create(admin_log)
                admin_log = []
          else:
            # Validation fails
            for error in form.non_field_errors():
              errors += 1
              yield (ERROR, rownumber, None, None, error)
            for field in form:
              for error in field.errors:
                errors += 1
                yield (ERROR, rownumber, field.name, rowWrapper[field.name], error)

      except Exception as e:
        errors += 1
        yield (ERROR, None, None, None, "Exception during upload: %s" % e)

  # Save remaining admin log entries
  LogEntry.objects.all().using(database).bulk_create(admin_log)

  yield (
    INFO, None, None, None,
    _('%(rows)d data rows, changed %(changed)d and added %(added)d records, %(errors)d errors, %(warnings)d warnings') % {
      'rows': rownumber - 1, 'changed': changed, 'added': added,
      'errors': errors, 'warnings': warnings
      }
    )


class BulkForeignKeyFormField(forms.fields.Field):

  def __init__(self, using=DEFAULT_DB_ALIAS, field=None, required=None,
               label=None, help_text='', *args, **kwargs):
    forms.fields.Field.__init__(
      self, *args,
      required=required if required is not None else not field.null,
      label=label, help_text=help_text, **kwargs
      )

    # Build a cache with the list of values - as long as it reasonable fits in memory
    self.model = field.remote_field.model
    field.remote_field.parent_link = True  # A trick to disable the model validation on foreign keys!
    if field.remote_field.model._default_manager.all().using(using).count() > 20000:
      self.queryset = field.remote_field.model._default_manager.all().using(using)
      self.cache = None
    else:
      self.queryset = None
      self.cache = { obj.pk: obj for obj in field.remote_field.model._default_manager.all().using(using) }


  def to_python(self, value):
    if value in EMPTY_VALUES:
      return None
    if self.cache is not None:
      try:
        return self.cache[value]
      except KeyError:
        #. Translators: Translation included with Django
        raise forms.ValidationError(_('Select a valid choice. That choice is not one of the available choices.'))
    else:
      try:
        return self.queryset.get(pk=value)
      except self.model.DoesNotExist:
        #. Translators: Translation included with Django
        raise forms.ValidationError(_('Select a valid choice. That choice is not one of the available choices.'))


  def has_changed(self, initial, data):
    return initial != data
