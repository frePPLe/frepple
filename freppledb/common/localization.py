#
# Copyright (C) 2022 by frePPLe bv
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

from datetime import date, datetime
from itertools import chain

from django.conf import settings
from django.utils import encoding
from django.utils.translation import gettext_lazy as _


def parseLocalizedDate(data):
    if isinstance(data, date):
        return data
    elif isinstance(data, datetime):
        return data.date()
    else:
        data = encoding.smart_str(data).strip()
        for format in settings.DATE_INPUT_FORMATS:
            try:
                return datetime.strptime(data, format).date()
            except (ValueError, TypeError):
                continue
        raise Exception(_("Invalid date format"))


def parseLocalizedDateTime(data):
    if isinstance(data, date):
        return datetime.combine(data, datetime.min.time())
    elif isinstance(data, datetime):
        return data
    else:
        data = encoding.smart_str(data).strip()
        for format in chain(
            settings.DATETIME_INPUT_FORMATS,
            settings.DATE_INPUT_FORMATS,
        ):
            try:
                return datetime.strptime(data, format)
            except (ValueError, TypeError) as e:
                continue
        raise Exception(_("Invalid date format"))
