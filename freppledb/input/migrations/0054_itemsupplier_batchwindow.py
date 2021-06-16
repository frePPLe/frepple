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

import datetime
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("input", "0053_operationplan_quantitycompleted"),
    ]

    operations = [
        migrations.AddField(
            model_name="itemsupplier",
            name="batchwindow",
            field=models.DurationField(
                blank=True,
                default=datetime.timedelta(days=7),
                help_text="Proposed purchase orders within this window will be grouped together",
                null=True,
                verbose_name="batching window",
            ),
        ),
    ]
