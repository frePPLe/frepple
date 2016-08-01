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

import json

import django.db.models as models
from django.utils import six


#
# DURATIONFIELD
#

class DurationField(models.DecimalField):
  '''
  Obsoleted database field type.
  Not used any longer, but the code is required to be kept here to make migrations run.
  '''
  pass


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
    # PostgreSQL also has a jsonb field. The difference is that jsonb is
    # 1) much more efficient in querying the field, 2) allows indexes to
    # be defined on the content, but 3) takes a bit more time to update.
    # The JSON fields is sufficient for us since we just want to store the
    # JSON data without complex operations.
    return 'json'
