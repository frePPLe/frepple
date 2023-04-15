#
# Copyright (C) 2011-2019 by frePPLe bv
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

from datetime import timedelta, datetime, date
import json
import logging
import os
from psycopg2.extras import execute_batch

from django.conf import settings
from django.db import connections, DEFAULT_DB_ALIAS, transaction

from freppledb.common.commands import (
    PlanTaskRegistry,
    PlanTask,
    clean_value,
    CopyFromGenerator,
)
from freppledb.input.models import OperationPlan
from freppledb.boot import getAttributes

logger = logging.getLogger(__name__)


@PlanTaskRegistry.register
class TruncatePlan(PlanTask):
    description = "Erasing previous plan"
    sequence = 400
    export = True

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
                if i.cluster in cluster:
                    cursor.execute(
                        "insert into cluster_keys (name) values (%s)", (i.name,)
                    )

            cursor.execute("create index on cluster_keys (name)")

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
                with opplans as (
                    select oplan_parent.reference
                    from operationplan as oplan_parent
                    inner join cluster_keys on oplan_parent.item_id = cluster_keys.name
                    where (oplan_parent.status='proposed' or oplan_parent.status is null or oplan_parent.type='STCK')
                    and oplan_parent.item_id = cluster_keys.name
                    union all
                    select oplan.reference
                    from operationplan as oplan
                    inner join cluster_keys on oplan.item_id = cluster_keys.name
                    where oplan.status='proposed' or oplan.status is null or oplan.type='STCK'
                ),
                opplanmat as (
                delete from operationplanmaterial
                using opplans
                where opplans.reference = operationplan_id
                ),
                opplanres as (
                delete from operationplanresource
                using opplans
                where opplans.reference = operationplan_id
                )
                delete from operationplan
                using opplans
                where opplans.reference = operationplan.reference
                """
            )

            cursor.execute("truncate table cluster_keys")
            for i in frepple.resources():
                if i.cluster in cluster:
                    cursor.execute(
                        "insert into cluster_keys (name) values (%s)", (i.name,)
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
                if i.cluster in cluster:
                    cursor.execute(
                        "insert into cluster_keys (name) select substring(%s from 1 for 300)",
                        (i.name,),
                    )
            cursor.execute(
                """
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
    export = True

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
            if cluster != -1 and owner.cluster not in cluster:
                continue
            yield "%s\v%s\v%s\v%s\v%s\v%s\v%s\n" % (
                clean_value(i.entity),
                clean_value(i.name),
                clean_value(owner.name)[:300],
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
    export = True

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
            if cluster != -1 and d.cluster not in cluster:
                continue
            for i in d.constraints:
                yield "%s\v%s\v%s\v%s\v%s\v%s\v%s\v%s\v%s\v%s\n" % (
                    clean_value(d.name)
                    if isinstance(d, frepple.demand_default)
                    else "\\N",
                    "\\N"
                    if isinstance(d, frepple.demand_default)
                    else clean_value(d.owner.name),
                    clean_value(d.item.name),
                    clean_value(i.entity),
                    clean_value(i.name),
                    (
                        isinstance(i.owner, frepple.operationplan)
                        and clean_value(i.owner.operation.name)
                        or clean_value(i.owner.name)
                    )[:300],
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
                "forecast",
                "item",
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
    export = True

    @classmethod
    def getWeight(cls, **kwargs):
        if "supply" in os.environ or kwargs.get("exportstatic", False):
            return 1
        else:
            return -1

    @staticmethod
    def getPegging(opplan, buffer=None):
        import frepple

        unavail = opplan.unavailable
        downstream_opplans = []
        upstream_opplans = []

        # downstream
        for j in opplan.pegging_downstream_first_level:
            # some security
            if j.operationplan == opplan:
                continue
            if (
                # regular time_per/fixed time
                # followed by a non-suboperation
                (
                    j.level == 1
                    and (opplan.owner == None)
                    and not isinstance(opplan.operation, frepple.operation_routing)
                    and not isinstance(j.operationplan.owner, frepple.operation_routing)
                    and not isinstance(
                        j.operationplan.owner, frepple.operation_alternate
                    )
                )
                # regular time_per/fixed time
                # followed by an alternate
                or (
                    j.level == 2
                    and (opplan.owner == None)
                    and not isinstance(opplan.operation, frepple.operation_routing)
                    and not isinstance(opplan.operation, frepple.operation_alternate)
                    and j.operationplan.owner
                    and isinstance(
                        j.operationplan.owner.operation, frepple.operation_alternate
                    )
                )
                # routings will flow into the first step
                or (
                    j.level == 1
                    and isinstance(opplan.operation, frepple.operation_routing)
                    and opplan == j.operationplan.owner
                    and len([k.priority for k in opplan.operation.suboperations]) > 0
                    and j.operationplan.operation.priority
                    == min([k.priority for k in opplan.operation.suboperations])
                )
                # suboperations flow into the next subop
                or (
                    j.level == 1
                    and opplan.owner != None
                    and isinstance(opplan.owner.operation, frepple.operation_routing)
                    and len(
                        [
                            k.priority
                            for k in opplan.owner.operation.suboperations
                            if k.priority > opplan.operation.priority
                        ]
                    )
                    > 0
                    and j.operationplan.operation.priority
                    == min(
                        [
                            k.priority
                            for k in opplan.owner.operation.suboperations
                            if k.priority > opplan.operation.priority
                        ]
                    )
                )
                # last subopration flows into next level
                or (
                    j.level == 2
                    and opplan.owner != None
                    and isinstance(opplan.owner.operation, frepple.operation_routing)
                    and len(
                        [
                            k.priority
                            for k in opplan.owner.operation.suboperations
                            if k.priority > opplan.operation.priority
                        ]
                    )
                    == 0
                )
                # parent is alternate
                or (
                    j.level == 2
                    and opplan.owner != None
                    and isinstance(opplan.owner.operation, frepple.operation_alternate)
                )
            ):
                downstream_opplans.append(
                    (j.operationplan.reference, j.quantity, j.offset)
                )

        # upstream
        for j in opplan.pegging_upstream_first_level:
            # some security
            if j.operationplan == opplan:
                continue
            if (
                # regular time_per/fixed time
                # followed by a non-suboperation
                (
                    j.level == 1
                    and (opplan.owner == None)
                    and j.operationplan.owner == None
                    and not isinstance(
                        j.operationplan.operation, frepple.operation_alternate
                    )
                )
                # routings will flow into the previous step
                or (
                    j.level == 1
                    and isinstance(opplan.operation, frepple.operation_routing)
                    and opplan == j.operationplan.owner
                    and len([k.priority for k in opplan.operation.suboperations]) > 0
                    and j.operationplan.operation.priority
                    == max([k.priority for k in opplan.operation.suboperations])
                )
                # suboperations flow into the previous subop
                or (
                    j.level == 1
                    and opplan.owner != None
                    and isinstance(opplan.owner.operation, frepple.operation_routing)
                    and len(
                        [
                            k.priority
                            for k in opplan.owner.operation.suboperations
                            if k.priority < opplan.operation.priority
                        ]
                    )
                    > 0
                    and j.operationplan.operation.priority
                    == max(
                        [
                            k.priority
                            for k in opplan.owner.operation.suboperations
                            if k.priority < opplan.operation.priority
                        ]
                    )
                )
                # first suboperation flows into previous level
                or (
                    j.level == 2
                    and opplan.owner != None
                    and isinstance(opplan.owner.operation, frepple.operation_routing)
                    and len(
                        [
                            k.priority
                            for k in opplan.owner.operation.suboperations
                            if k.priority < opplan.operation.priority
                        ]
                    )
                    == 0
                )
                # case of first suboperation of a routing where prev operation is an alternate
                or (
                    j.level == 3
                    and j.operationplan.owner
                    and isinstance(
                        j.operationplan.owner.operation, frepple.operation_alternate
                    )
                    and opplan.owner != None
                    and isinstance(opplan.owner.operation, frepple.operation_routing)
                    and len(
                        [
                            k.priority
                            for k in opplan.owner.operation.suboperations
                            if k.priority < opplan.operation.priority
                        ]
                    )
                    == 0
                )
                # parent is alternate
                or (
                    j.level == 2
                    and opplan.owner != None
                    and isinstance(opplan.owner.operation, frepple.operation_alternate)
                )
                or (
                    j.level == 2
                    and j.operationplan.owner != None
                    and isinstance(
                        j.operationplan.owner.operation, frepple.operation_alternate
                    )
                )
            ):
                upstream_opplans.append(
                    (j.operationplan.reference, j.quantity, j.offset)
                )

        pln = {
            "pegging": {
                j.demand.name: round(j.quantity, 8) for j in opplan.pegging_demand
            },
            "downstream_opplans": downstream_opplans,
            "upstream_opplans": upstream_opplans,
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
        if opplan.rule:
            pln["setuprule"] = [opplan.rule.setupmatrix.name, opplan.rule.priority]
        # We need to double any backslash to assure that the string remains
        # valid when passing it through postgresql (which eats them away)
        return json.dumps(pln).replace("\\", "\\\\")

    @classmethod
    def getData(cls, timestamp, cluster=-1, accepted_status=[]):
        import frepple

        linetemplate = "%s\v%s\v%s\v%s\v%s\v%s\v%s\v%s\v%s\v%s\v%s\v%s\v%s\v%s\v%s\v%s\v%s\v%s\v%s\v%s\v%s\v%s\v%s\v%s"
        for unused in cls.attrs:
            linetemplate += "\v%s"
        linetemplate += "\n"

        for i in frepple.operations():
            if cluster != -1 and i.cluster not in cluster:
                continue

            # variable used to make sure only first proposed operationplan has its color set.
            proposedFound = False
            proposedFoundDate = None

            for j in i.operationplans:
                status = j.status
                if status not in accepted_status:
                    continue
                delay = j.delay
                color = 100 - delay / 86400

                data = None
                if isinstance(i, frepple.operation_inventory):
                    # Export inventory
                    data = [
                        clean_value(i.name),
                        "STCK",
                        status,
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
                        "\\N",  # color is empty for stock
                        clean_value(j.reference),
                        clean_value(j.batch),
                        "\\N",
                    ]
                elif isinstance(i, frepple.operation_itemdistribution):
                    # Export DO
                    data = [
                        clean_value(i.name),
                        "DO",
                        status,
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
                        color
                        if (proposedFound is False and status == "proposed")
                        or (status == "proposed" and j.start == proposedFoundDate)
                        or status in ("confirmed", "approved")
                        else "\\N",  # color
                        clean_value(j.reference),
                        clean_value(j.batch),
                        "\\N",
                    ]
                elif isinstance(i, frepple.operation_itemsupplier):
                    # Export PO
                    data = [
                        clean_value(i.name),
                        "PO",
                        status,
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
                        color
                        if (proposedFound is False and status == "proposed")
                        or (status == "proposed" and j.start == proposedFoundDate)
                        or status in ("confirmed", "approved")
                        else "\\N",  # color
                        clean_value(j.reference),
                        clean_value(j.batch),
                        "\\N",
                    ]
                elif not i.hidden:
                    # Export MO
                    data = [
                        clean_value(i.name),
                        "MO",
                        status,
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
                        clean_value(i.item.name)
                        if i.item
                        else clean_value(i.owner.item.name)
                        if i.owner and i.owner.item
                        else clean_value(j.demand.item.name)
                        if j.demand and j.demand.item
                        else clean_value(j.owner.demand.item.name)
                        if j.owner and j.owner.demand and j.owner.demand.item
                        else "\\N",
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
                        color
                        if (proposedFound is False and status == "proposed")
                        or (status == "proposed" and j.start == proposedFoundDate)
                        or status in ("confirmed", "approved")
                        else "\\N",  # color
                        clean_value(j.reference),
                        clean_value(j.batch),
                        round(j.quantity_completed, 8)
                        if j.quantity_completed
                        else "\\N",
                    ]
                elif j.demand or (j.owner and j.owner.demand):
                    # Export shipments (with automatically created delivery operations)
                    data = [
                        clean_value(i.name),
                        "DLVR",
                        status,
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
                        clean_value(
                            j.owner.demand.item.name
                            if j.owner and j.owner.demand
                            else j.demand.item.name
                        ),
                        "\\N",
                        "\\N",
                        clean_value(
                            j.owner.demand.location.name
                            if j.owner and j.owner.demand
                            else j.demand.location.name
                        ),
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
                        "\\N",  # color is empty for deliver operation
                        clean_value(j.reference),
                        clean_value(j.batch),
                        "\\N",
                    ]
                if data:
                    for attr in cls.attrs:
                        v = getattr(j, attr[0], None)
                        if v is None:
                            data.append("\\N")
                        elif attr[2] == "boolean":
                            data.append(True if v else False)
                        elif attr[2] == "duration":
                            data.append(v)
                        elif attr[2] == "integer":
                            data.append(round(v))
                        elif attr[2] == "number":
                            data.append(round(v, 6))
                        elif attr[2] == "string":
                            data.append(clean_value(v))
                        elif attr[2] == "time":
                            data.append(v)
                        elif attr[2] == "date":
                            data.append(v)
                        elif attr[2] == "datetime":
                            data.append(v)
                        else:
                            raise Exception("Unknown attribute type %s" % attr[2])
                    yield linetemplate % tuple(data)
                if status == "proposed":
                    proposedFound = True
                    proposedFoundDate = j.start

    @classmethod
    def run(cls, cluster=-1, database=DEFAULT_DB_ALIAS, **kwargs):
        with_fcst = "freppledb.forecast" in settings.INSTALLED_APPS

        cls.attrs = [x for x in getAttributes(OperationPlan) if x[0] != "forecast"]

        # Export operationplans to a temporary table
        cursor = connections[database].cursor()
        sql = """
            create temporary table tmp_operationplan (
                name character varying(1000),
                type character varying(5) NOT NULL,
                status character varying(20),
                quantity numeric(20,8) NOT NULL,
                startdate timestamp with time zone,
                enddate timestamp with time zone,
                criticality numeric(20,8),
                delay numeric,
                plan jsonb,
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
                reference character varying(300) NOT NULL,
                batch character varying(300),
                quantity_completed numeric(20,8)
            """
        for attr in cls.attrs:
            if attr[2] == "boolean":
                sql += ", %s boolean" % attr[0]
            elif attr[2] == "duration":
                sql += ", %s interval" % attr[0]
            elif attr[2] == "integer":
                sql += ", %s integer" % attr[0]
            elif attr[2] == "number":
                sql += ", %s numeric(15,6)" % attr[0]
            elif attr[2] == "string":
                sql += ", %s character varying(300)" % attr[0]
            elif attr[2] == "time":
                sql += ", %s time without time zone" % attr[0]
            elif attr[2] == "date":
                sql += ", %s date" % attr[0]
            elif attr[2] == "datetime":
                sql += ", %s timestamp with time zone" % attr[0]
            else:
                raise Exception("Unknown attribute type %s" % attr[2])
        sql += ")"
        cursor.execute(sql)

        cursor.copy_from(
            CopyFromGenerator(
                cls.getData(
                    cls.parent.timestamp,
                    cluster=cluster,
                    accepted_status=["confirmed", "approved", "completed", "closed"],
                )
            ),
            table="tmp_operationplan",
            size=1024,
            sep="\v",
        )

        if with_fcst:
            forecastfield0 = " ,forecast=excluded.forecast"
            forecastfield1 = " ,forecast"
        else:
            forecastfield0 = ""
            forecastfield1 = ""

        # Merge temp table into the actual table
        sql = """
            insert into operationplan (reference, name, type, status, quantity, startdate, enddate,
            criticality, delay, plan, source, lastmodified, operation_id, owner_id, item_id,
            destination_id, origin_id, location_id, supplier_id, demand_id, due%s, color, batch, quantity_completed %s)

            select reference, name, type, status, quantity, startdate, enddate,
            criticality, delay * interval '1 second', plan, source, lastmodified, operation_id, owner_id, item_id,
            destination_id, origin_id, location_id, supplier_id, demand_id, due%s, color, batch, quantity_completed %s
            from tmp_operationplan

            on conflict (reference) do update

            set name=excluded.name, type=excluded.type, status=excluded.status,
                quantity=excluded.quantity, startdate=excluded.startdate, enddate=excluded.enddate,
                criticality=excluded.criticality, delay=excluded.delay,
                plan=excluded.plan, source=excluded.source,
                lastmodified=excluded.lastmodified, operation_id=excluded.operation_id, owner_id=excluded.owner_id,
                item_id=excluded.item_id, destination_id=excluded.destination_id, origin_id=excluded.origin_id,
                location_id=excluded.location_id, supplier_id=excluded.supplier_id, demand_id=excluded.demand_id,
                due=excluded.due%s, color=excluded.color, batch=excluded.batch, quantity_completed=excluded.quantity_completed%s
            """ % (
            forecastfield1,
            "".join(",%s " % a[0] for a in cls.attrs),
            forecastfield1,
            "".join(",%s " % a[0] for a in cls.attrs),
            forecastfield0,
            "".join([", %s = excluded.%s" % (a[0], a[0]) for a in cls.attrs]),
        )

        cursor.execute(sql)

        # Make sure any deleted confirmed MO from Plan Editor gets deleted in the database
        # Only MO can currently be deleted through Plan Editor
        cursor.execute(
            """
            delete from operationplan
            where status in ('confirmed','approved','completed','closed')
            and type = 'MO'
            and not exists (select 1 from tmp_operationplan where reference = operationplan.reference)
            """
        )

        # directly injecting proposed records in operationplan table
        cursor.copy_from(
            CopyFromGenerator(
                cls.getData(
                    cls.parent.timestamp,
                    cluster=cluster,
                    accepted_status=["proposed"],
                )
            ),
            table="operationplan",
            size=1024,
            sep="\v",
            columns=[
                "name",
                "type",
                "status",
                "quantity",
                "startdate",
                "enddate",
                "criticality",
                "delay",
                "plan",
                "source",
                "lastmodified",
                "operation_id",
                "owner_id",
                "item_id",
                "destination_id",
                "origin_id",
                "location_id",
                "supplier_id",
                "demand_id",
                "due",
                "color",
                "reference",
                "batch",
                "quantity_completed",
            ]
            + [a[0] for a in cls.attrs],
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
    export = True

    @classmethod
    def getWeight(cls, **kwargs):
        if "supply" in os.environ or kwargs.get("exportstatic", False):
            return 1
        else:
            return -1

    @staticmethod
    def getData(timestamp, cluster=-1, buffers=None, **kwargs):
        import frepple

        for i in buffers or frepple.buffers():
            if cluster != -1 and i.cluster not in cluster:
                continue
            for j in i.flowplans:
                if not j.quantity:
                    continue
                elif not j.operationplan.reference:
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
                        clean_value(j.operationplan.reference),
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
    def run(cls, cluster=-1, database=DEFAULT_DB_ALIAS, timestamp=None, **kwargs):
        cursor = connections[database].cursor()
        cursor.copy_from(
            CopyFromGenerator(
                cls.getData(
                    timestamp=timestamp or cls.parent.timestamp,
                    cluster=cluster,
                    **kwargs
                )
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


@PlanTaskRegistry.register
class ComputePeriodOfCover(PlanTask):
    description = ("Export plan", "Compute period of cover")
    sequence = (401, "export1", 5)
    export = True

    @classmethod
    def getWeight(cls, **kwargs):
        if "supply" in os.environ:
            return 1
        else:
            return -1

    @staticmethod
    def getItemsFromCluster(
        cluster=-1,
    ):
        import frepple

        for i in frepple.items():
            if i.cluster in cluster:
                yield "%s\n" % (clean_value(i.name),)

    @classmethod
    def run(cls, cluster=-1, database=DEFAULT_DB_ALIAS, **kwargs):
        import frepple

        currentdate = frepple.settings.current
        cursor = connections[database].cursor()

        if cluster != -1:
            cursor.execute(
                """
                create temp table cluster_item_tmp as select name from item where false;
                """
            )

            cursor.copy_from(
                CopyFromGenerator(cls.getItemsFromCluster(cluster)),
                "cluster_item_tmp",
                sep="\v",
            )

            cursor.execute("create unique index on cluster_item_tmp (name);")

        cursor.execute(
            """
            -- Query assumes there is only 1 location
            -- all quantities are then aggregated
            update item
            set periodofcover = floor(extract(epoch from coalesce(
                  -- backlogged demand exceeds the inventory: 0 days of inventory
                  (
                  select '0 days'::interval
                  from operationplanmaterial
                  %s
                  inner join operationplan on operationplanmaterial.operationplan_id = operationplan.reference
                  where operationplanmaterial.item_id = item.name and
                    (
                      (operationplanmaterial.quantity < 0 and operationplan.type = 'DLVR' and operationplan.due < %%s)
                      or ( operationplanmaterial.quantity > 0 and operationplan.status = 'closed' and operationplan.type = 'STCK')
                      or ( operationplanmaterial.quantity > 0 and operationplan.status in ('approved','confirmed','completed') and flowdate <= %%s + interval '1 second')
                    )
                  having sum(operationplanmaterial.quantity) <0
                  limit 1
                  ),
                  -- Normal case
                  (
                  select case
                    when periodofcover = 999 * 24 * 3600
                      then '999 days'::interval
                    when onhand > 0.00001
                      then date_trunc('day', least( periodofcover * '1 sec'::interval + flowdate - %%s, '999 days'::interval))
                    else null
                    end
                  from operationplanmaterial
                  %s
                  where flowdate < %%s
                    and operationplanmaterial.item_id = item.name
                  order by flowdate desc, id desc
                  limit 1
                 ),
                 -- No inventory and no backlog: use the date of next consumer
                 (
                 select greatest('0 days'::interval, least(
                     date_trunc('day', justify_interval(flowdate - %%s - coalesce(operationplan.delay, '0 day'::interval))),
                     '999 days'::interval
                     ))
                  from operationplanmaterial
                  %s
                  inner join operationplan on operationplanmaterial.operationplan_id = operationplan.reference
                  where operationplanmaterial.quantity < 0
                    and operationplanmaterial.item_id = item.name
                  order by flowdate asc, id asc
                  limit 1
                 ),
                 '999 days'::interval
                 ))/86400)
                 %s
        """
            % (
                "inner join cluster_item_tmp on cluster_item_tmp.name = operationplanmaterial.item_id"
                if cluster != -1
                else "",
                "inner join cluster_item_tmp on cluster_item_tmp.name = operationplanmaterial.item_id"
                if cluster != -1
                else "",
                "inner join cluster_item_tmp on cluster_item_tmp.name = operationplanmaterial.item_id"
                if cluster != -1
                else "",
                "where name in (select name from cluster_item_tmp)"
                if cluster != -1
                else "",
            ),
            ((currentdate,) * 5),
        )

        if cluster != -1:
            cursor.execute("drop table cluster_item_tmp;")


@PlanTaskRegistry.register
class ExportOperationPlanResources(PlanTask):
    description = ("Export plan", "Exporting operationplan resources")
    sequence = (401, "export1", 3)
    export = True

    @classmethod
    def getWeight(cls, **kwargs):
        if "supply" in os.environ or kwargs.get("exportstatic", False):
            return 1
        else:
            return -1

    @staticmethod
    def getData(timestamp, resources=None, cluster=-1, **kwargs):
        import frepple

        for i in resources or frepple.resources():
            if cluster != -1 and i.cluster not in cluster:
                continue
            for j in i.loadplans:
                if j.quantity >= 0:
                    continue
                elif not j.operationplan.reference:
                    logger.warning(
                        "Warning: skip exporting uninitialized operationplan: %s %s %s %s"
                        % (
                            j.operationplan.operation.name,
                            j.operationplan.quantity,
                            j.operationplan.start,
                            j.operationplan.end,
                        )
                    )
                else:
                    yield "%s\v%s\v%s\v%s\v%s\v%s\n" % (
                        clean_value(j.operationplan.reference),
                        clean_value(j.resource.name),
                        round(-j.quantity, 8),
                        clean_value(j.setup),
                        j.status,
                        timestamp,
                    )

    @classmethod
    def run(
        cls,
        cluster=-1,
        database=DEFAULT_DB_ALIAS,
        timestamp=None,
        resources=None,
        **kwargs
    ):
        cursor = connections[database].cursor()
        cursor.copy_from(
            CopyFromGenerator(
                cls.getData(
                    timestamp=timestamp or cls.parent.timestamp,
                    cluster=cluster,
                    resources=resources,
                    **kwargs
                )
            ),
            "operationplanresource",
            columns=(
                "operationplan_id",
                "resource_id",
                "quantity",
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
    export = True

    @classmethod
    def getWeight(cls, **kwargs):
        if "supply" in os.environ:
            return 1
        else:
            return -1

    @classmethod
    def run(cls, cluster=-1, database=DEFAULT_DB_ALIAS, resources=None, **kwargs):
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
            if cluster != -1 and i.cluster not in cluster:
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
            order by startdate
            """,
            (startdate, enddate),
        )
        buckets = [rec[0] for rec in cursor.fetchall()]

        def getData():
            # Loop over all reporting buckets of all resources
            for i in resources or frepple.resources():
                if cluster != -1 and cluster != i.cluster:
                    continue
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
    export = True

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
            if cluster != -1 and i.cluster not in cluster:
                continue
            if i.hidden or not isinstance(i, frepple.demand_default):
                continue
            peg = []
            maxlevel = -1
            for j in i.pegging_first_level:
                if maxlevel >= 0 and j.level > maxlevel:
                    break
                maxlevel = j.level
                peg.append(
                    {
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
