#
# Copyright (C) 2014 by Johan De Taeye, frePPLe bvba
#
# This library is free software; you can redistribute it and/or modify it
# under the terms of the GNU Affero General Public License as published
# by the Free Software Foundation; either version 3 of the License, or
#
# This library is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU Affero
# General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public
# License along with this program.  If not, see <http://www.gnu.org/licenses/>.
#

# TODO rename, which is rename of location, item, etc in openbravo will fail: The child objects are not renamed.


from __future__ import print_function
from optparse import make_option
import base64
from datetime import datetime, timedelta, date
from time import time
from xml.etree.cElementTree import iterparse
import httplib, urllib

from django.core.management.base import BaseCommand, CommandError
from django.db import transaction, connections, DEFAULT_DB_ALIAS
from django.conf import settings

from freppledb.common.models import Parameter
from freppledb.execute.models import Task


class Command(BaseCommand):

  help = "Loads data from an Openbravo instance into the frePPLe database"

  option_list = BaseCommand.option_list + (
      make_option('--user', dest='user', type='string',
        help='User running the command'),
      make_option('--delta', action='store', dest='delta', type="float",
        default='3650', help='Number of days for which we extract changed openbravo data'),
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
    self.delta = str(date.today() - timedelta(days=self.delta))

    # Pick up configuration parameters
    self.openbravo_user = Parameter.getValue("openbravo.user", self.database)
    self.openbravo_password = Parameter.getValue("openbravo.password", self.database)
    self.openbravo_host = Parameter.getValue("openbravo.host", self.database)

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
        if task.started or task.finished or task.status != "Waiting" or task.name != 'Openbravo import':
          raise CommandError("Invalid task identifier")
        task.status = '0%'
        task.started = now
      else:

        task = Task(name='Openbravo import', submitted=now, started=now, status='0%', user=user,
          arguments="--delta=%s" % self.delta)
      task.save(using=self.database)
      transaction.commit(using=self.database)

      # Create a database connection to the frePPLe database
      cursor = connections[self.database].cursor()

      # Dictionaries for the mapping between openbravo ids and frepple names
      self.customers = {}
      self.items = {}
      self.locations = {}
      self.resources = {}

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
      self.import_machines(cursor)
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
      #self.import_processplan(cursor)
      transaction.commit(using=self.database)
      task.status = '80%'
      task.save(using=self.database)

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


  def get_data(self, url):
    # Send the request
    webservice = httplib.HTTP(self.openbravo_host)
    webservice.putrequest("GET", url)
    webservice.putheader("Host", self.openbravo_host)
    webservice.putheader("User-Agent", "frePPLe-openbravo connector")
    webservice.putheader("Content-type", "text/html; charset=\"UTF-8\"")
    webservice.putheader("Content-length", "0")
    webservice.putheader("Authorization", "Basic %s" % base64.encodestring('%s:%s' % (self.openbravo_user, self.openbravo_password)).replace('\n', ''))
    webservice.endheaders()
    webservice.send('')

    # Get the response
    statuscode, statusmessage, header = webservice.getreply()
    if statuscode != httplib.OK:
      raise Exception(statusmessage)
    if self.verbosity > 2:
      res = webservice.getfile().read()
      print('Request: ', url)
      print('Response status: ', statuscode, statusmessage, header)
      print('Response content: ', res)
      conn = iter(iterparse(res, events=('start','end')))
    else:
      conn = iter(iterparse(webservice.getfile(), events=('start','end')))
    root = conn.next()[1]
    return conn, root


  # Importing customers
  #   - extracting recently changed BusinessPartner objects
  #   - meeting the criterion:
  #        - %active = True
  #        - %customer = True
  #   - mapped fields openbravo -> frePPLe customer
  #        - %searchKey %name -> name
  #        - %description -> description
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
        if i[1] == 'openbravo': self.customers[i[2]] = i[0]
        frepple_keys.add(i[0])
      insert = []
      update = []
      rename = []
      delete = []
      query = urllib.quote("updated>'%s' and customer=true" % self.delta)
      conn, root = self.get_data("/openbravo/ws/dal/BusinessPartner?where=%s&orderBy=name&includeChildren=false" % query)
      for event, elem in conn:
        if event != 'end' or elem.tag != 'BusinessPartner': continue
        searchkey = elem.find("searchKey").text
        name = elem.find("name").text
        unique_name = u'%s %s' % (searchkey, name)
        objectid = elem.get('id')
        description = elem.find("description").text
        active = elem.find("active").text
        if active:
          if unique_name in frepple_keys:
            # Already exists in frepple
            update.append( (description,objectid,unique_name) )
          elif objectid in self.customers:
            # Object previously exported from openbravo already, now renamed
            rename.append( (description,unique_name,objectid) )
          else:
            # Brand new object
            insert.append( (description,unique_name,objectid) )
          self.customers[objectid] = unique_name
        elif unique_name in frepple_keys:
          # Oject no longer active in openbravo
          delete.append( (unique_name,) )
        # Clean the XML hierarchy
        root.clear()

      cursor.executemany(
        "insert into customer \
          (description,name,source,subcategory,lastmodified) \
          values (%%s,%%s,%%s,'openbravo','%s')" % self.date,
        insert
        )
      cursor.executemany(
        "update customer \
          set description=%%s,source=%%s,subcategory='openbravo',lastmodified='%s' \
          where name=%%s" % self.date,
        update
        )
      cursor.executemany(
        "update customer \
          set description=%%s,name=%%s,lastmodified='%s' \
          where source=%%s and subcategory='openbravo'" % self.date,
        rename
        )
      for i in delete:
        try: cursor.execute("delete from customer where name=%s",i)
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
      print("Error importing customers: %s" % e)
    finally:
      transaction.commit(using=self.database)
      transaction.leave_transaction_management(using=self.database)


  # Importing products
  #   - extracting recently changed Product objects
  #   - meeting the criterion:
  #        - %active = True
  #   - mapped fields OpenERP -> frePPLe item
  #        - %searchKey %name -> name
  #        - %description -> description
  #        - %searchKey -> source
  #        - 'openbravo' -> subcategory
  def import_products(self, cursor):
    transaction.enter_transaction_management(using=self.database)
    try:
      starttime = time()
      if self.verbosity > 0:
        print("Importing products...")
      cursor.execute("SELECT name, subcategory, source FROM item")
      frepple_keys = set()
      for i in cursor.fetchall():
        if i[1] == 'openbravo': self.items[i[2]] = i[0]
        frepple_keys.add(i[0])
      query = urllib.quote("updated>'%s'" % self.delta)
      insert = []
      update = []
      rename = []
      delete = []
      conn, root = self.get_data("/openbravo/ws/dal/Product?where=%s&orderBy=name&includeChildren=false" % query)
      for event, elem in conn:
        if event != 'end' or elem.tag != 'Product': continue
        searchkey = elem.find("searchKey").text
        name = elem.find("name").text
        unique_name = u'%s %s' % (searchkey, name)
        description = elem.find("description").text
        active = elem.find("active").text
        objectid = elem.get('id')
        if active:
          if unique_name in frepple_keys:
            # Already exists in frepple
            update.append( (description,objectid,unique_name) )
          elif objectid in self.items:
            # Object previously exported from openbravo already, now renamed
            rename.append( (description,unique_name,objectid) )
          else:
            # Brand new object
            insert.append( (unique_name,description,objectid) )
          self.items[objectid] = unique_name
        elif unique_name in frepple_keys:
          delete.append( (unique_name,) )
        # Clean the XML hierarchy
        root.clear()

      cursor.executemany(
        "insert into item \
          (name,description,subcategory,source,lastmodified) \
          values (%%s,%%s,'openbravo',%%s,'%s')" % self.date,
        insert
        )
      cursor.executemany(
        "update item \
          set description=%%s, subcategory='openbravo', source=%%s, lastmodified='%s' \
          where name=%%s" % self.date,
        update
        )
      cursor.executemany(
        "update item \
          set description=%%s, name=%%s, lastmodified='%s' \
          where source=%%s and subcategory='openbravo'" % self.date,
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
      print("Error importing products: %s" % e)
    finally:
      transaction.commit(using=self.database)
      transaction.leave_transaction_management(using=self.database)


  # Importing locations
  #   - extracting warehouse objects
  #   - meeting the criterion:
  #        - %active = True
  #   - mapped fields OpenERP -> frePPLe location
  #        - %searchKey %name -> name
  #        - %searchKey -> category
  #        - 'openbravo' -> source
  def import_locations(self, cursor):
    transaction.enter_transaction_management(using=self.database)
    try:
      starttime = time()
      if self.verbosity > 0:
        print("Importing locations...")
      cursor.execute("SELECT name, subcategory, source FROM location")
      frepple_keys = set()
      for i in cursor.fetchall():
        if i[1] == 'openbravo': self.locations[i[2]] = i[0]
        frepple_keys.add(i[0])
      insert = []
      update = []
      rename = []
      delete = []
      query = urllib.quote("updated>'%s'" % self.delta)
      conn, root = self.get_data("/openbravo/ws/dal/Warehouse?where=%s&orderBy=name&includeChildren=false" % query)
      for event, elem in conn:
        if event != 'end' or elem.tag != 'Warehouse': continue
        searchkey = elem.find("searchKey").text
        name = elem.find("name").text
        unique_name = u'%s %s' % (searchkey, name)
        description = elem.find("description").text
        active = elem.find("active").text
        objectid = elem.get('id')
        if active:
          if unique_name in frepple_keys:
            update.append( (description,objectid,unique_name) )
          elif objectid in self.locations:
            rename.append( (description,unique_name,objectid) )
          else:
            insert.append( (description,objectid,unique_name) )
          self.locations[objectid] = unique_name
        elif name in frepple_keys:
          delete.append( (unique_name,) )
        # Clean the XML hierarchy
        root.clear()

      cursor.executemany(
        "insert into location \
          (description, source, subcategory, name, lastmodified) \
          values (%%s,%%s,'openbravo',%%s,'%s')" % self.date,
        insert
        )
      cursor.executemany(
        "update location \
          set description=%%s, subcategory='openbravo', source=%%s, lastmodified='%s' \
          where name=%%s" % self.date,
        update
        )
      cursor.executemany(
        "update location \
          set description=%%s, name=%%s, lastmodified='%s' \
          where source=%%s and subcategory='openbravo'" % self.date,
        rename
        )
      for i in delete:
        try: cursor.execute("delete from location where name=%s",i)
        except:
          # Delete fails when there are dependent records in the database.
          cursor.execute("update location set source=null, lastmodified='%s' where name=%%s" % self.date, i)
      transaction.commit(using=self.database)
      if self.verbosity > 0:
        print("Inserted %d new locations" % len(insert))
        print("Updated %d existing locations" % len(update))
        print("Renamed %d existing locations" % len(rename))
        print("Deleted %d locations" % len(delete))
        print("Imported locations in %.2f seconds" % (time() - starttime))
    except Exception as e:
      transaction.rollback(using=self.database)
      print("Error importing locations: %s" % e)
    finally:
      transaction.commit(using=self.database)
      transaction.leave_transaction_management(using=self.database)


  # Importing sales orders
  #   - Extracting recently changed order and orderline objects
  #   - meeting the criterion:
  #        - %sol_state = 'confirmed'
  #   - mapped fields openbravo -> frePPLe delivery operation
  #        - 'delivery %sol_product_id %sol_product_name from %loc' -> name
  #   - mapped fields openbravo -> frePPLe buffer
  #        - '%sol_product_id %sol_product_name @ %loc' -> name
  #   - mapped fields openbravo -> frePPLe delivery flow
  #        - 'delivery %sol_product_id %sol_product_name from %loc' -> operation
  #        - '%sol_product_id %sol_product_name @ %loc' -> buffer
  #        - quantity -> -1
  #        -  'start' -> type
  #   - mapped fields openbravo -> frePPLe demand
  #        - %sol_id %so_name %sol_sequence -> name
  #        - %sol_product_uom_qty -> quantity
  #        - %sol_product_id -> item
  #        - %so_partner_id -> customer
  #        - %so_requested_date or %so_date_order -> due
  #        - 'openbravo' -> source
  #        - 1 -> priority
  def import_salesorders(self, cursor):

    transaction.enter_transaction_management(using=self.database)
    try:
      starttime = time()
      deliveries = set()
      if self.verbosity > 0:
        print("Importing sales orders...")

      # Get the list of known demands in frePPLe
      cursor.execute("SELECT name FROM demand")
      frepple_keys = set([ i[0] for i in cursor.fetchall() ])

      # Get the list of sales order lines
      insert = []
      update = []
      deliveries = set()
      query = urllib.quote("updated>'%s' and salesOrder.salesTransaction=true" % self.delta)
      conn, root = self.get_data("/openbravo/ws/dal/OrderLine?where=%s&orderBy=salesOrder.creationDate&includeChildren=false" % query)
      for event, elem in conn:
        if event != 'end' or elem.tag != 'OrderLine': continue
        product = self.items.get(elem.find("product").get('id'), None)
        warehouse = self.locations.get(elem.find("warehouse").get('id'), None)
        businessPartner = self.customers.get(elem.find("businessPartner").get('id'), None)
        if not warehouse or not product or not businessPartner:
          # Product, customer or location are not known in frePPLe.
          # We assume that in that case you don't need to the demand either.
          continue
        objectid = elem.get('id')
        documentno = elem.find("salesOrder").get('identifier').split()[0]
        lineNo = elem.find("lineNo").text
        unique_name = "%s %s" % (documentno, lineNo)
        scheduledDeliveryDate = datetime.strptime(elem.find("scheduledDeliveryDate").text, '%Y-%m-%dT%H:%M:%S.%fZ')
        orderedQuantity = float(elem.find("orderedQuantity").text)
        deliveredQuantity = float(elem.find("deliveredQuantity").text)
        closed = deliveredQuantity >= orderedQuantity   # TODO Not the right criterion
        operation = u'ship %s from %s' % (product, warehouse)
        deliveries.update([(product,warehouse,operation,u'%s @ %s' % (product, warehouse)),])
        if unique_name in frepple_keys:
          update.append( (objectid, closed and orderedQuantity or orderedQuantity-deliveredQuantity,
              product, closed and 'closed' or 'open', scheduledDeliveryDate,
              businessPartner, operation, unique_name) )
        else:
          insert.append( (objectid, closed and orderedQuantity or orderedQuantity-deliveredQuantity,
              product, closed and 'closed' or 'open', scheduledDeliveryDate,
              businessPartner, operation, unique_name) )
          frepple_keys.add(unique_name)
        # Clean the XML hierarchy
        root.clear()

      # Create or update delivery operations
      cursor.execute("SELECT name FROM operation where name like 'ship %'")
      frepple_keys = set([ i[0] for i in cursor.fetchall()])
      cursor.executemany(
        "insert into operation \
          (name,location_id,subcategory,type,lastmodified) \
          values (%%s,%%s,'openbravo','fixed_time',%s')" % self.date,
        [ (i[2],i[1]) for i in deliveries if i[2] not in frepple_keys ])
      cursor.executemany(
        "update operation \
          set location_id=%%s, subcategory='openbravo', type='fixed_time', lastmodified='%s' where name=%%s" % self.date,
        [ (i[1],i[2]) for i in deliveries if i[2] in frepple_keys ])

      # Create or update delivery buffers
      cursor.execute("SELECT name FROM buffer")
      frepple_keys = set([ i[0] for i in cursor.fetchall()])
      cursor.executemany(
        "insert into buffer \
          (name,item_id,location_id,subcategory,lastmodified) \
          values(%%s,%%s,%%s,'openbravo','%s')" % self.date,
        [ (i[3],i[0],i[1]) for i in deliveries if i[3] not in frepple_keys ])
      cursor.executemany(
        "update buffer \
          set item_id=%%s, location_id=%%s, subcategory='openbravo', lastmodified='%s' where name=%%s" % self.date,
        [ (i[0],i[1],i[3]) for i in deliveries if i[3] in frepple_keys ])

      # Create or update flow on delivery operation
      cursor.execute("SELECT operation_id, thebuffer_id FROM flow")
      frepple_keys = set([ i for i in cursor.fetchall()])
      cursor.executemany(
        "insert into flow \
          (operation_id,thebuffer_id,quantity,type,source,lastmodified) \
          values(%%s,%%s,-1,'start','openbravo','%s')" % self.date,
        [ (i[2],i[3]) for i in deliveries if (i[2],i[3]) not in frepple_keys ])
      cursor.executemany(
        "update flow \
          set quantity=-1, type='start', source='openbravo', lastmodified='%s' where operation_id=%%s and thebuffer_id=%%s" % self.date,
        [ (i[2],i[3]) for i in deliveries if (i[2],i[3]) in frepple_keys ])

      # Create or update demands
      cursor.executemany(
        "insert into demand \
          (source, quantity, item_id, status, subcategory, due, customer_id, operation_id, name, priority, lastmodified) \
          values (%%s,%%s,%%s,%%s,'openbravo',%%s,%%s,%%s,%%s,0,'%s')" % self.date,
        insert
        )
      cursor.executemany(
        "update demand \
          set source=%%s, quantity=%%s, item_id=%%s, status=%%s, subcategory='openbravo', \
              due=%%s, customer_id=%%s, operation_id=%%s, lastmodified='%s' \
          where name=%%s" % self.date,
        update
        )

      if self.verbosity > 0:
        print("Created or updated %d delivery operations" % len(deliveries))
        print("Inserted %d new sales order lines" % len(insert))
        print("Updated %d existing sales order lines" % len(update))
        print("Imported sales orders in %.2f seconds" % (time() - starttime))
    except Exception as e:
      transaction.rollback(using=self.database)
      print("Error importing sales orders: %s" % e)
    finally:
      transaction.commit(using=self.database)
      transaction.leave_transaction_management(using=self.database)


  # Importing machines
  #   - extracting recently changed ManufacturingMachine objects
  #   - meeting the criterion:
  #        - %active = True
  #   - mapped fields openbravo -> frePPLe resource
  #        - %id %name -> name
  #        - %cost_hour -> cost
  #        - capacity_per_cycle -> maximum
  #        - 'openbravo' -> subcategory
  #   - A bit surprising, but OpenERP doesn't assign a location or company to
  #     a workcenter.
  #     You should assign a location in frePPLe to assure that the user interface
  #     working .
  #
  def import_machines(self, cursor):
    transaction.enter_transaction_management(using=self.database)
    try:
      starttime = time()
      if self.verbosity > 0:
        print("Importing machines...")
      cursor.execute("SELECT name, subcategory, source FROM resource")
      frepple_keys = set()
      for i in cursor.fetchall():
        if i[1] == 'openbravo': self.resources[i[2]] = i[0]
        frepple_keys.add(i[0])
      insert = []
      update = []
      rename = []
      delete = []
      query = urllib.quote("updated>'%s'" % self.delta)
      conn, root = self.get_data("/openbravo/ws/dal/ManufacturingMachine?where=%s&orderBy=name&includeChildren=false" % query)
      for event, elem in conn:
        if event != 'end' or elem.tag != 'ManufacturingMachine': continue
        unique_name = elem.get('identifier')
        objectid = elem.get('id')
        active = elem.find("active").text
        if active:
          if unique_name in frepple_keys:
            # Already exists in frepple
            update.append( (objectid,unique_name) )
          elif objectid in self.customers:
            # Object previously exported from openbravo already, now renamed
            rename.append( (unique_name,objectid) )
          else:
            # Brand new object
            insert.append( (unique_name,objectid) )
          self.resources[objectid] = unique_name
        elif unique_name in frepple_keys:
          # Oject no longer active in openbravo
          delete.append( (unique_name,) )
        # Clean the XML hierarchy
        root.clear()

      cursor.executemany(
        "insert into resource \
          (name,source,subcategory,lastmodified) \
          values (%%s,%%s,'openbravo','%s')" % self.date,
        insert
        )
      cursor.executemany(
        "update resource \
          set source=%%s,subcategory='openbravo',lastmodified='%s' \
          where name=%%s" % self.date,
        update
        )
      cursor.executemany(
        "update resource \
          set name=%%s,lastmodified='%s' \
          where source=%%s and subcategory='openbravo'" % self.date,
        rename
        )
      for i in delete:
        try: cursor.execute("delete from resource where name=%s",i)
        except:
          # Delete fails when there are dependent records in the database.
          cursor.execute("update resource set source=null, subcategory=null, lastmodified='%s' where name=%%s" % self.date,i)
      transaction.commit(using=self.database)
      if self.verbosity > 0:
        print("Inserted %d new machines" % len(insert))
        print("Updated %d existing machines" % len(update))
        print("Renamed %d existing machines" % len(update))
        print("Deleted %d machines" % len(delete))
        print("Imported machines in %.2f seconds" % (time() - starttime))
    except Exception as e:
      transaction.rollback(using=self.database)
      print("Error importing machines: %s" % e)
    finally:
      transaction.commit(using=self.database)
      transaction.leave_transaction_management(using=self.database)


  # Importing onhand
  #   - extracting all MaterialMgmtStorageDetail objects
  #   - No filtering for latest changes, ie always complete extract
  #   - meeting the criterion:
  #        - %qty > 0
  #        - Location already mapped in frePPLe
  #        - Product already mapped in frePPLe
  #   - mapped fields openbravo -> frePPLe buffer
  #        - %product @ %locator.warehouse -> name
  #        - %product -> item_id
  #        - %locator.warehouse -> location_id
  #        - %qty -> onhand
  #        - 'openbravo' -> subcategory
  def import_onhand(self, cursor):
    transaction.enter_transaction_management(using=self.database)
    try:
      starttime = time()
      if self.verbosity > 0:
        print("Importing onhand...")

      # Get a mapping of all locators to their warehouse
      locators = {}
      conn, root = self.get_data("/openbravo/ws/dal/Locator")
      for event, elem in conn:
        if event != 'end' or elem.tag != 'Locator': continue
        warehouse = elem.find("warehouse").get('id')
        objectid = elem.get('id')
        locators[objectid] = warehouse
        root.clear()

      # Get the list of all current frepple records
      cursor.execute("SELECT name, subcategory FROM buffer")
      frepple_buffers = {}
      for i in cursor.fetchall():
        frepple_buffers[i[0]] = i[1]

      # Reset stock levels in all openbravo buffers
      cursor.execute("UPDATE buffer SET onhand=0, lastmodified='%s' WHERE subcategory='openbravo'" % self.date )

      # Get all stock values. NO incremental load here!
      insert = []
      increment = []
      update = []
      query = urllib.quote("quantityOnHand>0")
      conn, root = self.get_data("/openbravo/ws/dal/MaterialMgmtStorageDetail?where=%s" % query)
      for event, elem in conn:
        if event != 'end' or elem.tag != 'MaterialMgmtStorageDetail': continue
        onhand = elem.find("quantityOnHand").text
        locator = elem.find("storageBin").get('id')
        product = elem.find("product").get('id')
        item = self.items.get(product,None)
        location = self.locations.get(locators[locator], None)
        buffer_name = "%s @ %s" % (item, location)
        if buffer_name in frepple_buffers:
          if frepple_buffers[buffer_name] == 'openbravo':
            # Existing buffer marked as openbravo buffer
            increment.append( (onhand, buffer_name) )
          else:
            # Existing buffer marked as a non-openbravo buffer
            set.append( (onhand, buffer_name) )
            frepple_buffers[buffer_name] = 'openbravo'
        elif item != None and location != None:
          # New buffer
          insert.append( (buffer_name, self.items[product], self.locations[locators[locator]], onhand) )
          frepple_buffers[buffer_name] = 'openbravo'
        # Clean the XML hierarchy
        root.clear()

      cursor.executemany(
        "insert into buffer \
          (name,item_id,location_id,onhand,subcategory,lastmodified) \
          values(%%s,%%s,%%s,%%s,'openbravo','%s')" % self.date,
        insert)
      cursor.executemany(
        "update buffer \
          set onhand=%d, subcategory='openbravo' \
          where name=%s",
        update
        )
      cursor.executemany(
        "update buffer \
          set onhand=%s+onhand \
          where name=%s",
        increment
        )
      transaction.commit(using=self.database)
      if self.verbosity > 0:
        print("Inserted onhand for %d new buffers" % len(insert))
        print("Updated onhand for %d existing buffers" % len(update))
        print("Incremented onhand %d times for existing buffers" % len(increment))
        print("Imported onhand in %.2f seconds" % (time() - starttime))
    except Exception as e:
      transaction.rollback(using=self.database)
      print("Error importing onhand: %s" % e)
    finally:
      transaction.commit(using=self.database)
      transaction.leave_transaction_management(using=self.database)


  # Load open purchase orders
  #   - extracting recently changed orderline objects
  #   - meeting the criterion:
  #        - %product_id already exists in frePPLe
  #        - %location_id already exists in frePPLe
  #        - %state = 'approved' or 'draft'
  #   - mapped fields openbravo -> frePPLe buffer
  #        - %id %name -> name
  #        - 'openbravo' -> subcategory
  #   - mapped fields openbravo -> frePPLe operation
  #        - %id %name -> name
  #        - 'openbravo' -> subcategory
  #   - mapped fields openbravo -> frePPLe flow
  #        - %id %name -> name
  #        - 1 -> quantity
  #   - mapped fields openbravo -> frePPLe operationplan
  #        - %documentNo -> identifier
  #        - 'openbravo' -> subcategory
  def import_purchaseorders(self, cursor):
    return

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
      cursor.execute("SELECT name, subcategory FROM buffer")
      frepple_buffers = {}
      for i in cursor.fetchall():
        frepple_buffers[i[0]] = i[1]
      query = urllib.quote("salesTransaction=false and delivered=false")
      conn = self.get_data("/openbravo/ws/dal/Order?where=%s" % query)
      for i in conn.getElementsByTagName('Order'):
        onhand = elem.find("quantityOnHand").text
      return
#        locator = elem.find("storageBin")[0].attributes['id'].value
#        product = elem.find("product")[0].attributes['id'].value
#        item = self.items.get(product,None)
#        location = self.locations.get(locators[locator], None)
#        buffer_name = "%s @ %s" % (item, location)



      insert = []
      delete = []
      update = []
      for i in self.openerp_data('purchase.order.line'):
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
          (name,item_id,location_id,source,lastmodified) \
          values(%%s,%%s,%%s,'OpenERP','%s')" % self.date,
        [ i for i in newBuffers(insert) ]
        )
      cursor.executemany(
        "insert into operation \
          (name,location_id,source,lastmodified) \
          values(%%s,%%s,'OpenERP','%s')" % self.date,
        [ i for i in newOperations(insert) ]
        )
      cursor.executemany(
        "insert into flow \
          (operation_id,thebuffer_id,type,quantity,source,lastmodified) \
          values(%%s,%%s,'end',1,'OpenERP','%s')" % self.date,
        [ i for i in newFlows(insert) ]
        )
      cursor.executemany(
        "insert into operationplan \
          (id,operation_id,startdate,enddate,quantity,locked,source,lastmodified) \
          values(%%s,%%s,%%s,%%s,%%s,'1','OpenERP',%s')" % self.date,
        [ (i[3], i[0], i[1], i[1], i[2], ) for i in insert ]
        )
      cursor.executemany(
        "update operationplan \
          set operation_id=%%s, enddate=%%s, startdate=%%s, quantity=%%s, locked='1', source='OpenERP', lastmodified='%s' \
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
  def import_processplan(self, cursor):
    transaction.enter_transaction_management(using=self.database)
    try:
      starttime = time()
      if self.verbosity > 0:
        print("Importing bills of material...")

      query = urllib.quote("updated>'%s'" % self.delta)
      conn = self.get_data("/openbravo/ws/dal/ManufacturingProcessPlan?where=%s&orderBy=name&includeChildren=true" % query)
      for i in conn.getElementsByTagName('ManufacturingProcessPlan'):
        print(i)
      return

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
      print("Error importing bills of material: %s" % e)
    finally:
      transaction.commit(using=self.database)
      transaction.leave_transaction_management(using=self.database)

