#
# Copyright (C) 2019 by frePPLe bvba
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

from freppledb.boot import registerAttribute

from django.utils.translation import gettext_lazy as _


registerAttribute(
    "freppledb.input.models.Item",
    [
        ("latedemandcount", _("count of late demands"), "integer", False, True),
        ("latedemandquantity", _("quantity of late demands"), "number", False, True),
        ("latedemandvalue", _("value of late demand"), "number", False, True),
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
            "integer",
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
