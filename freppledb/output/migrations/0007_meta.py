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

    dependencies = [("output", "0006_squashed_60")]

    operations = [
        migrations.AlterModelOptions(
            name="constraint",
            options={
                "default_permissions": [],
                "ordering": ["demand", "startdate"],
                "verbose_name": "constraint",
                "verbose_name_plural": "constraints",
            },
        ),
        migrations.AlterModelOptions(
            name="problem",
            options={
                "default_permissions": [],
                "ordering": ["startdate"],
                "verbose_name": "problem",
                "verbose_name_plural": "problems",
            },
        ),
        migrations.AlterModelOptions(
            name="resourcesummary",
            options={
                "default_permissions": [],
                "ordering": ["resource", "startdate"],
                "verbose_name": "resource summary",
                "verbose_name_plural": "resource summaries",
            },
        ),
    ]
