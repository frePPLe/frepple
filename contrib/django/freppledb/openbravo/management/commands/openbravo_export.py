#
# Copyright (C) 2014 by Johan De Taeye, frePPLe bvba
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
from __future__ import print_function
from optparse import make_option
from datetime import datetime
from time import time
import httplib
import base64

from django.core.management.base import BaseCommand, CommandError
from django.db import transaction, connections, DEFAULT_DB_ALIAS
from django.conf import settings

from freppledb.common.models import Parameter
from freppledb.execute.models import Task


class Command(BaseCommand):
  help = "Upload planning results from frePPle into an Openbravo instance"

  option_list = BaseCommand.option_list + (
      make_option('--user', dest='user', type='string',
        help='User running the command'),
      make_option('--database', action='store', dest='database',
        default=DEFAULT_DB_ALIAS, help='Nominates the frePPLe database to export from'),
      make_option('--task', dest='task', type='int',
        help='Task identifier (generated automatically if not provided)'),
  )

  requires_model_validation = False

  BOUNDARY = '----------ThIs_Is_tHe_bouNdaRY_$'

  def handle(self, **options):

    # Pick up the options
    if 'verbosity' in options: self.verbosity = int(options['verbosity'] or '1')
    else: self.verbosity = 1
    if 'user' in options: user = options['user']
    else: user = ''
    if 'database' in options: self.database = options['database'] or DEFAULT_DB_ALIAS
    else: self.database = DEFAULT_DB_ALIAS
    if not self.database in settings.DATABASES.keys():
      raise CommandError("No database settings known for '%s'" % self.database )

    # Pick up configuration parameters
    self.openbravo_user = Parameter.getValue("openbravo.user", self.database)
    self.openbravo_password = Parameter.getValue("openbravo.password", self.database)
    self.openbravo_host = Parameter.getValue("openbravo.host", self.database)

    # Make sure the debug flag is not set!
    # When it is set, the django database wrapper collects a list of all SQL
    # statements executed and their timings. This consumes plenty of memory
    # and cpu time.
    tmp_debug = settings.DEBUG
    settings.DEBUG = False

    now = datetime.now()
    ac = transaction.get_autocommit(using=self.database)
    transaction.set_autocommit(False, using=self.database)
    task = None
    try:
      # Initialize the task
      if 'task' in options and options['task']:
        try: task = Task.objects.all().using(self.database).get(pk=options['task'])
        except: raise CommandError("Task identifier not found")
        if task.started or task.finished or task.status != "Waiting" or task.name != 'Openbravo export':
          raise CommandError("Invalid task identifier")
        task.status = '0%'
        task.started = now
      else:
        task = Task(name='Openbravo export', submitted=now, started=now, status='0%', user=user)
      task.save(using=self.database)
      transaction.commit(using=self.database)

      # Create a database connection to the frePPLe database
      cursor = connections[self.database].cursor()

      # Upload all data
      #self.export_procurement_order(cursor)
      self.export_sales_order(cursor)

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
      if task: task.save(using=self.database)
      try: transaction.commit(using=self.database)
      except: pass
      settings.DEBUG = tmp_debug
      transaction.set_autocommit(ac, using=self.database)


  def post_data(self, url, xmldoc):
    # Send the request
    webservice = httplib.HTTP(self.openbravo_host)
    webservice.putrequest("POST", url)
    webservice.putheader("Host", self.openbravo_host)
    webservice.putheader("User-Agent", "frePPLe-Openbravo connector")
    webservice.putheader("Content-type", 'text/xml')
    webservice.putheader("Content-length", str(len(xmldoc)))
    webservice.putheader("Authorization", "Basic %s" % base64.encodestring('%s:%s' % (self.openbravo_user, self.openbravo_password)).replace('\n', ''))
    webservice.endheaders()
    webservice.send(xmldoc)

    # Get the response
    statuscode, statusmessage, header = webservice.getreply()
    if statuscode != httplib.OK:
      raise Exception(statusmessage)
    res = webservice.getfile().read()
    if self.verbosity > 2:
      print('Request: ', url)
      print('Response status: ', statuscode, statusmessage, header)
      print('Response content: ', res)


  # Update the committed date of sales orders
  #   - uploading for each frePPLe demand whose subcategory = 'openbravo'
  #   - mapped fields frePPLe -> Openbravo OrderLine
  #        - max(out_demand.plandate) -> description
  def export_sales_order(self, cursor):
    transaction.enter_transaction_management(using=self.database)
    try:
      starttime = time()
      if self.verbosity > 0:
        print("Exporting expected delivery date of sales orders...")
      cursor.execute('''select demand.source, max(plandate)
          from demand
          left outer join out_demand
            on demand.name = out_demand.demand
          where demand.subcategory = 'openbravo'
            and status = 'open'
          group by source
         ''')
      count = 0
      body = [
        '<?xml version="1.0" encoding="UTF-8"?>',
        '<ob:Openbravo xmlns:ob="http://www.openbravo.com">'
        ]
      for i in cursor.fetchall():
        body.append('<OrderLine id="%s"><description>Pongo d%s</description></OrderLine>' % i)
        count += 1
        if self.verbosity > 0 and count % 500 == 1:
          print('.', end="")
      if self.verbosity > 0: print ('')
      body.append('</ob:Openbravo>')
      self.post_data('/openbravo/ws/dal/OrderLine', '\n'.join(body))
      if self.verbosity > 0:
        print("Updated %d sales orders in %.2f seconds" % (count, (time() - starttime)))
    except Exception as e:
      print("Error updating sales orders: %s" % e)
    finally:
      transaction.rollback(using=self.database)
      transaction.leave_transaction_management(using=self.database)


  # Upload procurement order data
  #   - uploading frePPLe operationplans
  #   - meeting the criterion:
  #        - operation.subcategory = 'OpenERP'
  #        - not a delivery operationplan (since procurement order is directly
  #          created by the OpenERP sales order)
  #   - mapped fields frePPLe -> OpenERP production order
  #        - %id %name -> name
  #        - operationplan.quantity -> product_qty
  #        - operationplan.startdate -> date_planned
  #        - operation.location_id -> location_id
  #        - 1 (id for PCE) -> product_uom
  #        - 1 (hardcoded...) ->company_id
  #        - 'make_to_order' -> procure_method
  #        - 'frePPLe' -> origin
  #   - Note that purchase order are uploaded as quotations. Once the quotation
  #     is created in OpenERP it is not revised any more by frePPLe.
  #     For instance: if the need for the purchase disappears later on, the request still
  #     remains in OpenERP. We could delete/refresh the quotations suggested by frePPLe,
  #     but this could confuse the buyer who has already contacted the supplier or any
  #     other work on the quotation.
  #     FrePPLe would show an excess alert, but it's up to the planner to act on it
  #     and cancel the purchase orders or quotations.
  def export_procurement_order(self, cursor):
    transaction.enter_transaction_management(using=self.database)
    try:
      starttime = time()
      if self.verbosity > 0:
        print("Canceling draft procurement orders")
      ids = self.openerp_search('procurement.order',
        ['|',('state','=', 'draft'),('state','=','cancel'),('origin','=', 'frePPLe'),])
      self.sock.execute(self.openerp_db, self.uid, self.openerp_password, 'procurement.order', 'unlink', ids)
      if self.verbosity > 0:
        print("Cancelled %d draft procurement orders in %.2f seconds" % (len(ids), (time() - starttime)))
      starttime = time()
      if self.verbosity > 0:
        print("Exporting procurement orders...")
      self.cursor.execute('''SELECT
           out_operationplan.id, operation, out_operationplan.quantity,
           enddate,
           substring(buffer.location_id from '^.*? '),
           substring(buffer.item_id from '^.*? ')
         FROM out_operationplan
         inner join out_flowplan
           ON operationplan_id = out_operationplan.id
           AND out_flowplan.quantity > 0
         inner JOIN buffer
           ON buffer.name = out_flowplan.thebuffer
           AND buffer.subcategory = 'openbravo'
         ''')
      cnt = 0

      ddd='''
<ProcurementRequisition id="910913871D7C444B901E958647B72A47" identifier="10000000">
<id>910913871D7C444B901E958647B72A47</id>
<client id="23C59575B9CF467C9620760EB255B389" entity-name="ADClient" identifier="F&B International Group"/>
<organization id="E443A31992CB4635AFCAEABE7183CE85" entity-name="Organization" identifier="F&B España - Región Norte"/>
<active>true</active>
<creationDate transient="true">2014-01-14T16:04:29.910Z</creationDate>
<createdBy transient="true" id="100" entity-name="ADUser" identifier="Openbravo"/>
<updated transient="true">2014-01-14T16:12:59.0Z</updated>
<updatedBy transient="true" id="100" entity-name="ADUser" identifier="Openbravo"/>
<description xsi:nil="true"/>
<documentNo>10000000</documentNo>
<businessPartner id="FC78DDDA840A4775994A6D4DA1C2C986" entity-name="BusinessPartner" identifier="Generación Eléctrica, SA"/>
<priceList id="CBC16D5792744C669D388FC4F66B85FD" entity-name="PricingPriceList" identifier="Otros servicios"/>
<currency id="102" entity-name="Currency" identifier="EUR"/>
<createPO>false</createPO>
<documentStatus>CL</documentStatus>
<documentAction>CL</documentAction>
<processed>false</processed>
<userContact id="100" entity-name="ADUser" identifier="Openbravo"/>
<processNow>false</processNow>
<procurementRequisitionLineList>
<ProcurementRequisitionLine id="7111EF8F1B81412BB3D8C6F5295D2E33" identifier="10000000 - Alquiler de oficina - 1 - 15-01-2014">
<id>7111EF8F1B81412BB3D8C6F5295D2E33</id>
<client id="23C59575B9CF467C9620760EB255B389" entity-name="ADClient" identifier="F&B International Group"/>
<organization id="E443A31992CB4635AFCAEABE7183CE85" entity-name="Organization" identifier="F&B España - Región Norte"/>
<active>true</active>
<creationDate transient="true">2014-01-14T16:06:40.254Z</creationDate>
<createdBy transient="true" id="100" entity-name="ADUser" identifier="Openbravo"/>
<updated transient="true">2014-01-14T16:12:59.0Z</updated>
<updatedBy transient="true" id="100" entity-name="ADUser" identifier="Openbravo"/>
<requisition id="910913871D7C444B901E958647B72A47" entity-name="ProcurementRequisition" identifier="10000000"/>
<product id="19857ACFC55D45E2AECAF85B2506C3DB" entity-name="Product" identifier="Alquiler de oficina"/>
<quantity>1</quantity>
<listPrice>0</listPrice>
<lineNetAmount>0</lineNetAmount>
<businessPartner xsi:nil="true"/>
<uOM id="100" entity-name="UOM" identifier="Unit"/>
<orderUOM xsi:nil="true"/>
<orderQuantity xsi:nil="true"/>
<attributeSetValue xsi:nil="true"/>
<requisitionLineStatus>D</requisitionLineStatus>
<matchedPOQty>0</matchedPOQty>
<description xsi:nil="true"/>
<changeStatus>false</changeStatus>
<internalNotes xsi:nil="true"/>
<notesForSupplier xsi:nil="true"/>
<plannedDate inactive="true" xsi:nil="true"/>
<needByDate>2014-01-15T00:00:00.0Z</needByDate>
<unitPrice>0</unitPrice>
<discount>0</discount>
<currency id="102" entity-name="Currency" identifier="EUR"/>
<lockedBy xsi:nil="true"/>
<lockQty xsi:nil="true"/>
<lockPrice xsi:nil="true"/>
<priceList id="91AE1E96A30844209CD996917E193BE1" entity-name="PricingPriceList" identifier="Tarifa Bebidas Alegres"/>
<lockDate xsi:nil="true"/>
<lockCause xsi:nil="true"/>
<lineNo>10</lineNo>
<grossUnitPrice>0</grossUnitPrice>
<grossAmount>0</grossAmount>
<procurementRequisitionPOMatchList/>
</ProcurementRequisitionLine>
</procurementRequisitionLineList>
</ProcurementRequisition>'''




      ids_buy = []
      ids_produce = []
      for i, j, k, l, m, n in self.cursor.fetchall():
        proc_order = {
          'name': "%s %s" % (i,j),
          'product_qty': str(k),
          'date_planned': l.strftime('%Y-%m-%d'),
          'product_id': n,
          'company_id': 1,
          'product_uom': 1,
          'location_id': m,
          'procure_method': 'make_to_order',
          'origin': 'frePPLe'
          }
        proc_order_id = self.sock.execute(self.openerp_db, self.uid, self.openerp_password, 'procurement.order', 'create', proc_order)
        if j.find('rocure') >= 0:
          ids_buy.append(proc_order_id)
        else:
          ids_produce.append(proc_order_id)
        cnt += 1
      if self.verbosity > 0:
        print("Uploaded %d procurement orders in %.2f seconds" % (cnt, (time() - starttime)))
      starttime = time()
      if self.verbosity > 0:
        print("Confirming %d procurement orders into purchasing quotations" % (len(ids_buy)))
      self.sock.execute(self.openerp_db, self.uid, self.openerp_password, 'procurement.order', 'action_confirm', ids_buy)
      self.sock.execute(self.openerp_db, self.uid, self.openerp_password, 'procurement.order', 'action_po_assign', ids_buy)
      if self.verbosity > 0:
        print("Confirmed %d procurement orders in %.2f seconds" % (len(ids_buy), (time() - starttime)))
      starttime = time()
      if self.verbosity > 0:
        print("Confirming %d procurement orders into production orders" % (len(ids_produce)))
      self.sock.execute(self.openerp_db, self.uid, self.openerp_password, 'procurement.order', 'action_produce_assign_product', ids_produce)
      self.sock.execute(self.openerp_db, self.uid, self.openerp_password, 'procurement.order', 'action_confirm', ids_produce)
      if self.verbosity > 0:
        print("Confirmed %d procurement orders in %.2f seconds" % (len(ids_produce), (time() - starttime)))
    except Exception as e:
      print("Error exporting procurement orders: %s" % e)
    finally:
      transaction.rollback(using=self.database)
      transaction.leave_transaction_management(using=self.database)

