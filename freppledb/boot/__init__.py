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

"""
The boot app is placed at the top of the list in ``INSTALLED_APPS``
for the purpose of hooking into Django's ``class_prepared`` signal
and defining attribute fields.

This app is very closely inspired on http://mezzanine.jupo.org/
and its handling of injected extra fields.
"""
from importlib import import_module

from django.conf import settings
from django.db import models

from django.core.exceptions import ImproperlyConfigured
from django.db.models.signals import class_prepared


_register = {}


def add_extra_model_fields(sender, **kwargs):
  model_path = "%s.%s" % (sender.__module__, sender.__name__)
  for field_name, label, fieldtype, editable in _register.get(model_path, []):
    if fieldtype == 'string':
      field = models.CharField(label, max_length=300, null=True, blank=True, db_index=True, editable=editable)
    elif fieldtype == 'boolean':
      field = models.NullBooleanField(label, null=True, blank=True, db_index=True, editable=editable)
    elif fieldtype == 'number':
      # Note: Other numeric fields have precision 20, 8.
      # Changing the value below would require migrating existing attributes of all projects.
      field = models.DecimalField(label, max_digits=15, decimal_places=6, null=True, blank=True, db_index=True, editable=editable)
    elif fieldtype == 'integer':
      field = models.IntegerField(label, null=True, blank=True, db_index=True, editable=editable)
    elif fieldtype == 'date':
      field = models.DateField(label, null=True, blank=True, db_index=True, editable=editable)
    elif fieldtype == 'datetime':
      field = models.DateTimeField(label, null=True, blank=True, db_index=True, editable=editable)
    elif fieldtype == 'duration':
      field = models.DurationField(label, null=True, blank=True, db_index=True, editable=editable)
    elif fieldtype == 'time':
      field = models.TimeField(label, null=True, blank=True, db_index=True, editable=editable)
    else:
      raise ImproperlyConfigured("Invalid attribute type '%s'." % fieldtype)
    field.contribute_to_class(sender, field_name)


def registerAttribute(model, attrlist):
  '''
  Register a new attribute.
  '''
  if model not in _register:
    _register[model] = []
  for attr in attrlist:
    if len(attr) < 3:
      raise Exception("Invalid attribute definition: %s" % attr)
    elif len(attr) == 3:
      _register[model].append(attr + (True,))
    else:
      _register[model].append(attr)


def getAttributes(model):
  '''
  Return all attributes for a given model.
  '''
  return _register.get("%s.%s" % (model.__module__, model.__name__), [])


def getAttributeFields(model, related_name_prefix=None, initially_hidden=False):
  '''
  Return report fields for all attributes of a given model.
  '''
  from freppledb.common.report import GridFieldText, GridFieldBool, GridFieldNumber
  from freppledb.common.report import GridFieldInteger, GridFieldDate, GridFieldDateTime
  from freppledb.common.report import GridFieldDuration, GridFieldTime
  result = []
  for field_name, label, fieldtype, editable in _register.get("%s.%s" % (model.__module__, model.__name__), []):
    if related_name_prefix:
      field_name = "%s__%s" % (related_name_prefix, field_name)
      label = "%s - %s" % (related_name_prefix.split('__')[-1], label)
    else:
      label = "%s - %s" % (model.__name__, label)
    if fieldtype == 'string':
      result.append( GridFieldText(field_name, title=label, initially_hidden=initially_hidden, editable=editable) )
    elif fieldtype == 'boolean':
      result.append( GridFieldBool(field_name, title=label, initially_hidden=initially_hidden, editable=editable) )
    elif fieldtype == 'number':
      result.append( GridFieldNumber(field_name, title=label, initially_hidden=initially_hidden, editable=editable) )
    elif fieldtype == 'integer':
      result.append( GridFieldInteger(field_name, title=label, initially_hidden=initially_hidden, editable=editable) )
    elif fieldtype == 'date':
      result.append( GridFieldDate(field_name, title=label, initially_hidden=initially_hidden, editable=editable) )
    elif fieldtype == 'datetime':
      result.append( GridFieldDateTime(field_name, title=label, initially_hidden=initially_hidden, editable=editable) )
    elif fieldtype == 'duration':
      result.append( GridFieldDuration(field_name, title=label, initially_hidden=initially_hidden, editable=editable) )
    elif fieldtype == 'time':
      result.append( GridFieldTime(field_name, title=label, initially_hidden=initially_hidden, editable=editable) )
    else:
      raise Exception("Invalid attribute type '%s'." % fieldtype)
  return result


_first = True
if _first:
  _first = False
  # Scan attribute definitions from the settings
  for model, attrlist in settings.ATTRIBUTES:
    registerAttribute(model, attrlist)

  # Scan attribute definitions from the installed apps
  for app in reversed(settings.INSTALLED_APPS):
    try:
      mod = import_module('%s.attributes' % app)
    except ImportError as e:
      # Silently ignore if it's the menu module which isn't found
      if str(e) not in ("No module named %s.attributes" % app, "No module named '%s.attributes'" % app):
        raise e

  if _register:
    class_prepared.connect(add_extra_model_fields, dispatch_uid="frepple_attribute_injection")
