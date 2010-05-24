#
# Copyright (C) 2010 by Johan De Taeye
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

        
@transaction.commit_manually
class Command(BaseCommand):
  help = "Loads data from an OpenERP instance into the frePPLe database"

  option_list = BaseCommand.option_list + (
      make_option('--user', dest='user', type='string',
        help='User running the command'),
      make_option('--openerp_user', action='store', dest='openerp_user',
        default='admin', help='OpenErp user name to connect'),
      make_option('--openerp_pwd', action='store', dest='openerp_password',
        default='admin', help='OpenErp password to connect'),
      make_option('--openerp_database', action='store', dest='openerp_db',
        default='openerp', help='OpenErp database instance to import from'),
      make_option('--openerp_url', action='store', dest='openerp_url',
        default='http://localhost:8069/', help='OpenERP XMLRPC connection URL'),
      make_option('--delta', action='store', dest='delta', type="float",
        default='3650', help='Number of days for which we extract changed OpenERP data'),
      make_option('--database', action='store', dest='database',
        default=DEFAULT_DB_ALIAS, help='Nominates the frePPLe database to load'),
  )

  requires_model_validation = False

  @transaction.autocommit
  def handle(self, **options):

    # Pick up the options
    if 'verbosity' in options: self.verbosity = int(options['verbosity'] or '1')
    else: self.verbosity = 1
    if 'user' in options: user = options['user']
    else: user = ''
    if 'openerp_user' in options: self.openerp_user = options['openerp_user']
    else: self.openerp_user = 'admin'
    if 'openerp_password' in options: self.openerp_password = options['openerp_password']
    else: self.openerp_password = 'admin'
    if 'openerp_db' in options: self.openerp_db = options['openerp_db']
    else: self.openerp_db = 'openerp'
    if 'openerp_url' in options: self.openerp_url = options['openerp_url']
    else: self.openerp_url = 'http://localhost:8069/'
    if 'delta' in options: self.delta = float(options['delta'] or '3650')
    else: self.delta = 3650
    self.date = datetime.now()
    self.delta = self.date - timedelta(days=self.delta)
    print self.delta
    if 'openerp_url' in options: self.openerp_url = options['openerp_url']
    else: self.openerp_url = 'http://localhost:8069/'
    if 'database' in options: database = options['database'] or DEFAULT_DB_ALIAS
    else: database = DEFAULT_DB_ALIAS      
    if not database in settings.DATABASES.keys():
      raise CommandError("No database settings known for '%s'" % database )
    
    try:      
      # Log in to the openerp server
      sock_common = xmlrpclib.ServerProxy (self.openerp_url + 'xmlrpc/common')
      self.uid = sock_common.login(self.openerp_db, self.openerp_user, self.openerp_password)
      
      # Connect to openerp server
      sock = xmlrpclib.ServerProxy(self.openerp_url + 'xmlrpc/object')

      # Create a database connection to the frePPLe database
      cursor = connections[database].cursor()
      
      # Sequentially load all data
      self.import_customers(sock, cursor)
      self.import_products(sock, cursor)
      self.import_locations(sock, cursor)
      self.import_salesorders(sock, cursor)
            
    except Exception, e:
      raise CommandError(e)    
      

  # Importing customers
  #   - extracting recently changed res.partner objects
  #   - meeting the criterion: 
  #        - %active = True
  #        - %customer = True
  #   - mapped fields OpenERP -> frePPLe
  #        - %id %name -> name
  #        - %ref     -> description
  #        - 'OpenERP' -> subcategory
  @transaction.commit_manually
  def import_customers(self, sock, cursor):  
    starttime = time()
    cursor.execute("SELECT name FROM customer")
    frepple_keys = set([ i[0] for i in cursor.fetchall()])
    ids = sock.execute(self.openerp_db, self.uid, self.openerp_password, 
      'res.partner', 'search', 
      ['|',('Create_date','>', self.delta),('write_date','>', self.delta)])
    fields = ['name', 'active', 'customer', 'ref']
    if self.verbosity > 0:
      print "Importing customers..."
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
    cursor.executemany(
      "delete from customer where name=%s",
      delete)
    transaction.commit()
    if self.verbosity > 0:
      print "Inserted %d new customers" % len(insert)
      print "Updated %d existing customers" % len(update)
      print "Deleted %d customers" % len(delete)
      print "Imported customers in %.2f seconds" % (time() - starttime)
      
      
  # Importing products
  #   - extracting recently changed product.product objects
  #   - meeting the criterion: 
  #        - %active = True
  #   - mapped fields OpenERP -> frePPLe
  #        - %id %name -> name
  #        - %code     -> description
  #        - 'OpenERP' -> subcategory
  @transaction.commit_manually
  def import_products(self, sock, cursor):  
    starttime = time()
    cursor.execute("SELECT name FROM item")
    frepple_keys = set([ i[0] for i in cursor.fetchall()])
    ids = sock.execute(self.openerp_db, self.uid, self.openerp_password, 
      'product.product', 'search', 
      ['|',('Create_date','>', self.delta),('write_date','>', self.delta)])
    fields = ['name', 'code', 'active']
    if self.verbosity > 0:
      print "Importing products..."
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
    cursor.executemany(
      "delete from item where name=%s",
      delete)
    transaction.commit()
    if self.verbosity > 0:
      print "Inserted %d new products" % len(insert)
      print "Updated %d existing products" % len(update)
      print "Deleted %d products" % len(delete)
      print "Imported products in %.2f seconds" % (time() - starttime)

    
  # Importing locations
  #   - extracting recently changed stock.location objects
  #   - meeting the criterion: 
  #        - %active = True
  #        - %usage = 'internal'
  #   - mapped fields OpenERP -> frePPLe
  #        - %id %name -> name
  #        - 'OpenERP' -> subcategory
  @transaction.commit_manually
  def import_locations(self, sock, cursor):  
    starttime = time()
    cursor.execute("SELECT name FROM location")
    frepple_keys = set([ i[0] for i in cursor.fetchall()])
    ids = sock.execute(self.openerp_db, self.uid, self.openerp_password, 
      'stock.location', 'search', 
      ['|',('Create_date','>', self.delta),('write_date','>', self.delta)])
    fields = ['name', 'usage', 'active']
    if self.verbosity > 0:
      print "Importing locations..."
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
    cursor.executemany(
      "delete from location where name=%s",
      delete)
    transaction.commit()
    if self.verbosity > 0:
      print "Inserted %d new locations" % len(insert)
      print "Updated %d existing locations" % len(update)
      print "Deleted %d locations" % len(delete)
      print "Imported locations in %.2f seconds" % (time() - starttime)

    
  # Importing sales orders
  #   - extracting recently changed sales.order and sales.order.line objects
  #   - meeting the criterion: 
  #        - %sol_state = 'confirmed'
  #   - mapped fields OpenERP -> frePPLe
  #        - %sol_id %so_name %sol_sequence -> name
  #        - %sol_product_uom_qty -> quantity
  #        - %sol_product_id -> item
  #        - %so_partner_id -> customer
  #        - %so_date_order -> due
  #        - 'OpenERP' -> subcategory
  #        - 1 -> priority
  @transaction.commit_manually
  def import_salesorders(self, sock, cursor):  
    starttime = time()
    cursor.execute("SELECT name FROM demand")
    frepple_keys = set([ i[0] for i in cursor.fetchall()])
    ids = sock.execute(self.openerp_db, self.uid, self.openerp_password, 
      'sale.order.line', 'search', 
      ['|',('Create_date','>', self.delta),('write_date','>', self.delta)])
    fields = ['sequence', 'state', 'type', 'product_id', 'product_uom_qty', 'product_uom', 'order_id']
    fields2 = ['partner_id', 'date_order', ]
    if self.verbosity > 0:
      print "Importing sales orders..."
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
    cursor.executemany(
      "delete from demand where name=%s",
      delete)
    transaction.commit()
    if self.verbosity > 0:
      print "Inserted %d new sales orders" % len(insert)
      print "Updated %d existing sales orders" % len(update)
      print "Deleted %d sales orders" % len(delete)
      print "Imported sales orders in %.2f seconds" % (time() - starttime)
 
  # Load workcenters
  # Load onhand
  # Load open purchase orders
  # Load operations / routings    
  # Load buffers
  # Load reorder points      
  # Load flows       
  # Load loads    
  # Load WIP
  