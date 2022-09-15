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

import datetime
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ("input", "0066_demand_index"),
    ]

    operations = [
        migrations.AlterField(
            model_name="itemdistribution",
            name="location",
            field=models.ForeignKey(
                help_text="Destination location to be replenished",
                on_delete=django.db.models.deletion.CASCADE,
                related_name="itemdistributions_destination",
                to="input.location",
                verbose_name="location",
            ),
        ),
    ]
