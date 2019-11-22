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

    dependencies = [("metrics", "0001_item_resource_attributes")]

    operations = [
        migrations.AlterField(
            model_name="item",
            name="unplanneddemandcount",
            field=models.IntegerField(
                blank=True,
                db_index=True,
                null=True,
                verbose_name="count of unplanned demands",
            ),
        )
    ]
