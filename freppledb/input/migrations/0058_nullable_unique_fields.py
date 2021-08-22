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
            """
            delete from buffer a
            using (
                select max(id) as id, item_id, location_id, batch
                from buffer 
                group by item_id, location_id, batch
                having count(*) > 1
                ) b
            where a.item_id is not distinct from b.item_id
            and a.location_id is not distinct from b.location_id
            and a.batch is not distinct from b.batch
            and a.id is distinct from b.id
            """
        ),
        migrations.RunSQL(
            "update buffer set batch = '' where batch is null",
        ),
        migrations.RunSQL(
            "ALTER TABLE buffer ALTER COLUMN batch SET DEFAULT ''",
        ),
        migrations.RunSQL(
            """
            delete from calendarbucket a
            using (
                select max(id) as id, calendar_id, priority, startdate, enddate
                from calendarbucket 
                group by calendar_id, priority, startdate, enddate
                having count(*) > 1
                ) b
            where a.calendar_id is not distinct from b.calendar_id
            and a.priority is not distinct from b.priority
            and a.startdate is not distinct from b.startdate
            and a.enddate is not distinct from b.enddate
            and a.id is distinct from b.id
            """
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
            """
            delete from suboperation a
            using (
                select max(id) as id, operation_id, suboperation_id, effective_start
                from suboperation 
                group by operation_id, suboperation_id, effective_start
                having count(*) > 1
                ) b
            where a.operation_id is not distinct from b.operation_id
            and a.suboperation_id is not distinct from b.suboperation_id
            and a.effective_start is not distinct from b.effective_start
            and a.id is distinct from b.id
            """
        ),
        migrations.RunSQL(
            "update suboperation set effective_start = '1971-01-01'::timestamp where effective_start is null",
        ),
        migrations.RunSQL(
            "ALTER TABLE suboperation ALTER COLUMN effective_start SET DEFAULT '1971-01-01'::timestamp",
        ),
        migrations.RunSQL(
            """
            delete from operationmaterial a
            using (
                select max(id) as id, operation_id, item_id, effective_start
                from operationmaterial 
                group by operation_id, item_id, effective_start
                having count(*) > 1
                ) b
            where a.operation_id is not distinct from b.operation_id
            and a.item_id is not distinct from b.item_id
            and a.effective_start is not distinct from b.effective_start
            and a.id is distinct from b.id
            """
        ),
        migrations.RunSQL(
            "update operationmaterial set effective_start = '1971-01-01'::timestamp where effective_start is null",
        ),
        migrations.RunSQL(
            "ALTER TABLE operationmaterial ALTER COLUMN effective_start SET DEFAULT '1971-01-01'::timestamp",
        ),
        migrations.RunSQL(
            """
            delete from operationresource a
            using (
                select max(id) as id, operation_id, resource_id, effective_start
                from operationresource 
                group by operation_id, resource_id, effective_start
                having count(*) > 1
                ) b
            where a.operation_id is not distinct from b.operation_id
            and a.resource_id is not distinct from b.resource_id
            and a.effective_start is not distinct from b.effective_start
            and a.id is distinct from b.id
            """
        ),
        migrations.RunSQL(
            "update operationresource set effective_start = '1971-01-01'::timestamp where effective_start is null",
        ),
        migrations.RunSQL(
            "ALTER TABLE operationresource ALTER COLUMN effective_start SET DEFAULT '1971-01-01'::timestamp",
        ),
        migrations.RunSQL(
            """
            delete from itemsupplier a
            using (
                select max(id) as id, item_id, supplier_id, location_id, effective_start
                from itemsupplier 
                group by item_id, supplier_id, location_id, effective_start
                having count(*) > 1
                ) b
            where a.item_id is not distinct from b.item_id
            and a.supplier_id is not distinct from b.supplier_id
            and a.location_id is not distinct from b.location_id
            and a.effective_start is not distinct from b.effective_start
            and a.id is distinct from b.id
            """
        ),
        migrations.RunSQL(
            "update itemsupplier set effective_start = '1971-01-01'::timestamp where effective_start is null",
        ),
        migrations.RunSQL(
            "ALTER TABLE itemsupplier ALTER COLUMN effective_start SET DEFAULT '1971-01-01'::timestamp",
        ),
        migrations.RunSQL(
            """
            delete from itemdistribution a
            using (
                select max(id) as id, item_id, origin_id, location_id, effective_start
                from itemdistribution 
                group by item_id, origin_id, location_id, effective_start
                having count(*) > 1
                ) b
            where a.item_id is not distinct from b.item_id
            and a.origin_id is not distinct from b.origin_id
            and a.location_id is not distinct from b.location_id
            and a.effective_start is not distinct from b.effective_start
            and a.id is distinct from b.id
            """
        ),
        migrations.RunSQL(
            "update itemdistribution set effective_start = '1971-01-01'::timestamp where effective_start is null",
        ),
        migrations.RunSQL(
            "ALTER TABLE itemdistribution ALTER COLUMN effective_start SET DEFAULT '1971-01-01'::timestamp",
        ),
    ]
