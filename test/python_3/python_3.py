#!/usr/bin/python
#
# Copyright (C) 2007-2011 by Johan De Taeye, frePPLe bvba
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
# Foundation Inc., 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301 USA
#
#  file     : $URL$
#  revision : $LastChangedRevision$  $LastChangedBy$
#  date     : $LastChangedDate$

'''
This test shows how we can use Python to create a frePPLe model: we can
create objects, access existing objects and change objects.

All other tests are running the Python interpreter embedded in the frePPLe
executable.
This test however runs frePPLe as Python extension module.
'''

# Add the frePPLe directory to the Python module search path
import os
import site
if 'FREPPLE_HOME' in os.environ:
   site.addsitedir(os.environ['FREPPLE_HOME'])

import frepple
import datetime
import inspect
import types


def printModel(filename):
  '''
  A function that prints out all models to a file.
  '''

  # Open the output file
  output = open(filename,"wt")

  # Global settings
  print >>output, "Echoing global settings"
  print >>output, "Plan name:", frepple.settings.name
  print >>output, "Plan description:", frepple.settings.description
  print >>output, "Plan current:", frepple.settings.current

  # Solvers
  print >>output, "\nEchoing solvers:"
  for b in frepple.solvers():
    print >>output, "  Solver:", b.name, b.loglevel, getattr(b,'constraints',None)

  # Calendars
  print >>output, "\nEchoing calendars:"
  for b in frepple.calendars():
    print >>output, "  Calendar:", b.name, getattr(b,'default',None)
    for j in b.buckets:
      print >>output, "    Bucket:", getattr(j,'value',None), j.start, j.end, j.priority

  # Customers
  print >>output, "\nEchoing customers:"
  for b in frepple.customers():
    print >>output, "  Customer:", b.name, b.description, b.category, b.subcategory, b.owner

  # Locations
  print >>output, "\nEchoing locations:"
  for b in frepple.locations():
    print >>output, "  Location:", b.name, b.description, b.category, b.subcategory, b.owner

  # Items
  print >>output, "\nEchoing items:"
  for b in frepple.items():
    print >>output, "  Item:", b.name, b.description, b.category, b.subcategory, b.owner, b.operation

  # Resources
  print >>output, "\nEchoing resources:"
  for b in frepple.resources():
    print >>output, "  Resource:", b.name, b.description, b.category, b.subcategory, b.owner
    for l in b.loads:
      print >>output, "    Load:", l.operation.name, l.quantity, l.effective_start, l.effective_end
    for l in b.loadplans:
      print >>output, "    Loadplan:", l.operationplan.id, l.operationplan.operation.name, l.quantity, l.startdate, l.enddate

  # Buffers
  print >>output, "\nEchoing buffers:"
  for b in frepple.buffers():
    print >>output, "  Buffer:", b.name, b.description, b.category, b.subcategory, b.owner
    for l in b.flows:
      print >>output, "    Flow:", l.operation.name, l.quantity, l.effective_start, l.effective_end
    for l in b.flowplans:
      print >>output, "    Flowplan:", l.operationplan.id, l.operationplan.operation.name, l.quantity, l.date

  # Operations
  print >>output, "\nEchoing operations:"
  for b in frepple.operations():
    print >>output, "  Operation:", b.name, b.description, b.category, b.subcategory
    for l in b.loads:
      print >>output, "    Load:", l.resource.name, l.quantity, l.effective_start, l.effective_end
    for l in b.flows:
      print >>output, "    Flow:", l.buffer.name, l.quantity, l.effective_start, l.effective_end
    if isinstance(b, frepple.operation_alternate):
      for l in b.alternates:
        print >>output, "    Alternate:", l.name
    if isinstance(b, frepple.operation_routing):
      for l in b.steps:
        print >>output, "    Step:", l.name

  # Demands
  print >>output, "\nEchoing demands:"
  for b in frepple.demands():
    print >>output, "  Demand:", b.name, b.due, b.item.name, b.quantity
    for i in b.operationplans:
      print >>output, "    Operationplan:", i.id, i.operation.name, i.quantity, i.end

  # Operationplans
  print >>output, "\nEchoing operationplans:"
  for b in frepple.operationplans():
    print >>output, "  Operationplan:", b.operation.name, b.quantity, b.start, b.end
    for s in b.operationplans:
      print >>output, "       ", s.operation.name, s.quantity, s.start, s.end
      
  # Problems
  print >>output, "\nPrinting problems"
  for i in frepple.problems():
    print >>output, "  Problem:", i.entity, i.name, i.description, i.start, i.end, i.weight


def printExtensions():
  '''
  Echoes all entities in our extension module.
  Useful to create documentation.
  '''
  print "  Types:"
  for name, o in inspect.getmembers(frepple):
    if not inspect.isclass(o) or issubclass(o,Exception) or hasattr(o,"__iter__"): continue
    print "    %s: %s" % (o.__name__, inspect.getdoc(o))
  print "  Methods:"
  for name, o in inspect.getmembers(frepple):
    if not inspect.isroutine(o): continue
    print "    %s: %s" % (o.__name__, inspect.getdoc(o))
  print "  Exceptions:"
  for name, o in inspect.getmembers(frepple):
    if not inspect.isclass(o) or not issubclass(o,Exception): continue
    print "    %s" % (o.__name__)
  print "  Iterators:"
  for name, o in inspect.getmembers(frepple):
    if not inspect.isclass(o) or not hasattr(o,"__iter__"): continue
    print "    %s: %s" % (o.__name__, inspect.getdoc(o))
  print "  Other:"
  for name, o in inspect.getmembers(frepple):
    # Negating the exact same filters as in the previous blocks
    if not(not inspect.isclass(o) or issubclass(o,Exception) or hasattr(o,"__iter__")): continue
    if inspect.isroutine(o): continue
    if not(not inspect.isclass(o) or not issubclass(o,Exception)): continue
    if not(not inspect.isclass(o) or not hasattr(o,"__iter__")): continue
    print "    %s: %s" % (name, o)


###
print "\nUpdating global settings"
frepple.settings.name = "demo model"
frepple.settings.description = unicode("demo description in unicode object")
frepple.settings.current = datetime.datetime(2009,1,1)

###
print "\nCreating operations"
shipoper = frepple.operation_fixed_time(name="delivery end item", duration=86400)
choice = frepple.operation_alternate(name="make or buy item")
makeoper = frepple.operation_routing(name="make item")
makeoper.addStep(frepple.operation_fixed_time(name="make item - step 1", duration=4*86400))
makeoper.addStep(frepple.operation_fixed_time(name="make item - step 2", duration=3*86400))
buyoper = frepple.operation_fixed_time(name="buy item", duration=86400)
choice.addAlternate(operation=makeoper, priority=1)
choice.addAlternate(operation=buyoper, priority=2)

###
print "\nCreating calendars"
c = frepple.calendar_boolean(name="boolcal", default=False)
c.setValue(datetime.datetime(2009,1,1), datetime.datetime(2009,3,1), True)
c.setValue(datetime.datetime(2009,2,1), datetime.datetime(2009,5,1), True)
c.setValue(datetime.datetime(2009,2,1), datetime.datetime(2009,3,1), False)
frepple.calendar(name="doublecal", default=1.23)
frepple.calendar_void(name="voidcal")
c = frepple.calendar_operation(name="operationcal", default=choice)
c.setValue(datetime.datetime(2009,1,1), datetime.datetime(2009,3,1), makeoper)
c.setValue(datetime.datetime(2009,6,1), datetime.datetime(2009,9,1), buyoper)

### 
print "\nTesting the calendar iterator"
print"calendar events:"
for date, value in c.events():
  print "  ", date, value

###
print "\nDeleting a calendar"
frepple.calendar(name="voidcal", action="R")

# Load some data - These things can't be done yet from Python
frepple.readXMLdata('''<?xml version="1.0" encoding="UTF-8" ?>
<plan xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance">
  <resources>
    <resource name="Resource">
      <maximum_calendar name="Capacity" xsi:type="calendar_double">
        <buckets>
          <bucket start="2009-01-01T00:00:00">
            <value>1</value>
          </bucket>
        </buckets>
      </maximum_calendar>
      <loads>
        <load>
          <operation name="make item - step 1" />
        </load>
        <load>
          <operation name="make item - step 2" />
        </load>
      </loads>
    </resource>
  </resources>
  <flows>
    <flow xsi:type="flow_start">
      <operation name="delivery end item" />
      <buffer name="end item" />
      <quantity>-1</quantity>
    </flow>
    <flow xsi:type="flow_end">
      <operation name="make or buy item" />
      <buffer name="end item" />
      <quantity>1</quantity>
    </flow>
  </flows>
</plan>
''')

###
print "\nCreating operationplans"
opplan = frepple.operationplan(operation="make item", quantity=9, end=datetime.datetime(2011,1,1))
opplan.locked = True

###
print "\nCreating items"
item = frepple.item(name="end item", operation=shipoper)
itemlist = [ frepple.item(name="item %d" % i) for i in range(10) ]

###
print "\nTesting the comparison operator"
print "makoper < shipoper", makeoper < shipoper
print "shipoper < makeoper", shipoper < makeoper
print "shipoper != makeoper", shipoper != makeoper
print "shipoper == makeoper", shipoper == makeoper
print "shipoper == shipoper", shipoper == shipoper
try:
  print "makeoper == item", makeoper == item
except Exception, e:
  print "Catching exception %s: %s" % (e.__class__.__name__, e)

###
print "\nCreating a resource"
frepple.resource(name="machine", maximum_calendar=frepple.calendar(name="doublecal"))

###
print "\nCreating customers"
mycustomer = frepple.customer(name="client")

###
print "\nCreating locations"
locA = frepple.location(name="locA")
locB = frepple.location(name="locB")

###
print "\nCreating some buffers"

buf = frepple.buffer(name="end item", producing=choice, item=item)

buf1 = frepple.buffer_procure(name="buffer1",
  description="My description",
  category="My category",
  location=locA,
  item=itemlist[1])
print buf1, buf1.__class__, buf1.location, isinstance(buf1, frepple.buffer), \
  isinstance(buf1, frepple.buffer_default), \
  isinstance(buf1, frepple.buffer_procure), \
  isinstance(buf1, frepple.buffer_infinite)

buf2 = frepple.buffer(name="buffer2", owner=buf1)
print buf2, buf2.__class__, buf2.location, isinstance(buf2, frepple.buffer), \
  isinstance(buf2, frepple.buffer_default), \
  isinstance(buf2, frepple.buffer_procure), \
  isinstance(buf2, frepple.buffer_infinite)

###
print "\nCatching some exceptions"
try:
  print buf1.crazyfield
except Exception, e:
  print "Catching exception %s: %s" % (e.__class__.__name__, e)

try:
  buf1.crazyfield = "doesn't exist"
except Exception, e:
  print "Catching exception %s: %s" % (e.__class__.__name__, e)

try:
  buf1.owner = buf2
except Exception, e:
  print "Catching exception %s: %s" % (e.__class__.__name__, e)

###
print "\nCreating demands"
order1 = frepple.demand(name="order 1", item=item, quantity=10, priority=1, \
  due=datetime.datetime(2009,3,2,9), customer=mycustomer, maxlateness=0)
order2 = frepple.demand(name="order 2", item=item, quantity=10, priority=2, \
  due=datetime.datetime(2009,3,2,8,30,0), customer=mycustomer, maxlateness=0)
order3 = frepple.demand(name="order 3", item=item, quantity=10, priority=3, \
  due=datetime.datetime(2009,3,2,20,0,0), customer=mycustomer, maxlateness=0)

###
print "\nCreating a solver and running it"
frepple.solver_mrp(name="MRP", constraints=7, loglevel=0).solve()

###
print "\nEchoing the model to a file"
printModel("output.1.xml")

###
print "\nSaving the model to an XML-file"
frepple.saveXMLfile("output.2.xml")

###
print "\nPrinting some models in XML format"
print mycustomer.toXML()
print locA.toXML()
print opplan.toXML()
print item.toXML()
print order1.toXML()
print buf1.toXML()
print makeoper.toXML()
for i in frepple.problems():
  print i.toXML()

###
print "\nPrinting some models in XML format to a file"
output = open("output.3.xml","wt")
print >>output, mycustomer.toXML()
print >>output, locA.toXML()
print >>output, opplan.toXML()
print >>output, item.toXML()
print >>output, order1.toXML()
print >>output, buf1.toXML()
print >>output, makeoper.toXML()
for i in frepple.problems():
  print >>output, i.toXML()

###
print "\nDocumenting all available Python entities defined by frePPLe:"
printExtensions()
