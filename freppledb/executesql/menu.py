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

from django.utils.translation import gettext_lazy as _

from freppledb.menu import menu
from .views import ExecuteSQL

menu.addGroup("custom", label=_("custom"), index=750)
menu.addItem(
    "custom",
    "executesql",
    url="/executesql/",
    report=ExecuteSQL,
    label=_("Execute SQL"),
    index=1100,
)
