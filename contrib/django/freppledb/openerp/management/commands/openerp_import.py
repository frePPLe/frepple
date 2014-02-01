#
# Copyright (C) 2010-2014 by Johan De Taeye, frePPLe bvba
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

# TODO  SALES ORDER DATES modules computes the commitment date in a pretty naive way
#     and may not be appropriate for frePPLe integration. TODO...


from __future__ import print_function
from optparse import make_option
import xmlrpclib
from datetime import datetime, timedelta
from time import time

from django.core.management.base import BaseCommand, CommandError
from django.db import transaction, connections, DEFAULT_DB_ALIAS
from django.conf import settings

from freppledb.common.models import Parameter
from freppledb.execute.models import Task


class Command(BaseCommand):

  help = "Loads data from an OpenERP instance into the frePPLe database"

  option_list = BaseCommand.option_list + (
      make_option('--user', dest='user', type='string',
        help='User running the command'),
      make_option('--delta', action='store', dest='delta', type="float",
        default='3650', help='Number of days for which we extract changed OpenERP data'),
      make_option('--database', action='store', dest='database',
        default=DEFAULT_DB_ALIAS, help='Nominates the frePPLe database to load'),
      make_option('--task', dest='task', type='int',
        help='Task identifier (generated automatically if not provided)'),
  )

  requires_model_validation = False

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
    if 'delta' in options: self.delta = float(options['delta'] or '3650')
    else: self.delta = 3650
    self.date = datetime.now()

    # Pick up configuration parameters
    self.openerp_user = Parameter.getValue("openerp.user", self.database)
    self.openerp_password = Parameter.getValue("openerp.password", self.database)
    self.openerp_db = Parameter.getValue("openerp.db", self.database)
    self.openerp_url = Parameter.getValue("openerp.url", self.database)

    # Make sure the debug flag is not set!
    # When it is set, the django database wrapper collects a list of all sql
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
        if task.started or task.finished or task.status != "Waiting" or task.name != 'OpenERP import':
          raise CommandError("Invalid task identifier")
        task.status = '0%'
        task.started = now
      else:
        task = Task(name='OpenERP import', submitted=now, started=now, status='0%', user=user,
          arguments="--delta=%s" % self.delta)
      task.save(using=self.database)
      transaction.commit(using=self.database)

      # Initialize some global variables
      self.customers = {}
      self.items = {}
      self.locations = {} # A mapping between OpenERP stock.location ids and the name of the location in frePPLe
      self.warehouses = {}
      self.resources = {}
      self.shops = {}
      self.delta = str(self.date - timedelta(days=self.delta))

      # Log in to the OpenERP server
      sock_common = xmlrpclib.ServerProxy(self.openerp_url + 'xmlrpc/common')
      self.uid = sock_common.login(self.openerp_db, self.openerp_user, self.openerp_password)

      # Connect to OpenERP server
      self.sock = xmlrpclib.ServerProxy(self.openerp_url + 'xmlrpc/object')

      # Create a database connection to the frePPLe database
      cursor = connections[self.database].cursor()

      # Sequentially load all data
      self.import_customers(cursor)
      task.status = '10%'
      task.save(using=self.database)
      transaction.commit(using=self.database)
      self.import_products(cursor)
      task.status = '20%'
      task.save(using=self.database)
      transaction.commit(using=self.database)
      self.import_locations(cursor)
      task.status = '30%'
      task.save(using=self.database)
      transaction.commit(using=self.database)
      self.import_salesorders(cursor)
      task.status = '40%'
      task.save(using=self.database)
      transaction.commit(using=self.database)
      self.import_workcenters(cursor)
      task.status = '50%'
      task.save(using=self.database)
      transaction.commit(using=self.database)
      self.import_onhand(cursor)
      task.status = '60%'
      task.save(using=self.database)
      transaction.commit(using=self.database)
      self.import_purchaseorders(cursor)
      task.status = '70%'
      task.save(using=self.database)
#      self.import_boms(cursor)
      transaction.commit(using=self.database)
      task.status = '80%'
      task.save(using=self.database)
      self.import_policies(cursor)
      transaction.commit(using=self.database)
      task.status = '90%'
      task.save(using=self.database)
      transaction.commit(using=self.database)

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


  def openerp_search(self, a, b=[]):
    try:
      return self.sock.execute(self.openerp_db, self.uid, self.openerp_password, a, 'search', b)
    except xmlrpclib.Fault as e:
      raise CommandError(e.faultString)


  def openerp_data(self, a, b, c):
    try:
      return self.sock.execute(self.openerp_db, self.uid, self.openerp_password, a, 'read', b, c)
    except xmlrpclib.Fault as e:
      raise CommandError(e.faultString)


  # Importing customers
  #   - extracting recently changed res.partner objects
  #   - meeting the criterion:
  #        - %active = True
  #        - %customer = True
  #   - mapped fields OpenERP -> frePPLe customer
  #        - %id %name -> name
  #        - %ref     -> description
  #        - %id -> source
  #        - 'OpenERP' -> subcategory
  def import_customers(self, cursor):
    transaction.enter_transaction_management(using=self.database)
    try:
      starttime = time()
      if self.verbosity > 0:
        print("Importing customers...")
      cursor.execute("SELECT name, subcategory, source FROM customer")
      frepple_keys = set()
      for i in cursor.fetchall():
        if i[1] == 'OpenERP': self.customers[i[2]] = i[0]
        frepple_keys.add(i[0])
      ids = self.openerp_search( 'res.partner',
        ['|',('create_date','>', self.delta),('write_date','>', self.delta),
         '|',('active', '=', 1),('active', '=', 0)])
      fields = ['name', 'active', 'customer', 'ref']
      insert = []
      update = []
      rename = []
      delete = []
      for i in self.openerp_data('res.partner', ids, fields):
        name = u'%d %s' % (i['id'],i['name'])
        if i['active'] and i['customer']:
          if name in frepple_keys:
            update.append( (i['id'],name) )
          elif i['id'] in self.customers:
            # Object previously exported from OpenERP already, now renamed
            rename.append( (name,i['id']) )
          else:
            insert.append( (i['id'],name) )
          self.customers[i['id']] = name
        elif name in frepple_keys:
          delete.append( (name,) )
      cursor.executemany(
        "insert into customer \
          (source,name,subcategory,lastmodified) \
          values (%%s,%%s,'OpenERP','%s')" % self.date,
        insert)
      cursor.executemany(
        "update customer \
          set source=%%s, subcategory='OpenERP',lastmodified='%s' \
          where name=%%s" % self.date,
        update)
      cursor.executemany(
        "update customer \
          set name=%%s, lastmodified='%s' \
          where source=%%s and subcategory='OpenERP'" % self.date,
        rename
        )
      for i in delete:
        try: cursor.execute("delete from customer where source=%s",i)
        except:
          # Delete fails when there are dependent records in the database.
          cursor.execute("update customer set source=null, subcategory=null, lastmodified='%s' where name=%%s" % self.date,i)
      transaction.commit(using=self.database)
      if self.verbosity > 0:
        print("Inserted %d new customers" % len(insert))
        print("Updated %d existing customers" % len(update))
        print("Renamed %d existing customers" % len(rename))
        print("Deleted %d customers" % len(delete))
        print("Imported customers in %.2f seconds" % (time() - starttime))
    except Exception as e:
      transaction.rollback(using=self.database)
      raise CommandError("Error importing customers: %s" % e)
    finally:
      transaction.commit(using=self.database)
      transaction.leave_transaction_management(using=self.database)


  # Importing products
  #   - extracting recently changed product.product objects
  #   - meeting the criterion:
  #        - %active = True
  #   - mapped fields OpenERP -> frePPLe item
  #        - %code %name -> name
  #        - 'OpenERP' -> subcategory
  #        - %id -> source
  #   - We assume the code+name combination is unique, but this is not
  #     enforced at all in OpenERP. The only other option is to include
  #     the id in the name - not nice for humans...
  # TODO also get template.produce_delay, property_stock_production, property_stock_inventory, and property_stock_procurement?
  def import_products(self, cursor):
    transaction.enter_transaction_management(using=self.database)
    try:
      starttime = time()
      if self.verbosity > 0:
        print("Importing products...")
      cursor.execute("SELECT name, subcategory, source FROM item")
      frepple_keys = set()
      for i in cursor.fetchall():
        if i[1] == 'OpenERP': self.items[i[2]] = i[0]
        frepple_keys.add(i[0])
      ids = self.openerp_search('product.product', [
        '|',('create_date','>', self.delta),('write_date','>', self.delta),
        '|',('active', '=', 1),('active', '=', 0)
        ])
      fields = ['name', 'code', 'active', 'product_tmpl_id']
      insert = []
      update = []
      rename = []
      delete = []
      for i in self.openerp_data('product.product', ids, fields):
        if i['code']:
          name = u'[%s] %s' % (i['code'], i['name'])
        else:
          name = i['name']
        if i['active']:
          if name in frepple_keys:
            update.append( (i['id'],name) )
          elif i['id'] in self.items:
            # Object previously exported from OpenERP already, now renamed
            rename.append( (name,i['id']) )
          else:
            insert.append( (name,i['id']) )
          self.items[i['id']] = name
        elif name in frepple_keys:
          delete.append( (name,) )
      cursor.executemany(
        "insert into item \
          (name,source,subcategory,lastmodified) \
          values (%%s,%%s,'OpenERP','%s')" % self.date,
        insert
        )
      cursor.executemany(
        "update item \
          set source=%%s, subcategory='OpenERP', lastmodified='%s' \
          where name=%%s" % self.date,
        update
        )
      cursor.executemany(
        "update item \
          set name=%%s, lastmodified='%s' \
          where source=%%s and subcategory='OpenERP'" % self.date,
        rename
        )
      for i in delete:
        try: cursor.execute("delete from item where name=%s", i)
        except:
          # Delete fails when there are dependent records in the database.
          cursor.execute("update item set source=null, subcategory=null, lastmodified='%s' where name=%%s" % self.date, i)
      transaction.commit(using=self.database)
      if self.verbosity > 0:
        print("Inserted %d new products" % len(insert))
        print("Updated %d existing products" % len(update))
        print("Renamed %d existing products" % len(rename))
        print("Deleted %d products" % len(delete))
        print("Imported products in %.2f seconds" % (time() - starttime))
    except Exception as e:
      transaction.rollback(using=self.database)
      raise CommandError("Error importing products: %s" % e)
    finally:
      transaction.commit(using=self.database)
      transaction.leave_transaction_management(using=self.database)


  # Importing locations
  #   - extracting stock.warehouses objects
  #   - NO filter on recently changed records
  #   - meeting the criterion:
  #        - %active = True
  #   - mapped fields OpenERP -> frePPLe location
  #        - %name -> name
  #        - 'OpenERP' -> subcategory
  #        - %id -> source
  def import_locations(self, cursor):
    transaction.enter_transaction_management(using=self.database)
    try:
      starttime = time()
      if self.verbosity > 0:
        print("Importing warehouses...")
      cursor.execute("SELECT name, subcategory, source FROM location")
      frepple_keys = set()
      for i in cursor.fetchall():
        if i[1] == 'OpenERP': self.locations[i[2]] = i[0]
        frepple_keys.add(i[0])
      ids = self.openerp_search('stock.warehouse')
      fields = ['name', 'lot_stock_id', 'lot_input_id', 'lot_output_id']
      insert = []
      update = []
      rename = []
      for i in self.openerp_data('stock.warehouse', ids, fields):
        if i['name'] in frepple_keys:
          update.append( (i['id'],i['name']) )
        elif i['id'] in self.locations:
          # Object previously exported from OpenERP already, now renamed
          rename.append( (i['name'],i['id']) )
        else:
          insert.append( (i['name'],i['id']) )
        # Find all child locations of the warehouse.
        # We populate a mapping location-to-warehouse name for later lookups.
        ids2 = [ i['lot_stock_id'][0], i['lot_input_id'][0], i['lot_output_id'][0] ]
        fields2 = ['child_ids']
        for j in self.openerp_data('stock.location', ids2, fields2):
          self.locations[j['id']] = i['name']
          for k in j['child_ids']:
            self.locations[k] = i['name']
      cursor.executemany(
        "insert into location \
          (name,source,subcategory,lastmodified) \
          values (%%s,%%s,'OpenERP','%s')" % self.date,
        insert)
      cursor.executemany(
        "update location \
          set source=%%s, subcategory='OpenERP', lastmodified='%s' \
          where name=%%s" % self.date,
        update)
      cursor.executemany(
        "update location \
          set name= %%s, subcategory='OpenERP', lastmodified='%s' \
          where source=%%s" % self.date,
        rename)
      transaction.commit(using=self.database)
      if self.verbosity > 0:
        print("Inserted %d new warehouses" % len(insert))
        print("Updated %d existing warehouses" % len(update))
        print("Renamed %d existing warehouses" % len(rename))
        print("Imported warehouses in %.2f seconds" % (time() - starttime))
    except Exception as e:
      transaction.rollback(using=self.database)
      raise CommandError("Error importing warehouses: %s" % e)
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
  #        - 'OpenERP' -> source
  #        - 1 -> priority
  #   - The picking policy 'complete' is supported at the sales order line
  #     level only in frePPLe. FrePPLe doesn't allow yet to coordinate the
  #     delivery of multiple lines in a sales order (except with hacky
  #     modeling construct).
  #   - The field requested_date is only available when sale_order_dates is
  #     installed.
  def import_salesorders(self, cursor):
    transaction.enter_transaction_management(using=self.database)
    try:
      starttime = time()

      # Get the stocking location of each warehouse (where we deliver from)
      if self.verbosity > 0:
        print("Extracting shop list...")
      ids = self.openerp_search('sale.shop')
      fields = ['name', 'warehouse_id']
      for i in self.openerp_data('sale.shop', ids, fields):
        self.shops[i['id']] = i['warehouse_id'][1]

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
        name = u'%s %d - %d' % (i['order_id'][1], i['sequence'], i['id'])
        source = i['id']
        if i['state'] == 'confirmed':
          product = i['product_id'][1]
          j = self.openerp_data('sale.order', [i['order_id'][0],], fields2)[0]
          location = self.shops[j['shop_id'][0]]
          operation = u'Ship %s @ %s' % (product, location)
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
              source,
              name,
              ) )
          else:
            insert.append( (
              product,
              u'%d %s' % (j['partner_id'][0], j['partner_id'][1]),
              i['product_uom_qty'],
              j['picking_policy'] == 'one' and i['product_uom_qty'] or 1.0,
              j['requested_date'] or j['date_order'],
              operation,
              source,
              name,
              ) )
        elif name in frepple_keys:
          delete.append( (name,) )

      # Create or update delivery operations
      cursor.execute("SELECT name FROM operation where name like 'Ship %'")
      frepple_keys = set([ i[0] for i in cursor.fetchall()])
      cursor.executemany(
        "insert into operation \
          (name,location_id,subcategory,lastmodified) \
          values (%%s,%%s,'OpenERP','%s')" % self.date,
        [ (i[2],i[1]) for i in deliveries if i[2] not in frepple_keys ])
      cursor.executemany(
        "update operation \
          set location_id=%%s, subcategory='OpenERP', lastmodified='%s' where name=%%s" % self.date,
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
          (operation_id,thebuffer_id,quantity,type,source,lastmodified) \
          values(%%s,%%s,-1,'start','OpenERP','%s')" % self.date,
        [ (i[2],i[3]) for i in deliveries if (i[2],i[3]) not in frepple_keys ])
      cursor.executemany(
        "update flow \
          set quantity=-1, type='start', source='OpenERP', lastmodified='%s' where operation_id=%%s and thebuffer_id=%%s" % self.date,
        [ (i[2],i[3]) for i in deliveries if (i[2],i[3]) in frepple_keys ])

      # Create or update demands
      cursor.executemany(
        "insert into demand \
          (item_id,customer_id,quantity,minshipment,due,operation_id,priority,subcategory,lastmodified,source,name) \
          values (%%s,%%s,%%s,%%s,%%s,%%s,1,'OpenERP','%s',%%s,%%s)" % self.date,
        insert)
      cursor.executemany(
        "update demand \
          set item_id=%%s, customer_id=%%s, quantity=%%s, minshipment=%%s, due=%%s, operation_id=%%s, source=%%s, priority=1, subcategory='OpenERP', lastmodified='%s' \
          where name=%%s" % self.date,
        update)
      for i in delete:
        try: cursor.execute("delete from demand where name=%s",i)
        except:
          # Delete fails when there are dependent records in the database.
          cursor.execute("update demand set quantity=0, source=null, lastmodified='%s' where name=%%s" % self.date,i)

      if self.verbosity > 0:
        print("Created or updated %d delivery operations" % len(deliveries))
        print("Inserted %d new sales orders" % len(insert))
        print("Updated %d existing sales orders" % len(update))
        print("Deleted %d sales orders" % len(delete))
        print("Imported sales orders in %.2f seconds" % (time() - starttime))
    except Exception as e:
      transaction.rollback(using=self.database)
      raise CommandError("Error importing sales orders: %s" % e)
    finally:
      transaction.commit(using=self.database)
      transaction.leave_transaction_management(using=self.database)


  # Importing work centers
  #   - extracting recently changed mrp.workcenter objects
  #   - meeting the criterion:
  #        - %active = True
  #   - mapped fields OpenERP -> frePPLe resource
  #        - %id %name -> name
  #        - %cost_hour -> cost
  #        - capacity_per_cycle -> maximum
  #        - 'OpenERP' -> source
  #   - In OpenERP a work center links to a resource, and a resource has
  #     a calendar with working hours.
  #     We don't map the calendar to frePPLe, assuming that this is easy
  #     to maintain in frePPLe.
  def import_workcenters(self, cursor):
    transaction.enter_transaction_management(using=self.database)
    try:
      starttime = time()
      if self.verbosity > 0:
        print("Importing workcenters...")
      cursor.execute("SELECT name, subcategory, source FROM resource")
      frepple_keys = set()
      for i in cursor.fetchall():
        if i[1] == 'OpenERP': self.resources[i[2]] = i[0]
        frepple_keys.add(i[0])
      ids = self.openerp_search('mrp.workcenter',
        ['|',('create_date','>', self.delta),('write_date','>', self.delta),
         '|',('active', '=', 1),('active', '=', 0)])
      fields = ['name', 'active', 'costs_hour', 'capacity_per_cycle', 'time_cycle']
      insert = []
      update = []
      rename = []
      delete = []
      for i in self.openerp_data('mrp.workcenter', ids, fields):
        if i['active']:
          if i['name'] in frepple_keys:
            update.append( (i['id'],i['costs_hour'],i['capacity_per_cycle'] / (i['time_cycle'] or 1),i['name']) )
          elif i['id'] in self.resources:
            # Object previously exported from OpenERP already, now renamed
            rename.append( (i['name'],i['costs_hour'],i['capacity_per_cycle'] / (i['time_cycle'] or 1),i['id']) )
          else:
            insert.append( (i['id'],i['name'],i['costs_hour'],i['capacity_per_cycle'] / (i['time_cycle'] or 1)) )
          self.resources[i['id']] = i['name']
        elif i['name'] in frepple_keys:
          delete.append( (i['name'],) ),
      cursor.executemany(
        "insert into resource \
          (source,name,cost,maximum,subcategory,lastmodified) \
          values (%%s,%%s,%%s,%%s,'OpenERP','%s')" % self.date,
        insert)
      cursor.executemany(
        "update resource \
          set source=%%s, cost=%%s, maximum=%%s, subcategory='OpenERP', lastmodified='%s' \
          where name=%%s" % self.date,
        update)
      cursor.executemany(
        "update resource \
          set name=%%s, cost=%%s, maximum=%%s, subcategory='OpenERP', lastmodified='%s' \
          where source=%%s" % self.date,
        rename)
      for i in delete:
        try: cursor.execute("delete from resource where name=%s",i)
        except:
          # Delete fails when there are dependent records in the database.
          cursor.execute("update resource set source=null, subcategory=null, lastmodified='%s' where name=%%s" % self.date,i)
      transaction.commit(using=self.database)
      if self.verbosity > 0:
        print("Inserted %d new workcenters" % len(insert))
        print("Updated %d existing workcenters" % len(update))
        print("Renamed %d existing workcenters" % len(rename))
        print("Deleted %d workcenters" % len(delete))
        print("Imported workcenters in %.2f seconds" % (time() - starttime))
    except Exception as e:
      transaction.rollback(using=self.database)
      raise CommandError("Error importing workcenters: %s" % e)
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
  #        - 'OpenERP' -> source
  def import_onhand(self, cursor):
    transaction.enter_transaction_management(using=self.database)
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
        location = i['location_id'][0]
        if not location in self.locations: continue
        location = self.locations[location]  # Look up the warehouse of the location
        item = i['product_id'][1]
        name = u'%s @ %s' % (item, location)
        if item in frepple_items and location in frepple_locations:
          if name in frepple_keys:
            update.append( (i['qty'], name) )
          else:
            insert.append( (name, item, location, i['qty']) )
            frepple_keys.add(name)
      cursor.executemany(
        "insert into buffer \
          (name,item_id,location_id,onhand,subcategory,lastmodified) \
          values(%%s,%%s,%%s,%%s,'OpenERP','%s')" % self.date,
        insert
        )
      cursor.executemany(
        "update buffer \
          set onhand=onhand+%%s, subcategory='OpenERP', lastmodified='%s' \
          where name=%%s" % self.date,
        update
        )
      transaction.commit(using=self.database)
      if self.verbosity > 0:
        print("Inserted onhand for %d new buffers" % len(insert))
        print("Updated onhand for %d existing buffers" % len(update))
        print("Imported onhand in %.2f seconds" % (time() - starttime))
    except Exception as e:
      transaction.rollback(using=self.database)
      raise CommandError("Error importing onhand: %s" % e)
    finally:
      transaction.commit(using=self.database)
      transaction.leave_transaction_management(using=self.database)


  # Load open purchase orders and quotations
  #   - extracting all records every time. No net change capability.
  #   - meeting the criterion:
  #        - %product already exists in frePPLe
  #        - %location already exists in frePPLe
  #        - %state = 'approved' or 'draft'
  #   - mapped fields OpenERP -> frePPLe buffer
  #        - %product ' @ ' %name -> name
  #        - %location, mapped to warehouse -> location
  #        - %product -> product
  #        - 'OpenERP' -> subcategory
  #   - mapped fields OpenERP -> frePPLe operation
  #        - 'Purchase ' %product ' @ ' %location -> name
  #        - 'OpenERP' -> subcategory
  #        - 'fixed_time' -> type
  #   - mapped fields OpenERP -> frePPLe flow
  #        - 'Purchase ' %product ' @ ' %location -> operation
  #        - %product ' @ ' %name -> buffer
  #        - 1 -> quantity
  #        - 'end' -> type
  #        - 'OpenERP' -> source
  #   - mapped fields OpenERP -> frePPLe operationplan
  #        - %id %name -> name
  #        - 'OpenERP' -> source
  #   - Note that the current logic also treats the (draft) purchase quotations in the
  #     very same way as the (confirmed) purchase orders.
  #
  # TODO Possible to update PO without touching the date on the PO-lines? Rework code?
  # TODO Operationplan id is not the most robust way to find a match
  def import_purchaseorders(self, cursor):
    transaction.enter_transaction_management(using=self.database)
    try:
      starttime = time()
      if self.verbosity > 0:
        print("Importing purchase orders...")
      cursor.execute("SELECT name FROM item")
      frepple_items = set([ i[0] for i in cursor.fetchall()])
      cursor.execute("SELECT id FROM operationplan")
      frepple_keys = set([ i[0] for i in cursor.fetchall()])
      deliveries = set()
      ids = self.openerp_search('purchase.order.line')
      fields = ['name', 'date_planned', 'product_id', 'product_qty', 'order_id']
      fields2 = ['name', 'location_id', 'partner_id', 'state', 'received']
      insert = []
      delete = []
      update = []
      for i in self.openerp_data('purchase.order.line', ids, fields):
        item = i['product_id'][1]
        j = self.openerp_data('purchase.order', [i['order_id'][0],], fields2)[0]
        if j['location_id'][0] in self.locations and item in frepple_items and j['state'] in ('approved','draft'):
          location = self.locations[j['location_id'][0]]
          operation = u'Purchase %s @ %s' %(item,location)
          if i['id'] in frepple_keys:
            update.append( (
               operation, i['date_planned'], i['date_planned'], i['product_qty'], i['id']
              ) )
          else:
            insert.append( (
               operation, i['date_planned'], i['product_qty'], i['id'],
               operation, item, location
              ) )
          deliveries.update([(item,location,operation,u'%s @ %s' % (item, location)),])
        elif id in frepple_keys:
          delete.append( (i['id'],) )

      # Create or update procurement operations
      cursor.execute("SELECT name FROM operation where name like 'Purchase %'")
      frepple_keys = set([ i[0] for i in cursor.fetchall()])
      cursor.executemany(
        "insert into operation \
          (name,location_id,subcategory,type,lastmodified) \
          values (%%s,%%s,'openbravo','fixed_time','%s')" % self.date,
        [ (i[2],i[1]) for i in deliveries if i[2] not in frepple_keys ])
      cursor.executemany(
        "update operation \
          set location_id=%%s, subcategory='OpenERP', type='fixed_time', lastmodified='%s' where name=%%s" % self.date,
        [ (i[1],i[2]) for i in deliveries if i[2] in frepple_keys ])

      # Create or update purchasing buffers
      cursor.execute("SELECT name FROM buffer")
      frepple_keys = set([ i[0] for i in cursor.fetchall()])
      cursor.executemany(
        "insert into buffer \
          (name,item_id,location_id,subcategory,lastmodified) \
          values(%%s,%%s,%%s,'openbravo','%s')" % self.date,
        [ (i[3],i[0],i[1]) for i in deliveries if i[3] not in frepple_keys ])
      cursor.executemany(
        "update buffer \
          set item_id=%%s, location_id=%%s, subcategory='OpenERP', lastmodified='%s' where name=%%s" % self.date,
        [ (i[0],i[1],i[3]) for i in deliveries if i[3] in frepple_keys ])

      # Create or update flow on purchasing operation
      cursor.execute("SELECT operation_id, thebuffer_id FROM flow")
      frepple_keys = set([ i for i in cursor.fetchall()])
      cursor.executemany(
        "insert into flow \
          (operation_id,thebuffer_id,quantity,type,source,lastmodified) \
          values(%%s,%%s,1,'end','OpenERP','%s')" % self.date,
        [ (i[2],i[3]) for i in deliveries if (i[2],i[3]) not in frepple_keys ])
      cursor.executemany(
        "update flow \
          set quantity=1, type='end', source='OpenERP', lastmodified='%s' where operation_id=%%s and thebuffer_id=%%s" % self.date,
        [ (i[2],i[3]) for i in deliveries if (i[2],i[3]) in frepple_keys ])

      # Create purchasing operationplans
      cursor.executemany(
        "insert into operationplan \
          (id,operation_id,startdate,enddate,quantity,locked,source,lastmodified) \
          values(%%s,%%s,%%s,%%s,%%s,'1','OpenERP','%s')" % self.date,
        [ (i[3], i[0], i[1], i[1], i[2], ) for i in insert ]
        )
      cursor.executemany(
        "update operationplan \
          set operation_id=%%s, enddate=%%s, startdate=%%s, quantity=%%s, locked='1', source='OpenERP', lastmodified='%s' \
          where id=%%s" % self.date,
        update)
      cursor.executemany(
        "delete from operationplan where id=%s and source='OpenERP'",
        delete)
      transaction.commit(using=self.database)
      if self.verbosity > 0:
        print("Inserted %d purchase order lines" % len(insert))
        print("Updated %d purchase order lines" % len(update))
        print("Deleted %d purchase order lines" % len(delete))
        print("Imported purchase orders in %.2f seconds" % (time() - starttime))
    except Exception as e:
      transaction.rollback(using=self.database)
      raise CommandError("Error importing purchase orders: %s" % e)
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
  #        - 'OpenERP' -> source
  #   - mapped fields OpenERP -> frePPLe buffer
  #        - %product_id.id %product_id.name @ %routing_id.location_id %routing_id.location_id.name -> name
  #        - %product_id.id %product_id.name -> item_id
  #        - %routing_id.location_id %routing_id.location_id.name -> location_id
  #        - %bom_id %bom_name @ %routing_id.location_id %routing_id.location_id.name -> producing_id
  #        - 'OpenERP' -> source
  #   - mapped fields OpenERP -> frePPLe flow
  #        - %product_id.id %product_id.name @ %routing_id.location_id %routing_id.location_id.name -> thebuffer_id
  #        - make %product_id.id %product_id.name @ %routing_id.location_id %routing_id.location_id.name -> operation_id
  #        - %product_qty * %product_efficiency -> quantity
  #        - 'flow_end' -> type
  #
  def import_boms(self, cursor):
    transaction.enter_transaction_management(using=self.database)
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
            default_location = self.warehouses.itervalues().next()
            if len(self.warehouses) > 1:
              print("Warning: Only single warehouse configurations are supported. Creating only boms for '%s'" % default_location)
          location = default_location

        # Determine operation name and item
        operation = u'%d %s @ %s' % (i['id'], i['name'], location)
        product = u'%d %s' % (i['product_id'][0], i['product_id'][1][i['product_id'][1].find(']')+2:])
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
                frepple_loads.add( (j[0],operation) )
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
        product = u'%d %s' % (i['product_id'][0], i['product_id'][1][i['product_id'][1].find(']')+2:])
        buffer = u'%d %s @ %s' % (i['product_id'][0], i['product_id'][1][i['product_id'][1].find(']')+2:], location)

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
          (name,location_id,source,sizemultiple,lastmodified) \
          values(%%s,%%s,'OpenERP',%%s,'%s')" % self.date,
        operation_insert
        )
      cursor.executemany(
        "update operation \
          set location_id=%%s, sizemultiple=%%s, source='OpenERP', lastmodified='%s' \
          where name=%%s" % self.date,
        operation_update
        )
      cursor.executemany(
        "update operation \
          set source=null, lastmodified='%s' \
          where name=%%s" % self.date,
        operation_delete
        )
      cursor.executemany(
        "insert into buffer \
          (name,item_id,location_id,producing_id,source,lastmodified) \
          values(%%s,%%s,%%s,%%s,'OpenERP','%s')" % self.date,
        buffer_insert
        )
      cursor.executemany(
        "update buffer \
          set item_id=%%s, location_id=%%s, producing_id=%%s, source='OpenERP', lastmodified='%s' \
          where name = %%s" % self.date,
        buffer_update
        )
      cursor.executemany(
        "insert into flow \
          (operation_id,thebuffer_id,quantity,type,effective_start,effective_end,source,lastmodified) \
          values(%%s,%%s,%%s,%%s,%%s,%%s,'OpenERP','%s')" % self.date,
        flow_insert
        )
      cursor.executemany(
        "update flow \
          set quantity=%%s, type=%%s, effective_start=%%s ,effective_end=%%s, source='OpenERP', lastmodified='%s' \
          where operation_id=%%s and thebuffer_id=%%s" % self.date,
        flow_update
        )
      cursor.executemany(
        "insert into resourceload \
          (operation_id,resource_id,quantity,source,lastmodified) \
          values(%%s,%%s,%%s,'OpenERP','%s')" % self.date,
        load_insert
        )
      cursor.executemany(
        "update resourceload \
          set quantity=%%s, lastmodified='%s', source='OpenERP' \
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
      raise CommandError("Error importing bills of material: %s" % e)
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
    try:
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
          where item_id = %%s and source = 'OpenERP'" % self.date,
        buy)
      cursor.executemany(
        "update buffer \
          set lastmodified='%s' \
          where item_id = %%s and source = 'OpenERP'" % self.date,
        produce)

      transaction.commit(using=self.database)
      if self.verbosity > 0:
        print("Updated buffers for %d procured items" % len(buy))
        print("Updated buffers for %d produced items" % len(produce))
    except Exception as e:
      transaction.rollback(using=self.database)
      raise CommandError("Error importing policies: %s" % e)
    finally:
      transaction.commit(using=self.database)
      transaction.leave_transaction_management(using=self.database)


# TODO:
#  - renaming an entity in OpenERP is not handled right: id remains the same in OpenERP, but the object name in frePPLe is different.
#  - Load reorder points
#  - Load loads
#  - Load WIP
#  - Unit of measures are not used

