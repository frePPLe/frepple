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
  for field_name, label, fieldtype in _register.get(model_path, []):
    if fieldtype == 'string':
      field = models.CharField(label, max_length=300, null=True, blank=True, db_index=True)
    elif fieldtype == 'boolean':
      field = models.NullBooleanField(label, null=True, blank=True, db_index=True)
    elif fieldtype == 'number':
      field = models.DecimalField(label, max_digits=15, decimal_places=6, null=True, blank=True, db_index=True)
    elif fieldtype == 'integer':
      field = models.IntegerField(label, null=True, blank=True, db_index=True)
    elif fieldtype == 'date':
      field = models.DateField(label, null=True, blank=True, db_index=True)
    elif fieldtype == 'datetime':
      field = models.DateTimeField(label, null=True, blank=True, db_index=True)
    elif fieldtype == 'duration':
      field = models.DurationField(label, null=True, blank=True, db_index=True)
    elif fieldtype == 'time':
      field = models.TimeField(label, null=True, blank=True, db_index=True)
    else:
      raise ImproperlyConfigured("Invalid attribute type '%s'." % fieldtype)
    field.contribute_to_class(sender, field_name)


def registerAttribute(model, attrlist):
  '''
  Register a new attribute.
  '''
  if model not in _register:
    _register[model] = []
  for name, label, fieldtype in attrlist:
    _register[model].append( (name, label, fieldtype, ) )


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
  for field_name, label, fieldtype in _register.get("%s.%s" % (model.__module__, model.__name__), []):
    if related_name_prefix:
      field_name = "%s__%s" % (related_name_prefix, field_name)
      label = "%s - %s" % (related_name_prefix.split('__')[-1], label)
    else:
      label = "%s - %s" % (model.__name__, label)
    if fieldtype == 'string':
      result.append( GridFieldText(field_name, title=label, initially_hidden=initially_hidden) )
    elif fieldtype == 'boolean':
      result.append( GridFieldBool(field_name, title=label, initially_hidden=initially_hidden) )
    elif fieldtype == 'number':
      result.append( GridFieldNumber(field_name, title=label, initially_hidden=initially_hidden) )
    elif fieldtype == 'integer':
      result.append( GridFieldInteger(field_name, title=label, initially_hidden=initially_hidden) )
    elif fieldtype == 'date':
      result.append( GridFieldDate(field_name, title=label, initially_hidden=initially_hidden) )
    elif fieldtype == 'datetime':
      result.append( GridFieldDateTime(field_name, title=label, initially_hidden=initially_hidden) )
    elif fieldtype == 'duration':
      result.append( GridFieldDuration(field_name, title=label, initially_hidden=initially_hidden) )
    elif fieldtype == 'time':
      result.append( GridFieldTime(field_name, title=label, initially_hidden=initially_hidden) )
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
