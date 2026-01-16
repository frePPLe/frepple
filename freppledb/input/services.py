#
# Copyright (C) 2023 by frePPLe bv
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

import frepple

from collections import OrderedDict
import json

from channels.db import database_sync_to_async
from channels.generic.http import AsyncHttpConsumer

from freppledb.boot import getAttributes
from freppledb.common.commands import PlanTaskRegistry
from freppledb.common.localization import parseLocalizedDateTime, parseLocalizedDate
from freppledb.input.models import OperationPlan
from freppledb.webservice.utils import lock


@database_sync_to_async
def savePlan(
    deleted_opplans,
    related_opplans,
    related_resources,
    related_buffers,
    related_demands,
    database,
    cluster,
):
    try:
        PlanTaskRegistry.run(
            export=1,
            cluster=cluster,
            database=database,
            deleted_opplans=deleted_opplans,
            opplans=related_opplans,
            resources=related_resources,
            buffers=related_buffers,
            demands=related_demands,
        )
    except Exception as e:
        print("Error saving plan:", e)
        raise e


def collectRelated(
    opplan,
    related_opplans,
    related_resources,
    related_buffers,
    related_demands,
):
    for d in opplan.loadplans:
        related_resources.add(d.resource)
    for d in opplan.flowplans:
        related_buffers.add(d.buffer)
        for flpln in d.buffer.flowplans:
            if isinstance(flpln.operationplan.operation, frepple.operation_inventory):
                # Force stck opplan to be present in the database
                related_opplans.add(flpln.operationplan)
            break
    for c in opplan.operationplans:
        if c not in related_opplans:
            related_opplans.add(c)
            collectRelated(
                c,
                related_opplans,
                related_resources,
                related_buffers,
                related_demands,
            )
    if opplan.demand:
        related_demands.add(opplan.demand)
    if opplan.owner:
        if opplan.owner not in related_opplans:
            related_opplans.add(opplan.owner)
            collectRelated(
                opplan.owner,
                related_opplans,
                related_resources,
                related_buffers,
                related_demands,
            )
    for i in opplan.blockedby:
        if i.first not in related_opplans:
            related_opplans.add(i.first)
            collectRelated(
                i.first,
                related_opplans,
                related_resources,
                related_buffers,
                related_demands,
            )
    for i in opplan.blocking:
        if i.second not in related_opplans:
            related_opplans.add(i.second)
            collectRelated(
                i.second,
                related_opplans,
                related_resources,
                related_buffers,
                related_demands,
            )


opplanAttributes = [a for a in getAttributes(OperationPlan)]


class OperationplanService(AsyncHttpConsumer):
    msgtemplate = """
        <!doctype html>
        <html lang="en">
            <head>
            <meta http-equiv="content-type" content="text/html; charset=utf-8">
            </head>
            <body>%s</body>
        </html>
        """

    async def handle(self, body):
        errors = []
        try:
            if self.scope["method"] != "POST":
                self.scope["response_headers"].append((b"Content-Type", b"text/html"))
                await self.send_response(
                    401,
                    (self.msgtemplate % "Only POST requests allowed").encode(),
                    headers=self.scope["response_headers"],
                )
                return

            data = json.loads(body.decode("utf-8"))
            deleted_opplans = set()
            related_opplans = set()
            related_resources = set()
            related_buffers = set()
            related_demands = set()

            async with lock:
                # Update the plan in memory
                for rec in data:
                    try:
                        for d in rec.get("delete", []):
                            if self.scope["user"].has_perm(
                                "input.delete_operationplan"
                            ):
                                opplan = frepple.operationplan(
                                    {"reference": d, "action": "C"}
                                )
                                if opplan:
                                    collectRelated(
                                        opplan,
                                        related_opplans,
                                        related_resources,
                                        related_buffers,
                                        related_demands,
                                    )
                                    deleted_opplans.add(opplan.reference)
                                    del opplan
                            elif "permission denied" not in errors:
                                errors.append("permission denied")

                        # Build arguments
                        rsrcs_by_ref = None
                        changes = OrderedDict()
                        ref = rec.get(
                            "operationplan__reference",
                            rec.get(
                                "operationplan__id",
                                rec.get("reference", rec.get("id", None)),
                            ),
                        )
                        if ref:
                            changes["reference"] = ref
                            opplan = frepple.operationplan(reference=ref, action="C")
                            changes["ordertype"] = opplan.ordertype
                        else:
                            changes["ordertype"] = rec.get("type", "MO")
                        if changes["ordertype"] == "PO":
                            if "location" in rec:
                                changes["location"] = frepple.location(
                                    name=rec["location"], action="C"
                                )
                            if "supplier" in rec:
                                changes["supplier"] = frepple.supplier(
                                    name=rec["supplier"], action="C"
                                )
                            if "item" in rec:
                                changes["item"] = frepple.item(
                                    name=rec["item"], action="C"
                                )
                        elif changes["ordertype"] == "DO":
                            if "destination" in rec:
                                changes["location"] = frepple.location(
                                    name=rec["destination"], action="C"
                                )
                            if "origin" in rec:
                                changes["origin"] = frepple.location(
                                    name=rec["origin"], action="C"
                                )
                            if "item" in rec:
                                changes["item"] = frepple.item(
                                    name=rec["item"], action="C"
                                )
                        elif changes["ordertype"] == "MO":
                            if "operation" in rec:
                                changes["operation"] = frepple.operation(
                                    name=rec["operation"], action="C"
                                )
                        if "operationplan__quantity" in rec:
                            changes["quantity"] = float(rec["operationplan__quantity"])
                        elif "quantity" in rec:
                            changes["quantity"] = float(rec["quantity"])
                        if "operationplan__quantity_completed" in rec:
                            changes["quantity_completed"] = float(
                                rec["operationplan__quantity_completed"]
                            )
                        elif "quantity_completed" in rec:
                            changes["quantity_completed"] = float(
                                rec["quantity_completed"]
                            )
                        if "enddate" in rec and rec["enddate"] != "\xa0":
                            changes["end"] = parseLocalizedDateTime(
                                rec["enddate"]
                            ).strftime("%Y-%m-%dT%H:%M:%S")
                        elif (
                            "operationplan__enddate" in rec
                            and rec["operationplan__enddate"] != "\xa0"
                        ):
                            changes["end"] = parseLocalizedDateTime(
                                rec["operationplan__enddate"]
                            ).strftime("%Y-%m-%dT%H:%M:%S")
                        if "startdate" in rec and rec["startdate"] != "\xa0":
                            changes["start"] = parseLocalizedDateTime(
                                rec["startdate"]
                            ).strftime("%Y-%m-%dT%H:%M:%S")
                        elif (
                            "operationplan__startdate" in rec
                            and rec["operationplan__startdate"] != "\xa0"
                        ):
                            changes["start"] = parseLocalizedDateTime(
                                rec["operationplan__startdate"]
                            ).strftime("%Y-%m-%dT%H:%M:%S")
                        if "demand" in rec:
                            changes["demand"] = rec["demand"]
                        if "batch" in rec:
                            changes["batch"] = rec["batch"]
                        if "status" in rec:
                            changes["status"] = rec["status"]
                        elif "operationplan__status" in rec:
                            changes["status"] = rec["operationplan__status"]
                        rsrcs = rec.get("resources", rec.get("resource", None))
                        if rsrcs:
                            # Force deletion of existing loadplans (because the loadplan data isn't in delta mode)
                            if isinstance(rsrcs, str):
                                changes["resources"] = [rsrcs]
                            else:
                                rsrcs_by_ref = {}
                                for l in rsrcs:
                                    if l[2] in rsrcs_by_ref:
                                        rsrcs_by_ref[l[2]].append(l[0])
                                    else:
                                        rsrcs_by_ref[l[2]] = [l[0]]
                                if changes.get("reference", None) in rsrcs_by_ref:
                                    changes["resources"] = rsrcs_by_ref[
                                        changes["reference"]
                                    ]
                                    del rsrcs_by_ref[changes["reference"]]
                        if "remark" in rec:
                            changes["remark"] = rec["remark"]
                        for attr in opplanAttributes:
                            if attr[0] in rec and attr[3]:
                                if attr[2] in ("integer", "number"):
                                    changes[attr[0]] = float(rec[attr[0]])
                                elif attr[2] == "datetime":
                                    changes[attr[0]] = parseLocalizedDateTime(
                                        rec[attr[0]]
                                    ).strftime("%Y-%m-%dT%H:%M:%S")
                                elif attr[2] == "date":
                                    changes[attr[0]] = parseLocalizedDate(
                                        rec[attr[0]]
                                    ).strftime("%Y-%m-%d")
                                else:
                                    changes[attr[0]] = rec[attr[0]]

                        # Update the engine
                        if changes or rsrcs_by_ref:
                            if self.scope["user"].has_perm(
                                "input.change_operationplan"
                                if ref
                                else "input.add_operationplan"
                            ):
                                if ref:
                                    # Original related objects
                                    collectRelated(
                                        opplan,
                                        related_opplans,
                                        related_resources,
                                        related_buffers,
                                        related_demands,
                                    )
                                    # Update children
                                    if rsrcs_by_ref:
                                        for child_ref, res in rsrcs_by_ref.items():
                                            child_opplan = frepple.operationplan(
                                                reference=child_ref, action="C"
                                            )
                                            collectRelated(
                                                child_opplan,
                                                related_opplans,
                                                related_resources,
                                                related_buffers,
                                                related_demands,
                                            )
                                            child_opplan = frepple.operationplan(
                                                reference=child_ref,
                                                resources=res,
                                                action="C",
                                            )
                                            collectRelated(
                                                child_opplan,
                                                related_opplans,
                                                related_resources,
                                                related_buffers,
                                                related_demands,
                                            )
                                    # Update
                                    changes["action"] = "C"
                                    opplan = frepple.operationplan(**changes)
                                    if "end" in changes:
                                        opplan.end_force = changes["end"]
                                    if "start" in changes:
                                        opplan.start_force = changes["start"]
                                else:
                                    opplan = frepple.operationplan(**changes)
                                    for fld, val in changes.items():
                                        if fld == "end":
                                            setattr(opplan, "end_force", val)
                                        elif fld == "start":
                                            setattr(opplan, "start_force", val)
                                        elif fld != "reference":
                                            setattr(opplan, fld, val)
                                # New related objects
                                related_opplans.add(opplan)
                                collectRelated(
                                    opplan,
                                    related_opplans,
                                    related_resources,
                                    related_buffers,
                                    related_demands,
                                )
                            elif "permission denied" not in errors:
                                errors.append("permission denied")

                    except Exception as e:
                        errors.append(str(e))

                # Save all changes
                if (
                    deleted_opplans
                    or related_opplans
                    or related_resources
                    or related_buffers
                    or related_demands
                ):
                    try:
                        await savePlan(
                            deleted_opplans,
                            related_opplans,
                            related_resources,
                            related_buffers,
                            related_demands,
                            self.scope["database"],
                            -2,
                        )
                    except Exception as e:
                        print("exception " % e)
                        errors.append("Error saving plan")

            self.scope["response_headers"].append((b"Content-Type", b"text/html"))
            if errors:
                await self.send_response(
                    500,
                    json.dumps({"errors": errors}).encode(),
                    headers=self.scope["response_headers"],
                )
            else:
                await self.send_response(
                    200,
                    b'{"OK": 1}',
                    headers=self.scope["response_headers"],
                )
        except Exception as e:
            print("exception " % e)
            await self.send_response(
                500,
                b"Error updating operationplans",
                headers=self.scope["response_headers"],
            )
