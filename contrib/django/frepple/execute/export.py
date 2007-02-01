from frepple.input.models import *
from datetime import datetime 
dateformat = '%Y-%m-%dT%H:%M:%S'

def export2xml(filename):
  global dateformat
  # Open the output file
  out = open(filename,'wt')
  
  try:
    # Print the header
    print '<?xml version="1.0" encoding="UTF-8"?>'
    print '<PLAN xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance">'

    # Plan (limited to the first one only)
    for i in Plan.objects.all()[:1]:
      if i.name: print '<NAME>%s</NAME>' % i.name 
      if i.description: print '<DESCRIPTION>%s</DESCRIPTION>' % i.description
      print '<CURRENT>%s</CURRENT>' % i.current.strftime(dateformat)

    # Locations
    print '<LOCATIONS>'
    for i in Item.objects.all():
      print '<LOCATION NAME="%s">' % i.name
      if i.description: print '<DESCRIPTION>%s</DESCRIPTION>' % i.description
      if i.owner: print '<OWNER NAME="%s">' % i.description
      print '</LOCATION>'
      pass
    print '</LOCATIONS>'

    # Customers
    print '<CUSTOMERS>'
    for i in Customer.objects.all():
      print '<CUSTOMER NAME="%s">' % i.name
      if i.description: print '<DESCRIPTION>%s</DESCRIPTION>' % i.description
      if i.owner: print '<OWNER NAME="%s">' % i.description
      print '</CUSTOMER>'
      pass
    print '</CUSTOMERS>'

    # Items
    print '<ITEMS>'
    for i in Item.objects.all():
      print '<ITEM NAME="%s">' % i.name
      if i.description: print '<DESCRIPTION>%s</DESCRIPTION>' % i.description
      print '</ITEM>'
      pass
    print '</ITEMS>'
  
    # Operations
    print '<OPERATIONS>'
    for i in Operation.objects.all():
      print '<OPERATION NAME="%s">' % i.name
      print '</OPERATION>'
      pass
    print '</OPERATIONS>'
  
    # Buffers
    print '<BUFFERS>'
    for i in Buffer.objects.all():
      print '<BUFFER NAME="%s">' % i.name
      if i.description: print '<DESCRIPTION>%s</DESCRIPTION>' % i.description
      if i.location: print '<LOCATION NAME="%s"/>' % i.location.name
      if i.onhand>0: print '<ONHAND>%f</ONHAND>' % i.onhand
      if i.producing: print '<PRODUCING NAME="%s"/>' % i.producing
      if i.consuming: print '<CONSUMING NAME="%s"/>' % i.consuming
      print '</BUFFER>'
    print '</BUFFERS>'

    # Resources
    print '<RESOURCES>'
    for i in Resource.objects.all():
      print '<RESOURCE NAME="%s">' % i.name
      if i.description: print '<DESCRIPTION>%s</DESCRIPTION>' % i.description
      if i.location: print '<LOCATION NAME="%s"/>' % i.location.name
      print '</RESOURCE>'
    print '</RESOURCES>'

    # Flows
    print '<FLOWS>'
    for i in Flow.objects.all():
      print '<FLOW><BUFFER NAME="%s"><OPERATION NAME="%s">' % (i.thebuffer.name,i.operation.name)
      if i.quantity != 1: print '<QUANTITY>%f</DESCRIPTION>' % i.quantity
      print '</FLOW>'
    print '</FLOWS>'

    # Loads
    print '<LOADS>'
    for i in Flow.objects.all():
      print '<LOAD><BUFFER NAME="%s"><OPERATION NAME="%s">' % (i.resource.name,i.operation.name)
      if i.usagefactor != 1: print '<QUANTITY>%f</DESCRIPTION>' % i.usagefactor
      print '</LOAD>'
    print '</LOADS>'

    # OperationPlan
    print '<OPERATION_PLANS>'
    for i in OperationPlan.objects.all():
      print '<OPERATION_PLAN ID="%d" OPERATION="%s">' % (i.identifier,i.operation.name)
      print '<QUANTITY>%f</DESCRIPTION>' % i.quantity
      if i.start: print '<START>%s</START>' % i.start.strftime(dateformat)
      if i.end: print '<END>%s</END>' % i.end.strftime(dateformat)
      if i.locked: print '<LOCKED>True</LOCKED>'
      print '</OPERATION_PLAN>'
    print '</OPERATION_PLANS>'

    # Demand
    print '<DEMANDS>'
    for i in Demand.objects.all():
      print '<DEMANDS NAME="%s" PRIORITY="%d">' % (i.name,i.priority)
      print '<QUANTITY>%f</DESCRIPTION>' % i.quantity
      print '<DUE>%s</DUE>' % i.due.strftime(dateformat)
      print '<ITEM NAME="%s"/>' % i.item.name
      if i.customer: print '<CUSTOMER NAME="%s/>' % i.customer.name
      if i.operation: print '<OPERATION NAME="%s/>' % i.operation.name
      if i.owner: print '<OWNER NAME="%s"/>' % i.owner.name
      print '</DEMAND>'
    print '</DEMANDS>'

    # Footer
    print '<PLAN>'
  finally:
    out.close()

export2xml('test')
