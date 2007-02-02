from freppledb.input.models import *
from datetime import datetime 
dateformat = '%Y-%m-%dT%H:%M:%S'

def loadfrepple():
  global dateformat

  # Plan (limited to the first one only)
  print 'Import plan...'
  x = [ '<?xml version="1.0" encoding="UTF-8" ?><PLAN xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance">' ]
  for i in Plan.objects.all()[:1]:
    if i.name: x.append('<NAME>%s</NAME>' % i.name)
    if i.description: x.append('<DESCRIPTION>%s</DESCRIPTION>' % i.description)
    x.append('<CURRENT>%s</CURRENT>' % i.current.strftime(dateformat))
  x.append('</PLAN>')
  frepple.readXMLdata('\n'.join(x),False,False)
    
  # Locations
  print 'Importing locations...'
  x = [ '<?xml version="1.0" encoding="UTF-8" ?><PLAN xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance">' ]
  x.append('<LOCATIONS>')
  for i in Location.objects.all(): x.append(i.xml())
  x.append('</LOCATIONS></PLAN>')
  frepple.readXMLdata('\n'.join(x),False,False)
    
  # Operations
  print 'Importing operations...'
  x = [ '<?xml version="1.0" encoding="UTF-8" ?><PLAN xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance">' ]
  x.append('<OPERATIONS>')
  for i in Operation.objects.all():
    x.append('<OPERATION NAME="%s">' % i.name)
    if i.owner: x.append('<OWNER NAME="%s"/>' % i.owner)
    x.append('</OPERATION>')
  x.append('</OPERATIONS></PLAN>')
  frepple.readXMLdata('\n'.join(x),False,False)
    
  # Items
  print 'Importing items...'
  x = [ '<?xml version="1.0" encoding="UTF-8" ?><PLAN xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance">' ]
  x.append('<ITEMS>')
  for i in Item.objects.all():
    x.append('<ITEM NAME="%s">' % i.name)
    if i.operation: x.append('<OPERATION NAME="%s"/>' % i.operation)
    x.append('</ITEM>')
  x.append('</ITEMS></PLAN>')
  frepple.readXMLdata('\n'.join(x),False,False)
  '''
  # Buffers
  print 'Importing items...'
  x = [ '<?xml version="1.0" encoding="UTF-8" ?><PLAN xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance">' ]
  x.append( '<BUFFERS>'
  for i in Buffer.objects.all():
    x.append( '<BUFFER NAME="%s">' % i.name
    if i.description: x.append( '<DESCRIPTION>%s</DESCRIPTION>' % i.description
    if i.location: x.append( '<LOCATION NAME="%s"/>' % i.location.name
    if i.onhand>0: x.append( '<ONHAND>%f</ONHAND>' % i.onhand
    if i.producing: x.append( '<PRODUCING NAME="%s"/>' % i.producing
    if i.consuming: x.append( '<CONSUMING NAME="%s"/>' % i.consuming
    x.append( '</BUFFER>'
  x.append( '</BUFFERS>'

  # Resources
  print 'Importing items...'
  x = [ '<?xml version="1.0" encoding="UTF-8" ?><PLAN xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance">' ]
  x.append( '<RESOURCES>'
  for i in Resource.objects.all():
    x.append( '<RESOURCE NAME="%s">' % i.name
    if i.description: x.append( '<DESCRIPTION>%s</DESCRIPTION>' % i.description
    if i.location: x.append( '<LOCATION NAME="%s"/>' % i.location.name
    x.append( '</RESOURCE>'
  x.append( '</RESOURCES>'

  # Flows
  print 'Importing items...'
  x = [ '<?xml version="1.0" encoding="UTF-8" ?><PLAN xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance">' ]
  x.append( '<FLOWS>'
  for i in Flow.objects.all():
    x.append( '<FLOW><BUFFER NAME="%s"><OPERATION NAME="%s">' % (i.thebuffer.name,i.operation.name)
    if i.quantity != 1: x.append( '<QUANTITY>%f</DESCRIPTION>' % i.quantity
    x.append( '</FLOW>'
  x.append( '</FLOWS>'

  # Loads
  print 'Importing items...'
  x = [ '<?xml version="1.0" encoding="UTF-8" ?><PLAN xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance">' ]
  x.append( '<LOADS>'
  for i in Flow.objects.all():
    x.append( '<LOAD><BUFFER NAME="%s"><OPERATION NAME="%s">' % (i.resource.name,i.operation.name)
    if i.usagefactor != 1: x.append( '<QUANTITY>%f</DESCRIPTION>' % i.usagefactor
    x.append( '</LOAD>'
  x.append( '</LOADS>'

  # OperationPlan
  print 'Importing items...'
  x = [ '<?xml version="1.0" encoding="UTF-8" ?><PLAN xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance">' ]
  x.append( '<OPERATION_PLANS>'
  for i in OperationPlan.objects.all():
    x.append( '<OPERATION_PLAN ID="%d" OPERATION="%s">' % (i.identifier,i.operation.name)
    x.append( '<QUANTITY>%f</DESCRIPTION>' % i.quantity
    if i.start: x.append( '<START>%s</START>' % i.start.strftime(dateformat)
    if i.end: x.append( '<END>%s</END>' % i.end.strftime(dateformat)
    if i.locked: x.append( '<LOCKED>True</LOCKED>'
    x.append( '</OPERATION_PLAN>'
  x.append( '</OPERATION_PLANS>'

  # Demand
  print 'Importing items...'
  x = [ '<?xml version="1.0" encoding="UTF-8" ?><PLAN xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance">' ]
  x.append( '<DEMANDS>'
  for i in Demand.objects.all():
    x.append( '<DEMANDS NAME="%s" PRIORITY="%d">' % (i.name,i.priority)
    x.append( '<QUANTITY>%f</DESCRIPTION>' % i.quantity
    x.append( '<DUE>%s</DUE>' % i.due.strftime(dateformat)
    x.append( '<ITEM NAME="%s"/>' % i.item.name
    if i.customer: x.append( '<CUSTOMER NAME="%s/>' % i.customer.name
    if i.operation: x.append( '<OPERATION NAME="%s/>' % i.operation.name
    if i.owner: x.append( '<OWNER NAME="%s"/>' % i.owner.name
    x.append( '</DEMAND>'
  x.append( '</DEMANDS>'
  '''

def dumpfrepple():
  print "ole"
