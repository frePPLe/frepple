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
from django.utils.translation import ugettext as _

from freppledb.input.models import Parameter
from freppledb.execute.models import log
        
      
class Command(BaseCommand):
  help = "Uploads planning results from frePPle into an OpenERP instance"

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
      #self.export_mrp(sock, cursor)
      
      # Logging message
      log(category='EXPORT', theuser=user,
        message=_('Finished exporting to OpenERP')).save(using=self.database)
      
    except Exception, e:
      log(category='EXPORT', theuser=user,
        message=u'%s: %s' % (_('Failed exporting to OpenERP'),e)).save(using=self.database)
      raise CommandError(e)    
    finally:
      transaction.commit(using=self.database)
      settings.DEBUG = tmp_debug
      transaction.leave_transaction_management(using=self.database)
      

  # Upload MRP work order data
  #   - extracting recently changed res.partner objects
  #   - meeting the criterion: 
  #        - %active = True
  #        - %customer = True
  #   - mapped fields OpenERP -> frePPLe customer
  #        - %id %name -> name
  #        - %ref     -> description
  #        - 'OpenERP' -> subcategory
  def export_mrp(self, sock, cursor):  
    # Performance test: created 10000 partners in 22m44s, 7.3 per second
    # Bottleneck is openerp server, not the db at all
    # cnt = 1
    # print datetime.now()
    # while cnt < 10000:
    #   partner = {
    #      'name': 'customer %d' % cnt,
    #      'active': True,
    #      'customer': True,
    #   }
    #   partner_id = sock.execute(self.openerp_db, self.uid, self.openerp_password, 'res.partner', 'create', partner)
    #   cnt += 1
    # print datetime.now()
    transaction.enter_transaction_management(using=self.database)
    transaction.managed(True, using=self.database)
    try:
      starttime = time()
      if self.verbosity > 0:
        print "Exporting MRP work orders..."
      cursor.execute("SELECT name FROM customer")
      frepple_keys = set([ i[0] for i in cursor.fetchall()])
      ids = sock.execute(self.openerp_db, self.uid, self.openerp_password, 
        'res.partner', 'search', 
        ['|',('Create_date','>', self.delta),('write_date','>', self.delta)])
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
      cursor.executemany(
        "delete from customer where name=%s",
        delete)
      transaction.commit(using=self.database)
      if self.verbosity > 0:
        print "Inserted %d new customers" % len(insert)
        print "Updated %d existing customers" % len(update)
        print "Deleted %d customers" % len(delete)
        print "Imported customers in %.2f seconds" % (time() - starttime)
    except Exception, e:
      transaction.rollback(using=self.database)
      print "Error exporting MRP work orders: %s" % e
    finally:
      transaction.commit(using=self.database)
      transaction.leave_transaction_management(using=self.database)
                       