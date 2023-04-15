#
# Copyright (C) 2007-2013 by frePPLe bv
#
# Permission is hereby granted, free of charge, to any person obtaining
# a copy of this software and associated documentation files (the
# "Software"), to deal in the Software without restriction, including
# without limitation the rights to use, copy, modify, merge, publish,
# distribute, sublicense, and/or sell copies of the Software, and to
# permit persons to whom the Software is furnished to do so, subject to
# the following conditions:
#
# The above copyright notice and this permission notice shall be
# included in all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND,
# EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF
# MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND
# NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE
# LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION
# OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION
# WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.
#

import json

import django.db.models as models


#
# DURATIONFIELD
#


class DurationField(models.DecimalField):
    """
    Obsoleted database field type.
    Not used any longer, but the code is required to be kept here to make migrations run.
    """

    pass


#
# JSONFIELD
#
class JSONField(models.TextField):
    """
    Obsoleted database field type.
    Not used any longer, but the code is required to be kept here to make migrations run.
    """

    def __init__(self, *args, **kwargs):
        self.dump_kwargs = kwargs.pop("dump_kwargs", {"separators": (",", ":")})
        self.load_kwargs = kwargs.pop("load_kwargs", {})
        super().__init__(*args, **kwargs)

    def to_python(self, value):
        """Convert a json string to a Python value."""
        if isinstance(value, str) and value:
            return json.loads(value)
        else:
            return value

    def from_db_value(self, value, expression, connection):
        if isinstance(value, str) and value:
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
        value = super().value_from_object(obj)
        if self.null and value is None:
            return None
        return self.dumps_for_display(value)

    def dumps_for_display(self, value):
        return json.dumps(value)

    def db_type(self, connection):
        # A json field stores the data as a text string, that is parsed whenever
        # a json operation is performed on the field.
        return "json"


class JSONBField(JSONField):
    """
    Obsoleted database field type.
    Not used any longer, but the code is required to be kept here to make migrations run.
    """

    def db_type(self, connection):
        # A jsonb field is 1) much more efficient in querying the field,
        # 2) allows indexes to be defined on the content, but 3) takes a bit
        # more time to update.
        return "jsonb"


#
# ALIASFIELD
#


class AliasField(models.Field):
    """
    This field is an alias for another database field

    Sources:
    https://shezadkhan.com/aliasing-fields-in-django/

    Note: This uses some django functions that are being deprecated in django 2.0.
    """

    def contribute_to_class(self, cls, name, private_only=False):
        super().contribute_to_class(cls, name, private_only=True)
        setattr(cls, name, self)

    def __set__(self, instance, value):
        setattr(instance, self.db_column, value)

    def __get__(self, instance, instance_type=None):
        return getattr(instance, self.db_column)


class AliasDateTimeField(models.DateTimeField):
    """
    This field is an alias for another database field

    Sources:
    https://shezadkhan.com/aliasing-fields-in-django/

    Note: This uses some django functions that are being deprecated in django 2.0.
    """

    def contribute_to_class(self, cls, name, private_only=False):
        super().contribute_to_class(cls, name, private_only=True)
        setattr(cls, name, self)

    def __set__(self, instance, value):
        setattr(instance, self.db_column, value)

    def __get__(self, instance, instance_type=None):
        return getattr(instance, self.db_column)
