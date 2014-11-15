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

from decimal import Decimal
import json
import math
import re

import django.forms.fields as fields
import django.db.models as models
from django.utils.translation import ugettext_lazy as _
from django.utils import six
from django.conf import settings
from django.forms.widgets import TextInput
from django.core.exceptions import ValidationError


#
# DURATIONFIELD
#
# This field is stored in the database as an Decimal field, but it is displayed
# in forms as a text in the form 'DD HH:MM:SS'.
#

class DurationWidget(TextInput):

    def render(self, name, value, attrs=None):
      try:
        value = float(value)
        days = math.floor(value / 86400)
        hours = math.floor((value - (days * 86400)) / 3600)
        minutes = math.floor((value - (days * 86400) - (hours * 3600)) / 60)
        seconds = value - (days * 86400) - (hours * 3600) - (minutes * 60)
        if days > 0:
          value = "%d %02d:%02d:%02d" % (days, hours, minutes, seconds)
        elif hours > 0:
          value = "%2d:%02d:%02d" % (hours, minutes, seconds)
        elif minutes > 0:
          value = "%2d:%02d" % (minutes, seconds)
        else:
          value = seconds
      except:
        pass
      return super(DurationWidget, self).render(name, value, attrs)


numericTypes = (Decimal, float) + six.integer_types


class DurationFormField(fields.RegexField):

  widget = DurationWidget

  regex = re.compile(r'[0-9]*$')

  def __init__(self, *args, **kwargs):
    self.max_digits = kwargs.pop('decimal_places', settings.DECIMAL_PLACES)
    self.decimal_places = kwargs.pop('max_digits', settings.MAX_DIGITS)
    kwargs.update({
      'regex': self.regex,
      'error_message': _('Expected format "DD HH:MM:SS", "HH:MM:SS", "MM:SS" or "SS"')
      })
    super(DurationFormField, self).__init__(**kwargs)

  def to_python(self, value):
    if isinstance(value, numericTypes) or value is None:
      # Empty fields and numeric values pass directly
      return value
    if value == '':
      return None

    # Parse the input string to a decimal number, representing the number of seconds
    try:
      t = value.split(":")
      tl = len(t)
      if tl <= 1:
        # Seconds only
        return float(t[0])
      elif tl == 2:
        # Minutes and seconds
        return int(t[0]) * 60 + float(t[1])
      elif tl == 3:
        v = t[0].split(' ')
        if len(v) > 1:
          # Days, hours, minutes, seconds
          return int(v[0]) * 86400 + int(v[1]) * 3600 + int(t[1]) * 60 + float(t[2])
        else:
          # Hours, minutes, seconds
          return int(t[0]) * 3600 + int(t[1]) * 60 + float(t[2])
    except:
      raise ValidationError(_('Expected format "DD HH:MM:SS", "HH:MM:SS", "MM:SS" or "SS"'), code='invalid')


class DurationField(models.DecimalField):

  def formfield(self, **kwargs):
    defaults = {'form_class': DurationFormField, }
    defaults.update(kwargs)
    return super(DurationField, self).formfield(**defaults)


#
# JSONFIELD
#
# JSONField is a generic textfield that serializes/unserializes JSON objects.
#
# This code is very loosely inspired on the code found at:
#    https://github.com/bradjasper/django-jsonfield

class JSONField(models.TextField, metaclass=models.SubfieldBase):

  def __init__(self, *args, **kwargs):
    self.dump_kwargs = kwargs.pop('dump_kwargs', {
        'separators': (',', ':')
    })
    self.load_kwargs = kwargs.pop('load_kwargs', {})
    super(JSONField, self).__init__(*args, **kwargs)

  def to_python(self, value):
    """Convert a json string to a Python value."""
    if isinstance(value, six.string_types) and value:
      return json.loads(value)
    else:
      return value

  def get_db_prep_value(self, value, connection, prepared=False):
    """Convert JSON object to a string."""
    if self.null and value is None:
      return None
    return json.dumps(value, **self.dump_kwargs)

  def value_to_string(self, obj):
    value = self._get_val_from_obj(obj)
    return self.get_db_prep_value(value, None)

  def value_from_object(self, obj):
    value = super(JSONField, self).value_from_object(obj)
    if self.null and value is None:
      return None
    return self.dumps_for_display(value)

  def dumps_for_display(self, value):
    return json.dumps(value)

  def db_type(self, connection):
    if connection.vendor == 'postgresql' and connection.pg_version >= 90200:
      return 'json'
    else:
      return super(JSONField, self).db_type(connection)
