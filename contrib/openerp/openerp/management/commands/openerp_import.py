#
# Copyright (C) 2010-2011 by Johan De Taeye, frePPLe bvba
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
# Foundation Inc., 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301 USA
#

#  file     : $URL$
#  revision : $LastChangedRevision$  $LastChangedBy$
#  date     : $LastChangedDate$

from optparse import make_option
import xmlrpclib
from datetime import datetime, timedelta
from time import time

from django.core.management.base import BaseCommand, CommandError
from django.db import transaction, connections, DEFAULT_DB_ALIAS
from django.template.loader import render_to_string
from django.conf import settings
from django.utils.translation import ugettext as _

from freppledb.input.models import Parameter
from freppledb.execute.models import log
        
      
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
      except Exception, e:
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
      sock = xmlrpclib.ServerProxy(self.openerp_url + 'xmlrpc/object')

      # Create a database connection to the frePPLe database
      cursor = connections[self.database].cursor()
      
      # Sequentially load all data
      self.import_customers(sock, cursor)
      self.import_products(sock, cursor)
      self.import_locations(sock, cursor)
      self.import_salesorders(sock, cursor)
      self.import_workcenters(sock, cursor)
      self.import_onhand(sock, cursor)
      self.import_purchaseorders(sock, cursor)
      self.import_boms(sock, cursor)
      self.import_setupmatrices(sock, cursor)
      
      # Logging message
      log(category='IMPORT', theuser=user,
        message=_('Finished importing from OpenERP')).save(using=self.database)
      
    except Exception, e:
      log(category='IMPORT', theuser=user,
        message=u'%s: %s' % (_('Failed importing from OpenERP'),e)).save(using=self.database)
      raise CommandError(e)    
    finally:
      transaction.commit(using=self.database)
      settings.DEBUG = tmp_debug
      transaction.leave_transaction_management(using=self.database)
      

  # Importing customers
  #   - extracting recently changed res.partner objects
  #   - meeting the criterion: 
  #        - %active = True
  #        - %customer = True
  #   - mapped fields OpenERP -> frePPLe customer
  #        - %id %name -> name
  #        - %ref     -> description
  #        - 'OpenERP' -> subcategory
  def import_customers(self, sock, cursor):  
    transaction.enter_transaction_management(using=self.database)
    transaction.managed(True, using=self.database)
    try:
      starttime = time()
      if self.verbosity > 0:
        print "Importing customers..."
      cursor.execute("SELECT name FROM customer")
      frepple_keys = set([ i[0] for i in cursor.fetchall()])
      print self.delta
      ids = sock.execute(self.openerp_db, self.uid, self.openerp_password, 
        'res.partner', 'search', 
        ['|',('Create_date','>', self.delta),('write_date','>', self.delta),
         '|',('active', '=', 1),('active', '=', 0)])
      fields = ['name', 'active', 'customer', 'ref']
      insert = []
      update = []
      delete = []
      for i in sock.execute(self.openerp_db, self.uid, self.openerp_password, 'res.partner', 'read', ids, fields):
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
           i['ref']
         ) for i in insert
        ])
      cursor.executemany(
        "update customer \
          set description=%%s, subcategory='OpenERP',lastmodified='%s' \
          where name=%%s" % self.date,
        [(
           i['ref'],
           u'%d %s' % (i['id'],i['name'])
         ) for i in update
        ])
      for i in delete:
        try: cursor.execute("delete from customer where name=%s",i)
        except: 
          # Delete fails when there are dependent records in the database.
          cursor.execute("update customer set subcategory = null where name=%s",i)
      transaction.commit(using=self.database)
      if self.verbosity > 0:
        print "Inserted %d new customers" % len(insert)
        print "Updated %d existing customers" % len(update)
        print "Deleted %d customers" % len(delete)
        print "Imported customers in %.2f seconds" % (time() - starttime)
    except Exception, e:
      transaction.rollback(using=self.database)
      print "Error importing customers: %s" % e
    finally:
      transaction.commit(using=self.database)
      transaction.leave_transaction_management(using=self.database)
      
      
  # Importing products
  #   - extracting recently changed product.product objects
  #   - meeting the criterion: 
  #        - %active = True
  #   - mapped fields OpenERP -> frePPLe item
  #        - %id %name -> name
  #        - %code     -> description
  #        - 'OpenERP' -> subcategory
  # TODO also get template.produce_delay? 
  def import_products(self, sock, cursor):  
    transaction.enter_transaction_management(using=self.database)
    transaction.managed(True, using=self.database)
    try:
      starttime = time()
      if self.verbosity > 0:
        print "Importing products..."
      cursor.execute("SELECT name FROM item")
      frepple_keys = set([ i[0] for i in cursor.fetchall()])
      ids = sock.execute(self.openerp_db, self.uid, self.openerp_password, 
        'product.product', 'search', 
        ['|',('Create_date','>', self.delta),('write_date','>', self.delta),
         '|',('active', '=', 1),('active', '=', 0)])
      fields = ['name', 'code', 'active', 'product_tmpl_id']
      insert = []
      update = []
      delete = []
      for i in sock.execute(self.openerp_db, self.uid, self.openerp_password, 'product.product', 'read', ids, fields):
        name = i['code'] and u'%d [%s] %s' % (i['id'], i['code'], i['name']) or u'%d %s' % (i['id'], i['name'])
        if i['active']:
          if name in frepple_keys:
            update.append(i)
          else:
            insert.append(i)
        elif name in frepple_keys:
          delete.append( (name,) )
      cursor.executemany(
        "insert into item \
          (name,description,subcategory,lastmodified) \
          values (%%s,%%s,'OpenERP','%s')" % self.date,
        [(
           i['code'] and u'%d [%s] %s' % (i['id'], i['code'], i['name']) or u'%d %s' % (i['id'], i['name']),
           i['code'] or None
         ) for i in insert
        ])
      cursor.executemany(
        "update item \
          set description=%%s, subcategory='OpenERP', lastmodified='%s' \
          where name=%%s" % self.date,
        [(
           i['code'] or None,
           i['code'] and u'%d [%s] %s' % (i['id'], i['code'], i['name']) or u'%d %s' % (i['id'], i['name'])
         ) for i in update
        ])
      for i in delete:
        try: cursor.execute("delete from item where name=%s",i)
        except: 
          # Delete fails when there are dependent records in the database.
          cursor.execute("update item set subcategory = null where name=%s",i)
      transaction.commit(using=self.database)
      if self.verbosity > 0:
        print "Inserted %d new products" % len(insert)
        print "Updated %d existing products" % len(update)
        print "Deleted %d products" % len(delete)
        print "Imported products in %.2f seconds" % (time() - starttime)
    except Exception, e:
      transaction.rollback(using=self.database)
      print "Error importing products: %s" % e
    finally:
      transaction.commit(using=self.database)
      transaction.leave_transaction_management(using=self.database)

    
  # Importing locations
  #   - extracting recently changed stock.location objects
  #   - meeting the criterion: 
  #        - %active = True
  #        - %usage = 'internal'
  #   - mapped fields OpenERP -> frePPLe location
  #        - %id %name -> name
  #        - 'OpenERP' -> subcategory
  def import_locations(self, sock, cursor):  
    transaction.enter_transaction_management(using=self.database)
    transaction.managed(True, using=self.database)
    try:
      starttime = time()
      if self.verbosity > 0:
        print "Importing locations..."
      cursor.execute("SELECT name FROM location")
      frepple_keys = set([ i[0] for i in cursor.fetchall()])
      ids = sock.execute(self.openerp_db, self.uid, self.openerp_password, 
        'stock.location', 'search', 
        ['|',('Create_date','>', self.delta),('write_date','>', self.delta),
         '|',('active', '=', 1),('active', '=', 0)])
      fields = ['name', 'usage', 'active']
      insert = []
      update = []
      delete = []
      for i in sock.execute(self.openerp_db, self.uid, self.openerp_password, 'stock.location', 'read', ids, fields):
        name = u'%d %s' % (i['id'],i['name'])
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
          cursor.execute("update location set subcategory = null where name=%s",i)
      transaction.commit(using=self.database)
      if self.verbosity > 0:
        print "Inserted %d new locations" % len(insert)
        print "Updated %d existing locations" % len(update)
        print "Deleted %d locations" % len(delete)
        print "Imported locations in %.2f seconds" % (time() - starttime)
    except Exception, e:
      transaction.rollback(using=self.database)
      print "Error importing locations: %s" % e
    finally:
      transaction.commit(using=self.database)
      transaction.leave_transaction_management(using=self.database)
    
    
  # Importing sales orders
  #   - extracting recently changed sales.order and sales.order.line objects
  #   - meeting the criterion: 
  #        - %sol_state = 'confirmed'
  #   - mapped fields OpenERP -> frePPLe demand
  #        - %sol_id %so_name %sol_sequence -> name
  #        - %sol_product_uom_qty -> quantity
  #        - %sol_product_id -> item
  #        - %so_partner_id -> customer
  #        - %so_date_order -> due
  #        - 'OpenERP' -> subcategory
  #        - 1 -> priority
  def import_salesorders(self, sock, cursor):  
    transaction.enter_transaction_management(using=self.database)
    transaction.managed(True, using=self.database)
    try:
      starttime = time()
      if self.verbosity > 0:
        print "Importing sales orders..."
      cursor.execute("SELECT name FROM demand")
      frepple_keys = set([ i[0] for i in cursor.fetchall()])
      ids = sock.execute(self.openerp_db, self.uid, self.openerp_password, 
        'sale.order.line', 'search', 
        ['|',('Create_date','>', self.delta),('write_date','>', self.delta),
         '|',('active', '=', 1),('active', '=', 0)])
      fields = ['sequence', 'state', 'type', 'product_id', 'product_uom_qty', 'product_uom', 'order_id']
      fields2 = ['partner_id', 'date_order', ]
      insert = []
      update = []
      delete = []
      for i in sock.execute(self.openerp_db, self.uid, self.openerp_password, 'sale.order.line', 'read', ids, fields):
        name = u'%d %s %d' % (i['id'], i['order_id'][1], i['sequence'])
        if i['state'] == 'confirmed':
          j = sock.execute(self.openerp_db, self.uid, self.openerp_password, 'sale.order', 'read', [i['order_id'][0],], fields2)[0]
          if name in frepple_keys:
            update.append( (
              u'%s %s' % (i['product_id'][0], i['product_id'][1]),
              u'%s %s' % (j['partner_id'][0], j['partner_id'][1]),
              i['product_uom_qty'],
              j['date_order'],
              u'%d %s %d' % (i['id'], i['order_id'][1], i['sequence']),
              ) )
          else:
            insert.append( (
              u'%d %s %d' % (i['id'], i['order_id'][1], i['sequence']),
              u'%d %s' % (i['product_id'][0], i['product_id'][1]),
              u'%d %s' % (j['partner_id'][0], j['partner_id'][1]),
              i['product_uom_qty'],
              j['date_order'],
              ) )      
        elif name in frepple_keys:
          delete.append( (name,) )
      cursor.executemany(
        "insert into demand \
          (name,item_id,customer_id,quantity,due,priority,subcategory,lastmodified) \
          values (%%s,%%s,%%s,%%s,%%s,1,'OpenERP','%s')" % self.date,
        insert)
      cursor.executemany(
        "update demand \
          set item_id=%%s, customer_id=%%s, quantity=%%s, due=%%s, priority=1, subcategory='OpenERP', lastmodified='%s' \
          where name=%%s" % self.date,
        update)
      for i in delete:
        try: cursor.execute("delete from demand where name=%s",i)
        except: 
          # Delete fails when there are dependent records in the database.
          cursor.execute("update demand set subcategory = null where name=%s",i)
      transaction.commit(using=self.database)
      if self.verbosity > 0:
        print "Inserted %d new sales orders" % len(insert)
        print "Updated %d existing sales orders" % len(update)
        print "Deleted %d sales orders" % len(delete)
        print "Imported sales orders in %.2f seconds" % (time() - starttime)
    except Exception, e:
      transaction.rollback(using=self.database)
      print "Error importing sales orders: %s" % e
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
  # Concept:
  #  A bit surprising, but OpenERP doesn't assign a location to a workcenter. 
  #  We don't know where it is.
  #  You can always assign a location in frePPLe.
  #
  def import_workcenters(self, sock, cursor):  
    transaction.enter_transaction_management(using=self.database)
    transaction.managed(True, using=self.database)
    try:
      starttime = time()
      if self.verbosity > 0:
        print "Importing workcenters..."
      cursor.execute("SELECT name FROM resource")
      frepple_keys = set([ i[0] for i in cursor.fetchall()])
      ids = sock.execute(self.openerp_db, self.uid, self.openerp_password, 
        'mrp.workcenter', 'search', 
        ['|',('Create_date','>', self.delta),('write_date','>', self.delta),
         '|',('active', '=', 1),('active', '=', 0)])
      fields = ['name', 'active', 'costs_hour', 'capacity_per_cycle']
      insert = []
      update = []
      delete = []
      for i in sock.execute(self.openerp_db, self.uid, self.openerp_password, 'mrp.workcenter', 'read', ids, fields):
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
          cursor.execute("update resource set subcategory = null where name=%s",i)
      transaction.commit(using=self.database)
      if self.verbosity > 0:
        print "Inserted %d new workcenters" % len(insert)
        print "Updated %d existing workcenters" % len(update)
        print "Deleted %d workcenters" % len(delete)
        print "Imported workcenters in %.2f seconds" % (time() - starttime)
    except Exception, e:
      transaction.rollback(using=self.database)
      print "Error importing workcenters: %s" % e
    finally:
      transaction.commit(using=self.database)
      transaction.leave_transaction_management(using=self.database)


  # Importing onhand  
  #   - extracting all stock.report.prodlots objects
  #   - No filtering for latest changes, ie always complete extract
  #   - meeting the criterion: 
  #        - %name > 0
  #        - Location already mapped in frePPLe
  #        - Product already mapped in frePPLe
  #   - mapped fields OpenERP -> frePPLe buffer
  #        - %product_id %product_name @ %name -> name
  #        - %product_id %product_name -> item_id
  #        - %location_id %location_name -> location_id
  #        - %name -> quantity
  #        - 'OpenERP' -> subcategory
  def import_onhand(self, sock, cursor):  
    transaction.enter_transaction_management(using=self.database)
    transaction.managed(True, using=self.database)
    try:
      starttime = time()
      if self.verbosity > 0:
        print "Importing onhand..."
      cursor.execute("update buffer set onhand = 0 where subcategory = 'OpenERP'")
      cursor.execute("SELECT name FROM item")
      frepple_items = set([ i[0] for i in cursor.fetchall()])
      cursor.execute("SELECT name FROM location")
      frepple_locations = set([ i[0] for i in cursor.fetchall()])
      cursor.execute("SELECT name FROM buffer")
      frepple_keys = set([ i[0] for i in cursor.fetchall()])
      ids = sock.execute(self.openerp_db, self.uid, self.openerp_password, 
        'stock.report.prodlots', 'search',  
        [('name','>', 0),])
      fields = ['prodlot_id', 'location_id', 'name', 'product_id']
      insert = []
      update = []
      for i in sock.execute(self.openerp_db, self.uid, self.openerp_password, 'stock.report.prodlots', 'read', ids, fields):
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
           i['name'],
         ) for i in insert
        ])
      cursor.executemany(
        "update buffer \
          set onhand=%%s, subcategory='OpenERP', lastmodified='%s' \
          where name=%%s" % self.date,
        [(
           i['name'],
           u'%d %s @ %d %s' % (i['product_id'][0], i['product_id'][1], i['location_id'][0], i['location_id'][1]),
         ) for i in update
        ])
      transaction.commit(using=self.database)
      if self.verbosity > 0:
        print "Inserted onhand for %d new buffers" % len(insert)
        print "Updated onhand for %d existing buffers" % len(update)
        print "Imported onhand in %.2f seconds" % (time() - starttime)
    except Exception, e:
      transaction.rollback(using=self.database)
      print "Error importing onhand: %s" % e
    finally:
      transaction.commit(using=self.database)
      transaction.leave_transaction_management(using=self.database)
      
        
  # Load open purchase orders
  #   - extracting recently changed purchase.order.line objects
  #   - meeting the criterion: 
  #        - %product_id already exists in frePPLe
  #        - %location_id already exists in frePPLe
  #        - %state = 'approved'
  # Q: Should purchase orders in state 'draft' be shown in frePPLe?
  #   - mapped fields OpenERP -> frePPLe buffer
  #        - %id %name -> name
  #        - %cost_hour -> cost
  #        - 'OpenERP' -> subcategory
  #   - mapped fields OpenERP -> frePPLe operation
  #        - %id %name -> name
  #        - %cost_hour -> cost
  #        - 'OpenERP' -> subcategory
  #   - mapped fields OpenERP -> frePPLe flow
  #        - %id %name -> name
  #        - %cost_hour -> cost
  #        - 'OpenERP' -> subcategory
  #   - mapped fields OpenERP -> frePPLe operationplan
  #        - %id %name -> name
  #        - %cost_hour -> cost
  #        - 'OpenERP' -> subcategory
  # 
  # TODO Possible to update PO without touching the date on the PO-lines? Rework code?
  # TODO Operationplan id is not a good way to find a match
  def import_purchaseorders(self, sock, cursor): 
    
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
        print "Importing purchase orders..."
      cursor.execute("SELECT name FROM item")
      frepple_items = set([ i[0] for i in cursor.fetchall()])
      cursor.execute("SELECT name FROM location")
      frepple_locations = set([ i[0] for i in cursor.fetchall()])
      cursor.execute("SELECT id FROM operationplan")
      frepple_keys = set([ i[0] for i in cursor.fetchall()])        
      ids = sock.execute(self.openerp_db, self.uid, self.openerp_password, 
        'purchase.order.line', 'search', 
        ['|',('Create_date','>', self.delta),('write_date','>', self.delta)])                
      fields = ['name', 'date_planned', 'product_id', 'product_qty', 'order_id']
      fields2 = ['name', 'location_id', 'partner_id', 'state', 'received']
      insert = []
      delete = []
      update = []
      for i in sock.execute(self.openerp_db, self.uid, self.openerp_password, 'purchase.order.line', 'read', ids, fields):
        item = u'%d %s' % (i['product_id'][0], i['product_id'][1])   
        j = sock.execute(self.openerp_db, self.uid, self.openerp_password, 'purchase.order', 'read', [i['order_id'][0],], fields2)[0]
        location = u'%d %s' % (j['location_id'][0], j['location_id'][1])
        if location in frepple_locations and item in frepple_items and j['state'] == 'approved':
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
        "delete from operationplan where id = %s",
        delete)
      transaction.commit(using=self.database)
      if self.verbosity > 0:
        print "Inserted %d purchase orders" % len(insert)
        print "Updated %d purchase orders" % len(update)
        print "Deleted %d purchase orders" % len(delete)
        print "Imported purchase orders in %.2f seconds" % (time() - starttime)               
    except Exception, e:
      transaction.rollback(using=self.database)
      print "Error importing purchase orders: %s" % e
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
  #        - %routing_id is not empty 
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
  # Concepts: 
  #   OpenERP assigns a location to a BOM in 2 ways:
  #     - If the routing of the bom specifies a producing location, that's where the bom is.
  #     - If the routing is empty or it has no producing location, the bom is applied where 
  #       the order is (when the work order is created)
  #   The first type is created here.
  #   TODO The second type should be created when we map the sales orders to frePPLe.
  #   TODO Subcontracting boms are also of the second type. We need to create them at based on what?
  #
  def import_boms(self, sock, cursor):  
    transaction.enter_transaction_management(using=self.database)
    transaction.managed(True, using=self.database)
    try:
      starttime = time()
      if self.verbosity > 0:
        print "Importing bills of material..."
      # Pick up all manufacturing routings
      cursor.execute("SELECT name FROM location")
      frepple_locations = set([ i[0] for i in cursor.fetchall()])
      ids = sock.execute(self.openerp_db, self.uid, self.openerp_password, 
        'mrp.routing', 'search', [('location_id','!=',False),])
      openerp_mfg_routings = {}
      for i in sock.execute(self.openerp_db, self.uid, self.openerp_password, 
        'mrp.routing', 'read', ids, ['location_id',]):
          location = u'%s %s' % (i['location_id'][0], i['location_id'][1])
          if location in frepple_locations:
            openerp_mfg_routings[i['id']] = location
      # Pick up existing operations in frePPLe
      cursor.execute("SELECT name FROM operation")
      frepple_keys = set([ i[0] for i in cursor.fetchall()])
      # Loop over all manufacturing boms
      ids = sock.execute(self.openerp_db, self.uid, self.openerp_password, 
        'mrp.bom', 'search', 
        [('bom_id','=',False),'|',('Create_date','>', self.delta),('write_date','>', self.delta)])
      fields = ['name', 'active', 'product_qty','date_start','date_stop','product_efficiency',
        'product_id','routing_id','bom_id','type','method','sub_products','product_rounding']
      for i in sock.execute(self.openerp_db, self.uid, self.openerp_password, 'mrp.bom', 'read', ids, fields):
        if i['active'] and i['routing_id'] and i['routing_id'][0] in openerp_mfg_routings.keys():
          data.append(i)
      # Create operations
      insert = []
      update = []
      delete = []
      # Create buffers
      insert = []
      update = []
      delete = []
      #  name = u'%d %s' % (i['id'],i['name'])
      #  if i['active']:
      #    if name in frepple_keys:
      #      update.append(i)
      #    else:
      #      insert.append(i)
      #  elif name in frepple_keys:
      #    delete.append( (name,) )                   
      #cursor.executemany(
      #  "insert into resource \
      #    (name,cost,subcategory,lastmodified) \
      #    values (%%s,%%s,'OpenERP','%s')" % self.date,
      #  [(
      #     u'%d %s' % (i['id'],i['name']),
      #     i['costs_hour'] or 0,
      #   ) for i in insert
      #  ])
      #cursor.executemany(
      #  "update resource \
      #    set cost=%%s, subcategory='OpenERP', lastmodified='%s' \
      #    where name=%%s" % self.date,
      #  [(
      #     i['costs_hour'] or 0,
      #     u'%d %s' % (i['id'],i['name']),
      #   ) for i in update
      #  ])
      #cursor.executemany(
      #  "delete from resource where name=%s",
      #  delete)
      transaction.commit(using=self.database)
      if self.verbosity > 0:
        print "Inserted %d new bills of material" % len(insert)
        print "Updated %d existing bills of material" % len(update)
        print "Deleted %d bills of material" % len(delete)
        print "Imported bills of material in %.2f seconds" % (time() - starttime)
    except Exception, e:
      transaction.rollback(using=self.database)
      print "Error importing bills of material: %s" % e
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
  def import_setupmatrices(self, sock, cursor):  
    transaction.enter_transaction_management(using=self.database)
    transaction.managed(True, using=self.database)
    try:
      starttime = time()
      if self.verbosity > 0:
        print "Importing setup matrices..."
      cursor.execute("delete FROM setuprule")
      cursor.execute("delete FROM setupmatrix")
      
      # Get all setup matrices
      ids = sock.execute(self.openerp_db, self.uid, self.openerp_password, 
        'frepple.setupmatrix', 'search', ['|',('active', '=', 1),('active', '=', 0)])
      fields = ['name',]
      datalist = []
      for i in sock.execute(self.openerp_db, self.uid, self.openerp_password, 'frepple.setupmatrix', 'read', ids, fields):
        datalist.append((u'%d %s' % (i['id'],i['name']),))
      cursor.executemany(
        "insert into setupmatrix \
          (name,lastmodified) \
          values (%%s,'%s')" % self.date,
        datalist
        )
      if self.verbosity > 0:
        print "Inserted %d new setup matrices" % len(datalist)
      
      # Get all setup rules
      ids = sock.execute(self.openerp_db, self.uid, self.openerp_password, 
        'frepple.setuprule', 'search', [])
      fields = ['priority', 'fromsetup', 'tosetup', 'duration', 'cost', 'active', 'setupmatrix_id' ]
      cnt = 0
      datalist = []      
      for i in sock.execute(self.openerp_db, self.uid, self.openerp_password, 'frepple.setuprule', 'read', ids, fields):
        datalist.append( (cnt, i['priority'], u'%d %s' % (i['setupmatrix_id'][0],i['setupmatrix_id'][1]), i['fromsetup'], i['tosetup'], i['duration']*3600, i['cost']) )
        cnt += 1       
      cursor.executemany(
        "insert into setuprule \
          (id, priority, setupmatrix_id, fromsetup, tosetup, duration, cost, lastmodified) \
          values (%%s,%%s,%%s,%%s,%%s,%%s,%%s,'%s')" % self.date,
        datalist
        )               
      if self.verbosity > 0:
        print "Inserted %d new setup rules" % len(datalist)
        
      transaction.commit(using=self.database)        
    except Exception, e:
      try:
        if e.faultString.find("Object frepple.setupmatrix doesn't exist") >= 0:
          print "Warning importing setup matrices:"
          print "  The frePPLe add-on is not installed on your OpenERP server."
          print "  No setup matrices will be downloaded."
        else:
          print "Error importing setup matrices: %s" % e
      except:
        print "Error importing setup matrices: %s" % e
      transaction.rollback(using=self.database)
    finally:
      transaction.commit(using=self.database)
      transaction.leave_transaction_management(using=self.database)


# TODO:
#   - renaming an entity while its id stays the same is not handled right.
#   - Load bom components  
#   - Load reorder points      
#   - Load loads    
#   - Load WIP
                       