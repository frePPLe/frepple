#
# Copyright (C) 2011-2013 by frePPLe bvba
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

r"""
Exports the plan information from the frePPLe C++ core engine into a
PostgreSQL database.

The code in this file is executed NOT by the Django web application, but by the
embedded Python interpreter from the frePPLe engine.
"""
from datetime import timedelta, datetime, date
import io
import json
import logging
import os
from psycopg2.extensions import adapt
from psycopg2.extras import execute_batch
from time import time
from threading import Thread

from django.db import connections, DEFAULT_DB_ALIAS, transaction
from django.conf import settings

import frepple

logger = logging.getLogger(__name__)


def clean_value(value):
    if value is None:
        return "\\N"
    elif "\n" in value or "\\" in value:
        return value.replace("\n", "\\n").replace("\\", "\\\\")
    else:
        return value


class CopyFromGenerator(io.TextIOBase):
    """
    Inspired on and copied from:
      https://hakibenita.com/fast-load-data-python-postgresql
    """

    def __init__(self, itr):
        self._iter = itr
        self._buff = ""

    def readable(self):
        return True

    def _read1(self, n=None):
        while not self._buff:
            try:
                self._buff = next(self._iter)
            except StopIteration:
                break
        ret = self._buff[:n]
        self._buff = self._buff[len(ret) :]
        return ret

    def read(self, n=None):
        line = []
        if n is None or n < 0:
            while True:
                m = self._read1()
                if not m:
                    break
                line.append(m)
        else:
            while n > 0:
                m = self._read1(n)
                if not m:
                    break
                n -= len(m)
                line.append(m)
        return "".join(line)


class DatabasePipe(Thread):
    """
  An auxiliary class that allows us to run a function with its own
  PostgreSQL process pipe.
  """

    def __init__(self, owner, *f):
        self.owner = owner
        super().__init__()
        self.functions = f

    def run(self):
        # Pass the database password to the psql environment
        try:
            for f in self.functions:
                f(self.owner)
        finally:
            pass


class export:
    def __init__(self, cluster=-1, verbosity=1, database=None):
        self.cluster = cluster
        self.verbosity = verbosity
        if database:
            self.database = database
        else:
            if "FREPPLE_DATABASE" in os.environ:
                self.database = os.environ["FREPPLE_DATABASE"]
            else:
                self.database = DEFAULT_DB_ALIAS
        self.encoding = "UTF8"
        self.timestamp = str(datetime.now())

    def getPegging(self, opplan, buffer=None):
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

    def truncate(self):
        cursor = connections[self.database].cursor()
        if self.verbosity:
            logger.info("Emptying database plan tables...")
        starttime = time()
        if self.cluster == -1:
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
                if i.cluster == self.cluster:
                    cursor.execute(
                        (
                            "insert into cluster_keys (name) values (%s);\n"
                            % adapt(i.name).getquoted().decode(self.encoding)
                        )
                    )
            cursor.execute(
                "delete from out_constraint where demand in (select demand.name from demand inner join cluster_keys on cluster_keys.name = demand.item_id)"
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
            # TODO next subqueries are not efficient - the exists condition triggers a sequential scan
            cursor.execute(
                "delete from out_constraint where exists (select 1 from forecast inner join cluster_keys on cluster_keys.name = forecast.item_id and out_constraint.demand like forecast.name || ' - %')"
            )
            cursor.execute(
                "delete from out_problem where entity = 'demand' and exists (select 1 from forecast inner join cluster_keys on cluster_keys.name = forecast.item_id and out_problem.owner like forecast.name || ' - %')"
            )
            cursor.execute("truncate table cluster_keys")
            for i in frepple.resources():
                if i.cluster == self.cluster:
                    cursor.execute(
                        (
                            "insert into cluster_keys (name) values (%s)"
                            % adapt(i.name).getquoted().decode(self.encoding)
                        )
                    )
            cursor.execute(
                "delete from out_problem where entity = 'demand' and owner in (select demand.name from demand inner join cluster_keys on cluster_keys.name = demand.item_id)"
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
                if i.cluster == self.cluster:
                    cursor.execute(
                        (
                            "insert into cluster_keys (name) values (%s)"
                            % adapt(i.name).getquoted().decode(self.encoding)
                        )
                    )
            cursor.execute(
                "delete from out_problem using cluster_keys where entity = 'operation' and owner = cluster_keys.name"
            )
            cursor.execute(
                "delete from operationplan using cluster_keys where (status='proposed' or status is null) and operationplan.name = cluster_keys.name"
            )
            cursor.execute("drop table cluster_keys")
        if self.verbosity:
            logger.info("Emptied plan tables in %.2f seconds" % (time() - starttime))

    def exportProblems(self):
        def getData():
            for i in frepple.problems():
                if isinstance(i.owner, frepple.operationplan):
                    owner = i.owner.operation
                else:
                    owner = i.owner
                if self.cluster != -1 and owner.cluster != self.cluster:
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

        if self.verbosity:
            logger.info("Exporting problems...")
        starttime = time()
        cursor = connections[self.database].cursor()
        cursor.copy_from(
            CopyFromGenerator(getData()),
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
        if self.verbosity:
            logger.info("Exported problems in %.2f seconds" % (time() - starttime))

    def exportConstraints(self):
        def getData():
            for d in frepple.demands():
                if self.cluster != -1 and self.cluster != d.cluster:
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

        if self.verbosity:
            logger.info("Exporting constraints...")
        starttime = time()
        cursor = connections[self.database].cursor()
        cursor.copy_from(
            CopyFromGenerator(getData()),
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

        if self.verbosity:
            logger.info("Exported constraints in %.2f seconds" % (time() - starttime))

    def exportOperationplans(self):
        def getData():
            for i in frepple.operations():
                if self.cluster != -1 and self.cluster != i.cluster:
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
                            self.getPegging(j),
                            clean_value(j.source),
                            self.timestamp,
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
                            self.getPegging(j),
                            clean_value(j.source),
                            self.timestamp,
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
                            self.getPegging(j),
                            clean_value(j.source),
                            self.timestamp,
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
                            self.getPegging(j),
                            clean_value(j.source),
                            self.timestamp,
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
                            self.getPegging(j),
                            clean_value(j.source),
                            self.timestamp,
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

        if self.verbosity:
            logger.info("Exporting operationplans...")
        starttime = time()
        cursor = connections[self.database].cursor()

        # Export operationplans to a temporary table
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
            CopyFromGenerator(getData()), table="tmp_operationplan", size=1024, sep="\v"
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
            delete
            from operationplan
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

        if self.verbosity:
            logger.info(
                "Exported operationplans in %.2f seconds" % (time() - starttime)
            )

    def exportOperationPlanMaterials(self):
        def getData():
            for i in frepple.buffers():
                if self.cluster != -1 and self.cluster != i.cluster:
                    continue
                for j in i.flowplans:
                    # if the record is confirmed, it is already in the table.
                    if not j.operationplan.reference:
                        print(
                            "Warning: skip exporting uninitialized operationplan",
                            j.operationplan.operation.name,
                            j.operationplan.quantity,
                            j.operationplan.start,
                            j.operationplan.end,
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
                            self.timestamp,
                        )

        if self.verbosity:
            logger.info("Exporting operationplan materials...")
        starttime = time()
        cursor = connections[self.database].cursor()
        updates = []
        cursor.copy_from(
            CopyFromGenerator(getData()),
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
        if self.verbosity:
            logger.info(
                "Exported operationplan materials in %.2f seconds"
                % (time() - starttime)
            )

    def exportOperationPlanResources(self):
        def getData():
            for i in frepple.resources():
                if self.cluster != -1 and self.cluster != i.cluster:
                    continue
                for j in i.loadplans:
                    if j.quantity >= 0:
                        continue
                    if not j.operationplan.reference:
                        print(
                            "Warning: skip exporting uninitialized operationplan: ",
                            j.operationplan.operation.name,
                            j.operationplan.quantity,
                            j.operationplan.start,
                            j.operationplan.end,
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
                            self.timestamp,
                        )

        if self.verbosity:
            logger.info("Exporting operationplan resources...")
        starttime = time()
        cursor = connections[self.database].cursor()
        cursor.copy_from(
            CopyFromGenerator(getData()),
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
        if self.verbosity:
            logger.info(
                "Exported operationplan resources in %.2f seconds"
                % (time() - starttime)
            )

    def exportResourceplans(self):
        # Build a list of horizon buckets
        if self.verbosity:
            logger.info("Exporting resourceplans...")
        starttime = time()

        # Determine start and end date of the reporting horizon
        # The start date is computed as 5 weeks before the start of the earliest loadplan in
        # the entire plan.
        # The end date is computed as 5 weeks after the end of the latest loadplan in
        # the entire plan.
        # If no loadplans exist at all we use the current date +- 1 month.
        cursor = connections[self.database].cursor()
        startdate = datetime.max
        enddate = datetime.min
        for i in frepple.resources():
            if self.cluster != -1 and self.cluster != i.cluster:
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
        if self.verbosity:
            logger.info("Exported resourceplans in %.2f seconds" % (time() - starttime))

    def exportPegging(self):
        def getDemandPlan():
            for i in frepple.demands():
                if self.cluster != -1 and self.cluster != i.cluster:
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

        logger.info("Exporting demand pegging...")
        starttime = time()
        with transaction.atomic(using=self.database, savepoint=False):
            cursor = connections[self.database].cursor()
            execute_batch(
                cursor,
                "update demand set plan=%s where name=%s",
                getDemandPlan(),
                page_size=200,
            )
        logger.info("Exported demand pegging in %.2f seconds" % (time() - starttime))

    def run(self):
        """
        This function exports the data from the frePPLe memory into the database.
        The export runs in parallel over 2 connections to PostgreSQL.
        """
        # Truncate
        task = DatabasePipe(self, export.truncate)
        task.start()
        task.join()

        # Export process
        tasks = (
            DatabasePipe(
                self,
                export.exportResourceplans,
                export.exportProblems,
                export.exportConstraints,
            ),
            DatabasePipe(
                self,
                export.exportOperationplans,
                export.exportOperationPlanMaterials,
                export.exportOperationPlanResources,
                export.exportPegging,
            ),
        )

        # Start all threads
        for i in tasks:
            i.start()
        # Wait for all threads to finish
        for i in tasks:
            i.join()

        # Report on the output
        if self.verbosity:
            cursor = connections[self.database].cursor()
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
