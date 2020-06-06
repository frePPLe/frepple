#
# Copyright (C) 2019 by frePPLe bv
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

    dependencies = [("common", "0014_squashed_60")]

    operations = [
        migrations.AlterModelOptions(
            name="comment",
            options={
                "default_permissions": [],
                "ordering": ("id",),
                "verbose_name": "comment",
                "verbose_name_plural": "comments",
            },
        ),
        migrations.AlterModelOptions(
            name="scenario",
            options={
                "default_permissions": ("copy", "release"),
                "ordering": ["name"],
                "verbose_name": "scenario",
                "verbose_name_plural": "scenarios",
            },
        ),
        migrations.AlterModelOptions(
            name="userpreference",
            options={
                "default_permissions": [],
                "verbose_name": "preference",
                "verbose_name_plural": "preferences",
            },
        ),
    ]
