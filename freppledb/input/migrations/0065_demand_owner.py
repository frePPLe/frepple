# Copyright (C) 2022 by frePPLe bv
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

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("input", "0064_opm_opr_sequence_cycle"),
    ]

    operations = [
        migrations.RemoveField(
            model_name="demand",
            name="lft",
        ),
        migrations.RemoveField(
            model_name="demand",
            name="lvl",
        ),
        migrations.RemoveField(
            model_name="demand",
            name="rght",
        ),
        migrations.AddField(
            model_name="demand",
            name="policy",
            field=models.CharField(
                blank=True,
                choices=[
                    ("independent", "independent"),
                    ("alltogether", "all together"),
                    ("inratio", "in ratio"),
                ],
                default="independent",
                help_text="Defines how sales orders are shipped together",
                max_length=15,
                null=True,
                verbose_name="policy",
            ),
        ),
        migrations.AlterField(
            model_name="demand",
            name="owner",
            field=models.CharField(
                blank=True,
                db_index=True,
                max_length=300,
                null=True,
                verbose_name="owner",
            ),
        ),
    ]
