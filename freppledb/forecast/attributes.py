#
# Copyright (C) 2023 by frePPLe bv
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

# TODO we'ld actually want this field to be a foreign key, such that it can be use in queries
registerAttribute(
    "freppledb.input.models.OperationPlan",
    [("forecast", _("forecast"), "string", False, True)],
)
# Average Demand Interval and Coefficient of Variation Square
registerAttribute(
    "freppledb.input.models.Item",
    [
        ("demand_pattern", _("demand_pattern"), "string", False, True),
        ("adi", _("adi"), "number", False, True),
        ("cv2", _("cv2"), "number", False, True),
        ("outlier_1b", _("outliers last bucket"), "number", False, True),
        ("outlier_6b", _("outliers last 6 buckets"), "number", False, True),
        ("outlier_12b", _("outliers last 12 buckets"), "number", False, True),
    ],
)
