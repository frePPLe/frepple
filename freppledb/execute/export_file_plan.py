#
# Copyright (C) 2007-2013 by frePPLe bv
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

r"""
Exports frePPLe plan information to a set of flat files.
The code iterates over all objects in the C++ core engine, and writes this
information to a set of text files.

The code in this file is NOT executed by Django, but by the embedded Python
interpreter from the frePPLe engine.

THIS CODE IS CURRENTLY NOT USED, AND IS NOT UPDATED OR TESTED.
WE LEAVE IT HERE AS-IS, HOPING IT MIGHT BE USEFUL TO SOME FOLKS IN
THE USER COMMUNITY.
"""
from time import time
from datetime import datetime, timedelta
import csv

import frepple


def exportProblems():
    print("Exporting problems...")
    starttime = time()
    writer = csv.writer(
        open("problems.csv", "w", newline="", encoding="utf-8"), quoting=csv.QUOTE_ALL
    )
    writer.writerow(
        ("#entity", "name", "description", "start date", "end date", "weight")
    )
    for i in frepple.problems():
        writer.writerow(
            (i.entity, i.name, i.owner.name, i.description, i.start, i.end, i.weight)
        )
    print("Exported problems in %.2f seconds" % (time() - starttime))


def exportConstraints():
    print("Exporting constraints...")
    starttime = time()
    writer = csv.writer(
        open("constraints.csv", "w", newline="", encoding="utf-8"),
        quoting=csv.QUOTE_ALL,
    )
    writer.writerow(
        (
            "#demand",
            "entity",
            "name",
            "owner",
            "description",
            "start date",
            "end date",
            "weight",
        )
    )
    for d in frepple.demands():
        for i in d.constraints:
            writer.writerow(
                (
                    d.name,
                    i.entity,
                    i.name,
                    i.owner.name,
                    i.description,
                    i.start,
                    i.end,
                    i.weight,
                )
            )
    print("Exported constraints in %.2f seconds" % (time() - starttime))


def exportOperationplans():
    print("Exporting operationplans...")
    starttime = time()
    writer = csv.writer(
        open("operations.csv", "w", newline="", encoding="utf-8"), quoting=csv.QUOTE_ALL
    )
    writer.writerow(
        (
            "#reference",
            "operation",
            "quantity",
            "start date",
            "end date",
            "status",
            "unavailable",
            "owner",
        )
    )
    for i in frepple.operationplans():
        writer.writerow(
            (
                i.reference,
                i.operation.name,
                i.quantity,
                i.start,
                i.end,
                i.status,
                i.unavailable,
                i.owner and i.owner.id or None,
            )
        )
    print("Exported operationplans in %.2f seconds" % (time() - starttime))


def exportFlowplans():
    print("Exporting flowplans...")
    starttime = time()
    writer = csv.writer(
        open("flowplans.csv", "w", newline="", encoding="utf-8"), quoting=csv.QUOTE_ALL
    )
    writer.writerow(
        ("#operationplan", "item", "location", "quantity", "date", "on hand")
    )
    for i in frepple.buffers():
        for j in i.flowplans:
            writer.writerow(
                (
                    j.operationplan.reference,
                    j.buffer.item.name,
                    j.buffer.location.name,
                    j.quantity,
                    j.date,
                    j.onhand,
                )
            )
    print("Exported flowplans in %.2f seconds" % (time() - starttime))


def exportLoadplans():
    print("Exporting loadplans...")
    starttime = time()
    writer = csv.writer(
        open("loadplans.csv", "w", newline="", encoding="utf-8"), quoting=csv.QUOTE_ALL
    )
    writer.writerow(
        ("#operationplan", "resource", "quantity", "start date", "end date", "setup")
    )
    for i in frepple.resources():
        for j in i.loadplans:
            if j.quantity < 0:
                writer.writerow(
                    (
                        j.operationplan.reference,
                        j.resource.name,
                        -j.quantity,
                        j.startdate,
                        j.enddate,
                        j.setup and j.setup or None,
                    )
                )
    print("Exported loadplans in %.2f seconds" % (time() - starttime))


def exportResourceplans():
    print("Exporting resourceplans...")
    starttime = time()
    writer = csv.writer(
        open("resources.csv", "w", newline="", encoding="utf-8"), quoting=csv.QUOTE_ALL
    )
    writer.writerow(
        ("#resource", "startdate", "available", "unavailable", "setup", "load", "free")
    )

    # Determine start and end date of the reporting horizon
    # The start date is computed as 5 weeks before the start of the earliest loadplan in
    # the entire plan.
    # The end date is computed as 5 weeks after the end of the latest loadplan in
    # the entire plan.
    # If no loadplan exists at all we use the current date +- 1 month.
    startdate = datetime.max
    enddate = datetime.min
    for i in frepple.resources():
        for j in i.loadplans:
            if j.startdate < startdate:
                startdate = j.startdate
            if j.enddate > enddate:
                enddate = j.enddate
    if not startdate:
        startdate = frepple.settings.current
    if not enddate:
        enddate = frepple.settings.current
    startdate -= timedelta(weeks=5)
    enddate += timedelta(weeks=5)
    startdate = startdate.replace(hour=0, minute=0, second=0)
    enddate = enddate.replace(hour=0, minute=0, second=0)

    # Build a list of horizon buckets
    buckets = []
    while startdate < enddate:
        buckets.append(startdate)
        startdate += timedelta(days=1)

    # Loop over all reporting buckets of all resources
    for i in frepple.resources():
        for j in i.plan(buckets):
            writer.writerow(
                (
                    i.name,
                    j["start"],
                    j["available"],
                    j["unavailable"],
                    j["setup"],
                    j["load"],
                    j["free"],
                )
            )
    print("Exported resourceplans in %.2f seconds" % (time() - starttime))


def exportDemand():
    def deliveries(d):
        cumplanned = 0
        n = d
        while n.hidden and n.owner:
            n = n.owner
        n = n and n.name or "unspecified"
        # Loop over all delivery operationplans
        for i in d.operationplans:
            cumplanned += i.quantity
            cur = i.quantity
            if cumplanned > d.quantity:
                cur -= cumplanned - d.quantity
                if cur < 0:
                    cur = 0
            yield (
                n,
                d.item.name,
                d.customer and d.customer.name or None,
                d.due,
                cur,
                i.end,
                i.quantity,
                i.id,
            )
        # Extra record if planned short
        if cumplanned < d.quantity:
            yield (
                n,
                d.item.name,
                d.customer and d.customer.name or None,
                d.due,
                d.quantity - cumplanned,
                None,
                None,
                None,
            )

    print("Exporting demand plans...")
    starttime = time()
    writer = csv.writer(
        open("demands.csv", "w", newline="", encoding="utf-8"), quoting=csv.QUOTE_ALL
    )
    writer.writerow(
        (
            "#demand",
            "item",
            "customer",
            "due date",
            "requested quantity",
            "plan date",
            "plan quantity",
            "operationplan",
        )
    )
    for i in frepple.demands():
        if i.quantity == 0:
            continue
        for j in deliveries(i):
            writer.writerow(j)
    print("Exported demand plans in %.2f seconds" % (time() - starttime))


def exportPegging():
    print("Exporting pegging...")
    starttime = time()
    writer = csv.writer(
        open("demand_pegging.csv", "w", newline="", encoding="utf-8"),
        quoting=csv.QUOTE_ALL,
    )
    writer.writerow(("#demand", "level", "operationplan", "quantity"))
    for i in frepple.demands():
        # Find non-hidden demand owner
        n = i
        while n.hidden and n.owner:
            n = n.owner
        n = n and n.name or "unspecified"
        # Export pegging
        for j in i.pegging:
            writer.writerow((n, j.level, j.operationplan.reference, j.quantity))
    print("Exported pegging in %.2f seconds" % (time() - starttime))


def exportfrepple():
    exportProblems()
    exportConstraints()
    exportOperationplans()
    exportFlowplans()
    exportLoadplans()
    exportResourceplans()
    exportDemand()
    exportPegging()
