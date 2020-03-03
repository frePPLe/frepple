#
# Copyright (C) 2020 by frePPLe bvba
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

    dependencies = [("input", "0046_sql_role")]

    operations = [
        migrations.AddField(
            model_name="demand",
            name="batch",
            field=models.CharField(
                blank=True,
                db_index=True,
                help_text="MTO batch name",
                max_length=300,
                null=True,
                verbose_name="batch",
            ),
        ),
        migrations.AddField(
            model_name="item",
            name="type",
            field=models.CharField(
                blank=True,
                choices=[
                    ("make to stock", "make to stock"),
                    ("make to order", "make to order"),
                ],
                max_length=20,
                null=True,
                verbose_name="type",
            ),
        ),
        migrations.AddField(
            model_name="operationplan",
            name="batch",
            field=models.CharField(
                blank=True,
                db_index=True,
                help_text="MTO batch name",
                max_length=300,
                null=True,
                verbose_name="batch",
            ),
        ),
    ]
