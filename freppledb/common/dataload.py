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

from django import forms
from django.core.validators import EMPTY_VALUES
from django.db import DEFAULT_DB_ALIAS
from django.utils.translation import ugettext_lazy as _


class BulkForeignKeyFormField(forms.fields.Field):

  def __init__(self, using=DEFAULT_DB_ALIAS, field=None, required=None,
               label=None, help_text='', *args, **kwargs):
    forms.fields.Field.__init__(
      self, *args,
      required=required if required is not None else field.null,
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
    if self.cache:
      try:
        return self.cache[value]
      except KeyError:
        raise forms.ValidationError(_(
          'Select a valid choice. That choice is not one of'
          ' the available choices.'
          ))
    else:
      try:
        return self.queryset.get(pk=value)
      except self.model.DoesNotExist:
        raise forms.ValidationError(_(
          'Select a valid choice. That choice is not one of'
          ' the available choices.'
          ))
