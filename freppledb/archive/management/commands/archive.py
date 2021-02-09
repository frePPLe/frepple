#
# Copyright (C) 2020 by frePPLe bv
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

from datetime import datetime
from dateutil.parser import parse

from django.db import DEFAULT_DB_ALIAS, connections
from django.core.management.base import BaseCommand

from freppledb import __version__
from freppledb.archive.models import ArchiveManager
from freppledb.common.models import Parameter


class Command(BaseCommand):
    help = """
      This command archives historical plan data.
      """

    requires_system_checks = False

    def get_version(self):
        return __version__

    def add_arguments(self, parser):
        parser.add_argument(
            "--database",
            default=DEFAULT_DB_ALIAS,
            help="database where the task should be launched",
        )
        parser.add_argument(
            "--force",
            action="store_true",
            default=False,
            help="Overwrite any existing snapshot already for the current period",
        )

    def handle(self, **options):
        database = options["database"]
        verbosity = int(options["verbosity"])
        with connections[database].cursor() as cursor:
            try:
                now = parse(
                    Parameter.objects.using(database).get(name="currentdate").value
                )
            except Exception:
                now = datetime.now()

            # Check the archiving frequency
            cursor.execute(
                """
               select common_bucket.name
               from common_bucket
               inner join common_parameter
                 on common_parameter.name = 'archive.frequency'
                 and common_bucket.name = common_parameter.value
               """
            )
            frequency = cursor.fetchone()
            if frequency:
                frequency = frequency[0]
            else:
                # No archiving activated
                if verbosity > 0:
                    print(
                        "Skipping archiving: missing or invalid 'archive.frequency' parameter"
                    )
                return

            # Check if a snapshot already exists in this period
            cursor.execute(
                """
                select snapshot_date
                from ax_manager
                inner join common_bucketdetail
                  on bucket_id = %s
                  and snapshot_date >= common_bucketdetail.startdate
                  and snapshot_date < common_bucketdetail.enddate
                where %s >= common_bucketdetail.startdate
                and %s < common_bucketdetail.enddate
                """,
                (frequency, now, now),
            )
            snapshots = [r[0] for r in cursor.fetchall()]
            if snapshots:
                if options["force"]:
                    # Delete previous snapshot for the period
                    for s in snapshots:
                        if verbosity > 0:
                            print("Deleting archive", s)
                        cursor.execute(
                            "delete from ax_manager where snapshot_date = %s", (s,)
                        )
                else:
                    # We already have a snapshot for this period
                    if verbosity > 0:
                        print(
                            "Skipping archiving: snapshot already exists for this period"
                        )
                    return

            if verbosity > 0:
                print("Creating history archive snapshot", now)
            mgr = ArchiveManager(
                snapshot_date=now,
                total_records=0,
                buffer_records=0,
                demand_records=0,
                operationplan_records=0,
            )
            mgr.save(using=database)

            # Archiving buffer table
            cursor.execute(
                """
                insert into ax_buffer (item, location, batch, onhand, cost, safetystock, snapshot_date_id)
                select item_id, location_id, batch, cost, onhand, safetystock, '%s'
                from (
                  select operationplanmaterial.item_id,
                  operationplanmaterial.location_id,
                  operationplan.batch,
                  item.cost,
                  operationplanmaterial.onhand,
                  (select safetystock from
                    (
                    select 1 as priority, coalesce(
                      (select value from calendarbucket
                       where calendar_id = 'SS for '||operationplanmaterial.item_id||' @ '||operationplanmaterial.location_id
                       and '%s' >= startdate and '%s' < enddate
                       order by priority limit 1),
                      (select defaultvalue from calendar where name = 'SS for '||operationplanmaterial.item_id||' @ '||operationplanmaterial.location_id)
                      ) as safetystock
                    union all
                    select 2 as priority, coalesce(
                      (select value
                       from calendarbucket
                       where calendar_id = buffer.minimum_calendar_id
                       and '%s' >= startdate
                       and '%s' < enddate
                       order by priority limit 1),
                      (select defaultvalue
                       from calendar
                       where name = buffer.minimum_calendar_id
                      )
                    ) as safetystock
                    union all
                    select 3 as priority, buffer.minimum
                    ) t
                    where t.safetystock is not null
                    order by priority
                    limit 1
                  ) safetystock,
                  row_number() over (
                    partition by operationplanmaterial.item_id, operationplanmaterial.location_id, operationplan.batch
                    order by operationplanmaterial.flowdate desc, operationplanmaterial.onhand asc
                    ) as rownumber
                  from operationplanmaterial
                  inner join operationplan on operationplan.reference = operationplanmaterial.operationplan_id
                  left outer join buffer on buffer.item_id = operationplanmaterial.item_id
                  and buffer.location_id = operationplanmaterial.location_id
                  and buffer.batch is not distinct from operationplan.batch
                  inner join item on item.name = operationplanmaterial.item_id
                  where flowdate < '%s'
                ) recs
                where rownumber = 1
                """
                % ((now,) * 6)
            )
            buffer_records = cursor.rowcount

            # Archiving demand table
            cursor.execute(
                """
                insert into ax_demand (name, item, location, customer, cost, due, status, priority, quantity,
                                      deliverydate, quantityplanned, snapshot_date_id)
                select demand.name, demand.item_id, demand.location_id, demand.customer_id, item.cost,
                demand.due, demand.status, demand.priority, demand.quantity, operationplan.enddate, operationplan.quantity, '%s'
                from demand
                inner join item on demand.item_id = item.name
                left outer join operationplan on operationplan.demand_id = demand.name
                where demand.status in ('open', 'quote')
                """
                % (now,)
            )
            demand_records = cursor.rowcount

            # Archiving POs
            cursor.execute(
                """
                insert into ax_operationplan
                (reference, status, type, quantity, startdate, enddate, item, supplier, location, item_cost, itemsupplier_cost, snapshot_date_id)
                select op.reference, op.status, op.type, op.quantity, op.startdate, op.enddate, op.item_id, op.supplier_id, op.location_id,
                item.cost, itemsupplier.cost, '%s'
                from operationplan op
                inner join item on op.item_id = item.name
                left outer join itemsupplier on itemsupplier.item_id = op.item_id and itemsupplier.supplier_id = op.supplier_id
                where
                op.type = 'PO' and op.status in ('confirmed','approved')
                """
                % (now,)
            )
            operationplan_records = cursor.rowcount

            mgr.buffer_records = buffer_records
            mgr.demand_records = demand_records
            mgr.operationplan_records = operationplan_records
            mgr.total_records = buffer_records + demand_records + operationplan_records
            mgr.save(using=database)

            # TODO Deleted archived data we don't need to any longer
