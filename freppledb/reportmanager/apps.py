#
# Copyright (C) 2021 by frePPLe bv
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

from django.apps import AppConfig
from django.conf import settings
from django.core import checks


@checks.register(checks.Tags.database)
def check_python_packages(app_configs, **kwargs):
    errors = []
    for db, dbparams in settings.DATABASES.items():
        if "SQL_QROLE" not in dbparams:
            errors.append(db)
    return (
        [
            checks.Error(
                "No SQL_ROLE setting configured in djangosettings.py for databases: %s"
                % ", ".join(errors),
                id="reportmanager.E001",
            )
        ]
        if errors
        else []
    )


class ReportManagerConfig(AppConfig):
    name = "freppledb.reportmanager"
    verbose_name = "reportmanager"
