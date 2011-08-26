#
# Copyright (C) 2007-2011 by Johan De Taeye, frePPLe bvba
#
# This library is free software; you can redistribute it and/or modify it
# under the terms of the GNU Lesser General Public License as published
# by the Free Software Foundation; either version 2.1 of the License, or
# (at your option) any later version.
#
# This library is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU Lesser
# General Public License for more details.
#
# You should have received a copy of the GNU Lesser General Public
# License along with this library; if not, write to the Free Software
# Foundation Inc., 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301, USA
#

# file : $URL$
# revision : $LastChangedRevision$  $LastChangedBy$
# date : $LastChangedDate$

from decimal import Decimal

import django.forms.fields as fields
import django.db.models as models
from django.db.backends.util import format_number
from django.forms.widgets import MultiWidget, TextInput, Select
from django.utils.translation import ugettext_lazy as _
from django.conf import settings


#
# DURATIONFIELD
#
# This field is stored in the database as an Decimal field, but it is displayed
# in forms as a combination of a text window and a dropdown to select the time units.
#

class DurationWidget(MultiWidget):
  def __init__(self, attrs=None):
    widgets = (
      TextInput(attrs),
      Select(choices=(
            ("",""),
            ("seconds",_("seconds")),
            ("minutes",_("minutes")),
            ("hours",_("hours")),
            ("days",_("days")),
            ("weeks",_("weeks"))
            ), attrs={'onclick': 'getUnits(this)', 'onchange':'setUnits(this)'} ),
      )
    super(DurationWidget, self).__init__(widgets, attrs)

  def decompress(self, value):
    if value == None or value == 0: return [value, '']
    if value % 604800 == 0: return [value/Decimal(604800), 'weeks']
    if value % 60 == 0 and value < 3600: return [value/Decimal(60), 'minutes']
    if value % 3600 != 0 and value < 86400: return [value, 'seconds']
    if value % 86400 != 0 and value < 604800: return [value/Decimal(3600), 'hours']
    return [value/Decimal(86400), u"days"]

  def format_output(self, rendered_widgets):
    return "%s&nbsp;%s" % (rendered_widgets[0], rendered_widgets[1])

  def value_from_datadict(self, data, files, name):
    return [data.get(name,data.get('%s_0' % name,0)), data.get('%s_1' % name,'seconds')]


class DurationFormField(fields.MultiValueField):

  widget = DurationWidget

  def __init__(self, *args, **kwargs):
    self.max_digits = kwargs.pop('decimal_places', settings.DECIMAL_PLACES)
    self.decimal_places = kwargs.pop('max_digits', settings.MAX_DIGITS)
    kwargs.update({'required':False})
    f = (
        fields.DecimalField(*args, **kwargs),
        fields.ChoiceField(
          choices=(
            ("seconds",_("seconds")),
            ("minutes",_("minutes")),
            ("hours",_("hours")),
            ("days",_("days")),
            ("weeks",_("weeks")),
            ), required=False)
        )
    super(DurationFormField, self).__init__(
      fields=f, widget=DurationWidget(),
      label=kwargs.get('label',''),
      help_text=kwargs.get('help_text',None)
      )
    self.required = kwargs.get('required',False)

  def compress(self, data_list):
    if len(data_list) == 0: return None
    val, unit = data_list
    if val == None or val == u'': return None
    elif unit == 'hours': val = val * Decimal(3600)
    elif unit == 'minutes': val = val * Decimal(60)
    elif unit == 'days': val = val * Decimal(86400)
    elif unit != 'seconds': val = val * Decimal(604800)
    return format_number(float(val), self.max_digits, self.decimal_places)


class DurationField(models.DecimalField):

  def formfield(self, **kwargs):
    defaults = {'form_class': DurationFormField, }
    defaults.update(kwargs)
    return super(DurationField, self).formfield(**defaults)
