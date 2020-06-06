#
# Copyright (C) 2018 by frePPLe bv
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

    dependencies = [("input", "0033_lastmodified_default")]

    operations = [
        migrations.AddField(
            model_name="itemdistribution",
            name="sizemaximum",
            field=models.DecimalField(
                blank=True,
                decimal_places=8,
                help_text="A maximum shipping quantity",
                max_digits=20,
                null=True,
                verbose_name="size maximum",
            ),
        ),
        migrations.AddField(
            model_name="itemsupplier",
            name="sizemaximum",
            field=models.DecimalField(
                blank=True,
                decimal_places=8,
                help_text="A maximum purchasing quantity",
                max_digits=20,
                null=True,
                verbose_name="size maximum",
            ),
        ),
    ]
