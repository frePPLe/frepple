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

from datetime import date, datetime, timedelta
from itertools import chain
import re

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
                return (
                    datetime.strptime(data, format)
                    if settings.DATE_STYLE_WITH_HOURS
                    else datetime.strptime(data, format).date()
                )
            except (ValueError, TypeError):
                continue
        raise Exception(_("Invalid date format"))


def parseInterval(interval):
    """
    Converts "D HH:MM:SS" to total seconds.
    """
    # Case 1: Input is already a number, we assume we are talking seconds here
    if isinstance(interval, (int, float)):
        return timedelta(seconds=interval)

    # Case 2 & 3: Input is a string
    if isinstance(interval, str):
        s = interval.strip()
        # If the string is composed only of digits (or a float), treat it as seconds
        if re.match(r"^\d+(\.\d+)?$", s):
            return timedelta(seconds=float(s))

        # Pattern to match: [[days] hours:]minutes:seconds
        # This regex looks for: (Optional Days), (Optional Hours), Minutes, Seconds
        pattern = (
            r"^((?P<days>\d+)\s+)?((?P<hours>\d+):)?(?P<minutes>\d+):(?P<seconds>\d+)$"
        )
        match = re.match(pattern, s)

        if not match:
            raise Exception(_("Invalid time format"))

        times = match.groupdict()

        # Convert dictionary values to integers, defaulting to 0 if None
        d = int(times["days"] or 0)
        h = int(times["hours"] or 0)
        m = int(times["minutes"] or 0)
        s = int(times["seconds"] or 0)

        return timedelta(seconds=d * 86400 + h * 3600 + m * 60 + s)

    raise Exception(_("Input must be a string or a number."))
