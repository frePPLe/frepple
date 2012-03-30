#
# Copyright (C) 2010-2012 by Johan De Taeye, frePPLe bvba
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
    # When it is set, the django database wrapper collects a list of all sql
    # statements executed and their timings. This consumes plenty of memory
    # and cpu time.
    tmp_debug = settings.DEBUG
    settings.DEBUG = False
    
    transaction.enter_transaction_management(using=self.database)
    transaction.managed(True, using=self.database)
    try:
      # Logging message
      log(category='EXPORT', theuser=user,
        message=_('Start exporting to OpenERP')).save(using=self.database)
      transaction.commit(using=self.database)

      # Log in to the openerp server
      sock_common = xmlrpclib.ServerProxy(self.openerp_url + 'xmlrpc/common')
      self.uid = sock_common.login(self.openerp_db, self.openerp_user, self.openerp_password)
      
      # Connect to openerp server
      sock = xmlrpclib.ServerProxy(self.openerp_url + 'xmlrpc/object')

      # Create a database connection to the frePPLe database
      cursor = connections[self.database].cursor()
      
      # Upload all data
      self.export_mrp(sock, cursor)
      
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
      
            
  # Upload MRP work order data
  #   - uploading frePPLe operationplans
  #   - meeting the criterion: 
  #        - %active = True
  #        - %customer = True
  #   - mapped fields OpenERP -> frePPLe customer
  #        - %id %name -> name
  #        - %ref     -> description
  #        - 'OpenERP' -> subcategory
  # TODO Delete/net previous workorders
  # TODO XML-RPC interface is too slow! Instead, write to a file and code in the OpenERP module to import and confirm the orders
  def export_mrp(self, sock, cursor):  
    transaction.enter_transaction_management(using=self.database)
    transaction.managed(True, using=self.database)
    try:
      starttime = time()
      if self.verbosity > 0:
        print "Exporting MRP work orders..."      
      cursor.execute('''SELECT id, operation, quantity, startdate, enddate   
         FROM out_operationplan, operation
         WHERE out_operationplan.operation = operation.name
         AND operation.subcategory = 'OpenERP'
         AND out_operationplan.owner is null
         ''')
      cnt = 0    
      for i, j, k, l in cursor.fetchall():
        print i,j,k,l
        mrp_proc = {
          'name': i,
          'date_planned': l.strftime('%Y-%m-%d'),
          'product_id': 1, #  TODO WHICH PRODUCT ID to use here
          'product_qty': k,
          'product_uom': 1, # This assumes PCE...
          'location_id': 1, # TODO WHICH LOCATION ID to use here
          'procure_method': 'make_to_order',
          'origin': 'frePPLe'
        }
        mrp_proc_id = sock.execute(self.openerp_db, self.uid, self.openerp_password, 'mrp.procurement', 'create', mrp_proc)
        cnt += 1
      transaction.commit(using=self.database)
      if self.verbosity > 0:
        print "Uploaded %d MRP work orders" % cnt
    except Exception as e:
      transaction.rollback(using=self.database)
      print "Error exporting MRP work orders: %s" % e
    finally:
      transaction.commit(using=self.database)
      transaction.leave_transaction_management(using=self.database)


#bin\addons\mrp\mrp.py
#bin\addons\mrp\schedulers.py
#
#_procure_confirm:
#For each mrp.procurement where state = 'confirmed' 
#and procure_method 'make to order' and date_planned < scheduling window
#  'check' button
#        
#_procure_orderpoint_confirm:
#  if automatic: self.create_automatic_op(cr, uid, context=context)
#  for all defined order points
#    if virtual onhand < minimum at this location
#              qty = max(op.product_min_qty, op.product_max_qty)-prods
#              reste = qty % op.qty_multiple
#              if reste > 0:
#                  qty += op.qty_multiple - reste
#              newdate = DateTime.now() + DateTime.RelativeDateTime(
#                      days=int(op.product_id.seller_delay))
#              if op.product_id.supply_method == 'buy':
#                  location_id = op.warehouse_id.lot_input_id
#              elif op.product_id.supply_method == 'produce':
#                  location_id = op.warehouse_id.lot_stock_id
#              else:
#                  continue
#              if qty <= 0:
#                  continue
#              if op.product_id.type not in ('consu'):
#                  proc_id = procurement_obj.create(cr, uid, {
#                      'name': 'OP:' + str(op.id),
#                      'date_planned': newdate.strftime('%Y-%m-%d'),
#                      'product_id': op.product_id.id,
#                      'product_qty': qty,
#                      'product_uom': op.product_uom.id,
#                      'location_id': op.warehouse_id.lot_input_id.id,
#                      'procure_method': 'make_to_order',
#                      'origin': op.name
#                  })
#         wf_service.trg_validate(uid, 'mrp.procurement', proc_id,'button_confirm', cr)    
#              State changes from 'draft' to 'confirmed'
#              Confirmed status creates stock moves, and recursively creates extra mrp.procurement records
#         wf_service.trg_validate(uid, 'mrp.procurement', proc_id, 'button_check', cr)
#         orderpoint_obj.write(cr, uid, [op.id], {'procurement_id': proc_id})     WHY???? WHER USED???
#
#create_automatic_op:
#For each product & warehouse combination
#  if virtual inventory < 0
#    create mrp.procurement with
#        if product.supply_method == 'buy':
#            location_id = warehouse.lot_input_id.id
#        elif product.supply_method == 'produce':
#            location_id = warehouse.lot_stock_id.id
#        else:
#            continue
#        proc_id = proc_obj.create(cr, uid, {
#            'name': 'Automatic OP: %s' % product.name,
#            'origin': 'SCHEDULER',
#            'date_planned': newdate.strftime('%Y-%m-%d %H:%M:%S'),
#            'product_id': product.id,
#            'product_qty': -product.virtual_available,
#            'product_uom': product.uom_id.id,
#            'location_id': location_id,
#            'procure_method': 'make_to_order',
#            })
#    wf_service.trg_validate(uid, 'mrp.procurement', proc_id, 'button_confirm', cr)   (State changes from 'draft' to 'confirmed')
#    wf_service.trg_validate(uid, 'mrp.procurement', proc_id, 'button_check', cr)
                       