#
# Copyright (C) 2007-2013 by Johan De Taeye, frePPLe bvba
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

r'''
Exports frePPLe information to flat files.

The code in this file is executed NOT by Django, but by the embedded Python
interpreter from the frePPLe engine.

The code iterates over all objects in the C++ core engine, and writes this
information to a set of text files.
'''
from time import time
from datetime import datetime, timedelta
import csv
import inspect

from django.conf import settings

import frepple

encoding = settings.CSV_CHARSET


def exportProblems():
  print("Exporting problems...")
  starttime = time()
  writer = csv.writer(open("problems.csv", "wb"), quoting=csv.QUOTE_ALL)
  writer.writerow((
    '#entity', 'name', 'description', 'start date', 'end date', 'weight'
    ))
  for i in frepple.problems():
    writer.writerow((
      i.entity, i.name.encode(encoding, "ignore"), i.owner.name.encode(encoding, "ignore"),
      i.description.encode(encoding, "ignore"), i.start, i.end, i.weight
      ))
  print('Exported problems in %.2f seconds' % (time() - starttime))


def exportConstraints():
  print("Exporting constraints...")
  starttime = time()
  writer = csv.writer(open("constraints.csv", "wb"), quoting=csv.QUOTE_ALL)
  writer.writerow((
    '#demand', 'entity', 'name', 'owner', 'description', 'start date', 'end date', 'weight'
    ))
  for d in frepple.demands():
    for i in d.constraints:
      writer.writerow((
        d.name.encode(encoding, "ignore"), i.entity, i.name.encode(encoding, "ignore"),
        i.owner.name.encode(encoding, "ignore"), i.description.encode(encoding, "ignore"),
        i.start, i.end, i.weight
        ))
  print('Exported constraints in %.2f seconds' % (time() - starttime))


def exportOperationplans():
  print("Exporting operationplans...")
  starttime = time()
  writer = csv.writer(open("operations.csv", "wb"), quoting=csv.QUOTE_ALL)
  writer.writerow((
    '#id', 'operation', 'quantity', 'start date', 'end date', 'locked'
    ))
  for i in frepple.operationplans():
    writer.writerow((
       i.id, i.operation.name.encode(encoding, "ignore"), i.quantity, i.start, i.end,
       i.locked, i.unavailable, i.owner and i.owner.id or None
     ))
  print('Exported operationplans in %.2f seconds' % (time() - starttime))


def exportFlowplans():
  print("Exporting flowplans...")
  starttime = time()
  writer = csv.writer(open("flowplans.csv", "wb"), quoting=csv.QUOTE_ALL)
  writer.writerow((
    '#operationplan id', 'buffer', 'quantity', 'date', 'on hand'
    ))
  for i in frepple.buffers():
    for j in i.flowplans:
      writer.writerow((
       j.operationplan.id, j.buffer.name.encode(encoding, "ignore"),
       j.quantity, j.date, j.onhand
       ))
  print('Exported flowplans in %.2f seconds' % (time() - starttime))


def exportLoadplans():
  print("Exporting loadplans...")
  starttime = time()
  writer = csv.writer(open("loadplans.csv", "wb"), quoting=csv.QUOTE_ALL)
  writer.writerow((
    '#operationplan id', 'resource', 'quantity', 'start date', 'end date', 'setup'
    ))
  for i in frepple.resources():
    for j in i.loadplans:
      if j.quantity < 0:
        writer.writerow((
          j.operationplan.id, j.resource.name.encode(encoding, "ignore"),
          -j.quantity, j.startdate, j.enddate, j.setup and j.setup.encode(encoding, "ignore") or None
          ))
  print('Exported loadplans in %.2f seconds' % (time() - starttime))


def exportResourceplans():
  print("Exporting resourceplans...")
  starttime = time()
  writer = csv.writer(open("resources.csv", "wb"), quoting=csv.QUOTE_ALL)
  writer.writerow((
    '#resource', 'startdate', 'available', 'unavailable', 'setup', 'load', 'free'
    ))

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
      writer.writerow((
        i.name.encode(encoding, "ignore"), j['start'], j['available'],
        j['unavailable'], j['setup'], j['load'], j['free']
        ))
  print('Exported resourceplans in %.2f seconds' % (time() - starttime))


def exportDemand():

  def deliveries(d):
    cumplanned = 0
    n = d
    while n.hidden and n.owner:
      n = n.owner
    n = n and n.name or 'unspecified'
    # Loop over all delivery operationplans
    for i in d.operationplans:
      cumplanned += i.quantity
      cur = i.quantity
      if cumplanned > d.quantity:
        cur -= cumplanned - d.quantity
        if cur < 0:
          cur = 0
      yield (
        n.encode(encoding, "ignore"), d.item.name.encode(encoding, "ignore"),
        d.customer and d.customer.name.encode(encoding, "ignore") or None, d.due,
        cur, i.end, i.quantity, i.id
        )
    # Extra record if planned short
    if cumplanned < d.quantity:
      yield (
        n.encode(encoding, "ignore"), d.item.name.encode(encoding, "ignore"),
        d.customer and d.customer.name.encode(encoding, "ignore") or None, d.due,
        d.quantity - cumplanned, None, None, None
        )

  print("Exporting demand plans...")
  starttime = time()
  writer = csv.writer(open("demands.csv", "wb"), quoting=csv.QUOTE_ALL)
  writer.writerow((
    '#demand', 'item', 'customer', 'due date', 'requested quantity',
    'plan date', 'plan quantity', 'operationplan id'
    ))
  for i in frepple.demands():
    if i.quantity == 0:
      continue
    for j in deliveries(i):
      writer.writerow(j)
  print('Exported demand plans in %.2f seconds' % (time() - starttime))


def exportPegging():
  print("Exporting pegging...")
  starttime = time()
  writer = csv.writer(open("demand_pegging.csv", "wb"), quoting=csv.QUOTE_ALL)
  writer.writerow((
    '#demand', 'level', 'consuming operationplan id', 'consuming date',
    'producing operationplan id', 'producing date', 'buffer', 'item',
    'quantity demand', 'quantity buffer'
    ))
  for i in frepple.demands():
    # Find non-hidden demand owner
    n = i
    while n.hidden and n.owner:
      n = n.owner
    n = n and n.name or 'unspecified'
    # Export pegging
    for j in i.pegging:
      writer.writerow((
       n.encode(encoding, "ignore"), j.level, j.consuming and j.consuming.id or '',
       j.consuming_date,
       j.producing and j.producing.id or '', j.producing_date,
       j.buffer and j.buffer.name.encode(encoding, "ignore") or '',
       (j.buffer and j.buffer.item and j.buffer.item.name.encode(encoding, "ignore")) or '',
       j.quantity_demand, j.quantity_buffer
       ))
  print('Exported pegging in %.2f seconds' % (time() - starttime))


def exportForecast():
  # Detect whether the forecast module is available
  if not 'demand_forecast' in [ a[0] for a in inspect.getmembers(frepple) ]:
    return

  print("Exporting forecast plans...")
  starttime = time()
  writer = csv.writer(open("forecast.csv", "wb"), quoting=csv.QUOTE_ALL)
  writer.writerow((
    '#forecast', 'start date', 'end date', 'total quantity',
    'net quantity', 'consumed quantity'
    ))
  for i in frepple.demands():
    if not isinstance(i, frepple.demand_forecastbucket) or i.total <= 0.0:
      continue
    writer.writerow((
      i.name.encode(encoding, "ignore"), i.startdate, i.enddate, i.total, i.quantity, i.consumed
      ))
  print('Exported forecast plans in %.2f seconds' % (time() - starttime))


def exportfrepple():
  exportProblems()
  exportConstraints()
  exportOperationplans()
  exportFlowplans()
  exportLoadplans()
  exportResourceplans()
  exportDemand()
  exportPegging()
  exportForecast()
