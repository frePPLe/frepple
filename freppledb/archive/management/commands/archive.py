#
# Copyright (C) 2020 by frePPLe bv
#
# Permission is hereby granted, free of charge, to any person obtaining
# a copy of this software and associated documentation files (the
# "Software"), to deal in the Software without restriction, including
# without limitation the rights to use, copy, modify, merge, publish,
# distribute, sublicense, and/or sell copies of the Software, and to
# permit persons to whom the Software is furnished to do so, subject to
# the following conditions:
#
# The above copyright notice and this permission notice shall be
# included in all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND,
# EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF
# MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND
# NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE
# LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION
# OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION
# WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.
#

from datetime import datetime, timedelta

from django.db import DEFAULT_DB_ALIAS, connections
from django.core.management.base import BaseCommand

from freppledb import __version__
from freppledb.archive.models import ArchiveManager
from freppledb.common.models import Parameter
from freppledb.common.report import getCurrentDate


class Command(BaseCommand):
    help = """
      This command archives historical plan data.
      """

    requires_system_checks = []

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

        # Delete archived data we don't need any longer
        p = int(Parameter.getValue("archive.duration", database, "365"))
        now = getCurrentDate(database)
        ArchiveManager.objects.using(database).filter(
            snapshot_date__lt=now - timedelta(days=p)
        ).delete()

        # create a new snapshot
        with connections[database].cursor() as cursor:

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
                select item_id, location_id, batch, onhand, cost, safetystock, '%s'
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
                (reference, status, type, quantity, startdate, enddate, item, operation, supplier, location, item_cost, itemsupplier_cost, snapshot_date_id)
                select op.reference, op.status, op.type, op.quantity, op.startdate, op.enddate, op.item_id, op.operation_id, op.supplier_id, op.location_id,
                item.cost, itemsupplier.cost, '%s'
                from operationplan op
                inner join item on op.item_id = item.name
                left outer join itemsupplier on itemsupplier.item_id = op.item_id and itemsupplier.supplier_id = op.supplier_id
                where
                op.type <> 'STCK' and op.status in ('confirmed','approved','completed')
                """
                % (now,)
            )
            operationplan_records = cursor.rowcount

            mgr.buffer_records = buffer_records
            mgr.demand_records = demand_records
            mgr.operationplan_records = operationplan_records
            mgr.total_records = buffer_records + demand_records + operationplan_records
            mgr.save(using=database)
