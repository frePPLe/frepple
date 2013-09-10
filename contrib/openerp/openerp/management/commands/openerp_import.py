#
# Copyright (C) 2010-2012 by Johan De Taeye, frePPLe bvba
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
from django.conf import settings
from django.utils.translation import ugettext as _

from freppledb.common.models import Parameter
from freppledb.execute.models import log

locations = {}
warehouses = {}
shops = {}

class Command(BaseCommand):

  help = "Loads data from an OpenERP instance into the frePPLe database"

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
      make_option('--delta', action='store', dest='delta', type="float",
        default='3650', help='Number of days for which we extract changed OpenERP data'),
      make_option('--database', action='store', dest='database',
        default=DEFAULT_DB_ALIAS, help='Nominates the frePPLe database to load'),
  )

  requires_model_validation = False

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
    if 'delta' in options: self.delta = float(options['delta'] or '3650')
    else: self.delta = 3650
    self.date = datetime.now()
    self.delta = str(self.date - timedelta(days=self.delta))
    if 'database' in options: self.database = options['database'] or DEFAULT_DB_ALIAS
    else: self.database = DEFAULT_DB_ALIAS
    if not self.database in settings.DATABASES.keys():
      raise CommandError("No database settings known for '%s'" % self.database )

    # Make sure the debug flag is not set!
    # When it is set, the django database wrapper collects a list of all sql
    # statements executed and their timings. This consumes plenty of memory
    # and cpu time.
    tmp_debug = settings.DEBUG
    settings.DEBUG = False

    transaction.enter_transaction_management(using=self.database)
    transaction.managed(True, using=self.database)
    try:
      # Logging message
      log(category='IMPORT', theuser=user,
        message=_('Start importing from OpenERP')).save(using=self.database)
      transaction.commit(using=self.database)

      # Log in to the openerp server
      sock_common = xmlrpclib.ServerProxy(self.openerp_url + 'xmlrpc/common')
      self.uid = sock_common.login(self.openerp_db, self.openerp_user, self.openerp_password)

      # Connect to openerp server
      self.sock = xmlrpclib.ServerProxy(self.openerp_url + 'xmlrpc/object')

      # Create a database connection to the frePPLe database
      cursor = connections[self.database].cursor()

      # Sequentially load all data
      self.import_customers(cursor)
      self.import_products(cursor)
      self.import_locations(cursor)
      self.import_salesorders(cursor)
      self.import_workcenters(cursor)
      self.import_onhand(cursor)
      self.import_purchaseorders(cursor)
      self.import_boms(cursor)
      self.import_policies(cursor)
      #self.import_setupmatrices(cursor)

      # Logging message
      log(category='IMPORT', theuser=user,
        message=_('Finished importing from OpenERP')).save(using=self.database)

    except Exception as e:
      log(category='IMPORT', theuser=user,
        message=u'%s: %s' % (_('Failed importing from OpenERP'),e)).save(using=self.database)
      raise CommandError(e)
    finally:
      transaction.commit(using=self.database)
      settings.DEBUG = tmp_debug
      transaction.leave_transaction_management(using=self.database)


  def openerp_search(self, a, b=[]):
    return self.sock.execute(self.openerp_db, self.uid, self.openerp_password, a, 'search', b)


  def openerp_data(self, a, b, c):
    return self.sock.execute(self.openerp_db, self.uid, self.openerp_password, a, 'read', b, c)


  # Importing customers
  #   - extracting recently changed res.partner objects
  #   - meeting the criterion:
  #        - %active = True
  #        - %customer = True
  #   - mapped fields OpenERP -> frePPLe customer
  #        - %id %name -> name
  #        - %ref     -> description
  #        - 'OpenERP' -> subcategory
  def import_customers(self, cursor):
    transaction.enter_transaction_management(using=self.database)
    transaction.managed(True, using=self.database)
    try:
      starttime = time()
      if self.verbosity > 0:
        print("Importing customers...")
      cursor.execute("SELECT name FROM customer")
      frepple_keys = set([ i[0] for i in cursor.fetchall()])
      ids = self.openerp_search( 'res.partner',
        ['|',('create_date','>', self.delta),('write_date','>', self.delta),
         '|',('active', '=', 1),('active', '=', 0)])
      fields = ['name', 'active', 'customer', 'ref']
      insert = []
      update = []
      delete = []
      for i in self.openerp_data('res.partner', ids, fields):
        name = u'%d %s' % (i['id'],i['name'])
        if i['active'] and i['customer']:
          if name in frepple_keys:
            update.append(i)
          else:
            insert.append(i)
        elif name in frepple_keys:
          delete.append( (name,) )
      cursor.executemany(
        "insert into customer \
          (name,description,subcategory,lastmodified) \
          values (%%s,%%s,'OpenERP','%s')" % self.date,
        [(
           u'%d %s' % (i['id'],i['name']),
           i['ref'] or '',
         ) for i in insert
        ])
      cursor.executemany(
        "update customer \
          set description=%%s, subcategory='OpenERP',lastmodified='%s' \
          where name=%%s" % self.date,
        [(
           i['ref'] or '',
           u'%d %s' % (i['id'],i['name'])
         ) for i in update
        ])
      for i in delete:
        try: cursor.execute("delete from customer where name=%s",i)
        except:
          # Delete fails when there are dependent records in the database.
          cursor.execute("update customer set subcategory=null, lastmodified='%s' where name=%%s" % self.date,i)
      transaction.commit(using=self.database)
      if self.verbosity > 0:
        print("Inserted %d new customers" % len(insert))
        print("Updated %d existing customers" % len(update))
        print("Deleted %d customers" % len(delete))
        print("Imported customers in %.2f seconds" % (time() - starttime))
    except Exception as e:
      transaction.rollback(using=self.database)
      print("Error importing customers: %s" % e)
    finally:
      transaction.commit(using=self.database)
      transaction.leave_transaction_management(using=self.database)


  # Importing products
  #   - extracting recently changed product.product objects
  #   - meeting the criterion:
  #        - %active = True
  #   - mapped fields OpenERP -> frePPLe item
  #        - %id %name -> name
  #        - %code     -> description & name
  #        - %variants -> name
  #        - 'OpenERP' -> subcategory
  #   - The modeling in frePPLe is independent of the procurement method in
  #     OpenERP. For both "on order" and "on stock" we bring the order to
  #     frePPLe and propagate upstream.
  #   - The name of the item in frePPLe is different whether or not the   TODO verify
  #     CODE and VARIANTS fields are filled in in OpenERP.
  #     This rule matches the convention used internal in OpenERP for a text
  #     description of an item, and MUST be followed.

  # TODO also get template.produce_delay, property_stock_production, property_stock_inventory, and property_stock_procurement?

  def import_products(self, cursor):
    transaction.enter_transaction_management(using=self.database)
    transaction.managed(True, using=self.database)
    try:
      starttime = time()
      if self.verbosity > 0:
        print("Importing products...")
      cursor.execute("SELECT name FROM item")
      frepple_keys = set([ i[0] for i in cursor.fetchall()])
      ids = self.openerp_search('product.product', [
        '|',('create_date','>', self.delta),('write_date','>', self.delta),
        '|',('active', '=', 1),('active', '=', 0)
        ])
      fields = ['name', 'code', 'active', 'product_tmpl_id', 'variants']
      insert = []
      update = []
      delete = []
      for i in self.openerp_data('product.product', ids, fields):
        #if i['code'] and i['variants']:
        #  name = u'%d [%s] %s - %s' % (i['id'], i['code'], i['name'], i['variants'])
        #elif i['code']:
        #  name = u'%d [%s] %s' % (i['id'], i['code'], i['name'])
        #elif i['variants']:
        #  name = u'%d %s - %s' % (i['id'], i['code'], i['name'], i['variants'])
        #else:
        name = u'%d %s' % (i['id'], i['name'])
        if i['active']:
          if name in frepple_keys:
            update.append( (i['code'] or '',name) )
          else:
            insert.append( (name, i['code'] or '') )
        elif name in frepple_keys:
          delete.append( (name,) )
      cursor.executemany(
        "insert into item \
          (name,description,subcategory,lastmodified) \
          values (%%s,%%s,'OpenERP','%s')" % self.date,
        insert
        )
      cursor.executemany(
        "update item \
          set description=%%s, subcategory='OpenERP', lastmodified='%s' \
          where name=%%s" % self.date,
        update
        )
      for i in delete:
        try: cursor.execute("delete from item where name=%s", i)
        except:
          # Delete fails when there are dependent records in the database.
          cursor.execute("update item set subcategory=null, lastmodified='%s' where name=%%s" % self.date, i)
      transaction.commit(using=self.database)
      if self.verbosity > 0:
        print("Inserted %d new products" % len(insert))
        print("Updated %d existing products" % len(update))
        print("Deleted %d products" % len(delete))
        print("Imported products in %.2f seconds" % (time() - starttime))
    except Exception as e:
      transaction.rollback(using=self.database)
      print("Error importing products: %s" % e)
    finally:
      transaction.commit(using=self.database)
      transaction.leave_transaction_management(using=self.database)


  # Importing locations
  #   - extracting stock.location objects
  #   - NO filter on recently changed locations
  #   - meeting the criterion:
  #        - %active = True
  #        - %usage = 'internal'
  #   - mapped fields OpenERP -> frePPLe location
  #        - %id %name -> name
  #        - 'OpenERP' -> subcategory
  def import_locations(self, cursor):
    global locations
    transaction.enter_transaction_management(using=self.database)
    transaction.managed(True, using=self.database)
    try:
      starttime = time()
      if self.verbosity > 0:
        print("Importing locations...")
      cursor.execute("SELECT name FROM location")
      frepple_keys = set([ i[0] for i in cursor.fetchall()])
      ids = self.openerp_search('stock.location', ['|',('active', '=', 1),('active', '=', 0)])
      fields = ['name', 'usage', 'active']
      insert = []
      update = []
      delete = []
      for i in self.openerp_data('stock.location', ids, fields):
        name = u'%d %s' % (i['id'],i['name'])
        locations[i['id']] = name
        if i['active'] and i['usage'] == 'internal':
          if name in frepple_keys:
            update.append(i)
          else:
            insert.append(i)
        elif name in frepple_keys:
          delete.append( (name,) )
      cursor.executemany(
        "insert into location \
          (name,subcategory,lastmodified) \
          values (%%s,'OpenERP','%s')" % self.date,
        [(
           u'%d %s' % (i['id'],i['name']),
         ) for i in insert
        ])
      cursor.executemany(
        "update location \
          set subcategory='OpenERP', lastmodified='%s' \
          where name=%%s" % self.date,
        [(
           u'%d %s' % (i['id'],i['name']),
         ) for i in update
        ])
      for i in delete:
        try: cursor.execute("delete from location where name=%s",i)
        except:
          # Delete fails when there are dependent records in the database.
          cursor.execute("update location set subcategory=null, lastmodified='%s' where name=%%s" % self.date, i)
      transaction.commit(using=self.database)
      if self.verbosity > 0:
        print("Inserted %d new locations" % len(insert))
        print("Updated %d existing locations" % len(update))
        print("Deleted %d locations" % len(delete))
        print("Imported locations in %.2f seconds" % (time() - starttime))
    except Exception as e:
      transaction.rollback(using=self.database)
      print("Error importing locations: %s" % e)
    finally:
      transaction.commit(using=self.database)
      transaction.leave_transaction_management(using=self.database)


  # Importing sales orders
  #   - Extracting recently changed sales.order and sales.order.line objects
  #   - The delivery location is derived as follows:
  #       - each SO has a "shop" field
  #       - that shop is linked to a "warehouse"
  #       - that warehouse has a "stock location"
  #       - the order will be delivered from this location
  #   - meeting the criterion:
  #        - %sol_state = 'confirmed'
  #   - mapped fields OpenERP -> frePPLe delivery operation
  #        - 'delivery %sol_product_id %sol_product_name from %loc' -> name
  #   - mapped fields OpenERP -> frePPLe buffer
  #        - '%sol_product_id %sol_product_name @ %loc' -> name
  #   - mapped fields OpenERP -> frePPLe delivery flow
  #        - 'delivery %sol_product_id %sol_product_name from %loc' -> operation
  #        - '%sol_product_id %sol_product_name @ %loc' -> buffer
  #        - quantity -> -1
  #        -  'start' -> type
  #   - mapped fields OpenERP -> frePPLe demand
  #        - %sol_id %so_name %sol_sequence -> name
  #        - %sol_product_uom_qty -> quantity
  #        - %sol_product_id -> item
  #        - %so_partner_id -> customer
  #        - %so_requested_date or %so_date_order -> due
  #        - 'OpenERP' -> subcategory
  #        - 1 -> priority
  #   - The picking policy 'complete' is supported at the sales order line
  #     level only in frePPLe. FrePPLe doesn't allow yet to coordinate the
  #     delivery of multiple lines in a sales order (except with hacky
  #     modeling construct).
  #   - The field requested_date is only available when sale_order_dates is
  #     installed.
  #     However, that module computes the commitment date in a pretty naive way
  #     and may not be appropriate for frePPLe integration. TODO...
  def import_salesorders(self, cursor):
    global warehouses, shops
    transaction.enter_transaction_management(using=self.database)
    transaction.managed(True, using=self.database)
    try:
      starttime = time()

      # Get the stocking location of each warehouse (where we deliver from)
      if self.verbosity > 0:
        print("Extracting warehouse list...")
      ids = self.openerp_search('stock.warehouse')
      fields = ['name', 'lot_stock_id']
      for i in self.openerp_data('stock.warehouse', ids, fields):
        warehouses[i['id']] = locations[i['lot_stock_id'][0]]

      # Get the stocking location of each warehouse (where we deliver from)
      if self.verbosity > 0:
        print("Extracting shop list...")
      ids = self.openerp_search('sale.shop')
      fields = ['name', 'warehouse_id']
      for i in self.openerp_data('sale.shop', ids, fields):
        shops[i['id']] = warehouses[i['warehouse_id'][0]]

      # Now the list of sales orders
      deliveries = set()
      if self.verbosity > 0:
        print("Importing sales orders...")
      cursor.execute("SELECT name FROM demand")
      frepple_keys = set([ i[0] for i in cursor.fetchall()])
      ids = self.openerp_search('sale.order.line',
        ['|',('create_date','>', self.delta),('write_date','>', self.delta),])
      fields = ['sequence', 'state', 'type', 'product_id', 'product_uom_qty', 'product_uom', 'order_id']
      fields2 = ['partner_id', 'requested_date', 'date_order', 'picking_policy', 'shop_id']
      insert = []
      update = []
      delete = []
      for i in self.openerp_data('sale.order.line', ids, fields):
        name = u'%d %d %s %d' % (i['order_id'][0], i['id'], i['order_id'][1], i['sequence'])
        if i['state'] == 'confirmed':
          product = u'%s %s' % (i['product_id'][0], i['product_id'][1])
          j = self.openerp_data('sale.order', [i['order_id'][0],], fields2)[0]
          location = shops[j['shop_id'][0]]
          operation = u'delivery %s from %s' % (product, location)
          buffer = u'%s @ %s' % (product, location)
          deliveries.update([(product,location,operation,buffer),])
          if name in frepple_keys:
            update.append( (
              product,
              u'%s %s' % (j['partner_id'][0], j['partner_id'][1]),
              i['product_uom_qty'],
              j['picking_policy'] == 'one' and i['product_uom_qty'] or 1.0,
              j['requested_date'] or j['date_order'],
              operation,
              name,
              ) )
          else:
            insert.append( (
              name,
              product,
              u'%d %s' % (j['partner_id'][0], j['partner_id'][1]),
              i['product_uom_qty'],
              j['picking_policy'] == 'one' and i['product_uom_qty'] or 1.0,
              j['requested_date'] or j['date_order'],
              operation,
              ) )
        elif name in frepple_keys:
          delete.append( (name,) )

      # Create or update delivery operations
      cursor.execute("SELECT name FROM operation where name like 'delivery%'")
      frepple_keys = set([ i[0] for i in cursor.fetchall()])
      cursor.executemany(
        "insert into operation \
          (name,location_id,subcategory,lastmodified) \
          values (%%s,%%s,'OpenERP','%s')" % self.date,
        [ (i[2],i[1]) for i in deliveries if i[2] not in frepple_keys ])
      cursor.executemany(
        "update operation \
          set location_id=%%s, subcategory='OpenERP' ,lastmodified='%s' where name=%%s" % self.date,
        [ (i[1],i[2]) for i in deliveries if i[2] in frepple_keys ])

      # Create or update delivery buffers
      cursor.execute("SELECT name FROM buffer")
      frepple_keys = set([ i[0] for i in cursor.fetchall()])
      cursor.executemany(
        "insert into buffer \
          (name,item_id,location_id,subcategory,lastmodified) \
          values(%%s,%%s,%%s,'OpenERP','%s')" % self.date,
        [ (i[3],i[0],i[1]) for i in deliveries if i[3] not in frepple_keys ])
      cursor.executemany(
        "update buffer \
          set item_id=%%s, location_id=%%s, subcategory='OpenERP', lastmodified='%s' where name=%%s" % self.date,
        [ (i[0],i[1],i[3]) for i in deliveries if i[3] in frepple_keys ])

      # Create or update flow on delivery operation
      cursor.execute("SELECT operation_id, thebuffer_id FROM flow")
      frepple_keys = set([ i for i in cursor.fetchall()])
      cursor.executemany(
        "insert into flow \
          (operation_id,thebuffer_id,quantity,type,lastmodified) \
          values(%%s,%%s,-1,'start','%s')" % self.date,
        [ (i[2],i[3]) for i in deliveries if (i[2],i[3]) not in frepple_keys ])
      cursor.executemany(
        "update flow \
          set quantity=-1, type='start', lastmodified='%s' where operation_id=%%s and thebuffer_id=%%s" % self.date,
        [ (i[2],i[3]) for i in deliveries if (i[2],i[3]) in frepple_keys ])

      # Create or update demands
      cursor.executemany(
        "insert into demand \
          (name,item_id,customer_id,quantity,minshipment,due,operation_id,priority,subcategory,lastmodified) \
          values (%%s,%%s,%%s,%%s,%%s,%%s,%%s,1,'OpenERP','%s')" % self.date,
        insert)
      cursor.executemany(
        "update demand \
          set item_id=%%s, customer_id=%%s, quantity=%%s, minshipment=%%s, due=%%s, operation_id=%%s, priority=1, subcategory='OpenERP', lastmodified='%s' \
          where name=%%s" % self.date,
        update)
      for i in delete:
        try: cursor.execute("delete from demand where name=%s",i)
        except:
          # Delete fails when there are dependent records in the database.
          cursor.execute("update demand set quantity=0, subcategory=null, lastmodified='%s' where name=%%s" % self.date,i)

      if self.verbosity > 0:
        print("Created or updated %d delivery operations" % len(deliveries))
        print("Inserted %d new sales orders" % len(insert))
        print("Updated %d existing sales orders" % len(update))
        print("Deleted %d sales orders" % len(delete))
        print("Imported sales orders in %.2f seconds" % (time() - starttime))
    except Exception as e:
      transaction.rollback(using=self.database)
      print("Error importing sales orders: %s" % e)
    finally:
      transaction.commit(using=self.database)
      transaction.leave_transaction_management(using=self.database)


  # Importing workcenters
  #   - extracting recently changed mrp.workcenter objects
  #   - meeting the criterion:
  #        - %active = True
  #   - mapped fields OpenERP -> frePPLe resource
  #        - %id %name -> name
  #        - %cost_hour -> cost
  #        - capacity_per_cycle -> maximum
  #        - 'OpenERP' -> subcategory
  #   - A bit surprising, but OpenERP doesn't assign a location or company to
  #     a workcenter.
  #     You should assign a location in frePPLe to assure that the user interface
  #     working .
  #
  def import_workcenters(self, cursor):
    transaction.enter_transaction_management(using=self.database)
    transaction.managed(True, using=self.database)
    try:
      starttime = time()
      if self.verbosity > 0:
        print("Importing workcenters...")
      cursor.execute("SELECT name FROM resource")
      frepple_keys = set([ i[0] for i in cursor.fetchall()])
      ids = self.openerp_search('mrp.workcenter',
        ['|',('create_date','>', self.delta),('write_date','>', self.delta),
         '|',('active', '=', 1),('active', '=', 0)])
      fields = ['name', 'active', 'costs_hour', 'capacity_per_cycle']
      insert = []
      update = []
      delete = []
      for i in self.openerp_data('mrp.workcenter', ids, fields):
        name = u'%d %s' % (i['id'],i['name'])
        if i['active']:
          if name in frepple_keys:
            update.append(i)
          else:
            insert.append(i)
        elif name in frepple_keys:
          delete.append( (name,) )
      cursor.executemany(
        "insert into resource \
          (name,cost,maximum,subcategory,lastmodified) \
          values (%%s,%%s,%%s,'OpenERP','%s')" % self.date,
        [(
           u'%d %s' % (i['id'],i['name']),
           i['costs_hour'] or 0,
           i['capacity_per_cycle'] or 1,
         ) for i in insert
        ])
      cursor.executemany(
        "update resource \
          set cost=%%s, maximum=%%s, subcategory='OpenERP', lastmodified='%s' \
          where name=%%s" % self.date,
        [(
           i['costs_hour'] or 0,
           i['capacity_per_cycle'] or 1,
           u'%d %s' % (i['id'],i['name']),
         ) for i in update
        ])
      for i in delete:
        try: cursor.execute("delete from resource where name=%s",i)
        except:
          # Delete fails when there are dependent records in the database.
          cursor.execute("update resource set subcategory=null, lastmodified='%s' where name=%%s" % self.date,i)
      transaction.commit(using=self.database)
      if self.verbosity > 0:
        print("Inserted %d new workcenters" % len(insert))
        print("Updated %d existing workcenters" % len(update))
        print("Deleted %d workcenters" % len(delete))
        print("Imported workcenters in %.2f seconds" % (time() - starttime))
    except Exception as e:
      transaction.rollback(using=self.database)
      print("Error importing workcenters: %s" % e)
    finally:
      transaction.commit(using=self.database)
      transaction.leave_transaction_management(using=self.database)


  # Importing onhand
  #   - extracting all stock.report.prodlots objects
  #   - No filtering for latest changes, ie always complete extract
  #   - meeting the criterion:
  #        - %qty > 0
  #        - Location already mapped in frePPLe
  #        - Product already mapped in frePPLe
  #   - mapped fields OpenERP -> frePPLe buffer
  #        - %product_id %product_name @ %name -> name
  #        - %product_id %product_name -> item_id
  #        - %location_id %location_name -> location_id
  #        - %qty -> onhand
  #        - 'OpenERP' -> subcategory
  def import_onhand(self, cursor):
    transaction.enter_transaction_management(using=self.database)
    transaction.managed(True, using=self.database)
    try:
      starttime = time()
      if self.verbosity > 0:
        print("Importing onhand...")
      cursor.execute("SELECT name FROM item")
      frepple_items = set([ i[0] for i in cursor.fetchall()])
      cursor.execute("SELECT name FROM location")
      frepple_locations = set([ i[0] for i in cursor.fetchall()])
      cursor.execute("SELECT name FROM buffer")
      frepple_keys = set([ i[0] for i in cursor.fetchall()])
      cursor.execute("update buffer set onhand = 0 where subcategory = 'OpenERP'")
      ids = self.openerp_search('stock.report.prodlots', [('qty','>', 0),])
      fields = ['prodlot_id', 'location_id', 'qty', 'product_id']
      insert = []
      update = []
      for i in self.openerp_data('stock.report.prodlots', ids, fields):
        name = u'%d %s @ %d %s' % (i['product_id'][0], i['product_id'][1], i['location_id'][0], i['location_id'][1])
        item = u'%d %s' % (i['product_id'][0], i['product_id'][1])
        location = u'%d %s' % (i['location_id'][0], i['location_id'][1])
        if item in frepple_items and location in frepple_locations:
          if name in frepple_keys:
            update.append(i)
          else:
            insert.append(i)
      cursor.executemany(
        "insert into buffer \
          (name,item_id,location_id,onhand,subcategory,lastmodified) \
          values(%%s,%%s,%%s,%%s,'OpenERP','%s')" % self.date,
        [(
           u'%d %s @ %d %s' % (i['product_id'][0], i['product_id'][1], i['location_id'][0], i['location_id'][1]),
           u'%d %s' % (i['product_id'][0], i['product_id'][1]),
           u'%d %s' % (i['location_id'][0], i['location_id'][1]),
           i['qty'],
         ) for i in insert
        ])
      cursor.executemany(
        "update buffer \
          set onhand=%%s, subcategory='OpenERP', lastmodified='%s' \
          where name=%%s" % self.date,
        [(
           i['qty'],
           u'%d %s @ %d %s' % (i['product_id'][0], i['product_id'][1], i['location_id'][0], i['location_id'][1]),
         ) for i in update
        ])
      transaction.commit(using=self.database)
      if self.verbosity > 0:
        print("Inserted onhand for %d new buffers" % len(insert))
        print("Updated onhand for %d existing buffers" % len(update))
        print("Imported onhand in %.2f seconds" % (time() - starttime))
    except Exception as e:
      transaction.rollback(using=self.database)
      print("Error importing onhand: %s" % e)
    finally:
      transaction.commit(using=self.database)
      transaction.leave_transaction_management(using=self.database)


  # Load open purchase orders and quotations
  #   - extracting recently changed purchase.order.line objects
  #   - meeting the criterion:
  #        - %product_id already exists in frePPLe
  #        - %location_id already exists in frePPLe
  #        - %state = 'approved' or 'draft'
  #   - mapped fields OpenERP -> frePPLe buffer
  #        - %id %name -> name
  #        - 'OpenERP' -> subcategory
  #   - mapped fields OpenERP -> frePPLe operation
  #        - %id %name -> name
  #        - 'OpenERP' -> subcategory
  #   - mapped fields OpenERP -> frePPLe flow
  #        - %id %name -> name
  #        - 'OpenERP' -> subcategory
  #   - mapped fields OpenERP -> frePPLe operationplan
  #        - %id %name -> name
  #        - 'OpenERP' -> subcategory
  #   - Note that the current logic also treats the (draft) purchase quotations in the
  #     very same way as the (confirmed) purchase orders.
  #
  # TODO Possible to update PO without touching the date on the PO-lines? Rework code?
  # TODO Operationplan id is not the most robust way to find a match
  def import_purchaseorders(self, cursor):

    def newBuffers(insert):
      cursor.execute("SELECT name FROM buffer")
      frepple_buffers = set([ i[0] for i in cursor.fetchall()])
      for i in insert:
        if i[4] not in frepple_buffers:
          frepple_buffers.add(i[4])
          yield (i[4], i[5], i[6],)

    def newOperations(insert):
      cursor.execute("SELECT name FROM operation")
      frepple_operations = set([ i[0] for i in cursor.fetchall()])
      for i in insert:
        if i[0] not in frepple_operations:
          frepple_operations.add(i[0])
          yield (i[0], i[6],)

    def newFlows(insert):
      cursor.execute("SELECT operation_id, thebuffer_id FROM flow")
      frepple_flows = set([ u'%sx%s' % (i[0],i[1]) for i in cursor.fetchall()])
      for i in insert:
        k = u'%sx%s' %(i[0], i[4])
        if k not in frepple_flows:
          frepple_flows.add(k)
          yield (i[0], i[4],)

    transaction.enter_transaction_management(using=self.database)
    transaction.managed(True, using=self.database)
    try:
      starttime = time()
      if self.verbosity > 0:
        print("Importing purchase orders...")
      cursor.execute("SELECT name FROM item")
      frepple_items = set([ i[0] for i in cursor.fetchall()])
      cursor.execute("SELECT name FROM location")
      frepple_locations = set([ i[0] for i in cursor.fetchall()])
      cursor.execute("SELECT id FROM operationplan")
      frepple_keys = set([ i[0] for i in cursor.fetchall()])
      ids = self.openerp_search('purchase.order.line',
        ['|',('create_date','>', self.delta),('write_date','>', self.delta)])
      fields = ['name', 'date_planned', 'product_id', 'product_qty', 'order_id']
      fields2 = ['name', 'location_id', 'partner_id', 'state', 'received']
      insert = []
      delete = []
      update = []
      for i in self.openerp_data('purchase.order.line', ids, fields):
        item = u'%d %s' % (i['product_id'][0], i['product_id'][1])
        j = self.openerp_data('purchase.order', [i['order_id'][0],], fields2)[0]
        location = u'%d %s' % (j['location_id'][0], j['location_id'][1])
        if location in frepple_locations and item in frepple_items and j['state'] in ('approved','draft'):
          if i['id'] in frepple_keys:
            update.append( (
               u'procure for %s @ %s' %(item,location), i['date_planned'], i['date_planned'], i['product_qty'], i['id']
              ) )
          else:
            insert.append( (
               u'procure for %s @ %s' %(item,location), i['date_planned'], i['product_qty'], i['id'],
               u'%s @ %s' %(item,location), item, location
              ) )
        elif id in frepple_keys:
          delete.append( (i['id'],) )
      cursor.executemany(
        "insert into buffer \
          (name,item_id,location_id,subcategory,lastmodified) \
          values(%%s,%%s,%%s,'OpenERP','%s')" % self.date,
        [ i for i in newBuffers(insert) ]
        )
      cursor.executemany(
        "insert into operation \
          (name,location_id,subcategory,lastmodified) \
          values(%%s,%%s,'OpenERP','%s')" % self.date,
        [ i for i in newOperations(insert) ]
        )
      cursor.executemany(
        "insert into flow \
          (operation_id,thebuffer_id,type,quantity,lastmodified) \
          values(%%s,%%s,'flow_end',1,'%s')" % self.date,
        [ i for i in newFlows(insert) ]
        )
      cursor.executemany(
        "insert into operationplan \
          (id,operation_id,startdate,enddate,quantity,locked,lastmodified) \
          values(%%s,%%s,%%s,%%s,%%s,'1','%s')" % self.date,
        [ (i[3], i[0], i[1], i[1], i[2], ) for i in insert ]
        )
      cursor.executemany(
        "update operationplan \
          set operation_id=%%s, enddate=%%s, startdate=%%s, quantity=%%s, locked='1', lastmodified='%s' \
          where id=%%s" % self.date,
        update)
      cursor.executemany(
        "delete from operationplan where id=%s",
        delete)
      transaction.commit(using=self.database)
      if self.verbosity > 0:
        print("Inserted %d purchase orders" % len(insert))
        print("Updated %d purchase orders" % len(update))
        print("Deleted %d purchase orders" % len(delete))
        print("Imported purchase orders in %.2f seconds" % (time() - starttime))
    except Exception as e:
      transaction.rollback(using=self.database)
      print("Error importing purchase orders: %s" % e)
    finally:
      transaction.commit(using=self.database)
      transaction.leave_transaction_management(using=self.database)


  # Importing boms
  #   - extracting recently changed mrp.bom objects
  #   - not supported yet:
  #        - date effectivity
  #        - phantom boms
  #        - subproducts
  #        - routings
  #   - meeting the criterion:
  #        - %active = True
  #        - %bom_id = False (otherwise it's a bom component
  #        - %routing_id is not empty    TODO update doc here
  #          and %routing_id.location_id is not null
  #          and the location already exists in frePPLe
  #   - mapped fields OpenERP -> frePPLe operation
  #        - make %product_id.id %product_id.name @ %routing_id.location_id %routing_id.location_id.name -> name
  #        - %routing_id.location_id %routing_id.location_id.name -> location_id
  #        - %product_rounding -> size_multiple
  #        - 'OpenERP' -> subcategory
  #   - mapped fields OpenERP -> frePPLe buffer
  #        - %product_id.id %product_id.name @ %routing_id.location_id %routing_id.location_id.name -> name
  #        - %product_id.id %product_id.name -> item_id
  #        - %routing_id.location_id %routing_id.location_id.name -> location_id
  #        - %bom_id %bom_name @ %routing_id.location_id %routing_id.location_id.name -> producing_id
  #        - 'OpenERP' -> subcategory
  #   - mapped fields OpenERP -> frePPLe flow
  #        - %product_id.id %product_id.name @ %routing_id.location_id %routing_id.location_id.name -> thebuffer_id
  #        - make %product_id.id %product_id.name @ %routing_id.location_id %routing_id.location_id.name -> operation_id
  #        - %product_qty * %product_efficiency -> quantity
  #        - 'flow_end' -> type
  #
  def import_boms(self, cursor):
    transaction.enter_transaction_management(using=self.database)
    transaction.managed(True, using=self.database)
    try:
      starttime = time()
      if self.verbosity > 0:
        print("Importing bills of material...")

      # Pick up existing flows in frePPLe
      cursor.execute("SELECT thebuffer_id, operation_id FROM flow")
      frepple_flows = set(cursor.fetchall())

      # Pick up existing loads in frePPLe
      cursor.execute("SELECT resource_id, operation_id FROM resourceload")
      frepple_loads = set(cursor.fetchall())

      # Pick up existing buffers in frePPLe
      cursor.execute("SELECT name FROM buffer")
      frepple_buffers = set([i[0] for i in cursor.fetchall()])

      # Pick up existing operations in frePPLe
      cursor.execute("SELECT name FROM operation")
      frepple_operations = set([i[0] for i in cursor.fetchall()])

      # Pick up all existing locations in frePPLe
      cursor.execute("SELECT name FROM location")
      frepple_locations = set([i[0] for i in cursor.fetchall()])

      # Pick up all active manufacturing routings
      openerp_mfg_routings = {}
      ids = self.openerp_search('mrp.routing')
      for i in self.openerp_data('mrp.routing', ids, ['location_id',]):
        if i['location_id']:
          openerp_mfg_routings[i['id']] = u'%s %s' % (i['location_id'][0], i['location_id'][1])
        else:
          openerp_mfg_routings[i['id']] = None

      # Pick up all workcenters in the routing
      routing_workcenters = {}
      ids = self.openerp_search('mrp.routing.workcenter')
      fields = ['routing_id','workcenter_id','sequence','cycle_nbr','hour_nbr',]
      for i in self.openerp_data('mrp.routing.workcenter', ids, fields):
        if i['routing_id'][0] in routing_workcenters:
          routing_workcenters[i['routing_id'][0]].append( (u'%s %s' % (i['workcenter_id'][0], i['workcenter_id'][1]), i['cycle_nbr'],) )
        else:
          routing_workcenters[i['routing_id'][0]] = [ (u'%s %s' % (i['workcenter_id'][0], i['workcenter_id'][1]), i['cycle_nbr'],), ]

      # Create operations
      operation_insert = []
      operation_update = []
      operation_delete = []
      buffer_insert = []
      buffer_update = []
      flow_insert = []
      flow_update = []
      flow_delete = []
      load_insert = []
      load_update = []
      default_location = None

      # Loop over all "producing" bom records
      boms = {}
      ids = self.openerp_search('mrp.bom', [
        ('bom_id','=',False), #'|',('create_date','>', self.delta),('write_date','>', self.delta),
        '|',('active', '=', 1),('active', '=', 0)])
      fields = ['name', 'active', 'product_qty','date_start','date_stop','product_efficiency',
        'product_id','routing_id','bom_id','type','sub_products','product_rounding',]
      for i in self.openerp_data('mrp.bom', ids, fields):
        # Determine the location
        if i['routing_id']:
          location = openerp_mfg_routings[i['routing_id'][0]]
        else:
          location = None
        if not location:
          if not default_location:
            default_location = warehouses.itervalues().next()
            if len(warehouses) > 1:
              print("Warning: Only single warehouse configurations are supported. Creating only boms for '%s'" % default_location)
          location = default_location

        # Determine operation name and item
        operation = u'%d %s @ %s' % (i['id'], i['name'], location)
        product = u'%d %s' % (i['product_id'][0], i['product_id'][1])
        boms[i['id']] = (operation, location)
        buffer = u'%d %s @ %s' % (i['product_id'][0], i['product_id'][1], location)  # TODO if policy is produce, then this should be the producting operation

        if i['active']:
          # Creation or update operations
          if operation in frepple_operations:
            operation_update.append( (
              location, i['product_rounding'] or 1, operation,
              ) )
          else:
            frepple_operations.add(operation)
            operation_insert.append( (
              operation, location, i['product_rounding'] or 1
              ) )
          # Creation buffer
          if not buffer in frepple_buffers:
            frepple_buffers.add(buffer)
            buffer_insert.append( (
              buffer, product, location, operation
              ))
          else:
            buffer_update.append( (
              product, location, operation, buffer
              ))
          # Producing flow on a bom
          if (buffer,operation) in frepple_flows:
            flow_update.append( (
              i['product_qty']*i['product_efficiency'], 'end', i['date_start'] or None, i['date_stop'] or None, operation, buffer,
              ) )
          else:
            flow_insert.append( (
              operation, buffer, i['product_qty']*i['product_efficiency'], 'end', i['date_start'] or None, i['date_stop'] or None
              ) )
          # Create workcentre loads
          if i['routing_id']:
            for j in routing_workcenters[i['routing_id'][0]]:
              if (j[0],operation) in frepple_loads:
                load_update.append((
                  j[1], operation, j[0]
                  ))
              else:
                load_insert.append((
                  operation, j[0], j[1]
                  ))
        else:
          # Not active any more
          if operation in frepple_operations:
            operation_delete.append( (operation,) )
          if (buffer,operation) in frepple_flows:   # TODO filter only based on operation???
            flow_delete.append( (buffer,operation) )

      # Loop over all "consuming" bom records
      ids = self.openerp_search('mrp.bom', [
        ('bom_id','!=',False), #'|',('create_date','>', self.delta),('write_date','>', self.delta),
        '|',('active', '=', 1),('active', '=', 0)])
      fields = ['name', 'active', 'product_qty','date_start','date_stop','product_efficiency',
        'product_id','routing_id','bom_id','type','sub_products','product_rounding',]
      for i in self.openerp_data('mrp.bom', ids, fields):
        # Determine operation and buffer
        (operation, location) = boms[i['bom_id'][0]]
        product = u'%d %s' % (i['product_id'][0], i['product_id'][1])
        buffer = u'%d %s @ %s' % (i['product_id'][0], i['product_id'][1], location)

        if i['active']:
          # Creation buffer
          if not buffer in frepple_buffers:
            frepple_buffers.add(buffer)
            buffer_insert.append( (
              buffer, product, location, None
              ))
          # Creation of flow
          if (buffer,operation) in frepple_flows:
            flow_update.append( (
              -i['product_qty']*i['product_efficiency'], 'start', i['date_start'] or None, i['date_stop'] or None, operation, buffer,
              ) )
          else:
            flow_insert.append( (
              operation, buffer, -i['product_qty']*i['product_efficiency'], 'start', i['date_start'] or None, i['date_stop'] or None
              ) )
        else:
          # Not active any more
          if (buffer,operation) in frepple_flows:
            flow_delete.append( (buffer,operation) )

      # Process in the frePPLe database
      cursor.executemany(
        "insert into operation \
          (name,location_id,subcategory,sizemultiple,lastmodified) \
          values(%%s,%%s,'OpenERP',%%s,'%s')" % self.date,
        operation_insert
        )
      cursor.executemany(
        "update operation \
          set location_id=%%s, sizemultiple=%%s, subcategory='OpenERP', lastmodified='%s' \
          where name=%%s" % self.date,
        operation_update
        )
      cursor.executemany(
        "update operation \
          set subcategory=null, lastmodified='%s' \
          where name=%%s" % self.date,
        operation_delete
        )
      cursor.executemany(
        "insert into buffer \
          (name,item_id,location_id,producing_id,subcategory,lastmodified) \
          values(%%s,%%s,%%s,%%s,'OpenERP','%s')" % self.date,
        buffer_insert
        )
      cursor.executemany(
        "update buffer \
          set item_id=%%s, location_id=%%s, producing_id=%%s, subcategory='OpenERP', lastmodified='%s' \
          where name = %%s" % self.date,
        buffer_update
        )
      cursor.executemany(
        "insert into flow \
          (operation_id,thebuffer_id,quantity,type,effective_start,effective_end,lastmodified) \
          values(%%s,%%s,%%s,%%s,%%s,%%s,'%s')" % self.date,
        flow_insert
        )
      cursor.executemany(
        "update flow \
          set quantity=%%s, type=%%s, effective_start=%%s ,effective_end=%%s, lastmodified='%s' \
          where operation_id=%%s and thebuffer_id=%%s" % self.date,
        flow_update
        )
      cursor.executemany(
        "insert into resourceload \
          (operation_id,resource_id,quantity,lastmodified) \
          values(%%s,%%s,%%s,'%s')" % self.date,
        load_insert
        )
      cursor.executemany(
        "update resourceload \
          set quantity=%%s, lastmodified='%s' \
          where operation_id=%%s and resource_id=%%s" % self.date,
        load_update
        )
      cursor.executemany(
        "delete flow \
          where operation_id=%%s and thebuffer_id=%%s",
        flow_delete
        )

      # TODO multiple boms for the same item -> alternate operation

      transaction.commit(using=self.database)
      if self.verbosity > 0:
        print("Inserted %d new bills of material operations" % len(operation_insert))
        print("Updated %d existing bills of material operations" % len(operation_update))
        print("Deleted %d bills of material operations" % len(operation_delete))
        print("Inserted %d new bills of material buffers" % len(buffer_insert))
        print("Inserted %d new bills of material flows" % len(flow_insert))
        print("Updated %d existing bills of material flows" % len(flow_update))
        print("Inserted %d new bills of material loads" % len(load_insert))
        print("Updated %d existing bills of material loads" % len(load_update))
        print("Deleted %d bills of material flows" % len(flow_delete))
        print("Imported bills of material in %.2f seconds" % (time() - starttime))
    except Exception as e:
      transaction.rollback(using=self.database)
      import sys, traceback
      traceback.print_exc(file=sys.stdout)
      print("Error importing bills of material: %s" % e)
    finally:
      transaction.commit(using=self.database)
      transaction.leave_transaction_management(using=self.database)


  # Importing setup matrices and setup rules
  #   - extracting ALL frepple.setupmatrix and frepple.setuprule objects.
  #     This mapping assumes ALL matrices are maintained in OpenERP only.
  #   - meeting the criterion:
  #        - %active = True
  #   - mapped fields OpenERP -> frePPLe setupmatrix
  #        - %id %name -> name
  #   - adapter is NOT implemented in delta mode!
  def import_setupmatrices(self, cursor):
    transaction.enter_transaction_management(using=self.database)
    transaction.managed(True, using=self.database)
    try:
      starttime = time()
      if self.verbosity > 0:
        print("Importing setup matrices...")
      cursor.execute("delete FROM setuprule")
      cursor.execute("delete FROM setupmatrix")

      # Get all setup matrices
      ids = self.openerp_search('frepple.setupmatrix', ['|',('active', '=', 1),('active', '=', 0)])
      fields = ['name',]
      datalist = []
      for i in self.openerp_data('frepple.setupmatrix', ids, fields):
        datalist.append((u'%d %s' % (i['id'],i['name']),))
      cursor.executemany(
        "insert into setupmatrix \
          (name,lastmodified) \
          values (%%s,'%s')" % self.date,
        datalist
        )
      if self.verbosity > 0:
        print("Inserted %d new setup matrices" % len(datalist))

      # Get all setup rules
      ids = self.openerp_search('frepple.setuprule')
      fields = ['priority', 'fromsetup', 'tosetup', 'duration', 'cost', 'active', 'setupmatrix_id' ]
      cnt = 0
      datalist = []
      for i in self.openerp_data('frepple.setuprule', ids, fields):
        datalist.append( (cnt, i['priority'], u'%d %s' % (i['setupmatrix_id'][0],i['setupmatrix_id'][1]), i['fromsetup'], i['tosetup'], i['duration']*3600, i['cost']) )
        cnt += 1
      cursor.executemany(
        "insert into setuprule \
          (id, priority, setupmatrix_id, fromsetup, tosetup, duration, cost, lastmodified) \
          values (%%s,%%s,%%s,%%s,%%s,%%s,%%s,'%s')" % self.date,
        datalist
        )
      if self.verbosity > 0:
        print("Inserted %d new setup rules" % len(datalist))

      transaction.commit(using=self.database)
    except Exception as e:
      try:
        if e.faultString.find("Object frepple.setupmatrix doesn't exist") >= 0:
          print("Warning importing setup matrices:")
          print("  The frePPLe module is not installed on your OpenERP server.")
          print("  No setup matrices will be downloaded.")
        else:
          print("Error importing setup matrices: %s" % e)
      except:
        print("Error importing setup matrices: %s" % e)
      transaction.rollback(using=self.database)
    finally:
      transaction.commit(using=self.database)
      transaction.leave_transaction_management(using=self.database)


  # Importing policies
  #   - extracting recently changed res.partner objects
  #   - meeting the criterion:
  #        - %active = True
  #        - %customer = True
  #   - mapped fields OpenERP -> frePPLe customer
  #        - %id %name -> name
  #        - %ref     -> description
  #        - 'OpenERP' -> subcategory
  def import_policies(self, cursor):
    transaction.enter_transaction_management(using=self.database)
    transaction.managed(True, using=self.database)
    try:
      starttime = time()
      if self.verbosity > 0:
        print("Importing policies...")

      # Get the list of item ids and the template info
      cursor.execute("SELECT name FROM item where subcategory='OpenERP'")
      ids = [ int(i[0].partition(' ')[0]) for i in cursor.fetchall()]
      templates = {}
      fields = ['product_tmpl_id','name']
      fields2 = ['purchase_ok','procure_method','supply_method','produce_delay']
      buy = []
      produce = []
      for i in self.openerp_data('product.product', ids, fields):
        item = u'%d %s' % (i['id'],i['name'])
        if not i['product_tmpl_id'][0] in templates:
          templates[i['product_tmpl_id'][0]] = self.openerp_data('product.template', [i['id']], fields2)[0]
        tmpl = templates[i['product_tmpl_id'][0]]
        if tmpl['purchase_ok'] and tmpl['supply_method'] == 'buy':
          buy.append( (item,))
        else:
          produce.append((item,))

      # Update the frePPLe buffers
      cursor.execute("update buffer set type=null where subcategory = 'OpenERP'")
      cursor.executemany(
        "update buffer \
          set type= 'procure', lastmodified='%s' \
          where item_id = %%s and subcategory = 'OpenERP'" % self.date,
        buy)
      cursor.executemany(
        "update buffer \
          set lastmodified='%s' \
          where item_id = %%s and subcategory = 'OpenERP'" % self.date,
        produce)

      transaction.commit(using=self.database)
      if self.verbosity > 0:
        print("Updated buffers for %d procured items" % len(buy))
        print("Updated buffers for %d produced items" % len(produce))
    except Exception as e:
      transaction.rollback(using=self.database)
      print("Error importing policies: %s" % e)
    finally:
      transaction.commit(using=self.database)
      transaction.leave_transaction_management(using=self.database)


# TODO:
#  - renaming an entity in OpenERP is not handled right: id remains the same in OpenERP, but the object name in frePPLe is different.
#  - Load reorder points
#  - Load loads
#  - Load WIP
#  - Unit of measures are not used

