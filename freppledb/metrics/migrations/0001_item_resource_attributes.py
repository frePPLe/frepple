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

from django.db import migrations, models

from freppledb.common.migrate import AttributeMigration


class Migration(AttributeMigration):

    extends_app_label = "input"

    dependencies = [("input", "0016_squashed_41")]

    operations = [
        migrations.AddField(
            model_name="item",
            name="latedemandcount",
            field=models.IntegerField(
                blank=True,
                db_index=True,
                null=True,
                verbose_name="count of late demands",
            ),
        ),
        migrations.AddField(
            model_name="item",
            name="latedemandquantity",
            field=models.DecimalField(
                blank=True,
                db_index=True,
                decimal_places=8,
                max_digits=20,
                null=True,
                verbose_name="quantity of late demands",
            ),
        ),
        migrations.AddField(
            model_name="item",
            name="latedemandvalue",
            field=models.DecimalField(
                blank=True,
                db_index=True,
                decimal_places=8,
                max_digits=20,
                null=True,
                verbose_name="value of late demand",
            ),
        ),
        migrations.AddField(
            model_name="item",
            name="unplanneddemandcount",
            field=models.DecimalField(
                blank=True,
                db_index=True,
                decimal_places=8,
                max_digits=20,
                null=True,
                verbose_name="count of unplanned demands",
            ),
        ),
        migrations.AddField(
            model_name="item",
            name="unplanneddemandquantity",
            field=models.DecimalField(
                blank=True,
                db_index=True,
                decimal_places=8,
                max_digits=20,
                null=True,
                verbose_name="quantity of unplanned demands",
            ),
        ),
        migrations.AddField(
            model_name="item",
            name="unplanneddemandvalue",
            field=models.DecimalField(
                blank=True,
                db_index=True,
                decimal_places=8,
                max_digits=20,
                null=True,
                verbose_name="value of unplanned demands",
            ),
        ),
        migrations.AddField(
            model_name="resource",
            name="overloadcount",
            field=models.IntegerField(
                blank=True,
                db_index=True,
                null=True,
                verbose_name="count of capacity overload problems",
            ),
        ),
    ]
