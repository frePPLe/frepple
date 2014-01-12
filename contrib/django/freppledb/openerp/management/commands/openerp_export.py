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
from optparse import make_option
import xmlrpclib
from datetime import datetime, timedelta
from time import time

from django.core.management.base import BaseCommand, CommandError
from django.db import transaction, connections, DEFAULT_DB_ALIAS
from django.template.loader import render_to_string
from django.conf import settings
from django.utils.translation import ugettext as _

from freppledb.common.models import Parameter
from freppledb.execute.models import log


class Command(BaseCommand):
  help = "Upload planning results from frePPle into an OpenERP instance"

  option_list = BaseCommand.option_list + (
      make_option('--user', dest='user', type='string',
        help='User running the command'),
      make_option('--openerp_user', action='store', dest='openerp_user',
        help='OpenErp user name to connect'),
      make_option('--openerp_pwd', action='store', dest='openerp_password',
        help='OpenErp password to connect'),
      make_option('--openerp_db', action='store', dest='openerp_db',
        help='OpenErp database instance to import from'),
      make_option('--openerp_url', action='store', dest='openerp_url',
        help='OpenERP XMLRPC connection URL'),
      make_option('--database', action='store', dest='database',
        default=DEFAULT_DB_ALIAS, help='Nominates the frePPLe database to export from'),
  )

  requires_model_validation = False


  def openerp_search(self, a, b=[]):
    return self.sock.execute(self.openerp_db, self.uid, self.openerp_password, a, 'search', b)


  def openerp_data(self, a, b, c):
    return self.sock.execute(self.openerp_db, self.uid, self.openerp_password, a, 'read', b, c)


  def handle(self, **options):

    # Pick up the options
    if 'verbosity' in options: self.verbosity = int(options['verbosity'] or '1')
    else: self.verbosity = 1
    if 'user' in options: user = options['user']
    else: user = ''
    self.openerp_user = options['openerp_user']
    if not self.openerp_user:
      try:
        self.openerp_user = Parameter.objects.get(name="openerp_user").value
      except:
        self.openerp_user = 'admin'
    self.openerp_password = options['openerp_password']
    if not self.openerp_password:
      try:
        self.openerp_password = Parameter.objects.get(name="openerp_password").value
      except:
        self.openerp_password = 'admin'
    self.openerp_db = options['openerp_db']
    if not self.openerp_db:
      try:
        self.openerp_db = Parameter.objects.get(name="openerp_db").value
      except Exception as e:
        self.openerp_db = 'openerp'
    self.openerp_url = options['openerp_url']
    if not self.openerp_url:
      try:
        self.openerp_url = Parameter.objects.get(name="openerp_url").value
      except:
        self.openerp_url = 'http://localhost:8069/'
    if 'database' in options: self.database = options['database'] or DEFAULT_DB_ALIAS
    else: self.database = DEFAULT_DB_ALIAS
    if not self.database in settings.DATABASES.keys():
      raise CommandError("No database settings known for '%s'" % self.database )

    # Make sure the debug flag is not set!
    # When it is set, the django database wrapper collects a list of all SQL
    # statements executed and their timings. This consumes plenty of memory
    # and cpu time.
    tmp_debug = settings.DEBUG
    settings.DEBUG = False

    transaction.enter_transaction_management(using=self.database)
    try:
      # Logging message
      log(category='EXPORT', theuser=user,
        message=_('Start exporting to OpenERP')).save(using=self.database)
      transaction.commit(using=self.database)

      # Log in to the openerp server
      sock_common = xmlrpclib.ServerProxy(self.openerp_url + 'xmlrpc/common')
      self.uid = sock_common.login(self.openerp_db, self.openerp_user, self.openerp_password)

      # Connect to openerp server
      self.sock = xmlrpclib.ServerProxy(self.openerp_url + 'xmlrpc/object')

      # Create a database connection to the frePPLe database
      self.cursor = connections[self.database].cursor()

      # Upload all data
      self.export_procurement_order()
      self.export_sales_order()

      # Logging message
      log(category='EXPORT', theuser=user,
        message=_('Finished exporting to OpenERP')).save(using=self.database)

    except Exception as e:
      log(category='EXPORT', theuser=user,
        message=u'%s: %s' % (_('Failed exporting to OpenERP'),e)).save(using=self.database)
      raise CommandError(e)
    finally:
      transaction.commit(using=self.database)
      settings.DEBUG = tmp_debug
      transaction.leave_transaction_management(using=self.database)


  # Update the committed date of sales orders
  #   - uploading for each frePPLe demand whose subcategory = 'OpenERP'
  #   - mapped fields frePPLe -> OpenERP sale.order
  #        - max(out_demand.plandate) -> requested_date
  # Note: Ideally we'ld like to update the committed date instead. (But it is read-only)
  def export_sales_order(self):
    transaction.enter_transaction_management(using=self.database)
    try:
      starttime = time()
      if self.verbosity > 0:
        print("Exporting requested date of sales orders...")
      self.cursor.execute('''select substring(name from '^.*? '), max(plandate)
          from demand
          left outer join out_demand
            on demand.name = out_demand.demand
            and demand.subcategory = 'OpenERP'
            group by substring(name from '^.*? ')
         ''')
      cnt = 0
      for i, j in self.cursor.fetchall():
        result = self.sock.execute(self.openerp_db, self.uid, self.openerp_password, 'sale.order', 'write',
          [int(i)], {'requested_date': j and j.strftime('%Y-%m-%d') or 0,})
        cnt += 1
      if self.verbosity > 0:
        print("Updated %d sales orders in %.2f seconds" % (cnt, (time() - starttime)))
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
  def export_procurement_order(self):
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
           AND buffer.subcategory = 'OpenERP'
         ''')
      cnt = 0
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

