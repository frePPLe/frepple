#
# Copyright (C) 2019 by frePPLe bv
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

from freppledb.boot import registerAttribute

from django.utils.translation import gettext_lazy as _


registerAttribute(
    "freppledb.input.models.Item",
    [
        ("latedemandcount", _("count of late demands"), "integer", False, False),
        ("latedemandquantity", _("quantity of late demands"), "number", False, False),
        ("latedemandvalue", _("value of late demand"), "number", False, False),
        (
            "unplanneddemandcount",
            _("count of unplanned demands"),
            "integer",
            False,
            True,
        ),
        (
            "unplanneddemandquantity",
            _("quantity of unplanned demands"),
            "number",
            False,
            True,
        ),
        (
            "unplanneddemandvalue",
            _("value of unplanned demands"),
            "number",
            False,
            True,
        ),
    ],
)

registerAttribute(
    "freppledb.input.models.Resource",
    [
        (
            "overloadcount",
            _("count of capacity overload problems"),
            "integer",
            False,
            True,
        )
    ],
)
