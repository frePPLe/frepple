#
# Copyright (C) 2007 by Johan De Taeye
#
# This library is free software; you can redistribute it and/or modify it
# under the terms of the GNU Lesser General Public License as published
# by the Free Software Foundation; either version 2.1 of the License, or
# (at your option) any later version.
#
# This library is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU Lesser
# General Public License for more details.
#
# You should have received a copy of the GNU Lesser General Public
# License along with this library; if not, write to the Free Software
# Foundation Inc., 59 Temple Place, Suite 330, Boston, MA 02111-1307, USA
#

# file : $URL$
# revision : $LastChangedRevision$  $LastChangedBy$
# date : $LastChangedDate$

r'''
Exports frePPLe information to flat files.

The code in this file is executed NOT by Django, but by the embedded Python
interpreter from the frePPLe engine.

The code iterates over all objects in the C++ core engine, and writes this
information to a set of text files.
'''


from time import time
import csv
from threading import Thread


import frepple


def exportProblems():
  print "Exporting problems..."
  starttime = time()
  writer = csv.writer(open("problems.csv", "wb"), quoting=csv.QUOTE_ALL)
  for i in frepple.problems():
    writer.writerow(
      (i.entity, i.name, i.description, i.start, i.end, i.weight)
      )
  print 'Exported problems in %.2f seconds' % (time() - starttime)


def exportOperationplans():
  print "Exporting operationplans..."
  starttime = time()
  writer = csv.writer(open("operations.csv", "wb"), quoting=csv.QUOTE_ALL)
  for i in frepple.operationplans():
    writer.writerow(
     ( i.id, i.operation.name, i.quantity, i.start, i.end,
       i.demand and i.demand.name or '', i.locked)
     )
  print 'Exported operationplans in %.2f seconds' % (time() - starttime)


def exportFlowplans():
  print "Exporting flowplans..."
  starttime = time()
  writer = csv.writer(open("buffers.csv", "wb"), quoting=csv.QUOTE_ALL)
  for i in frepple.buffers():
    for j in i.flow_plans:
      writer.writerow(
       (j.operation_plan.id, j.buffer.name, j.quantity,
        j.date, j.onhand)
       )
  print 'Exported flowplans in %.2f seconds' % (time() - starttime)


def exportLoadplans():
  print "Exporting loadplans..."
  starttime = time()
  writer = csv.writer(open("resources.csv", "wb"), quoting=csv.QUOTE_ALL)
  for i in frepple.resources():
    for j in i.load_plans:
      writer.writerow(
       (j.operation_plan.id, j.resource.name, j.quantity,
        j.startdate, j.enddate)
       )
  print 'Exported loadplans in %.2f seconds' % (time() - starttime)


def exportDemand():

  def deliveries(d):
    cumplanned = 0
    n = d
    while n.hidden and n.owner: n = n.owner
    n = n and n.name or 'unspecified'
    # Loop over all delivery operationplans
    for i in d.operation_plans:
      cumplanned += i.quantity
      cur = i.quantity
      if cumplanned > d.quantity:
        cur -= cumplanned - d.quantity
        if cur < 0: cur = 0
      yield (n, d.item.name, d.due, cur, i.end, i.quantity, i.id)
    # Extra record if planned short
    if cumplanned < d.quantity:
      yield (n, d.item.name, d.due, d.quantity - cumplanned, None, None, None)

  print "Exporting demand plans..."
  starttime = time()
  writer = csv.writer(open("demands.csv", "wb"), quoting=csv.QUOTE_ALL)
  for i in frepple.demands():
    if i.quantity == 0: continue
    for j in deliveries(i):
      writer.writerow(j)
  print 'Exported demand plans in %.2f seconds' % (time() - starttime)


def exportPegging():
  print "Exporting pegging..."
  starttime = time()
  writer = csv.writer(open("demand_pegging.csv", "wb"), quoting=csv.QUOTE_ALL)
  for i in frepple.demands():
    # Find non-hidden demand owner
    n = i
    while n.hidden and n.owner: n = n.owner
    n = n and n.name or 'unspecified'
    # Export pegging
    for j in i.pegging:
      writer.writerow((
        n, j['level'], j['consuming'] and j['consuming'].id or '',
        j['cons_date'],
        j['producing'] and j['producing'].id or '', j['prod_date'],
        j['buffer'] and j['buffer'].name or '',
        j['quantity_demand'], j['quantity_buffer'], j['pegged']
       ))
  print 'Exported pegging in %.2f seconds' % (time() - starttime)


def exportForecast():
  # Detect whether the forecast module is available
  try: import freppleforecast
  except: return

  print "Exporting forecast plans..."
  starttime = time()
  writer = csv.writer(open("forecast.csv", "wb"), quoting=csv.QUOTE_ALL)
  for i in freppleforecast.forecast():
    for j in i['buckets']:
      if j['totalqty'] > 0:
        writer.writerow((
          i['name'], j['start_date'], j['end_date'], j['totalqty'],
          j['netqty'], j['consumedqty']
         ))
  print 'Exported forecast plans in %.2f seconds' % (time() - starttime)


def exportfrepple():
  exportProblems()
  exportOperationplans()
  exportFlowplans()
  exportLoadplans()
  exportDemand()
  exportPegging()
  exportForecast()
