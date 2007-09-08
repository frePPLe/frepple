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


def exportProblems_csv():
  print "Exporting problems..."
  starttime = time()
  writer = csv.writer(open("problems.csv", "wb"), quoting=csv.QUOTE_ALL)
  for i in frepple.problem():
    writer.writerow([ str(s).encode("utf-8") for s in
      (i['ENTITY'], i['TYPE'], i['DESCRIPTION'], i['START'], i['END'], i['WEIGHT'])
      ])
  print 'Exported problems in %.2f seconds' % (time() - starttime)


def exportOperationplans_csv():
  print "Exporting operationplans..."
  starttime = time()
  writer = csv.writer(open("operations.csv", "wb"), quoting=csv.QUOTE_ALL)
  for i in frepple.operationplan():
    writer.writerow([ str(s).encode("utf-8") for s in
     ( i['IDENTIFIER'], i['OPERATION'], i['QUANTITY'], i['START'], i['END'],
       i['DEMAND'] or '', i['LOCKED'])
     ])
  print 'Exported operationplans in %.2f seconds' % (time() - starttime)


def exportFlowplans_csv():
  print "Exporting flowplans..."
  starttime = time()
  writer = csv.writer(open("buffers.csv", "wb"), quoting=csv.QUOTE_ALL)
  for i in frepple.buffer():
    for j in i['FLOWPLANS']:
      writer.writerow([ str(s).encode("utf-8") for s in
       (j['OPERATIONPLAN'], j['OPERATION'], j['BUFFER'],
        j['QUANTITY'], j['DATE'], j['DATE'], j['ONHAND'])
       ])
  print 'Exported flowplans in %.2f seconds' % (time() - starttime)


def exportLoadplans_csv():
  print "Exporting loadplans..."
  starttime = time()
  writer = csv.writer(open("resources.csv", "wb"), quoting=csv.QUOTE_ALL)
  for i in frepple.resource():
    for j in i['LOADPLANS']:
      writer.writerow([ str(s).encode("utf-8") for s in
       (j['OPERATIONPLAN'], j['RESOURCE'], j['QUANTITY'],
        j['STARTDATE'], j['ENDDATE'])
       ])
  print 'Exported loadplans in %.2f seconds' % (time() - starttime)


def exportDemand_csv():
  print "Exporting demands..."
  starttime = time()
  writer = csv.writer(open("demands.csv", "wb"), quoting=csv.QUOTE_ALL)
  for i in frepple.demand():
    for j in i['DELIVERY']:
      writer.writerow([ str(s).encode("utf-8") for s in
       (i['NAME'], i['DUE'], j['QUANTITY'], j['PLANDATE'] or '',
        j['PLANQUANTITY'] or '', j['OPERATIONPLAN'] or '')
       ])
  print 'Exported demands in %.2f seconds' % (time() - starttime)


def exportPegging_csv():
  print "Exporting pegging..."
  starttime = time()
  writer = csv.writer(open("demand_pegging.csv", "wb"), quoting=csv.QUOTE_ALL)
  for i in frepple.demand():
    for j in i['PEGGING']:
      writer.writerow([ str(s).encode("utf-8") for s in
       (i['NAME'], j['LEVEL'], j['OPERATIONPLAN'],
        j['BUFFER'], j['QUANTITY'], j['DATE'], j['FACTOR'], j['PEGGED'])
       ])
  print 'Exported pegging in %.2f seconds' % (time() - starttime)


def exportfrepple():
  exportProblems_csv()
  exportOperationplans_csv()
  exportFlowplans_csv()
  exportLoadplans_csv()
  exportDemand_csv()
  exportPegging_csv()
