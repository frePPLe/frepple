#
# Copyright (C) 2014 by frePPLe bvba
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

from io import StringIO
from optparse import make_option
from datetime import datetime
from time import time
import urllib
from uuid import uuid4
from xml.etree.cElementTree import iterparse

from django.core.management.base import BaseCommand, CommandError
from django.db import connections, DEFAULT_DB_ALIAS
from django.conf import settings

from freppledb.common.models import Parameter
from freppledb.execute.models import Task
from freppledb.openbravo.utils import get_data


class Command(BaseCommand):
  help = "Upload planning results from frePPle into an Openbravo instance"

  option_list = BaseCommand.option_list + (
    make_option(
      '--user', dest='user', type='string',
      help='User running the command'
      ),
    make_option(
      '--database', action='store', dest='database', default=DEFAULT_DB_ALIAS,
      help='Nominates the frePPLe database to export from'
      ),
    make_option(
      '--task', dest='task', type='int',
      help='Task identifier (generated automatically if not provided)'
      ),
    make_option(
      '--filter', action="store_true", dest='filter', default = False,
      help='Use filter set for automated exports'
      ),
    )

  requires_system_checks = False

  def handle(self, **options):

    # Pick up the options
    if 'verbosity' in options:
      self.verbosity = int(options['verbosity'] or '1')
    else:
      self.verbosity = 1
    if 'user' in options:
      user = options['user']
    else:
      user = ''
    if 'database' in options:
      self.database = options['database'] or DEFAULT_DB_ALIAS
    else:
      self.database = DEFAULT_DB_ALIAS
    if self.database not in settings.DATABASES.keys():
      raise CommandError("No database settings known for '%s'" % self.database )
    self.filteredexport = 'filter' in options

    # Pick up configuration parameters
    self.openbravo_user = Parameter.getValue("openbravo.user", self.database)
    # Passwords in djangosettings file are preferably used
    self.openbravo_password = settings.OPENBRAVO_PASSWORDS.get(self.database, None)
    if not self.openbravo_password:
      self.openbravo_password = Parameter.getValue("openbravo.password", self.database)
    self.openbravo_host = Parameter.getValue("openbravo.host", self.database)
    self.openbravo_organization = Parameter.getValue("openbravo.organization", self.database)
    if not self.openbravo_user:
      raise CommandError("Missing or invalid parameter openbravo_user")
    if not self.openbravo_password:
      raise CommandError("Missing or invalid parameter openbravo_password")
    if not self.openbravo_host:
      raise CommandError("Missing or invalid parameter openbravo_host")
    if not self.openbravo_organization:
      raise CommandError("Missing or invalid parameter openbravo_organization")

    # Make sure the debug flag is not set!
    # When it is set, the django database wrapper collects a list of all SQL
    # statements executed and their timings. This consumes plenty of memory
    # and cpu time.
    tmp_debug = settings.DEBUG
    settings.DEBUG = False

    now = datetime.now()
    task = None
    try:
      # Initialize the task
      if 'task' in options and options['task']:
        try:
          task = Task.objects.all().using(self.database).get(pk=options['task'])
        except:
          raise CommandError("Task identifier not found")
        if task.started or task.finished or task.status != "Waiting" or task.name != 'Openbravo export':
          raise CommandError("Invalid task identifier")
        task.status = '0%'
        task.started = now
      else:
        task = Task(name='Openbravo export', submitted=now, started=now, status='0%', user=user)
      task.save(using=self.database)

      # Create a database connection to the frePPLe database
      cursor = connections[self.database].cursor()

      # Look up the id of the Openbravo user
      query = urllib.parse.quote("name='%s'" % self.openbravo_user)
      print ("/ws/dal/ADUser?where=%s&includeChildren=false" % query)
      data = get_data(
        "/ws/dal/ADUser?where=%s&includeChildren=false" % query,
        self.openbravo_host,
        self.openbravo_user,
        self.openbravo_password
        )
      self.openbravo_user_id = None
      for event, elem in iterparse(StringIO(data), events=('start', 'end')):
        if event != 'end' or elem.tag != 'ADUser':
          continue
        self.openbravo_user_id = elem.get('id')
      if not self.openbravo_user_id:
        raise CommandError("Can't find user id in Openbravo")

      # Look up the id of the Openbravo organization id
      query = urllib.parse.quote("name='%s'" % self.openbravo_organization)
      data = get_data(
        "/ws/dal/Organization?where=%s&includeChildren=false" % query,
        self.openbravo_host,
        self.openbravo_user,
        self.openbravo_password
        )
      self.organization_id = None
      for event, elem in iterparse(StringIO(data), events=('start', 'end')):
        if event != 'end' or elem.tag != 'Organization':
          continue
        self.organization_id = elem.get('id')
      if not self.organization_id:
        raise CommandError("Can't find organization id in Openbravo")

      # Upload all data
      self.exportData(task, cursor)

      # Log success
      task.status = 'Done'
      task.finished = datetime.now()

    except Exception as e:
      if task:
        task.status = 'Failed'
        task.message = '%s' % e
        task.finished = datetime.now()
      raise e

    finally:
      if task:
        task.save(using=self.database)
      settings.DEBUG = tmp_debug


  # We have two modes of bringing the results to openbravo:
  #  - generate purchase requisitions and manufacturing work orders
  #  - generate purchasing plans (which is the object where
  #    openbravo's MRP stores its results as well)
  # The first one is the recommended approach
  def exportData(self, task, cursor):
    exportPurchasingPlan = Parameter.getValue("openbravo.exportPurchasingPlan", self.database, default="false")
    if exportPurchasingPlan.lower() == "true":
      self.export_purchasingplan(cursor)
    else:
      self.export_procurement_order(cursor)
      self.export_work_order(cursor)
      self.export_sales_order(cursor)


  # Update the committed date of sales orders
  #   - uploading for each frePPLe demand whose subcategory = 'openbravo'
  #   - mapped fields frePPLe -> Openbravo OrderLine
  #        - max(out_demand.plandate) -> description
  def export_sales_order(self, cursor):
    try:
      starttime = time()
      if self.verbosity > 0:
        print("Exporting expected delivery date of sales orders...")

      fltr = Parameter.getValue('openbravo.filter_export_sales_order', self.database, "")
      if self.filteredexport and fltr:
        filter_expression = 'and (%s) ' % fltr
      else:
        filter_expression = ""

      cursor.execute('''select demand.source, max(operationplan.enddate)
          from demand
          inner join operationplan 
            on operationplan.demand_id = demand.name
          inner join item on demand.item_id = item.name
          inner join location on demand.location_id = location.name
          inner join customer on demand.customer_id = customer.name
          where demand.subcategory = 'openbravo'
            and demand.status = 'open' %s
          group by demand.source
         ''' % filter_expression)
      count = 0
      body = [
        '<?xml version="1.0" encoding="UTF-8"?>',
        '<ob:Openbravo xmlns:ob="http://www.openbravo.com">'
        ]
      for i in cursor.fetchall():
        body.append('<OrderLine id="%s"><description>frePPLe planned delivery date: %s</description></OrderLine>' % i)
        count += 1
        if self.verbosity > 0 and count % 500 == 1:
          print('.', end="")
      if self.verbosity > 0:
        print ('')
      body.append('</ob:Openbravo>')
      get_data(        
        '/ws/dal/OrderLine',
        self.openbravo_host, self.openbravo_user, self.openbravo_password,
        method='POST', xmldoc='\n'.join(body)
        )
      if self.verbosity > 0:
        print("Updated %d sales orders in %.2f seconds" % (count, (time() - starttime)))
    except Exception as e:
      raise CommandError("Error updating sales orders: %s" % e)


  # Upload procurement order data
  #   - uploading frePPLe operationplans
  #   - meeting the criterion:
  #        - operation.subcategory = 'openbravo'
  #   - mapped fields frePPLe -> Openbravo ProcurementRequisition
  #        - 0/All organization -> organization
  #        - 'frePPLe ' + timestamp -> DocumentNo
  #        - 'frePPLe export of ' + timestamp -> description
  #   - mapped fields frePPLe -> Openbravo ProcurementRequisitionLine
  #        - counter -> lineNo
  #        - operationplan.quantity -> quantity
  #        - operationplan.startdate -> needByDate
  #        - 100 (id for 'unit') -> product_uom
  def export_procurement_order(self, cursor):

    def parse(conn):
      # Stores the processplan documents
      records = 0
      root = None
      for event, elem in conn:
        if not root:
          root = elem
          continue
        if event != 'end' or elem.tag != 'ManufacturingProcessPlan':
          continue
        records += 1
        processplans[elem.get('id')] = elem
      return records
    
    requisition = '''<?xml version="1.0" encoding="UTF-8"?>
        <ob:Openbravo xmlns:ob="http://www.openbravo.com">
        <ProcurementRequisition id="%s">
        <organization id="%s" entity-name="Organization"/>
        <active>true</active>
        <documentNo>frePPLe %s</documentNo>
        <description>frePPLe export of %s</description>
        <createPO>false</createPO>
        <documentStatus>DR</documentStatus>
        <userContact id="%s" entity-name="ADUser" identifier="%s"/>
        <processNow>false</processNow>
        <procurementRequisitionLineList>'''
    requisitionline = '''<ProcurementRequisitionLine>
          <active>true</active>
          <requisition id="%s" entity-name="ProcurementRequisition"/>
          <product id="%s" entity-name="Product"/>
          <quantity>%s</quantity>
          <uOM id="100" entity-name="UOM" identifier="Unit"/>
          <requisitionLineStatus>O</requisitionLineStatus>
          <needByDate>%s.0Z</needByDate>
          <lineNo>%s</lineNo>
          </ProcurementRequisitionLine>'''
    try:
      # Close old purchase requisitions generated by frePPLe
      if self.verbosity > 0:
        print("Closing previous purchase requisitions from frePPLe")
      body = [
        '<?xml version="1.0" encoding="UTF-8"?>',
        '<ob:Openbravo xmlns:ob="http://www.openbravo.com">'
        ]
      query = urllib.parse.quote("documentStatus='DR' and documentNo like 'frePPLe %'")
      data = get_data("/ws/dal/ProcurementRequisition?where=%s&includeChildren=false" % query,
        self.openbravo_host, self.openbravo_user, self.openbravo_password
        )
      conn = iterparse(StringIO(data), events=('end',))
      for event, elem in conn:
        if event != 'end' or elem.tag != 'ProcurementRequisition':
          continue
        body.append('<ProcurementRequisition id="%s">' % elem.get('id'))
        body.append('<documentStatus>CL</documentStatus>')
        body.append('</ProcurementRequisition>')
      body.append('</ob:Openbravo>')
      get_data(
        '/ws/dal/ProcurementRequisition',
        self.openbravo_host, self.openbravo_user, self.openbravo_password,
        method='POST', xmldoc='\n'.join(body)
        )

      # Create new requisition
      starttime = time()
      if self.verbosity > 0:
        print("Exporting new purchase requisition...")
      count = 0
      now = datetime.now().strftime('%Y/%m/%d %H:%M:%S')
      identifier = uuid4().hex

      filter_expression_po = Parameter.getValue('openbravo.filter_export_purchase_order', self.database, "")
      if self.filteredexport and filter_expression_po:
        filter_expression_po = ' and (%s) ' % filter_expression_po
      else:
        filter_expression_po = ""

      filter_expression_do = Parameter.getValue('openbravo.filter_export_distribution_order', self.database, "")
      if self.filteredexport and filter_expression_do:
        filter_expression_do = ' and (%s) ' %filter_expression_do
      else:      
        filter_expression_do = ""

      body = [requisition % (identifier, self.organization_id, now, now, self.openbravo_user_id, self.openbravo_user)]
      cursor.execute('''
         select item.source, location.source, enddate, quantity
         FROM operationplan
         inner JOIN buffer
           ON buffer.item_id = operationplan.item_id
           AND buffer.location_id = operationplan.location_id
           AND buffer.subcategory = 'openbravo'
         inner join item
           ON item.name = operationplan.item_id
           and item.source is not null
           and item.subcategory = 'openbravo'
         inner join location
           ON operationplan.location_id = location.name
           and location.source is not null
           and location.subcategory = 'openbravo'
         where operationplan.status = 'proposed' and operationplan.type = 'PO' %s
       union all
       select item.source, location.source, enddate, quantity
         FROM operationplan
         inner JOIN buffer
           ON buffer.item_id = operationplan.item_id
           AND buffer.location_id = operationplan.destination_id
           AND buffer.subcategory = 'openbravo'
         inner join item
           ON item.name = operationplan.item_id
           and item.source is not null
           and item.subcategory = 'openbravo'
         inner join location
           ON operationplan.destination_id = location.name
           and location.source is not null
           and location.subcategory = 'openbravo'
         where operationplan.status = 'proposed' and operationplan.type = 'DO' %s
         ''' % (filter_expression_po,filter_expression_do))
      for i in cursor.fetchall():
        body.append(requisitionline % (identifier, i[0], i[3], i[2].strftime("%Y-%m-%dT%H:%M:%S"), count))
        count += 1
      body.append('</procurementRequisitionLineList>')
      body.append('</ProcurementRequisition>')
      body.append('</ob:Openbravo>')
      get_data(
        '/ws/dal/ProcurementRequisition',
        self.openbravo_host, self.openbravo_user, self.openbravo_password,
        method='POST', xmldoc='\n'.join(body)
        )
      if self.verbosity > 0:
        print("Created requisition with %d lines in %.2f seconds" % (count, (time() - starttime)))

      # Change the status of the new requisition. Doesn't seem to work...
      #body = ['<?xml version="1.0" encoding="UTF-8"?>',
      #  '<ob:Openbravo xmlns:ob="http://www.openbravo.com">',
      #  '<ProcurementRequisition id="%s">' % identifier,
      #  '<documentStatus>CO</documentStatus>',
      #  '<documentAction>CO</documentAction>',
      #  '</ProcurementRequisition>',
      #  '</ob:Openbravo>'
      #  ]
      #get_data(
      #  '/ws/dal/ProcurementRequisition/',
      #  self.openbravo_host, self.openbravo_user, self.openbravo_password,
      #  method='POST', xmldoc='\n'.join(body)
      #  )

    except Exception as e:
      raise CommandError("Error generation purchase requisitions: %s" % e)


  # Export work requirements
  #   - uploading for each frePPLe demand whose subcategory = 'openbravo'
  #   - mapped fields frePPLe -> Openbravo ManufacturingWorkRequirement
  #        -
  def export_work_order(self, cursor):

    fltr = Parameter.getValue('openbravo.filter_export_manufacturing_order', self.database, "")
    if self.filteredexport and fltr:
      filter_expression = 'and (%s) ' % fltr
    else:
      filter_expression = ""

    if True: #try:
      starttime = time()
      if self.verbosity > 0:
        print("Exporting work orders...")
      cursor.execute('''
        select operation.source, operationplan.quantity, startdate, enddate
        from operationplan
        inner join operation
          on operationplan.operation_id = operation.name
          and operation.type = 'routing'
          and operation.name like 'Process%%'
        where operationplan.type = 'MO' %s ''' % filter_expression)
      count = 0
      body = [
        '<?xml version="1.0" encoding="UTF-8"?>',
        '<ob:Openbravo xmlns:ob="http://www.openbravo.com">'
        ]
      for i in cursor.fetchall():
        body.append('''<ManufacturingWorkRequirement>
          <organization id="%s" entity-name="Organization" identifier="%s"/>
          <active>true</active>
          <processPlan id="%s" entity-name="ManufacturingProcessPlan"/>
          <quantity>%s</quantity>
          <startingDate>%s</startingDate>
          <endingDate>%s</endingDate>
          <closed>false</closed>
          <insertProductsAndorPhases>false</insertProductsAndorPhases>
          <processed>false</processed>
          <includePhasesWhenInserting>true</includePhasesWhenInserting>
          <processQuantity>0</processQuantity>
          <createworkrequirement>false</createworkrequirement>
          <closedStat>false</closedStat>
          </ManufacturingWorkRequirement>
           ''' % (
             self.organization_id, self.openbravo_organization,
             i[0], i[1], i[2].strftime("%Y-%m-%d %H:%M:%S"), 
             i[3].strftime("%Y-%m-%d %H:%M:%S")
             ))
        count += 1
        if self.verbosity > 0 and count % 500 == 1:
          print('.', end="")
      if self.verbosity > 0:
        print('')
      body.append('</ob:Openbravo>')
      get_data(
        '/ws/org.openbravo.warehouse.advancedwarehouseoperations.manufacturing.AddWorkRequirementsWS',
        self.openbravo_host, self.openbravo_user, self.openbravo_password,
        method="PUT",
        xmldoc='\n'.join(body),
        headers={'DoProcess': 'true'}
        )
      if self.verbosity > 0:
        print("Updated %d work orders in %.2f seconds" % (count, (time() - starttime)))
    #except Exception as e:
    #  raise CommandError("Error updating work orders: %s" % e)


  def export_purchasingplan(self, cursor):
    purchaseplan = '''<MRPPurchasingRun id="%s">
      <organization id="%s" entity-name="Organization" identifier="%s"/>
      <active>true</active>
      <name>FREPPLE %s</name>
      <description>Bulk export</description>
      <timeHorizon>365</timeHorizon>
      <safetyLeadTime>0</safetyLeadTime>
      <mRPPurchasingRunLineList>'''
    purchasingplanline = '''<MRPPurchasingRunLine id="%s">
      <active>true</active>
      <purchasingPlan id="%s" entity-name="MRPPurchasingRun"/>
      <product id="%s" entity-name="Product"/>
      <quantity>%s</quantity>
      <requiredQuantity>%s</requiredQuantity>
      <plannedDate>%s.0Z</plannedDate>
      <plannedOrderDate>%s.0Z</plannedOrderDate>
      <transactionType>%s</transactionType>
      <businessPartner id="%s"/>
      <fixed>true</fixed>
      <completed>false</completed>      
      </MRPPurchasingRunLine>'''
    try:
      # Close the old purchasing plan generated by frePPLe
      if self.verbosity > 0:
        print("Closing previous purchasing plan generated from frePPLe")  # 
      query = urllib.parse.quote("createdBy='%s' "
          # TODO the filter in the next line generates an incorrect query in Openbravo
          "and purchasingPlan.description='Bulk export' "
          "and salesOrderLine is null and workRequirement is null "
          "and requisitionLine is null" % self.openbravo_user_id)
      data = get_data(
        "/ws/dal/MRPPurchasingRunLine?where=%s" % query,
        self.openbravo_host,
        self.openbravo_user,
        self.openbravo_password,
        method="DELETE"
        )

      if self.filteredexport:        
        filter_expression_po = Parameter.getValue('openbravo.filter_export_purchase_order', self.database, "")
        if filter_expression_po:
          filter_expression_po = ' and (%s) ' %filter_expression_po
        filter_expression_do = Parameter.getValue('openbravo.filter_export_distribution_order', self.database, "")
        if filter_expression_do:
          filter_expression_do = ' and (%s) ' %filter_expression_do
      else:
        filter_expression_po = ""
        filter_expression_do = ""

      # Create new purchase plan
      starttime = time()
      if self.verbosity > 0:
        print("Exporting new purchasing plan...")
      count = 0
      now = datetime.now().strftime('%Y/%m/%d %H:%M:%S')
      identifier = uuid4().hex
      body = [
        #'<?xml version="1.0" encoding="UTF-8"?>',
        '<ob:Openbravo xmlns:ob="http://www.openbravo.com">',
        purchaseplan % (identifier, self.organization_id, self.openbravo_organization, now)
        ]
      cursor.execute('''
	       SELECT item.source, location.source, quantity, startdate, enddate, 'PO', supplier.source
         FROM purchase_order
         inner JOIN buffer
           ON buffer.item_id = purchase_order.item_id
           AND buffer.location_id = purchase_order.location_id
           AND buffer.subcategory = 'openbravo'
         inner join item
           ON item.name = purchase_order.item_id
           and item.source is not null
           and item.subcategory = 'openbravo'
         inner join location
           ON purchase_order.location_id = location.name
           and location.source is not null
           and location.subcategory = 'openbravo'
         inner join supplier
           on purchase_order.supplier_id = supplier.name
           and supplier.source is not null
           and supplier.subcategory = 'openbravo'
         where status = 'proposed' %s
         ''' % (filter_expression_po))
# 	   union all
# 	   select item.source, location.source, quantity, startdate, enddate, 'DO'
#          FROM distribution_order
#          inner JOIN buffer
#            ON buffer.item_id = distribution_order.item_id
#            AND buffer.location_id = distribution_order.destination_id
#            AND buffer.subcategory = 'openbravo'
#          inner join item
#            ON item.name = distribution_order.item_id
#            and item.source is not null
#            and item.subcategory = 'openbravo'
#          inner join location
#            ON distribution_order.destination_id = location.name
#            and location.source is not null
#            and location.subcategory = 'openbravo'
#          where status = 'proposed' %s
#         ''' % (filter_expression_po,filter_expression_do))
         
      for i in cursor.fetchall():
        body.append(purchasingplanline % (
          uuid4().hex, identifier, i[0], i[2], i[2],
          i[3].strftime("%Y-%m-%d %H:%M:%S"), 
          i[4].strftime("%Y-%m-%d %H:%M:%S"),
          i[5], i[6]
          ))
        count += 1
        break
        
      body.append('</mRPPurchasingRunLineList>')
      body.append('</MRPPurchasingRun>')
      body.append('</ob:Openbravo>')
      if count > 0:
        get_data(
          '/ws/dal/MRPPurchasingRun',
          self.openbravo_host, self.openbravo_user, self.openbravo_password,
          method="POST", xmldoc='\n'.join(body)
          )
      if self.verbosity > 0:
        print("Created purchasing plan with %d lines in %.2f seconds" % (count, (time() - starttime)))
    except Exception as e:
      raise CommandError("Error updating purchasing plan: %s" % e)
