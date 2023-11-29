#
# Copyright (C) 2022 by frePPLe bv
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
            ["%Y-%m-%dT%H:%M:%S"],
            settings.DATETIME_INPUT_FORMATS,
            settings.DATE_INPUT_FORMATS,
        ):
            try:
                return datetime.strptime(data, format)
            except (ValueError, TypeError):
                continue
        raise Exception(_("Invalid date format"))
