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

from freppledb.input.models import *
from datetime import datetime 

dateformat = '%Y-%m-%dT%H:%M:%S'
header = '<?xml version="1.0" encoding="UTF-8" ?><PLAN xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance">'

def loadfrepple():
  '''
  This function is expected to be run by the python interpreter in the 
  frepple application.
  It loads data from the database into the frepple memory.
  '''
  global dateformat
  global header

  # Plan (limited to the first one only)
  print 'Import plan...'
  x = [ header ]
  for i in Plan.objects.all()[:1]: x.append(i.xml())
  x.append('</PLAN>')
  frepple.readXMLdata('\n'.join(x),False,False)
    
  # Locations
  print 'Importing locations...'
  x = [ header ]
  x.append('<LOCATIONS>')
  for i in Location.objects.all(): x.append(i.xml())
  x.append('</LOCATIONS></PLAN>')
  frepple.readXMLdata('\n'.join(x),False,False)
    
  # Calendar
  print 'Importing calendars...'
  x = [ header ]
  x.append('<CALENDARS>')
  for i in Calendar.objects.all(): x.append(i.xml())
  x.append('</CALENDARS></PLAN>')
  frepple.readXMLdata('\n'.join(x),False,False)
    
  # Customers
  print 'Importing customers...'
  x = [ header ]
  x.append('<CUSTOMERS>')
  for i in Customer.objects.all(): x.append(i.xml())
  x.append('</CUSTOMERS></PLAN>')
  frepple.readXMLdata('\n'.join(x),False,False)
    
  # Operations
  print 'Importing operations...'
  x = [ header ]
  x.append('<OPERATIONS>')
  for i in Operation.objects.all(): x.append(i.xml())
  x.append('</OPERATIONS></PLAN>')
  frepple.readXMLdata('\n'.join(x),False,False)
    
  # Items
  print 'Importing items...'
  x = [ header ]
  x.append('<ITEMS>')
  for i in Item.objects.all(): x.append(i.xml())
  x.append('</ITEMS></PLAN>')
  frepple.readXMLdata('\n'.join(x),False,False)

  # Buffers
  print 'Importing buffers...'
  x = [ header ]
  x.append('<BUFFERS>')
  for i in Buffer.objects.all(): x.append(i.xml())
  x.append('</BUFFERS></PLAN>')
  frepple.readXMLdata('\n'.join(x),False,False)

  # Resources
  print 'Importing resources...'
  x = [ header ]
  x.append('<RESOURCES>')
  for i in Resource.objects.all(): x.append(i.xml())
  x.append('</RESOURCES></PLAN>')
  frepple.readXMLdata('\n'.join(x),False,False)

  # Flows
  print 'Importing flows...'
  x = [ header ]
  x.append('<FLOWS>')
  for i in Flow.objects.all(): x.append(i.xml())
  x.append('</FLOWS></PLAN>')
  frepple.readXMLdata('\n'.join(x),False,False)

  # Loads
  print 'Importing loads...'
  x = [ header ]
  x.append('<LOADS>')
  for i in Load.objects.all(): x.append(i.xml())
  x.append('</LOADS></PLAN>')
  frepple.readXMLdata('\n'.join(x),False,False)

  # OperationPlan
  print 'Importing operationplans...'
  x = [ header ]
  x.append('<OPERATION_PLANS>')
  for i in OperationPlan.objects.all(): x.append(i.xml())
  x.append('</OPERATION_PLANS></PLAN>')
  frepple.readXMLdata('\n'.join(x),False,False)

  # Demand
  print 'Importing demands...'
  x = [ header ]
  x.append('<DEMANDS>')
  for i in Demand.objects.all(): x.append(i.xml())
  x.append('</DEMANDS></PLAN>')
  frepple.readXMLdata('\n'.join(x),False,False)

def dumpfrepple():
  print "ole"
