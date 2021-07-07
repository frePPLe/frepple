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

from freppledb.input.models import Location
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("input", "0057_itemsupplier_extra_safety_lt"),
    ]

    operations = [
        migrations.RunSQL(
            "update buffer set batch = '' where batch is null",
        ),
        migrations.RunSQL(
            "ALTER TABLE buffer ALTER COLUMN batch SET DEFAULT ''",
        ),
        migrations.RunSQL(
            "update calendarbucket set startdate = '1971-01-01'::timestamp where startdate is null",
        ),
        migrations.RunSQL(
            "ALTER TABLE calendarbucket ALTER COLUMN startdate SET DEFAULT '1971-01-01'::timestamp",
        ),
        migrations.RunSQL(
            "update calendarbucket set enddate = '2030-12-31'::timestamp where enddate is null",
        ),
        migrations.RunSQL(
            "ALTER TABLE calendarbucket ALTER COLUMN enddate SET DEFAULT '2030-12-31'::timestamp",
        ),
        migrations.RunSQL(
            "update calendarbucket set priority = 0 where priority is null",
        ),
        migrations.RunSQL(
            "ALTER TABLE calendarbucket ALTER COLUMN priority SET DEFAULT 0",
        ),
        migrations.RunSQL(
            "update suboperation set effective_start = '1971-01-01'::timestamp where effective_start is null",
        ),
        migrations.RunSQL(
            "ALTER TABLE suboperation ALTER COLUMN effective_start SET DEFAULT '1971-01-01'::timestamp",
        ),
        migrations.RunSQL(
            "update operationmaterial set effective_start = '1971-01-01'::timestamp where effective_start is null",
        ),
        migrations.RunSQL(
            "ALTER TABLE operationmaterial ALTER COLUMN effective_start SET DEFAULT '1971-01-01'::timestamp",
        ),
        migrations.RunSQL(
            "update operationresource set effective_start = '1971-01-01'::timestamp where effective_start is null",
        ),
        migrations.RunSQL(
            "ALTER TABLE operationresource ALTER COLUMN effective_start SET DEFAULT '1971-01-01'::timestamp",
        ),
        migrations.RunSQL(
            "update itemsupplier set effective_start = '1971-01-01'::timestamp where effective_start is null",
        ),
        migrations.RunSQL(
            "ALTER TABLE itemsupplier ALTER COLUMN effective_start SET DEFAULT '1971-01-01'::timestamp",
        ),
        migrations.RunSQL(
            "update itemdistribution set effective_start = '1971-01-01'::timestamp where effective_start is null",
        ),
        migrations.RunSQL(
            "ALTER TABLE itemdistribution ALTER COLUMN effective_start SET DEFAULT '1971-01-01'::timestamp",
        ),
    ]
