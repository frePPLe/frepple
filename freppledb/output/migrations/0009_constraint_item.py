#
# Copyright (C) 2020 by frePPLe bv
#
# This library is free software; you can redistribute it and/or modify it
# under the terms of the GNU Affero General Public License as published
# by the Free Software Foundation; either version 3 of the License, or
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

    dependencies = [("output", "0008_sql_role")]

    operations = [
        migrations.AlterModelOptions(
            name="constraint",
            options={
                "default_permissions": [],
                "ordering": ["item", "startdate"],
                "verbose_name": "constraint",
                "verbose_name_plural": "constraints",
            },
        ),
        migrations.AlterField(
            model_name="constraint",
            name="demand",
            field=models.CharField(
                db_index=True, max_length=300, null=True, verbose_name="demand"
            ),
        ),
        migrations.AddField(
            model_name="constraint",
            name="forecast",
            field=models.CharField(
                db_index=True, max_length=300, null=True, verbose_name="forecast"
            ),
        ),
        migrations.AddField(
            model_name="constraint",
            name="item",
            field=models.CharField(
                db_index=True, max_length=300, null=True, verbose_name="item"
            ),
        ),
    ]
