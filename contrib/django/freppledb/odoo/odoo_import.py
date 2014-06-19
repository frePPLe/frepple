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
#     and may not be appropriate for frePPLe integration.


from __future__ import print_function
import xmlrpclib
from datetime import datetime, timedelta
from time import time
from operator import itemgetter

from django.core.management.base import CommandError
from django.db import transaction, connections, DEFAULT_DB_ALIAS

from freppledb.common.models import Parameter

import logging
logger = logging.getLogger(__name__)


class Connector(object):

  def __init__(self, task, delta=3650, database=DEFAULT_DB_ALIAS, verbosity=0):
    self.task = task
    self.database = database
    self.verbosity = verbosity
    self.delta = delta

    # Used as timestamp
    self.date = datetime.now()

    # Pick up configuration parameters
    self.odoo_user = Parameter.getValue("odoo.user", self.database)
    self.odoo_password = Parameter.getValue("odoo.password", self.database)
    self.odoo_db = Parameter.getValue("odoo.db", self.database)
    self.odoo_url = Parameter.getValue("odoo.url", self.database)
    self.odoo_production_location = Parameter.getValue("odoo.production_location", self.database)
    if not self.odoo_user:
      raise CommandError("Missing or invalid parameter odoo.user")
    if not self.odoo_password:
      raise CommandError("Missing or invalid parameter odoo.password")
    if not self.odoo_db:
      raise CommandError("Missing or invalid parameter odoo.db")
    if not self.odoo_url:
      raise CommandError("Missing or invalid parameter odoo.url")
    if not self.odoo_production_location:
      raise CommandError("Missing or invalid parameter odoo.production_location")

    # Initialize some global variables
    self.customers = {}
    self.items = {}
    self.locations = {} # A mapping between odoo stock.location ids and the name of the location in frePPLe
    self.resources = {}
    self.shops = {}
    self.delta = str(self.date - timedelta(days=self.delta))
    self.uom = {}
    self.calendar = None


  def run(self):
    # Log in to the odoo server
    sock_common = xmlrpclib.ServerProxy(self.odoo_url + 'xmlrpc/common')
    self.uid = sock_common.login(self.odoo_db, self.odoo_user, self.odoo_password)

    # Connect to odoo server
    self.sock = xmlrpclib.ServerProxy(self.odoo_url + 'xmlrpc/object')

    # Create a database connection to the frePPLe database
    cursor = connections[self.database].cursor()

    # Sequentially load all data
    self.load_uom(cursor)
    self.task.status = '2%'
    self.task.save(using=self.database)
    transaction.commit(using=self.database)
    self.import_calendar(cursor)
    self.task.status = '5%'
    self.task.save(using=self.database)
    transaction.commit(using=self.database)
    self.import_locations(cursor)
    self.task.status = '10%'
    self.task.save(using=self.database)
    transaction.commit(using=self.database)
    self.import_customers(cursor)
    self.task.status = '15%'
    self.task.save(using=self.database)
    transaction.commit(using=self.database)
    self.import_products(cursor)
    self.task.status = '25%'
    self.task.save(using=self.database)
    transaction.commit(using=self.database)
    self.import_salesorders(cursor)
    self.task.status = '35%'
    self.task.save(using=self.database)
    transaction.commit(using=self.database)
    self.import_workcenters(cursor)
    self.task.status = '40%'
    self.task.save(using=self.database)
    transaction.commit(using=self.database)
    self.import_onhand(cursor)
    self.task.status = '60%'
    self.task.save(using=self.database)
    transaction.commit(using=self.database)
    self.import_purchaseorders(cursor)
    self.task.status = '70%'
    self.task.save(using=self.database)
    self.import_boms(cursor)
    transaction.commit(using=self.database)
    self.task.status = '80%'
    self.task.save(using=self.database)
    self.import_policies(cursor)
    transaction.commit(using=self.database)
    self.task.status = '90%'
    self.task.save(using=self.database)
    transaction.commit(using=self.database)
    self.import_manufacturingorders(cursor)


  def odoo_search(self, a, b=[]):
    try:
      return self.sock.execute(self.odoo_db, self.uid, self.odoo_password, a, 'search', b)
    except xmlrpclib.Fault as e:
      raise CommandError(e.faultString)


  def odoo_data(self, a, b, c):
    try:
      return self.sock.execute(self.odoo_db, self.uid, self.odoo_password, a, 'read', b, c)
    except xmlrpclib.Fault as e:
      raise CommandError(e.faultString)


  # Loading units of measures
  #   - Extracting all active product.uom records
  #   - The data is not stored in the frePPLe database but extracted every
  #     time and kept in a Python dictionary variable.
  def load_uom(self, cursor):
    try:
      starttime = time()
      if self.verbosity > 0:
        print("Loading units of measure...")
      ids = self.odoo_search('product.uom', [])
      fields = ['factor','uom_type']
      count = 0
      for i in self.odoo_data('product.uom', ids, fields):
        if i['uom_type'] == 'reference':
          self.uom[i['id']] = 1.0
        elif i['uom_type'] == 'bigger':
          self.uom[i['id']] = i['factor']
        else:
          if i['factor'] > 0:
            self.uom[i['id']] = 1 / i['factor']
          else:
            self.uom[i['id']] = 1.0
        count += 1
      if self.verbosity > 0:
        print("Loaded %d units of measure in %.2f seconds" % (count, time() - starttime))
    except Exception as e:
      logger.error("Error loading units of measure", exc_info=1)
      raise CommandError("Error loading units of measure: %s" % e)


  # Importing customers
  #   - extracting recently changed res.partner objects
  #   - meeting the criterion:
  #        - %active = True
  #        - %customer = True
  #   - mapped fields odoo -> frePPLe customer
  #        - %id %name -> name
  #        - %ref     -> description
  #        - %id -> source
  #        - 'odoo' -> subcategory
  def import_customers(self, cursor):
    transaction.enter_transaction_management(using=self.database)
    try:
      starttime = time()
      if self.verbosity > 0:
        print("Importing customers...")

      # Collect existing frePPLe customers
      cursor.execute("SELECT name, subcategory, source FROM customer")
      frepple_keys = set()
      for i in cursor.fetchall():
        if i[1] == 'odoo':
          try: self.customers[int(i[2])] = i[0]
          except: pass
        frepple_keys.add(i[0])

      # Load all new Odoo customers
      ids = self.odoo_search( 'res.partner',
        ['|',('create_date','>', self.delta),('write_date','>', self.delta),
         '|',('active', '=', 1),('active', '=', 0)])
      fields = ['name', 'active', 'customer', 'ref']
      insert = []
      update = []
      rename = []
      delete = []
      for i in self.odoo_data('res.partner', ids, fields):
        name = u'%d %s' % (i['id'],i['name'])
        if i['active'] and i['customer']:
          if name in frepple_keys:
            update.append( (i['id'],name) )
          elif i['id'] in self.customers:
            # Object previously exported from odoo already, now renamed
            rename.append( (name,str(i['id'])) )
          else:
            insert.append( (i['id'],name) )
          self.customers[i['id']] = name
        elif i['id'] in self.customers:
          delete.append( (name,) )
          self.customers.pop(i['id'], None)

      # Apply the changes to the frePPLe database
      cursor.executemany(
        "insert into customer \
          (source,name,subcategory,lastmodified) \
          values (%%s,%%s,'odoo','%s')" % self.date,
        insert)
      cursor.executemany(
        "update customer \
          set source=%%s, subcategory='odoo',lastmodified='%s' \
          where name=%%s" % self.date,
        update)
      cursor.executemany(
        "update customer \
          set name=%%s, lastmodified='%s' \
          where source=%%s and subcategory='odoo'" % self.date,
        rename
        )
      cursor.executemany('update customer set owner_id=null where owner_id=%s',
        delete
        )
      cursor.executemany('update demand set customer_id=null where customer_id=%s',
        delete
        )
      cursor.executemany('delete from customer where name=%s',
        delete
        )
      transaction.commit(using=self.database)

      if self.verbosity > 0:
        print("Inserted %d new customers" % len(insert))
        print("Updated %d existing customers" % len(update))
        print("Renamed %d existing customers" % len(rename))
        print("Deleted %d customers" % len(delete))
        print("Imported customers in %.2f seconds" % (time() - starttime))
    except Exception as e:
      transaction.rollback(using=self.database)
      logger.error("Error importing customers", exc_info=1)
      raise CommandError("Error importing customers: %s" % e)
    finally:
      transaction.commit(using=self.database)
      transaction.leave_transaction_management(using=self.database)


  # Importing products
  #   - extracting recently changed product.product objects
  #   - meeting the criterion:
  #        - %active = True
  #   - mapped fields odoo -> frePPLe item
  #        - %code %name -> name
  #        - 'odoo' -> subcategory
  #        - %id -> source
  #   - We assume the code+name combination is unique, but this is not
  #     enforced at all in odoo. The only other option is to include
  #     the id in the name - not nice for humans...
  # TODO also get template.produce_delay, property_stock_production, property_stock_inventory, and property_stock_procurement?
  def import_products(self, cursor):
    transaction.enter_transaction_management(using=self.database)
    try:
      starttime = time()
      if self.verbosity > 0:
        print("Importing products...")

      # Get existing frePPLe items
      cursor.execute("SELECT name, subcategory, source FROM item")
      frepple_keys = set()
      for i in cursor.fetchall():
        if i[1] == 'odoo':
          try: self.items[int(i[2])] = i[0]
          except: pass
        frepple_keys.add(i[0])

      # Get all new Odoo products
      ids = self.odoo_search('product.product', [
        '|',('create_date','>', self.delta),('write_date','>', self.delta),
        '|',('active', '=', 1),('active', '=', 0)
        ])
      fields = ['name', 'code', 'active']
      insert = []
      update = []
      rename = []
      delete = []
      for i in self.odoo_data('product.product', ids, fields):
        if i['code']:
          name = u'[%s] %s' % (i['code'], i['name'])
        else:
          name = i['name']
        if i['active']:
          if name in frepple_keys:
            update.append( (i['id'],name) )
          elif i['id'] in self.items:
            # Object previously exported from odoo already, now renamed
            rename.append( (name,str(i['id'])) )
          else:
            insert.append( (name,i['id']) )
          self.items[i['id']] = name
          frepple_keys.add(name)
        elif i['id'] in self.items:
          delete.append( (name,) )
          self.items.pop(i['id'], None)

      # Apply the changes to the frePPLe database
      cursor.executemany(
        "insert into item \
          (name,source,subcategory,lastmodified) \
          values (%%s,%%s,'odoo','%s')" % self.date,
        insert
        )
      cursor.executemany(
        "update item \
          set source=%%s, subcategory='odoo', lastmodified='%s' \
          where name=%%s" % self.date,
        update
        )
      cursor.executemany(
        "update item \
          set name=%%s, lastmodified='%s' \
          where source=%%s and subcategory='odoo'" % self.date,
        rename
        )
      cursor.executemany("delete from demand where item_id=%s", delete)
      cursor.executemany("delete from flow \
         where thebuffer_id in (select name from buffer where item_id=%s)",
         delete
         )
      cursor.executemany("delete from buffer where item_id=%s", delete)
      cursor.executemany("delete from item where name=%s", delete)
      transaction.commit(using=self.database)

      if self.verbosity > 0:
        print("Inserted %d new products" % len(insert))
        print("Updated %d existing products" % len(update))
        print("Renamed %d existing products" % len(rename))
        print("Deleted %d products" % len(delete))
        print("Imported products in %.2f seconds" % (time() - starttime))
    except Exception as e:
      transaction.rollback(using=self.database)
      logger.error("Error importing products", exc_info=1)
      raise CommandError("Error importing products: %s" % e)
    finally:
      transaction.commit(using=self.database)
      transaction.leave_transaction_management(using=self.database)


  # Importing location calendar
  #  - Extract the resource calendar specified by the parameter odoo.calendar.
  #    If the parameter is empty, no calendar is assigned.
  #  - Extracting also the child objects resource.calendar.attendance to calendarbuckets.
  #  - NO filter on recently changed records
  #  - mapped fields odoo resource.calendar -> frePPLe calendar
  #       - parameter 'odoo.calendar' -> name
  #       - 'odoo' -> subcategory
  #  - mapped fields odoo resource.calendar.attendance -> frePPLe calendarbucket
  #       - parameter odoo.calendar -> calendar_id
  #       - dayofweek -> monday / tuesday / wednesday / thursday / friday /saturday /sunday
  #       - hour_from -> starttime
  #       - hour_to -> endtime
  #       - date_from -> startdate
  #       - 'odoo' -> source
  def import_calendar(self, cursor):
    transaction.enter_transaction_management(using=self.database)
    try:
      starttime = time()
      if self.verbosity > 0:
        print("Importing calendar...")

      # Pick up the calendar
      self.calendar = Parameter.getValue("odoo.calendar", self.database)
      if self.calendar:

        # Update calendar
        cnt = cursor.execute("update calendar \
          set defaultvalue=0, subcategory='odoo', lastmodified='%s' \
          where name=%%s" % self.date,
          [self.calendar,])
        if cnt == 0:
          # Create the calendar
          cursor.execute("insert into calendar \
           (name, subcategory, lastmodified) values (%s,'odoo','%s')"
           % self.date)
        else:
          # Delete existing calendar buckets
          cursor.execute("delete from calendarbucket where calendar_id=%s", [self.calendar,])

        # Create calendar buckets for the attendance records
        buckets = []
        ids = self.odoo_search('resource.calendar', [('name','=', self.calendar)])
        fields = ['name', 'attendance_ids']
        fields2 = ['dayofweek', 'date_from', 'hour_from', 'hour_to']
        for i in self.odoo_data('resource.calendar', ids, fields):
          for j in self.odoo_data('resource.calendar.attendance', i['attendance_ids'], fields2):
            buckets.append( [
              self.calendar, datetime.strptime(j['date_from'] or "2000-01-01", '%Y-%m-%d'),
              j['dayofweek'] == '0' and '1' or '0', j['dayofweek'] == '1' and '1' or '0',
              j['dayofweek'] == '2' and '1' or '0', j['dayofweek'] == '3' and '1' or '0',
              j['dayofweek'] == '4' and '1' or '0', j['dayofweek'] == '5' and '1' or '0',
              j['dayofweek'] == '6' and '1' or '0',
              '%s:%s:00' % (int(j['hour_from']), round( (j['hour_from'] - int(j['hour_from'])) * 60)),
              '%s:%s:00' % (int(j['hour_to']), round( (j['hour_to'] - int(j['hour_to'])) * 60)),
              1000
              ] )

        # Sort by start date.
        # Required to assure that records with a later start date get a
        # lower priority in frePPLe.
        buckets.sort(key=itemgetter(2))

        # Assign priorities
        priority = 1000
        for i in buckets:
          i[11] = priority
          priority -= 1

        # Create frePPLe records
        cursor.executemany(
          "insert into calendarbucket \
           (calendar_id, startdate, monday, tuesday, wednesday, thursday, friday, \
            saturday, sunday, starttime, endtime, priority, value, source, lastmodified) \
           values(%%s,%%s,%%s,%%s,%%s,%%s,%%s,%%s,%%s,%%s,%%s,%%s,1.0,'odoo','%s')" % self.date,
           buckets
          )

      transaction.commit(using=self.database)

      if self.verbosity > 0:
        print("Created calendar in %.2f seconds" % (time() - starttime))
    except Exception as e:
      transaction.rollback(using=self.database)
      logger.error("Error importing calendar", exc_info=1)
      raise CommandError("Error importing calendar: %s" % e)
    finally:
      transaction.commit(using=self.database)
      transaction.leave_transaction_management(using=self.database)


  # Importing locations
  #   - extracting stock.warehouses objects
  #   - NO filter on recently changed records
  #   - NO deletion of locations which become inactive
  #   - meeting the criterion:
  #        - %active = True
  #   - mapped fields odoo -> frePPLe location
  #        - %name -> name
  #        - 'odoo' -> subcategory
  #        - %id -> source
  def import_locations(self, cursor):
    transaction.enter_transaction_management(using=self.database)
    try:
      starttime = time()
      if self.verbosity > 0:
        print("Importing warehouses...")

      # Get existing locations
      cursor.execute("SELECT name, subcategory, source FROM location")
      frepple_keys = set()
      for i in cursor.fetchall():
        if i[1] == 'odoo':
          try: self.locations[int(i[2])] = i[0]
          except: pass
        frepple_keys.add(i[0])

      # Pick up all warehouses
      ids = self.odoo_search('stock.warehouse')
      fields = ['name', 'lot_stock_id', 'lot_input_id', 'lot_output_id']
      insert = []
      update = []
      rename = []
      childlocs = {}
      # Loop over the warehouses
      for i in self.odoo_data('stock.warehouse', ids, fields):
        if i['name'] in frepple_keys:
          update.append( (i['id'],i['name']) )
        elif i['id'] in self.locations:
          # Object previously exported from odoo already, now renamed
          rename.append( (i['name'],str(i['id'])) )
        else:
          insert.append( (i['name'],i['id']) )
        # Find all child locations of the warehouse.
        childlocs[i['lot_stock_id'][0]] = i['name']
        childlocs[i['lot_input_id'][0]] = i['name']
        childlocs[i['lot_output_id'][0]] = i['name']

      # Find all locations in the warehouse
      # We populate a mapping location-to-warehouse name for later lookups.
      fields2 = ['child_ids']
      for j in self.odoo_data('stock.location', childlocs.keys(), fields2):
        self.locations[j['id']] = childlocs[j['id']]
        for k in j['child_ids']:
          self.locations[k] = childlocs[j['id']]

      # Create records for the warehouses
      cursor.executemany(
        "insert into location \
          (name,source,subcategory,lastmodified) \
          values (%%s,%%s,'odoo','%s')" % self.date,
        insert)
      cursor.executemany(
        "update location \
          set source=%%s, subcategory='odoo', lastmodified='%s' \
          where name=%%s" % self.date,
        update)
      cursor.executemany(
        "update location \
          set name=%%s, subcategory='odoo', lastmodified='%s' \
          where source=%%s" % self.date,
        rename)

      # Update calendars
      if self.calendar:
        cursor.execute(
          "update location set available_id=%s where subcategory='odoo'",
          [self.calendar,]
          )
      transaction.commit(using=self.database)

      if self.verbosity > 0:
        print("Inserted %d new warehouses" % len(insert))
        print("Updated %d existing warehouses" % len(update))
        print("Renamed %d existing warehouses" % len(rename))
        print("Imported warehouses in %.2f seconds" % (time() - starttime))
    except Exception as e:
      transaction.rollback(using=self.database)
      logger.error("Error importing warehouses", exc_info=1)
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
  #   - mapped fields odoo -> frePPLe delivery operation
  #        - 'delivery %sol_product_id %sol_product_name from %loc' -> name
  #   - mapped fields odoo -> frePPLe buffer
  #        - '%sol_product_id %sol_product_name @ %loc' -> name
  #   - mapped fields odoo -> frePPLe delivery flow
  #        - 'delivery %sol_product_id %sol_product_name from %loc' -> operation
  #        - '%sol_product_id %sol_product_name @ %loc' -> buffer
  #        - quantity -> -1
  #        -  'start' -> type
  #   - mapped fields odoo -> frePPLe demand
  #        - %sol_id %so_name %sol_sequence -> name
  #        - %sol_product_uom_qty * uom conversion -> quantity
  #        - %sol_product_id -> item
  #        - %so_partner_id -> customer
  #        - %so_requested_date or %so_date_order -> due
  #        - 'odoo' -> source
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
      ids = self.odoo_search('sale.shop')
      fields = ['name', 'warehouse_id']
      for i in self.odoo_data('sale.shop', ids, fields):
        self.shops[i['id']] = i['warehouse_id'][1]

      # Now the list of sales orders
      deliveries = set()
      if self.verbosity > 0:
        print("Importing sales orders...")
      cursor.execute("SELECT name FROM demand")
      frepple_keys = set([ i[0] for i in cursor.fetchall()])
      ids = self.odoo_search('sale.order.line',
        ['|',('create_date','>', self.delta),('write_date','>', self.delta),])
      fields = ['state', 'type', 'product_id', 'product_uom_qty', 'product_uom', 'order_id']
      fields2 = ['partner_id', 'requested_date', 'date_order', 'picking_policy', 'shop_id']
      insert = []
      update = []
      delete = []
      so_line = [ i for i in self.odoo_data('sale.order.line', ids, fields)]
      so = { j['id']: j for j in self.odoo_data('sale.order', [i['order_id'][0] for i in so_line], fields2) }
      for i in so_line:
        name = u'%s %d' % (i['order_id'][1], i['id'])
        source = i['order_id'][0]
        if i['state'] == 'confirmed':
          product = i['product_id'][1]
          j = so[i['order_id'][0]]
          location = self.shops.get(j['shop_id'][0], None)
          customer = self.customers.get(j['partner_id'][0], None)
          if not(location and customer and i['product_id'][0] in self.items):
            continue
          operation = u'Ship %s @ %s' % (product, location)
          buffer = u'%s @ %s' % (product, location)
          deliveries.update([(product,location,operation,buffer),])
          due = datetime.strptime(j['requested_date'] or j['date_order'], '%Y-%m-%d')
          uom_factor = self.uom.get(i['product_uom'][0],1.0)
          if name in frepple_keys:
            update.append( (
              product,
              customer,
              i['product_uom_qty'] * uom_factor,
              j['picking_policy'] == 'one' and i['product_uom_qty'] or 1.0,
              due,
              operation,
              source,
              name,
              ) )
          else:
            insert.append( (
              product,
              customer,
              i['product_uom_qty'] * uom_factor,
              j['picking_policy'] == 'one' and i['product_uom_qty'] or 1.0,
              due,
              operation,
              source,
              name,
              ) )
        elif name in frepple_keys:
          # Only confirmed sales orders are shown in frePPLe
          delete.append( (name,) )

      # Create or update delivery operations
      cursor.execute("SELECT name FROM operation where name like 'Ship %'")
      frepple_keys = set([ i[0] for i in cursor.fetchall()])
      cursor.executemany(
        "insert into operation \
          (name,location_id,subcategory,lastmodified) \
          values (%%s,%%s,'odoo','%s')" % self.date,
        [ (i[2],i[1]) for i in deliveries if i[2] not in frepple_keys ])
      cursor.executemany(
        "update operation \
          set location_id=%%s, subcategory='odoo', lastmodified='%s' where name=%%s" % self.date,
        [ (i[1],i[2]) for i in deliveries if i[2] in frepple_keys ])

      # Create or update delivery buffers
      cursor.execute("SELECT name FROM buffer")
      frepple_keys = set([ i[0] for i in cursor.fetchall()])
      cursor.executemany(
        "insert into buffer \
          (name,item_id,location_id,subcategory,lastmodified) \
          values(%%s,%%s,%%s,'odoo','%s')" % self.date,
        [ (i[3],i[0],i[1]) for i in deliveries if i[3] not in frepple_keys ])
      cursor.executemany(
        "update buffer \
          set item_id=%%s, location_id=%%s, subcategory='odoo', lastmodified='%s' where name=%%s" % self.date,
        [ (i[0],i[1],i[3]) for i in deliveries if i[3] in frepple_keys ])

      # Create or update flow on delivery operation
      cursor.execute("SELECT operation_id, thebuffer_id FROM flow")
      frepple_keys = set([ i for i in cursor.fetchall()])
      cursor.executemany(
        "insert into flow \
          (operation_id,thebuffer_id,quantity,type,source,lastmodified) \
          values(%%s,%%s,-1,'start','odoo','%s')" % self.date,
        [ (i[2],i[3]) for i in deliveries if (i[2],i[3]) not in frepple_keys ])
      cursor.executemany(
        "update flow \
          set quantity=-1, type='start', source='odoo', lastmodified='%s' where operation_id=%%s and thebuffer_id=%%s" % self.date,
        [ (i[2],i[3]) for i in deliveries if (i[2],i[3]) in frepple_keys ])

      # Create or update demands
      cursor.executemany(
        "insert into demand \
          (item_id,customer_id,quantity,minshipment,due,operation_id,priority,subcategory,lastmodified,source,name) \
          values (%%s,%%s,%%s,%%s,%%s,%%s,1,'odoo','%s',%%s,%%s)" % self.date,
        insert)
      cursor.executemany(
        "update demand \
          set item_id=%%s, customer_id=%%s, quantity=%%s, minshipment=%%s, due=%%s, operation_id=%%s, source=%%s, priority=1, subcategory='odoo', lastmodified='%s' \
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
      logger.error("Error importing sales orders", exc_info=1)
      raise CommandError("Error importing sales orders: %s" % e)
    finally:
      transaction.commit(using=self.database)
      transaction.leave_transaction_management(using=self.database)


  # Importing work centers
  #   - extracting recently changed mrp.workcenter objects
  #   - meeting the criterion:
  #        - %active = True
  #   - mapped fields odoo -> frePPLe resource
  #        - %id %name -> name
  #        - %cost_hour -> cost
  #        - capacity_per_cycle -> maximum
  #          This field is only transfered when inserting a new workcenter.
  #          Later runs of the connector will not update the value any more,
  #          since this field is typically maintained in frePPLe.
  #        - 'odoo' -> source
  #   - In odoo a work center links to a resource, and a resource has
  #     a calendar with working hours.
  #     We don't map the calendar to frePPLe, assuming that this is easy
  #     to maintain in frePPLe.
  def import_workcenters(self, cursor):
    transaction.enter_transaction_management(using=self.database)
    try:
      starttime = time()
      if self.verbosity > 0:
        print("Importing workcenters...")

      # Get existing frePPLe resources
      cursor.execute("SELECT name, subcategory, source FROM resource")
      frepple_keys = set()
      for i in cursor.fetchall():
        if i[1] == 'odoo':
          try: self.resources[int(i[2])] = i[0]
          except: pass
        frepple_keys.add(i[0])

      # Pick up the list of new Odoo workcenters
      ids = self.odoo_search('mrp.workcenter',
        ['|',('create_date','>', self.delta),('write_date','>', self.delta),
         '|',('active', '=', 1),('active', '=', 0)])
      fields = ['name', 'active', 'costs_hour', 'capacity_per_cycle', 'time_cycle']
      insert = []
      update = []
      rename = []
      delete = []
      for i in self.odoo_data('mrp.workcenter', ids, fields):
        if i['active']:
          if i['name'] in frepple_keys:
            update.append( (i['id'],i['costs_hour'],i['name']) )
          elif i['id'] in self.resources:
            # Object previously exported from odoo already, now renamed
            rename.append( (i['name'],i['costs_hour'],str(i['id'])) )
          else:
            insert.append( (i['id'],i['name'],i['costs_hour'],i['capacity_per_cycle'] / (i['time_cycle'] or 1)) )
          self.resources[i['id']] = i['name']
        elif i['id'] in self.resources:
          delete.append( (str(i['id']),) ),

      # Apply the changes to the frePPLe database
      cursor.executemany(
        "insert into resource \
          (source,name,cost,maximum,subcategory,lastmodified) \
          values (%%s,%%s,%%s,%%s,'odoo','%s')" % self.date,
        insert)
      cursor.executemany(
        "update resource \
          set source=%%s, cost=%%s, subcategory='odoo', lastmodified='%s' \
          where name=%%s" % self.date,
        update)
      cursor.executemany(
        "update resource \
          set name=%%s, cost=%%s, subcategory='odoo', lastmodified='%s' \
          where source=%%s" % self.date,
        rename)
      cursor.executemany('delete from resourceload where resource_id=%s', delete)
      cursor.executemany('delete from resourceskill where resource_id=%s', delete)
      cursor.executemany('update resource set owner_id=NULL where owner_id=%s', delete)
      cursor.executemany('delete from resource where name=%s', delete)
      transaction.commit(using=self.database)

      if self.verbosity > 0:
        print("Inserted %d new workcenters" % len(insert))
        print("Updated %d existing workcenters" % len(update))
        print("Renamed %d existing workcenters" % len(rename))
        print("Deleted %d workcenters" % len(delete))
        print("Imported workcenters in %.2f seconds" % (time() - starttime))
    except Exception as e:
      transaction.rollback(using=self.database)
      logger.error("Error importing workcenters", exc_info=1)
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
  #   - mapped fields odoo -> frePPLe buffer
  #        - %product_id %product_name @ %name -> name
  #        - %product_id %product_name -> item_id
  #        - %location_id %location_name -> location_id
  #        - %qty -> onhand
  #        - 'odoo' -> source
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
      cursor.execute("update buffer set onhand = 0 where subcategory = 'odoo'")
      ids = self.odoo_search('stock.report.prodlots', [('qty','>', 0),])
      fields = ['prodlot_id', 'location_id', 'qty', 'product_id']
      insert = []
      update = []
      for i in self.odoo_data('stock.report.prodlots', ids, fields):
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
          values(%%s,%%s,%%s,%%s,'odoo','%s')" % self.date,
        insert
        )
      cursor.executemany(
        "update buffer \
          set onhand=onhand+%%s, subcategory='odoo', lastmodified='%s' \
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
      logger.error("Error importing onhand", exc_info=1)
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
  #   - mapped fields odoo -> frePPLe buffer
  #        - %product ' @ ' %name -> name
  #        - %location, mapped to warehouse -> location
  #        - %product -> product
  #        - 'odoo' -> subcategory
  #   - mapped fields odoo -> frePPLe operation
  #        - 'Purchase ' %product ' @ ' %location -> name
  #        - 'odoo' -> subcategory
  #        - 'fixed_time' -> type
  #   - mapped fields odoo -> frePPLe flow
  #        - 'Purchase ' %product ' @ ' %location -> operation
  #        - %product ' @ ' %name -> buffer
  #        - 1 -> quantity
  #        - 'end' -> type
  #        - 'odoo' -> source
  #   - mapped fields odoo -> frePPLe operationplan
  #        - %id %name -> name
  #        - 'odoo' -> source
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
      ids = self.odoo_search('purchase.order.line',['|',('create_date','>', self.delta),('write_date','>', self.delta)])
      fields = ['name', 'date_planned', 'product_id', 'product_qty', 'product_uom', 'order_id']
      fields2 = ['name', 'location_id', 'partner_id', 'state', 'shipped']
      insert = []
      delete = []
      update = []
      po_line = [ i for i in self.odoo_data('purchase.order.line', ids, fields) ]
      po = { j['id']: j for j in self.odoo_data('purchase.order', [i['order_id'][0] for i in po_line], fields2) }
      for i in po_line:
        if not i['product_id']: continue
        item = i['product_id'][1]
        j = po[i['order_id'][0]]
        location = j['location_id'] and self.locations.get(j['location_id'][0], None) or None
        if location and item in frepple_items and j['state'] in ('approved','draft') and not j['shipped']:
          operation = u'Purchase %s @ %s' % (item, location)
          due = datetime.strptime(i['date_planned'], '%Y-%m-%d')
          uom_factor = self.uom.get(i['product_uom'][0],1.0)
          if i['id'] in frepple_keys:
            update.append( (
               operation, due, due, i['product_qty']*uom_factor, i['id']
              ) )
          else:
            insert.append( (
               i['id'], operation, due, due, i['product_qty']*uom_factor
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
          values (%%s,%%s,'odoo','fixed_time','%s')" % self.date,
        [ (i[2],i[1]) for i in deliveries if i[2] not in frepple_keys ])
      cursor.executemany(
        "update operation \
          set location_id=%%s, subcategory='odoo', type='fixed_time', lastmodified='%s' where name=%%s" % self.date,
        [ (i[1],i[2]) for i in deliveries if i[2] in frepple_keys ])

      # Create or update purchasing buffers
      cursor.execute("SELECT name FROM buffer")
      frepple_keys = set([ i[0] for i in cursor.fetchall()])
      cursor.executemany(
        "insert into buffer \
          (name,item_id,location_id,subcategory,lastmodified) \
          values(%%s,%%s,%%s,'odoo','%s')" % self.date,
        [ (i[3],i[0],i[1]) for i in deliveries if i[3] not in frepple_keys ])
      cursor.executemany(
        "update buffer \
          set item_id=%%s, location_id=%%s, subcategory='odoo', lastmodified='%s' where name=%%s" % self.date,
        [ (i[0],i[1],i[3]) for i in deliveries if i[3] in frepple_keys ])

      # Create or update flow on purchasing operation
      cursor.execute("SELECT operation_id, thebuffer_id FROM flow")
      frepple_keys = set([ i for i in cursor.fetchall()])
      cursor.executemany(
        "insert into flow \
          (operation_id,thebuffer_id,quantity,type,source,lastmodified) \
          values(%%s,%%s,1,'end','odoo','%s')" % self.date,
        [ (i[2],i[3]) for i in deliveries if (i[2],i[3]) not in frepple_keys ])
      cursor.executemany(
        "update flow \
          set quantity=1, type='end', source='odoo', lastmodified='%s' where operation_id=%%s and thebuffer_id=%%s" % self.date,
        [ (i[2],i[3]) for i in deliveries if (i[2],i[3]) in frepple_keys ])

      # Create purchasing operationplans
      cursor.executemany(
        "insert into operationplan \
          (id,operation_id,startdate,enddate,quantity,locked,source,lastmodified) \
          values(%%s,%%s,%%s,%%s,%%s,'1','odoo','%s')" % self.date,
        insert
        )
      cursor.executemany(
        "update operationplan \
          set operation_id=%%s, startdate=%%s, enddate=%%s, quantity=%%s, locked='1', source='odoo', lastmodified='%s' \
          where id=%%s" % self.date,
        update)
      cursor.executemany(
        "delete from operationplan where id=%s and source='odoo'",
        delete)
      transaction.commit(using=self.database)

      if self.verbosity > 0:
        print("Inserted %d purchase order lines" % len(insert))
        print("Updated %d purchase order lines" % len(update))
        print("Deleted %d purchase order lines" % len(delete))
        print("Imported purchase orders in %.2f seconds" % (time() - starttime))
    except Exception as e:
      transaction.rollback(using=self.database)
      logger.error("Error importing purchase orders", exc_info=1)
      raise CommandError("Error importing purchase orders: %s" % e)
    finally:
      transaction.commit(using=self.database)
      transaction.leave_transaction_management(using=self.database)


  # Importing boms
  #   - extracting mrp.bom, mrp.routing.workcenter and mrp.routing.workcenter objects
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
  #   - mapped fields odoo -> frePPLe operation
  #        - make %product_id.id %product_id.name @ %routing_id.location_id %routing_id.location_id.name -> name
  #        - %routing_id.location_id %routing_id.location_id.name -> location_id
  #        - %product_rounding * uom conversion -> size_multiple
  #        - 'odoo' -> source
  #   - mapped fields odoo -> frePPLe buffer
  #        - %product_id.id %product_id.name @ %routing_id.location_id %routing_id.location_id.name -> name
  #        - %product_id.id %product_id.name -> item_id
  #        - %routing_id.location_id %routing_id.location_id.name -> location_id
  #        - %bom_id %bom_name @ %routing_id.location_id %routing_id.location_id.name -> producing_id
  #        - 'odoo' -> source
  #   - mapped fields odoo -> frePPLe flow
  #        - %product_id.id %product_id.name @ %routing_id.location_id %routing_id.location_id.name -> thebuffer_id
  #        - make %product_id.id %product_id.name @ %routing_id.location_id %routing_id.location_id.name -> operation_id
  #        - %product_qty * %product_efficiency * uom conversion -> quantity
  #        - 'flow_end' -> type
  #
  # TODO: Choice between detailed and simplified model
  #   -> Detailed mapping uses a routing operation, with sequence of workcenters
  #   -> Simplified model uses a single operation
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
      odoo_mfg_routings = {}
      ids = self.odoo_search('mrp.routing')
      for i in self.odoo_data('mrp.routing', ids, ['location_id',]):
        if i['location_id']:
          odoo_mfg_routings[i['id']] = self.locations.get(i['location_id'][0], None)
        else:
          odoo_mfg_routings[i['id']] = None

      # Pick up all workcenters in the routing
      routing_workcenters = {}
      ids = self.odoo_search('mrp.routing.workcenter')
      fields = ['routing_id','workcenter_id','sequence','cycle_nbr','hour_nbr',]
      for i in self.odoo_data('mrp.routing.workcenter', ids, fields):
        if i['routing_id'][0] in routing_workcenters:
          routing_workcenters[i['routing_id'][0]].append( (i['workcenter_id'][1], i['cycle_nbr'],) )
        else:
          routing_workcenters[i['routing_id'][0]] = [ (i['workcenter_id'][1], i['cycle_nbr'],), ]

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

      # Loop over all "producing" bom records
      boms = {}
      ids = self.odoo_search('mrp.bom', [
        ('bom_id','=',False), #'|',('create_date','>', self.delta),('write_date','>', self.delta),
        '|',('active', '=', 1),('active', '=', 0)])
      fields = ['name', 'active', 'product_qty', 'product_uom', 'date_start', 'date_stop',
        'product_efficiency', 'product_id', 'routing_id', 'bom_id', 'type', 'sub_products',
        'product_rounding',]
      for i in self.odoo_data('mrp.bom', ids, fields):
        # TODO Handle routing steps
        # Determine the location
        if i['routing_id']:
          location = odoo_mfg_routings.get(i['routing_id'][0], None) or self.odoo_production_location
        else:
          location = self.odoo_production_location

        # Determine operation name and item
        operation = u'%d %s @ %s' % (i['id'], i['name'], location)
        product = self.items.get(i['product_id'][0], None)
        if not product: continue
        buffer = u'%s @ %s' % (product, location)  # TODO if policy is produce, then this should be the producting operation
        uom_factor = self.uom.get(i['product_uom'][0],1.0)

        if i['active']:
          boms[i['id']] = (operation, location)
          # Creation or update operations
          if operation in frepple_operations:
            operation_update.append( (
              location, i['product_rounding']*uom_factor or 1, operation,
              ) )
          else:
            frepple_operations.add(operation)
            operation_insert.append( (
              operation, location, (i['product_rounding'] * uom_factor) or 1
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
              i['product_qty'] * i['product_efficiency'] * uom_factor, 'end',
              i['date_start'] or None, i['date_stop'] or None, operation, buffer,
              ) )
          else:
            flow_insert.append( (
              operation, buffer, i['product_qty'] * i['product_efficiency'] * uom_factor,
              'end', i['date_start'] or None, i['date_stop'] or None
              ) )
            frepple_flows.add( (buffer,operation) )
          # Create workcentre loads
          if i['routing_id']:
            for j in routing_workcenters.get(i['routing_id'][0],[]):
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
      ids = self.odoo_search('mrp.bom', [
        ('bom_id','!=',False), #'|',('create_date','>', self.delta),('write_date','>', self.delta),
        '|',('active', '=', 1),('active', '=', 0)])
      fields = ['name', 'active', 'product_qty', 'product_uom', 'date_start', 'date_stop',
        'product_id', 'routing_id', 'bom_id', 'type', 'sub_products', 'product_rounding',]
      for i in self.odoo_data('mrp.bom', ids, fields):
        # Determine operation and buffer
        (operation, location) = boms.get(i['bom_id'][0], (None, None))
        product = self.items.get(i['product_id'][0], None)
        if not location and not operation or not product: continue
        buffer = u'%s @ %s' % (product, location)
        uom_factor = self.uom.get(i['product_uom'][0],1.0)

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
              -i['product_qty'] * uom_factor, 'start', i['date_start'] or None, i['date_stop'] or None, operation, buffer,
              ) )
          else:
            flow_insert.append( (
              operation, buffer, -i['product_qty'] * uom_factor, 'start', i['date_start'] or None, i['date_stop'] or None
              ) )
            frepple_flows.add( (buffer,operation) )
        else:
          # Not active any more
          if (buffer,operation) in frepple_flows:
            flow_delete.append( (buffer,operation) )

      # Process in the frePPLe database
      cursor.executemany(
        "insert into operation \
          (name,location_id,subcategory,sizemultiple,lastmodified) \
          values(%%s,%%s,'odoo',%%s,'%s')" % self.date,
        operation_insert
        )
      cursor.executemany(
        "update operation \
          set location_id=%%s, sizemultiple=%%s, subcategory='odoo', lastmodified='%s' \
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
          values(%%s,%%s,%%s,%%s,'odoo','%s')" % self.date,
        buffer_insert
        )
      cursor.executemany(
        "update buffer \
          set item_id=%%s, location_id=%%s, producing_id=%%s, subcategory='odoo', lastmodified='%s' \
          where name = %%s" % self.date,
        buffer_update
        )
      cursor.executemany(
        "insert into flow \
          (operation_id,thebuffer_id,quantity,type,effective_start,effective_end,source,lastmodified) \
          values(%%s,%%s,%%s,%%s,%%s,%%s,'odoo','%s')" % self.date,
        flow_insert
        )
      cursor.executemany(
        "update flow \
          set quantity=%%s, type=%%s, effective_start=%%s ,effective_end=%%s, source='odoo', lastmodified='%s' \
          where operation_id=%%s and thebuffer_id=%%s" % self.date,
        flow_update
        )
      cursor.executemany(
        "insert into resourceload \
          (operation_id,resource_id,quantity,source,lastmodified) \
          values(%%s,%%s,%%s,'odoo','%s')" % self.date,
        load_insert
        )
      cursor.executemany(
        "update resourceload \
          set quantity=%%s, lastmodified='%s', source='odoo' \
          where operation_id=%%s and resource_id=%%s" % self.date,
        load_update
        )
      cursor.executemany(
        "delete from flow \
          where operation_id=%s and thebuffer_id=%s",
        flow_delete
        )

      # TODO multiple produce/procure boms for the same item -> alternate operation

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
      logger.error("Error importing bills of material", exc_info=1)
      raise CommandError("Error importing bills of material: %s" % e)
    finally:
      transaction.commit(using=self.database)
      transaction.leave_transaction_management(using=self.database)


  # Importing policies
  #   - Extracting product.template objects for all items mapped from odoo
  #   - TODO No net change functionality yet.
  #   - Extracting recently changed stock.warehouse.orderpoint objects
  #   - mapped fields product.template odoo -> frePPLe buffers
  #        - %product -> filter where buffer.item_id = %product and subcategory='odoo'
  #        - %type -> 'procure' when %purchase_ok=true and %supply_method='buy'
  #                   'default' for all other cases
  #        - %produce_delay -> leadtime
  #   - mapped fields stock.warehouse.orderpoint odoo -> frePPLe buffers
  #        - %product %warehouse -> filter where buffer.item_id = %product and buffer.location_id = %warehouse
  #        - %product_min_qty * uom conversion -> min_inventory
  #        - %product_max_qty * uom conversion -> max_inventory
  #        - %qty_multiple * uom conversion -> size_multiple
  def import_policies(self, cursor):
    transaction.enter_transaction_management(using=self.database)
    try:
      starttime = time()
      if self.verbosity > 0:
        print("Importing policies and reorderpoints...")

      # Get the list of item ids and the template info
      cursor.execute("SELECT name, source FROM item where subcategory='odoo'")
      items = {}
      for i in cursor.fetchall():
        try: items[int(i[1])] = i[0]
        except: pass
      fields = ['product_tmpl_id']
      fields2 = ['purchase_ok','procure_method','supply_method','produce_delay','list_price','uom_id']
      buy = []
      produce = []
      prod = [ i for i in self.odoo_data('product.product', items.keys(), fields) ]
      item_update = []
      templates = { j['id']: j for j in self.odoo_data('product.template', [i['product_tmpl_id'][0] for i in prod], fields2) }
      for i in prod:
        item = items.get(i['id'],None)
        if not item: continue
        tmpl = templates.get(i['product_tmpl_id'][0],None)
        if tmpl and tmpl['purchase_ok'] and tmpl['supply_method'] == 'buy':
          buy.append( (tmpl['produce_delay'] * 86400, item) )
        else:
          produce.append( (item,) )
        if tmpl:
          item_update.append( (tmpl['list_price'] * self.uom.get(tmpl['uom_id'][0],1),item,) )

      # Get recently changed reorderpoints
      ids = self.odoo_search('stock.warehouse.orderpoint',
        ['|',('create_date','>', self.delta),('write_date','>', self.delta),
         '|',('active', '=', 1),('active', '=', 0)])
      fields = ['active', 'warehouse_id', 'product_id', 'product_min_qty', 'product_max_qty', 'product_uom', 'qty_multiple']
      orderpoints = []
      for i in self.odoo_data('stock.warehouse.orderpoint', ids, fields):
        if i['active']:
          uom_factor = self.uom.get(i['product_uom'][0],1.0)
          orderpoints.append( (i['product_min_qty']*uom_factor, i['product_max_qty']*uom_factor,
            i['qty_multiple']*uom_factor, i['product_id'][1], i['warehouse_id'][1]) )
        else:
          orderpoints.append( (None, None, None, i['product_id'][1], i['warehouse_id'][1]) )

      # Update the frePPLe buffers
      cursor.execute("update buffer set type=null where subcategory = 'odoo'")
      cursor.executemany(
        "update buffer \
          set type= 'procure', leadtime=%%s, lastmodified='%s' \
          where item_id=%%s and subcategory='odoo'" % self.date,
        buy)
      cursor.executemany(
        "update buffer \
          set type='default', lastmodified='%s' \
          where item_id=%%s and subcategory='odoo'" % self.date,
        produce)
      cursor.executemany(
        "update buffer \
          set min_inventory=%s, max_inventory=%s, size_multiple=%s \
          where item_id=%s and location_id=%s and subcategory='odoo'",
        orderpoints
        )
      cursor.executemany(
        "update item set price=%s where name=%s",
        item_update
        )
      transaction.commit(using=self.database)
      if self.verbosity > 0:
        print("Updated buffers for %d procured items" % len(buy))
        print("Updated buffers for %d produced items" % len(produce))
        print("Updated reorderpoints for %d procured buffers" % len(orderpoints))
        print("Imported policies and reorderpoints in %.2f seconds" % (time() - starttime))
    except Exception as e:
      transaction.rollback(using=self.database)
      logger.error("Error importing policies and reorderpoints", exc_info=1)
      raise CommandError("Error importing policies and reorderpoints: %s" % e)
    finally:
      transaction.commit(using=self.database)
      transaction.leave_transaction_management(using=self.database)


  # Importing manufacturing orders
  #   - Extracting all mrp.production objects from odoo, except the ones in
  #     "draft" status.
  #   - mapped fields mrp.production odoo -> frePPLe operationplan
  #        - %state -> filter where state != 'draft'
  #        - %id + 1000000 -> identifier
  #        - %bom.id %bom.name @ %location_dest_id -> operation_id, which must already exist
  #        - %date_start if filled else %date_planned -> startdate and enddate
  #        - %product_qty * uom conversion -> quantity
  #        - "1" -> locked
  #
  # TODO More detailed WIP representation:
  #    - mrp_production
  #        |-> mrp_production_move_id
  #        |      |-> If stock moves has been executed, then set flowplan qty to 0 in frePPLe
  #        |-> mrp_production_workcenter_line
  #               |-> simplified model:
  #               |     if status is done, then set loadplan qty to 0 in frePPLe
  #               |-> detailed model:
  #                     if status is done, then skip that sequence step in the routing
  def import_manufacturingorders(self, cursor):
    transaction.enter_transaction_management(using=self.database)
    try:
      starttime = time()
      if self.verbosity > 0:
        print("Importing manufacturing orders...")

      # Get the list of existing operations and operationplans
      cursor.execute("SELECT id FROM operationplan")
      frepple_keys = set([ i[0] for i in cursor.fetchall()])
      cursor.execute("SELECT name FROM operation where subcategory='odoo'")
      operations = set([ i[0] for i in cursor.fetchall()])

      ids = self.odoo_search('mrp.production', [
        '|',('create_date','>', self.delta),('write_date','>', self.delta),
        ('state','!=','draft')
        ])
      fields = ['bom_id','date_start','date_planned','name','state','product_qty','product_uom','location_dest_id']
      update = []
      insert = []
      delete = []
      for i in self.odoo_data('mrp.production', ids, fields):
        identifier = i['id'] + 1000000   # Adding a million to distinguish POs and MOs
        if i['state'] in ('in_production','confirmed','ready') and i['bom_id']:
          # Open orders
          location = self.locations.get(i['location_dest_id'][0],None)
          operation = u'%d %s @ %s' % (i['bom_id'][0], i['bom_id'][1], location)
          try: startdate = datetime.strptime(i['date_start'] or i['date_planned'], '%Y-%m-%d %H:%M:%S')
          except Exception as e: startdate = None
          if not startdate or not location or not operation in operations:
            continue
          uom_factor = self.uom.get(i['product_uom'][0],1.0)
          if identifier in frepple_keys:
            update.append((
              operation,startdate,startdate,i['product_qty']*uom_factor,i['name'],identifier
              ))
          else:
            insert.append((
              identifier,operation,startdate,startdate,i['product_qty']*uom_factor,i['name']
              ))
        elif i['state'] in ('cancel','done'):
          # Closed orders
          if id in frepple_keys:
            delete.append( (identifier,) )
        elif i['bom_id']:
          print("Warning: ignoring unrecognized manufacturing order status %s" % i['state'])

      # Update the frePPLe operationplans
      cursor.executemany(
        "insert into operationplan \
          (id,operation_id,startdate,enddate,quantity,locked,source,lastmodified) \
          values(%%s,%%s,%%s,%%s,%%s,'1',%%s,'%s')" % self.date,
        insert
        )
      cursor.executemany(
        "update operationplan \
          set operation_id=%%s, startdate=%%s, enddate=%%s, quantity=%%s, locked='1', source=%%s, lastmodified='%s' \
          where id=%%s" % self.date,
        update)
      cursor.executemany(
        "delete from operationplan where id=%s",
        delete)
      transaction.commit(using=self.database)

      if self.verbosity > 0:
        print("Updated %d manufacturing orders" % len(update))
        print("Inserted %d new manufacturing orders" % len(insert))
        print("Deleted %d manufacturing orders" % len(delete))
        print("Imported manufacturing orders in %.2f seconds" % (time() - starttime))
    except Exception as e:
      transaction.rollback(using=self.database)
      logger.error("Error importing manufacturing orders", exc_info=1)
      raise CommandError("Error importing manufacturing orders: %s" % e)
    finally:
      transaction.commit(using=self.database)
      transaction.leave_transaction_management(using=self.database)

