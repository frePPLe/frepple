#
# Copyright (C) 2010-2013 by Johan De Taeye, frePPLe bvba
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
import xmlrpclib
from datetime import datetime
from time import time

from django.core.management.base import CommandError
from django.db import transaction, connections, DEFAULT_DB_ALIAS
from django.utils import six

from freppledb.common.models import Parameter

import logging
logger = logging.getLogger(__name__)


class Connector:

  def __init__(self, task, database=DEFAULT_DB_ALIAS, verbosity=0):
    self.task = task
    self.database = database
    self.verbosity = verbosity
    # Pick up configuration parameters
    self.odoo_user = Parameter.getValue("odoo.user", self.database)
    self.odoo_password = Parameter.getValue("odoo.password", self.database)
    self.odoo_db = Parameter.getValue("odoo.db", self.database)
    self.odoo_url = Parameter.getValue("odoo.url", self.database)
    self.odoo_company = Parameter.getValue("odoo.company", self.database)
    if not self.odoo_user:
      raise CommandError("Missing or invalid parameter odoo.user")
    if not self.odoo_password:
      raise CommandError("Missing or invalid parameter odoo.password")
    if not self.odoo_db:
      raise CommandError("Missing or invalid parameter odoo.db")
    if not self.odoo_url:
      raise CommandError("Missing or invalid parameter odoo.url")
    if not self.odoo_company:
      raise CommandError("Missing or invalid parameter odoo.company")
    self.odoo_language = Parameter.getValue("odoo.language", self.database, 'en_US')
    self.context = {'lang': self.odoo_language}


  def odoo_search(self, a, b=[]):
    return self.sock.execute(self.odoo_db, self.uid, self.odoo_password,
                               a, 'search', b, 0, 0, 0, self.context)


  def odoo_data(self, a, b, c):
    return self.sock.execute(self.odoo_db, self.uid, self.odoo_password,
                             a, 'read', b, c, self.context)


  def run(self):
      # Log in to the odoo server
      sock_common = xmlrpclib.ServerProxy(self.odoo_url + 'xmlrpc/common')
      self.uid = sock_common.login(self.odoo_db, self.odoo_user, self.odoo_password)

      # Connect to odoo server
      self.sock = xmlrpclib.ServerProxy(self.odoo_url + 'xmlrpc/object')

      # Create a database connection to the frePPLe database
      self.cursor = connections[self.database].cursor()

      # Upload all data
      self.export_procurement_order()
      self.task.status = '50%'
      self.task.save(using=self.database)
      transaction.commit(using=self.database)
      self.export_sales_order()
      self.task.status = '100%'
      self.task.save(using=self.database)
      transaction.commit(using=self.database)


  # Update the committed date of sales orders
  #   - uploading for each frePPLe demand where subcategory = 'odoo'
  #   - mapped fields frePPLe -> odoo sale.order
  #        - max(out_demand.plandate) -> requested_date
  # Note: Ideally we'ld like to update the committed date instead. (But it is read-only)
  def export_sales_order(self):
    transaction.enter_transaction_management(using=self.database)
    try:
      starttime = time()
      if self.verbosity > 0:
        print("Exporting requested date of sales orders...")
      self.cursor.execute('''select source, max(plandate)
          from demand
          left outer join out_demand
            on demand.name = out_demand.demand
          where demand.subcategory = 'odoo'
          group by source
         ''')
      cnt = 0
      for i, j in self.cursor.fetchall():
        if isinstance(j, six.string_types):
          # SQLite exports the date as a string
          j = datetime.strptime(j, "%Y-%m-%d %H:%M:%S")
        self.sock.execute(self.odoo_db, self.uid, self.odoo_password, 'sale.order', 'write',
          [int(i)], {'requested_date': j and j.strftime('%Y-%m-%d') or '1971-01-01',})
        cnt += 1
      if self.verbosity > 0:
        print("Updated %d sales orders in %.2f seconds" % (cnt, (time() - starttime)))
    except Exception as e:
      logger.error("Error updating sales orders", exc_info=1)
      raise CommandError("Error updating sales orders: %s" % e)
    finally:
      transaction.rollback(using=self.database)
      transaction.leave_transaction_management(using=self.database)


  # Upload procurement order data. They are translated in odoo into purchase orders
  # or manufacturing orders.
  #   - uploading frePPLe operationplans
  #   - meeting the criterion:
  #        - operation.subcategory = 'odoo'
  #        - not a delivery operationplan (since procurement order is directly
  #          created by the odoo sales order)
  #   - mapped fields frePPLe -> odoo production order
  #        - %id %name -> name
  #        - operationplan.quantity -> product_qty
  #        - operationplan.startdate -> date_planned
  #        - operation.location_id -> location_id
  #        - 1 (id for PCE) -> product_uom
  #        - configurable with parameter odoo.company -> company_id
  #        - 'make_to_order' -> procure_method
  #        - 'frePPLe' -> origin
  #   - Note that purchase order are uploaded as quotations. Once the quotation
  #     is created in odoo it is not revised any more by frePPLe.
  #     For instance: if the need for the purchase disappears later on, the request still
  #     remains in odoo. We could delete/refresh the quotations suggested by frePPLe,
  #     but this could confuse the buyer who has already contacted the supplier or any
  #     other work on the quotation.
  #     FrePPLe would show an excess alert, but it's up to the planner to act on it
  #     and cancel the purchase orders or quotations.
  def export_procurement_order(self):
    transaction.enter_transaction_management(using=self.database)
    try:
      starttime = time()

      # Look up the company id
      company_id = None
      for i in self.odoo_search('res.company', [('name','=',self.odoo_company)]):
        company_id = i
      if not company_id:
        raise Exception("Company configured in parameter odoo.company doesn't exist")

      if self.verbosity > 0:
        print("Canceling draft procurement orders")
      ids = self.odoo_search('procurement.order',
        ['|',('state','=', 'draft'),('state','=','cancel'),('origin','=', 'frePPLe'),])
      self.sock.execute(self.odoo_db, self.uid, self.odoo_password, 'procurement.order', 'unlink', ids)
      if self.verbosity > 0:
        print("Cancelled %d draft procurement orders in %.2f seconds" % (len(ids), (time() - starttime)))
      starttime = time()
      if self.verbosity > 0:
        print("Exporting procurement orders...")
      self.cursor.execute('''select
           out_operationplan.id, operation, out_operationplan.quantity,
           enddate, location.source as location,
           item.source as item, buffer.type
         from out_operationplan
         inner join out_flowplan
           on operationplan_id = out_operationplan.id
           and out_flowplan.quantity > 0
         inner join buffer
           on buffer.name = out_flowplan.thebuffer
           and buffer.subcategory = 'odoo'
         inner join location
           on location.name = buffer.location_id
           and location.subcategory = 'odoo'
         inner join item
           on item.name = buffer.item_id
           and item.subcategory = 'odoo'
         where out_operationplan.locked = 'f'
         ''')
      cnt = 0
      ids_buy = []
      ids_produce = []
      for i, j, k, l, m, n, o in self.cursor.fetchall():
        proc_order = {
          'name': ("%s %s" % (i,j)).encode('ascii','ignore'),  # TODO better handle unicode chars!
          'product_qty': str(k),
          'date_planned': l.strftime('%Y-%m-%d'),
          'product_id': int(n),
          'company_id': company_id,
          'product_uom': 1, # TODO set uom correctly?
          'location_id': int(m),
          'procure_method': 'make_to_order',
          'origin': 'frePPLe'
          }
        proc_order_id = self.sock.execute(self.odoo_db, self.uid, self.odoo_password, 'procurement.order', 'create', proc_order)
        if o == 'procure':
          ids_buy.append(proc_order_id)
        else:
          ids_produce.append(proc_order_id)
        cnt += 1
      if self.verbosity > 0:
        print("Uploaded %d procurement orders in %.2f seconds" % (cnt, (time() - starttime)))
      starttime = time()
      if self.verbosity > 0:
        print("Confirming %d procurement orders into purchasing quotations" % (len(ids_buy)))
      for i in ids_buy:
        self.sock.execute(self.odoo_db, self.uid, self.odoo_password, 'procurement.order', 'action_confirm', [i])
        self.sock.execute(self.odoo_db, self.uid, self.odoo_password, 'procurement.order', 'action_po_assign', [i])
      if self.verbosity > 0:
        print("Confirmed %d procurement orders in %.2f seconds" % (len(ids_buy), (time() - starttime)))
      starttime = time()
      if self.verbosity > 0:
        print("Confirming %d procurement orders into production orders" % (len(ids_produce)))
      for i in ids_produce:
        self.sock.execute(self.odoo_db, self.uid, self.odoo_password, 'procurement.order', 'action_produce_assign_product', [i])
        self.sock.execute(self.odoo_db, self.uid, self.odoo_password, 'procurement.order', 'action_confirm', [i])
      if self.verbosity > 0:
        print("Confirmed %d procurement orders in %.2f seconds" % (len(ids_produce), (time() - starttime)))
    except Exception as e:
      logger.error("Error exporting procurement orders", exc_info=1)
      raise CommandError("Error exporting procurement orders: %s" % e)
    finally:
      transaction.rollback(using=self.database)
      transaction.leave_transaction_management(using=self.database)

