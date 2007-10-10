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
# email : jdetaeye@users.sourceforge.net

from time import time
import csv

import frepple


def exportProblems():
  print "Exporting problems..."
  starttime = time()
  writer = csv.writer(open("problems.csv", "wb"), quoting=csv.QUOTE_ALL)
  for i in frepple.problem():
    writer.writerow(
      (i['ENTITY'].encode("utf-8"), i['TYPE'].encode("utf-8"), i['DESCRIPTION'].encode("utf-8"), i['START'], i['END'], i['WEIGHT'])
      )
  print 'Exported problems in %.2f seconds' % (time() - starttime)


def exportOperationplans():
  print "Exporting operationplans..."
  starttime = time()
  writer = csv.writer(open("operations.csv", "wb"), quoting=csv.QUOTE_ALL)
  for i in frepple.operationplan():
    writer.writerow(
     ( i['IDENTIFIER'], i['OPERATION'].encode("utf-8"), i['QUANTITY'], i['START'], i['END'],
       (i['DEMAND'] and i['DEMAND'].encode("utf-8")) or '', i['LOCKED'])
     )
  print 'Exported operationplans in %.2f seconds' % (time() - starttime)


def exportFlowplans():
  print "Exporting flowplans..."
  starttime = time()
  writer = csv.writer(open("buffers.csv", "wb"), quoting=csv.QUOTE_ALL)
  for i in frepple.buffer():
    for j in i['FLOWPLANS']:
      writer.writerow(
       (j['OPERATIONPLAN'], j['BUFFER'].encode("utf-8"), j['QUANTITY'],
        j['DATE'], j['ONHAND'])
       )
  print 'Exported flowplans in %.2f seconds' % (time() - starttime)


def exportLoadplans():
  print "Exporting loadplans..."
  starttime = time()
  writer = csv.writer(open("resources.csv", "wb"), quoting=csv.QUOTE_ALL)
  for i in frepple.resource():
    for j in i['LOADPLANS']:
      writer.writerow(
       (j['OPERATIONPLAN'], j['RESOURCE'].encode("utf-8"), j['QUANTITY'],
        j['STARTDATE'], j['ENDDATE'])
       )
  print 'Exported loadplans in %.2f seconds' % (time() - starttime)


def exportDemand():
  print "Exporting demands..."
  starttime = time()
  writer = csv.writer(open("demands.csv", "wb"), quoting=csv.QUOTE_ALL)
  for i in frepple.demand():
    for j in i['DELIVERY']:
      writer.writerow(
       (i['NAME'].encode("utf-8"), i['DUE'], j['QUANTITY'], j['PLANDATE'] or '',
        j['PLANQUANTITY'] or '', j['OPERATIONPLAN'] or '')
       )
  print 'Exported demands in %.2f seconds' % (time() - starttime)


def exportPegging():
  print "Exporting pegging..."
  starttime = time()
  writer = csv.writer(open("demand_pegging.csv", "wb"), quoting=csv.QUOTE_ALL)
  for i in frepple.demand():
    for j in i['PEGGING']:
      writer.writerow(
       (i['NAME'].encode("utf-8"), j['LEVEL'], j['OPERATIONPLAN'],
        j['BUFFER'].encode("utf-8"), j['QUANTITY'], j['DATE'], j['FACTOR'], j['PEGGED'])
       )
  print 'Exported pegging in %.2f seconds' % (time() - starttime)


def exportfrepple():
  exportProblems()
  exportOperationplans()
  exportFlowplans()
  exportLoadplans()
  exportDemand()
  exportPegging()
