#
# Copyright (C) 2015-2017 by frePPLe bv
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

from rest_framework.serializers import ModelSerializer as DefaultModelSerializer
from rest_framework.validators import UniqueValidator, UniqueTogetherValidator

from freppledb.boot import getAttributes


def getAttributeAPIFilterDefinition(cls):
    flt = {}
    for fld in getAttributes(cls):
        if fld[2] in (
            "number",
            "integer",
            "date",
            "datetime",
            "duration",
            "time",
        ):
            flt[fld[0]] = ["exact", "in", "gt", "gte", "lt", "lte"]
        elif fld[2] == "string":
            flt[fld[0]] = ["exact", "in", "contains"]
        elif fld[2] == "boolean":
            flt[fld[0]] = [
                "exact",
            ]
    return flt


def getAttributeAPIFields(cls):
    return tuple(i[0] for i in getAttributes(cls))


def getAttributeAPIReadOnlyFields(cls):
    return tuple(i[0] for i in getAttributes(cls) if not i[3])
