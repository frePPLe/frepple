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

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [("common", "0017_sql_role")]

    operations = [
        migrations.AlterModelOptions(
            name="Scenario",
            options={
                "db_table": "common_scenario",
                "ordering": ["name"],
                "verbose_name_plural": "scenarios",
                "verbose_name": "scenario",
                "permissions": (
                    ("copy_scenario", "Can copy a scenario"),
                    ("release_scenario", "Can release a scenario"),
                    ("promote_scenario", "Can promote a scenario"),
                ),
            },
        )
    ]
