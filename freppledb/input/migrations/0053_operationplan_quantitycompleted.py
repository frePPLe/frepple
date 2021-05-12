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

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [("input", "0052_item_periodofcover")]

    operations = [
        migrations.AddField(
            model_name="operationplan",
            name="quantity_completed",
            field=models.DecimalField(
                decimal_places=8,
                default="0.00",
                max_digits=20,
                verbose_name="completed quantity",
                null=True,
                blank=True,
            ),
        )
    ]
