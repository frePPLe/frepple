#
# Copyright (C) 2020 by frePPLe bv
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
import os

from django.db import DEFAULT_DB_ALIAS

from freppledb.common.commands import PlanTaskRegistry, PlanTask


@PlanTaskRegistry.register
class archiveData(PlanTask):
    description = "Archiving of data snapshot"
    sequence = 403

    @classmethod
    def getWeight(cls, database=DEFAULT_DB_ALIAS, **kwargs):
        if "supply" in os.environ:
            return 1
        else:
            return -1

    @classmethod
    def run(cls, database=DEFAULT_DB_ALIAS, **kwargs):
        from django.core import management

        management.call_command("archive", database=database)
