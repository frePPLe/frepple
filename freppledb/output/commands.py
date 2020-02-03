#
# Copyright (C) 2011-2019 by frePPLe bvba
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

from datetime import timedelta, datetime, date
import json
import logging
import os
from psycopg2.extensions import adapt
from psycopg2.extras import execute_batch

from django.db import connections, DEFAULT_DB_ALIAS, transaction

from freppledb.common.commands import (
    PlanTaskRegistry,
    PlanTask,
    clean_value,
    CopyFromGenerator,
)

logger = logging.getLogger(__name__)


@PlanTaskRegistry.register
class TruncatePlan(PlanTask):

    description = "Erasing previous plan"
    sequence = 400

    @classmethod
    def getWeight(cls, **kwargs):
        if "supply" in os.environ:
            return 1
        else:
            return -1

    @classmethod
    def run(cls, cluster=-1, database=DEFAULT_DB_ALIAS, **kwargs):
        import frepple

        cursor = connections[database].cursor()
        if cluster == -1:
            # Complete export for the complete model
            cursor.execute(
                "truncate table out_problem, out_resourceplan, out_constraint"
            )
            cursor.execute(
                """
                update operationplan
                  set owner_id = null
                  where owner_id is not null
                  and exists (
                    select 1
                    from operationplan op2
                    where op2.reference = operationplan.owner_id
                    and (op2.status is null or op2.status = 'proposed')
                    )
                """
            )
            cursor.execute(
                """
                truncate operationplanmaterial, operationplanresource
                """
            )
            cursor.execute(
                """
                delete from operationplan
                where (status='proposed' or status is null) or type = 'STCK'
                """
            )
        else:
            # Partial export for a single cluster
            cursor.execute(
                "create temporary table cluster_keys (name character varying(300), constraint cluster_key_pkey primary key (name))"
            )
            for i in frepple.items():
                if i.cluster == cluster:
                    cursor.execute(
                        (
                            "insert into cluster_keys (name) values (%s);\n"
                            % adapt(i.name).getquoted().decode("UTF8")
                        )
                    )
            cursor.execute(
                """
                delete from out_constraint
                where demand in (
                  select demand.name
                  from demand
                  inner join cluster_keys
                    on cluster_keys.name = demand.item_id
                  )
                """
            )

            cursor.execute(
                """
                delete from out_problem
                where entity = 'demand' and owner in (
                  select demand.name from demand inner join cluster_keys on cluster_keys.name = demand.item_id
                  )
                """
            )
            cursor.execute(
                """
                delete from out_problem
                where entity = 'material'
                and owner in (
                   select buffer.item_id || ' @ ' || buffer.location_id
                   from buffer
                   inner join cluster_keys on cluster_keys.name = buffer.item_id
                   )
                """
            )

            cursor.execute(
                """
                delete from operationplan
                using cluster_keys
                where owner_id in (
                  select oplan_parent.reference
                  from operationplan as oplan_parent
                  where (oplan_parent.status='proposed' or oplan_parent.status is null or oplan_parent.type='STCK')
                  and oplan_parent.item_id = cluster_keys.name
                  )
                """
            )
            cursor.execute(
                """
                delete from operationplan
                using cluster_keys
                where (status='proposed' or status is null or type='STCK')
                and item_id = cluster_keys.name
                """
            )
            cursor.execute("truncate table cluster_keys")
            for i in frepple.resources():
                if i.cluster == cluster:
                    cursor.execute(
                        (
                            "insert into cluster_keys (name) values (%s)"
                            % adapt(i.name).getquoted().decode("UTF8")
                        )
                    )
            cursor.execute(
                """
                delete from out_problem
                where entity = 'demand'
                and owner in (
                  select demand.name
                  from demand
                  inner join cluster_keys on cluster_keys.name = demand.item_id
                  )
                """
            )
            cursor.execute(
                "delete from operationplanresource using cluster_keys where resource_id = cluster_keys.name"
            )
            cursor.execute(
                "delete from out_resourceplan using cluster_keys where resource = cluster_keys.name"
            )
            cursor.execute(
                "delete from out_problem using cluster_keys where entity = 'capacity' and owner = cluster_keys.name"
            )
            cursor.execute("truncate table cluster_keys")
            for i in frepple.operations():
                if i.cluster == cluster:
                    cursor.execute(
                        (
                            "insert into cluster_keys (name) values (%s)"
                            % adapt(i.name).getquoted().decode("UTF8")
                        )
                    )
            cursor.execute(
                """"
                delete from out_problem
                using cluster_keys
                where entity = 'operation' and owner = cluster_keys.name
                """
            )
            cursor.execute(
                """
                delete from operationplan
                using cluster_keys
                where (status='proposed' or status is null)
                and operationplan.name = cluster_keys.name
                """
            )
            cursor.execute("drop table cluster_keys")


@PlanTaskRegistry.register
class ShowPlanStats(PlanTask):

    description = "Show plan statistics"
    sequence = 402

    @classmethod
    def getWeight(cls, **kwargs):
        if "supply" in os.environ:
            return 0.01
        else:
            return -1

    @staticmethod
    def run(database=DEFAULT_DB_ALIAS, **kwargs):
        cursor = connections[database].cursor()
        cursor.execute(
            """
            select 'out_problem', count(*) from out_problem
            union select 'out_constraint', count(*) from out_constraint
            union select 'operationplanmaterial', count(*) from operationplanmaterial
            union select 'operationplanresource', count(*) from operationplanresource
            union select 'out_resourceplan', count(*) from out_resourceplan
            union select 'operationplan', count(*) from operationplan
            order by 1
            """
        )
        for table, recs in cursor.fetchall():
            logger.info("Table %s: %d records" % (table, recs))


@PlanTaskRegistry.register
class ExportProblems(PlanTask):

    description = ("Export plan", "Exporting problems")
    sequence = (401, "export2", 2)

    @classmethod
    def getWeight(cls, **kwargs):
        if "supply" in os.environ:
            return 1
        else:
            return -1

    @staticmethod
    def getData(cluster=-1):
        import frepple

        for i in frepple.problems():
            if isinstance(i.owner, frepple.operationplan):
                owner = i.owner.operation
            else:
                owner = i.owner
            if cluster != -1 and owner.cluster != cluster:
                continue
            yield "%s\v%s\v%s\v%s\v%s\v%s\v%s\n" % (
                clean_value(i.entity),
                clean_value(i.name),
                clean_value(owner.name),
                clean_value(i.description),
                str(i.start),
                str(i.end),
                round(i.weight, 8),
            )

    @classmethod
    def run(cls, cluster=-1, database=DEFAULT_DB_ALIAS, **kwargs):
        cursor = connections[database].cursor()
        cursor.copy_from(
            CopyFromGenerator(cls.getData(cluster)),
            "out_problem",
            columns=(
                "entity",
                "name",
                "owner",
                "description",
                "startdate",
                "enddate",
                "weight",
            ),
            size=1024,
            sep="\v",
        )


@PlanTaskRegistry.register
class ExportConstraints(PlanTask):

    description = ("Export plan", "Exporting constraints")
    sequence = (401, "export2", 3)

    @classmethod
    def getWeight(cls, **kwargs):
        if "supply" in os.environ:
            return 1
        else:
            return -1

    @staticmethod
    def getData(cluster=-1):
        import frepple

        for d in frepple.demands():
            if cluster != -1 and cluster != d.cluster:
                continue
            for i in d.constraints:
                yield "%s\v%s\v%s\v%s\v%s\v%s\v%s\v%s\n" % (
                    clean_value(d.name),
                    clean_value(i.entity),
                    clean_value(i.name),
                    isinstance(i.owner, frepple.operationplan)
                    and clean_value(i.owner.operation.name)
                    or clean_value(i.owner.name),
                    clean_value(i.description),
                    str(i.start),
                    str(i.end),
                    round(i.weight, 8),
                )

    @classmethod
    def run(cls, cluster=-1, database=DEFAULT_DB_ALIAS, **kwargs):
        cursor = connections[database].cursor()
        cursor.copy_from(
            CopyFromGenerator(cls.getData(cluster=cluster)),
            "out_constraint",
            columns=(
                "demand",
                "entity",
                "name",
                "owner",
                "description",
                "startdate",
                "enddate",
                "weight",
            ),
            size=1024,
            sep="\v",
        )


@PlanTaskRegistry.register
class ExportOperationPlans(PlanTask):

    description = ("Export plan", "Exporting operationplans")
    sequence = (401, "export1", 1)

    @classmethod
    def getWeight(cls, **kwargs):
        if "supply" in os.environ:
            return 1
        else:
            return -1

    @staticmethod
    def getPegging(opplan, buffer=None):
        unavail = opplan.unavailable
        pln = {
            "pegging": {
                j.demand.name: round(j.quantity, 8) for j in opplan.pegging_demand
            },
            "unavailable": unavail,
            "interruptions": [
                (
                    i.start.strftime("%Y-%m-%d %H:%M:%S"),
                    i.end.strftime("%Y-%m-%d %H:%M:%S"),
                )
                for i in opplan.interruptions
            ]
            if unavail
            else [],
        }
        if not opplan.feasible:
            pln["feasible"] = False
        if opplan.setupend != opplan.start:
            pln["setup"] = opplan.setup
            pln["setupend"] = opplan.setupend.strftime("%Y-%m-%d %H:%M:%S")
        if buffer:
            if buffer.item:
                pln["item"] = buffer.item.name
            if buffer.location:
                pln["location"] = buffer.location.name
        # We need to double any backslash to assure that the string remains
        # valid when passing it through postgresql (which eats them away)
        return json.dumps(pln).replace("\\", "\\\\")

    @classmethod
    def getData(cls, timestamp, cluster=-1):
        import frepple

        for i in frepple.operations():
            if cluster != -1 and cluster != i.cluster:
                continue
            for j in i.operationplans:
                delay = j.delay
                color = 100 - delay / 86400

                if isinstance(i, frepple.operation_inventory):
                    # Export inventory
                    yield "%s\v%s\v%s\v%s\v%s\v%s\v%s\v%s\v%s\v%s\v%s\v%s\v%s\v%s\v%s\v%s\v%s\v%s\v%s\v%s\v%s\v%s\n" % (
                        clean_value(i.name),
                        "STCK",
                        j.status,
                        round(j.quantity, 8),
                        str(j.start),
                        str(j.end),
                        round(j.criticality, 8),
                        j.delay,
                        cls.getPegging(j),
                        clean_value(j.source),
                        timestamp,
                        "\\N",
                        clean_value(j.owner.reference)
                        if j.owner and not j.owner.operation.hidden
                        else "\\N",
                        clean_value(j.operation.buffer.item.name),
                        clean_value(j.operation.buffer.location.name),
                        "\\N",
                        "\\N",
                        "\\N",
                        clean_value(j.demand.name)
                        if j.demand
                        else clean_value(j.owner.demand.name)
                        if j.owner and j.owner.demand
                        else "\\N",
                        j.demand.due
                        if j.demand
                        else j.owner.demand.due
                        if j.owner and j.owner.demand
                        else "\\N",
                        color,
                        clean_value(j.reference),
                    )
                elif isinstance(i, frepple.operation_itemdistribution):
                    # Export DO
                    yield "%s\v%s\v%s\v%s\v%s\v%s\v%s\v%s\v%s\v%s\v%s\v%s\v%s\v%s\v%s\v%s\v%s\v%s\v%s\v%s\v%s\v%s\n" % (
                        clean_value(i.name),
                        "DO",
                        j.status,
                        round(j.quantity, 8),
                        str(j.start),
                        str(j.end),
                        round(j.criticality, 8),
                        j.delay,
                        cls.getPegging(j),
                        clean_value(j.source),
                        timestamp,
                        "\\N",
                        clean_value(j.owner.reference)
                        if j.owner and not j.owner.operation.hidden
                        else "\\N",
                        clean_value(j.operation.destination.item.name)
                        if j.operation.destination
                        else j.operation.origin.item.name,
                        clean_value(j.operation.destination.location.name)
                        if j.operation.destination
                        else "\\N",
                        clean_value(j.operation.origin.location.name)
                        if j.operation.origin
                        else "\\N",
                        "\\N",
                        "\\N",
                        clean_value(j.demand.name)
                        if j.demand
                        else clean_value(j.owner.demand.name)
                        if j.owner and j.owner.demand
                        else "\\N",
                        j.demand.due
                        if j.demand
                        else j.owner.demand.due
                        if j.owner and j.owner.demand
                        else "\\N",
                        color,
                        clean_value(j.reference),
                    )
                elif isinstance(i, frepple.operation_itemsupplier):
                    # Export PO
                    yield "%s\v%s\v%s\v%s\v%s\v%s\v%s\v%s\v%s\v%s\v%s\v%s\v%s\v%s\v%s\v%s\v%s\v%s\v%s\v%s\v%s\v%s\n" % (
                        clean_value(i.name),
                        "PO",
                        j.status,
                        round(j.quantity, 8),
                        str(j.start),
                        str(j.end),
                        round(j.criticality, 8),
                        j.delay,
                        cls.getPegging(j),
                        clean_value(j.source),
                        timestamp,
                        "\\N",
                        clean_value(j.owner.reference)
                        if j.owner and not j.owner.operation.hidden
                        else "\\N",
                        clean_value(j.operation.buffer.item.name),
                        "\\N",
                        "\\N",
                        clean_value(j.operation.buffer.location.name),
                        clean_value(j.operation.itemsupplier.supplier.name),
                        clean_value(j.demand.name)
                        if j.demand
                        else clean_value(j.owner.demand.name)
                        if j.owner and j.owner.demand
                        else "\\N",
                        j.demand.due
                        if j.demand
                        else j.owner.demand.due
                        if j.owner and j.owner.demand
                        else "\\N",
                        color,
                        clean_value(j.reference),
                    )
                elif not i.hidden:
                    # Export MO
                    yield "%s\v%s\v%s\v%s\v%s\v%s\v%s\v%s\v%s\v%s\v%s\v%s\v%s\v%s\v%s\v%s\v%s\v%s\v%s\v%s\v%s\v%s\n" % (
                        clean_value(i.name),
                        "MO",
                        j.status,
                        round(j.quantity, 8),
                        str(j.start),
                        str(j.end),
                        round(j.criticality, 8),
                        j.delay,
                        cls.getPegging(j),
                        clean_value(j.source),
                        timestamp,
                        clean_value(i.name),
                        clean_value(j.owner.reference)
                        if j.owner and not j.owner.operation.hidden
                        else "\\N",
                        clean_value(i.item.name) if i.item else "\\N",
                        "\\N",
                        "\\N",
                        clean_value(i.location.name) if i.location else "\\N",
                        "\\N",
                        clean_value(j.demand.name)
                        if j.demand
                        else clean_value(j.owner.demand.name)
                        if j.owner and j.owner.demand
                        else "\\N",
                        j.demand.due
                        if j.demand
                        else j.owner.demand.due
                        if j.owner and j.owner.demand
                        else "\\N",
                        color,
                        clean_value(j.reference),
                    )
                elif j.demand or (j.owner and j.owner.demand):
                    # Export shipments (with automatically created delivery operations)
                    yield "%s\v%s\v%s\v%s\v%s\v%s\v%s\v%s\v%s\v%s\v%s\v%s\v%s\v%s\v%s\v%s\v%s\v%s\v%s\v%s\v%s\v%s\n" % (
                        clean_value(i.name),
                        "DLVR",
                        j.status,
                        round(j.quantity, 8),
                        str(j.start),
                        str(j.end),
                        round(j.criticality, 8),
                        j.delay,
                        cls.getPegging(j),
                        clean_value(j.source),
                        timestamp,
                        "\\N",
                        clean_value(j.owner.reference)
                        if j.owner and not j.owner.operation.hidden
                        else "\\N",
                        clean_value(j.operation.buffer.item.name),
                        "\\N",
                        "\\N",
                        clean_value(j.operation.buffer.location.name),
                        "\\N",
                        clean_value(j.demand.name)
                        if j.demand
                        else clean_value(j.owner.demand.name)
                        if j.owner and j.owner.demand
                        else "\\N",
                        j.demand.due
                        if j.demand
                        else j.owner.demand.due
                        if j.owner and j.owner.demand
                        else "\\N",
                        color,
                        clean_value(j.reference),
                    )

    @classmethod
    def run(cls, cluster=-1, database=DEFAULT_DB_ALIAS, **kwargs):

        # Set the timestamp for the export tasks in this thread
        cls.parent.timestamp = datetime.now()

        # Export operationplans to a temporary table
        cursor = connections[database].cursor()
        cursor.execute(
            """
            create temporary table tmp_operationplan (
                name character varying(1000),
                type character varying(5) NOT NULL,
                status character varying(20),
                quantity numeric(20,8) NOT NULL,
                startdate timestamp with time zone,
                enddate timestamp with time zone,
                criticality numeric(20,8),
                delay numeric,
                plan json,
                source character varying(300),
                lastmodified timestamp with time zone NOT NULL,
                operation_id character varying(300),
                owner_id character varying(300),
                item_id character varying(300),
                destination_id character varying(300),
                origin_id character varying(300),
                location_id character varying(300),
                supplier_id character varying(300),
                demand_id character varying(300),
                due timestamp with time zone,
                color numeric(20,8),
                reference character varying(300) NOT NULL
            );
            """
        )
        cursor.copy_from(
            CopyFromGenerator(cls.getData(cls.parent.timestamp, cluster=cluster)),
            table="tmp_operationplan",
            size=1024,
            sep="\v",
        )

        # Merge temp table into the actual table
        cursor.execute(
            """
            update operationplan
                set name=tmp.name, type=tmp.type, status=tmp.status,
                quantity=tmp.quantity, startdate=tmp.startdate, enddate=tmp.enddate,
                criticality=tmp.criticality, delay=tmp.delay * interval '1 second',
                plan=tmp.plan, source=tmp.source,
                lastmodified=tmp.lastmodified, operation_id=tmp.operation_id, owner_id=tmp.owner_id,
                item_id=tmp.item_id, destination_id=tmp.destination_id, origin_id=tmp.origin_id,
                location_id=tmp.location_id, supplier_id=tmp.supplier_id, demand_id=tmp.demand_id,
                due=tmp.due, color=tmp.color
            from tmp_operationplan as tmp
            where operationplan.reference = tmp.reference;
            """
        )
        cursor.execute(
            """
            delete from operationplan
            where status in ('confirmed','approved','completed')
            and type = 'MO'
            and not exists (select 1 from tmp_operationplan where reference = operationplan.reference)
            """
        )

        cursor.execute(
            """
            insert into operationplan
              (name,type,status,quantity,startdate,enddate,
              criticality,delay,plan,source,lastmodified,
              operation_id,owner_id,
              item_id,destination_id,origin_id,
              location_id,supplier_id,
              demand_id,due,color,reference)
            select name,type,status,quantity,startdate,enddate,
              criticality,delay * interval '1 second',plan,source,lastmodified,
              operation_id,owner_id,
              item_id,destination_id,origin_id,
              location_id,supplier_id,
              demand_id,due,color,reference
            from tmp_operationplan
            where not exists (
              select 1
              from operationplan
              where operationplan.reference = tmp_operationplan.reference
              );
            """
        )

        # update demand table specific fields
        cursor.execute(
            """
            with cte as (
              select demand_id, sum(quantity) plannedquantity, max(enddate) deliverydate, max(enddate)-due as delay
              from operationplan
              where demand_id is not null and owner_id is null
              group by demand_id, due
            )
            update demand
              set delay = cte.delay,
              plannedquantity = cte.plannedquantity,
              deliverydate = cte.deliverydate
            from cte
            where cte.demand_id = demand.name
            """
        )
        cursor.execute(
            """
            update demand set
              delay = null,
              plannedquantity = null,
              deliverydate = null
            where (delay is not null or plannedquantity is not null or deliverydate is not null)
            and not exists(
              select 1 from operationplan where owner_id is null and operationplan.demand_id = demand.name
              )
            """
        )
        cursor.execute(
            """
            update demand
              set plannedquantity = 0
            where status in ('open','quote') and plannedquantity is null
            """
        )


@PlanTaskRegistry.register
class ExportOperationPlanMaterials(PlanTask):

    description = ("Export plan", "Exporting operationplan materials")
    sequence = (401, "export1", 2)

    @classmethod
    def getWeight(cls, **kwargs):
        if "supply" in os.environ:
            return 1
        else:
            return -1

    @staticmethod
    def getData(timestamp, cluster=-1):
        import frepple

        for i in frepple.buffers():
            if cluster != -1 and cluster != i.cluster:
                continue
            for j in i.flowplans:
                # if the record is confirmed, it is already in the table.
                if not j.operationplan.reference:
                    logger.error(
                        "Warning: skip exporting uninitialized operationplan %s %s %s %s"
                        % (
                            j.operationplan.operation.name,
                            j.operationplan.quantity,
                            j.operationplan.start,
                            j.operationplan.end,
                        )
                    )
                else:
                    yield "%s\v%s\v%s\v%s\v%s\v%s\v%s\v%s\v%s\v%s\n" % (
                        clean_value(j.operationplan.id),
                        clean_value(j.buffer.item.name),
                        clean_value(j.buffer.location.name),
                        round(j.quantity, 8),
                        str(j.date),
                        round(j.onhand, 8),
                        round(j.minimum, 8),
                        round(j.period_of_cover, 8),
                        j.status,
                        timestamp,
                    )

    @classmethod
    def run(cls, cluster=-1, database=DEFAULT_DB_ALIAS, **kwargs):
        cursor = connections[database].cursor()
        updates = []
        cursor.copy_from(
            CopyFromGenerator(
                cls.getData(timestamp=cls.parent.timestamp, cluster=cluster)
            ),
            "operationplanmaterial",
            columns=(
                "operationplan_id",
                "item_id",
                "location_id",
                "quantity",
                "flowdate",
                "onhand",
                "minimum",
                "periodofcover",
                "status",
                "lastmodified",
            ),
            size=1024,
            sep="\v",
        )
        if len(updates) > 0:
            cursor.execute("\n".join(updates))


@PlanTaskRegistry.register
class ExportOperationPlanResources(PlanTask):

    description = ("Export plan", "Exporting operationplan resources")
    sequence = (401, "export1", 3)

    @classmethod
    def getWeight(cls, **kwargs):
        if "supply" in os.environ:
            return 1
        else:
            return -1

    @staticmethod
    def getData(timestamp, cluster=-1):
        import frepple

        for i in frepple.resources():
            if cluster != -1 and cluster != i.cluster:
                continue
            for j in i.loadplans:
                if j.quantity >= 0:
                    continue
                if not j.operationplan.reference:
                    logger.warn(
                        "Warning: skip exporting uninitialized operationplan: %s %s %s %s"
                        % (
                            j.operationplan.operation.name,
                            j.operationplan.quantity,
                            j.operationplan.start,
                            j.operationplan.end,
                        )
                    )
                else:
                    yield "%s\v%s\v%s\v%s\v%s\v%s\v%s\v%s\n" % (
                        clean_value(j.operationplan.reference),
                        clean_value(j.resource.name),
                        round(-j.quantity, 8),
                        str(j.startdate),
                        str(j.enddate),
                        clean_value(j.setup),
                        j.status,
                        timestamp,
                    )

    @classmethod
    def run(cls, cluster=-1, database=DEFAULT_DB_ALIAS, **kwargs):
        cursor = connections[database].cursor()
        cursor.copy_from(
            CopyFromGenerator(
                cls.getData(timestamp=cls.parent.timestamp, cluster=cluster)
            ),
            "operationplanresource",
            columns=(
                "operationplan_id",
                "resource_id",
                "quantity",
                "startdate",
                "enddate",
                "setup",
                "status",
                "lastmodified",
            ),
            size=1024,
            sep="\v",
        )


@PlanTaskRegistry.register
class ExportResourcePlans(PlanTask):

    description = ("Export plan", "Exporting resource plans")
    sequence = (401, "export2", 1)

    @classmethod
    def getWeight(cls, **kwargs):
        if "supply" in os.environ:
            return 1
        else:
            return -1

    @classmethod
    def run(cls, cluster=-1, database=DEFAULT_DB_ALIAS, **kwargs):
        import frepple

        # Set the timestamp for the export tasks in this thread
        cls.parent.timestamp = datetime.now()

        # Determine start and end date of the reporting horizon
        # The start date is computed as 5 weeks before the start of the earliest loadplan in
        # the entire plan.
        # The end date is computed as 5 weeks after the end of the latest loadplan in
        # the entire plan.
        # If no loadplans exist at all we use the current date +- 1 month.
        cursor = connections[database].cursor()
        startdate = datetime.max
        enddate = datetime.min
        for i in frepple.resources():
            if cluster != -1 and cluster != i.cluster:
                continue
            for j in i.loadplans:
                if j.startdate < startdate:
                    startdate = j.startdate
                if j.enddate > enddate:
                    enddate = j.enddate
        if startdate == datetime.max:
            startdate = frepple.settings.current
        if enddate == datetime.min:
            enddate = frepple.settings.current
        startdate = (startdate - timedelta(days=30)).date()
        enddate = (enddate + timedelta(days=30)).date()
        if enddate > date(2030, 12, 30):  # This is the max frePPLe can represent.
            enddate = date(2030, 12, 30)
        cursor.execute(
            """
            select startdate
            from common_bucketdetail
            where startdate between %s and %s
              and bucket_id = (select name from common_bucket order by level desc limit 1)
            """,
            (startdate, enddate),
        )
        buckets = [rec[0] for rec in cursor.fetchall()]

        def getData():
            # Loop over all reporting buckets of all resources
            for i in frepple.resources():
                for j in i.plan(buckets):
                    yield "%s\v%s\v%s\v%s\v%s\v%s\v%s\n" % (
                        clean_value(i.name),
                        str(j["start"]),
                        round(j["available"], 8),
                        round(j["unavailable"], 8),
                        round(j["setup"], 8),
                        round(j["load"], 8),
                        round(j["free"], 8),
                    )

        cursor.copy_from(
            CopyFromGenerator(getData()),
            "out_resourceplan",
            columns=(
                "resource",
                "startdate",
                "available",
                "unavailable",
                "setup",
                "load",
                "free",
            ),
            size=1024,
            sep="\v",
        )


@PlanTaskRegistry.register
class ExportPegging(PlanTask):

    description = ("Export plan", "Exporting demand pegging")
    sequence = (401, "export1", 4)

    @classmethod
    def getWeight(cls, **kwargs):
        if "supply" in os.environ:
            return 1
        else:
            return -1

    @staticmethod
    def getDemandPlan(cluster=-1):
        import frepple

        for i in frepple.demands():
            if cluster != -1 and cluster != i.cluster:
                continue
            if i.hidden or not isinstance(i, frepple.demand_default):
                continue
            peg = []
            for j in i.pegging:
                peg.append(
                    {
                        "level": j.level,
                        "opplan": j.operationplan.reference,
                        "quantity": j.quantity,
                    }
                )
            yield (json.dumps({"pegging": peg}), i.name)

    @classmethod
    def run(cls, cluster=-1, database=DEFAULT_DB_ALIAS, **kwargs):
        with transaction.atomic(using=database, savepoint=False):
            cursor = connections[database].cursor()
            execute_batch(
                cursor,
                "update demand set plan=%s where name=%s",
                cls.getDemandPlan(cluster=cluster),
                page_size=200,
            )


@PlanTaskRegistry.register
class ExportPlanToFile(PlanTask):
    """
    Inactive task.
    """

    description = "Export plan to CSV files"
    sequence = 500

    @staticmethod
    def getWeight(**kwargs):
        return -1

    @staticmethod
    def run(database=DEFAULT_DB_ALIAS, **kwargs):
        from freppledb.execute.export_file_plan import exportfrepple

        exportfrepple()


@PlanTaskRegistry.register
class ExportPlanToXML(PlanTask):
    """
    Inactive task.
    """

    description = "Export plan to an XML file"
    sequence = 600

    @staticmethod
    def getWeight(**kwargs):
        return -1

    @staticmethod
    def run(database=DEFAULT_DB_ALIAS, **kwargs):
        import frepple

        frepple.saveXMLfile("output.1.xml", "BASE")
        # frepple.saveXMLfile("output.2.xml","PLAN")
        # frepple.saveXMLfile("output.3.xml","PLANDETAIL")
