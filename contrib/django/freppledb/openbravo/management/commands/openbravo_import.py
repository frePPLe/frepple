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
import httplib
import urllib
from StringIO import StringIO  # Note cStringIO doesn't handle unicode

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
      self.organizations = {}
      self.customers = {}
      self.items = {}
      self.locations = {}
      self.resources = {}
      self.locators = {}
      self.date = datetime.now()
      self.delta = str(date.today() - timedelta(days=self.delta))

      # Pick up the current date
      try:
        cursor.execute("SELECT value FROM common_parameter where name='currentdate'")
        d = cursor.fetchone()
        self.current = datetime.strptime(d[0], "%Y-%m-%d %H:%M:%S")
      except:
        self.current = datetime.now()

      # Sequentially load all data
      self.import_organizations(cursor)
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
      self.import_processplan(cursor)
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
    webservice.putheader("User-Agent", "frePPLe-Openbravo connector")
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
      conn = iter(iterparse(StringIO(res), events=('start','end')))
    else:
      conn = iter(iterparse(webservice.getfile(), events=('start','end')))
    root = conn.next()[1]
    return conn, root


  # Load a mapping of Openbravo organizations to their search key.
  # The result is used as a lookup in other interface where the
  # organization needs to be translated into a human readable form.
  #
  # If an organization is not present in the mapping dictionary, its
  # sales orders and purchase orders aren't mapped into frePPLe. This
  # can be used as a simple filter for some data.
  def import_organizations(self, cursor):
    transaction.enter_transaction_management(using=self.database)
    try:
      starttime = time()
      if self.verbosity > 0:
        print("Importing organizations...")
      conn = self.get_data("/openbravo/ws/dal/Organization?includeChildren=false")[0]
      count = 0
      for event, elem in conn:
        if event != 'end' or elem.tag != 'Organization': continue
        searchkey = elem.find("searchKey").text
        objectid = elem.get('id')
        self.organizations[objectid] = searchkey
        count += 1

      if self.verbosity > 0:
        print("Loaded %d organizations in %.2f seconds" % (count, time() - starttime))
    except Exception as e:
      transaction.rollback(using=self.database)
      raise CommandError("Error importing organizations: %s" % e)
    finally:
      transaction.commit(using=self.database)
      transaction.leave_transaction_management(using=self.database)


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
      count = 0
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
        count -= 1
        if self.verbosity > 0 and count < 0:
          count = 500
          print('.', end="")
      if self.verbosity > 0: print ('')

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
      raise CommandError("Error importing customers: %s" % e)
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
      count = 0
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
        count -= 1
        if self.verbosity > 0 and count < 0:
          count = 500
          print('.', end="")
      if self.verbosity > 0: print ('')

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
      raise CommandError("Error importing products: %s" % e)
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

      # Get existing locations
      cursor.execute("SELECT name, subcategory, source FROM location")
      frepple_keys = set()
      for i in cursor.fetchall():
        if i[1] == 'openbravo': self.locations[i[2]] = i[0]
        frepple_keys.add(i[0])

      # Get changes
      insert = []
      update = []
      rename = []
      delete = []
      query = urllib.quote("updated>'%s'" % self.delta)
      conn, root = self.get_data("/openbravo/ws/dal/Warehouse?where=%s&orderBy=name&includeChildren=false" % query)
      count = 0
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
        count -= 1
        if self.verbosity > 0 and count < 0:
          count = 500
          print('.', end="")
      if self.verbosity > 0: print ('')

      # Process changes
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

      # Get a mapping of all locators to their warehouse
      conn, root = self.get_data("/openbravo/ws/dal/Locator")
      for event, elem in conn:
        if event != 'end' or elem.tag != 'Locator': continue
        warehouse = elem.find("warehouse").get('id')
        objectid = elem.get('id')
        self.locators[objectid] = warehouse
        root.clear()

      transaction.commit(using=self.database)
      if self.verbosity > 0:
        print("Inserted %d new locations" % len(insert))
        print("Updated %d existing locations" % len(update))
        print("Renamed %d existing locations" % len(rename))
        print("Deleted %d locations" % len(delete))
        print("Imported locations in %.2f seconds" % (time() - starttime))
    except Exception as e:
      transaction.rollback(using=self.database)
      raise CommandError("Error importing locations: %s" % e)
    finally:
      transaction.commit(using=self.database)
      transaction.leave_transaction_management(using=self.database)


  # Importing sales orders
  #   - Extracting recently changed orderline objects
  #   - meeting the criterion:
  #        - %salesOrder.salesTransaction = true
  #   - mapped fields openbravo -> frePPLe delivery operation
  #        - 'Ship %product_searchkey %product_name @ %warehouse' -> name
  #   - mapped fields openbravo -> frePPLe buffer
  #        - '%product_searchkey %product_name @ %warehouse' -> name
  #   - mapped fields openbravo -> frePPLe delivery flow
  #        - 'Ship %product_searchkey %product_name @ %warehouse' -> operation
  #        - '%product_searchkey %product_name @ %warehouse' -> buffer
  #        - quantity -> -1
  #        -  'start' -> type
  #   - mapped fields openbravo -> frePPLe demand
  #        - %organization_searchkey %salesorder.documentno %lineNo -> name
  #        - if (%orderedQuantity > %deliveredQuantity, %orderedQuantity - %deliveredQuantity, %orderedQuantity) -> quantity
  #        - if (%orderedQuantity > %deliveredQuantity, 'open', 'closed') -> status
  #        - %sol_product_id -> item
  #        - %businessParnter.searchKey %businessParnter.name -> customer
  #        - %scheduledDeliveryDate -> due
  #        - 'openbravo' -> source
  #        - 1 -> priority
  # We assume that a lineNo is unique within an order. However, this is not enforced by Openbravo!
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
      query = urllib.quote("(updated>'%s' or salesOrder.updated>'%s') and salesOrder.salesTransaction=true" % (self.delta,self.delta))
      conn, root = self.get_data("/openbravo/ws/dal/OrderLine?where=%s&orderBy=salesOrder.creationDate&includeChildren=false" % query)
      count = 0
      for event, elem in conn:
        if event != 'end' or elem.tag != 'OrderLine': continue
        organization = self.organizations.get(elem.find("organization").get("id"), None)
        product = self.items.get(elem.find("product").get('id'), None)
        warehouse = self.locations.get(elem.find("warehouse").get('id'), None)
        businessPartner = self.customers.get(elem.find("businessPartner").get('id'), None)
        if not warehouse or not product or not businessPartner or not organization:
          # Product, customer, location or organization are not known in frePPLe.
          # We assume that in that case you don't need to the demand either.
          continue
        objectid = elem.get('id')
        documentno = elem.find("salesOrder").get('identifier').split()[0]
        lineNo = elem.find("lineNo").text
        unique_name = "%s %s %s" % (organization, documentno, lineNo)
        scheduledDeliveryDate = datetime.strptime(elem.find("scheduledDeliveryDate").text, '%Y-%m-%dT%H:%M:%S.%fZ')
        orderedQuantity = float(elem.find("orderedQuantity").text)
        deliveredQuantity = float(elem.find("deliveredQuantity").text)
        closed = deliveredQuantity >= orderedQuantity   # TODO Not the right criterion
        operation = u'Ship %s @ %s' % (product, warehouse)
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
        count -= 1
        if self.verbosity > 0 and count < 0:
          count = 500
          print('.', end="")
      if self.verbosity > 0: print ('')

      # Create or update delivery operations
      cursor.execute("SELECT name FROM operation where name like 'Ship %'")
      frepple_keys = set([ i[0] for i in cursor.fetchall()])
      cursor.executemany(
        "insert into operation \
          (name,location_id,subcategory,type,lastmodified) \
          values (%%s,%%s,'openbravo','fixed_time','%s')" % self.date,
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
      raise CommandError("Error importing sales orders: %s" % e)
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
      count = 0
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
        count -= 1
        if self.verbosity > 0 and count < 0:
          count = 500
          print('.', end="")
      if self.verbosity > 0: print ('')

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
        print("Renamed %d existing machines" % len(rename))
        print("Deleted %d machines" % len(delete))
        print("Imported machines in %.2f seconds" % (time() - starttime))
    except Exception as e:
      transaction.rollback(using=self.database)
      raise CommandError("Error importing machines: %s" % e)
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
      count = 0
      for event, elem in conn:
        if event != 'end' or elem.tag != 'MaterialMgmtStorageDetail': continue
        onhand = elem.find("quantityOnHand").text
        locator = elem.find("storageBin").get('id')
        product = elem.find("product").get('id')
        item = self.items.get(product,None)
        location = self.locations.get(self.locators[locator], None)
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
          insert.append( (buffer_name, self.items[product], self.locations[self.locators[locator]], onhand) )
          frepple_buffers[buffer_name] = 'openbravo'
        # Clean the XML hierarchy
        root.clear()
        count -= 1
        if self.verbosity > 0 and count < 0:
          count = 500
          print('.', end="")
      if self.verbosity > 0: print ('')

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
      raise CommandError("Error importing onhand: %s" % e)
    finally:
      transaction.commit(using=self.database)
      transaction.leave_transaction_management(using=self.database)


  # Load open purchase orders
  #   - extracting recently changed orderline objects
  #   - meeting the criterion:
  #        - %product already exists in frePPLe
  #        - %warehouse already exists in frePPLe
  #   - mapped fields openbravo -> frePPLe buffer
  #        - %product @ %warehouse -> name
  #        - %warehouse -> location
  #        - %product -> item
  #        - 'openbravo' -> subcategory
  #   - mapped fields openbravo -> frePPLe operation
  #        - 'Purchase ' %product ' @ ' %warehouse -> name
  #        - 'fixed_time' -> type
  #        - 'openbravo' -> subcategory
  #   - mapped fields openbravo -> frePPLe flow
  #        - 'Purchase ' %product ' @ ' %warehouse -> operation
  #        - %product ' @ ' %warehouse -> buffer
  #        - 1 -> quantity
  #        - 'end' -> type
  #   - mapped fields openbravo -> frePPLe operationplan
  #        - %documentNo -> identifier
  #        - 'Purchase ' %product ' @ ' %warehouse -> operation
  #        - %orderedQuantity - %deliveredQuantity -> quantity
  #        - %creationDate -> startdate
  #        - %scheduledDeliveryDate -> enddate
  #        - 'openbravo' -> source
  def import_purchaseorders(self, cursor):
    transaction.enter_transaction_management(using=self.database)
    try:
      starttime = time()
      if self.verbosity > 0:
        print("Importing purchase orders...")

      # Find all known operationplans in frePPLe
      cursor.execute("SELECT source FROM operationplan where source is not null and operation_id like 'Purchase %'")
      frepple_keys = set([ i[0] for i in cursor.fetchall()])
      cursor.execute("SELECT max(id) FROM operationplan")
      idcounter = cursor.fetchone()[0] or 1

      # Get the list of all open purchase orders
      insert = []
      update = []
      delete = []
      deliveries = set()
      query = urllib.quote("updated>'%s' and salesOrder.salesTransaction=false" % self.delta)
      conn, root = self.get_data("/openbravo/ws/dal/OrderLine?where=%s&orderBy=salesOrder.creationDate&includeChildren=false" % query)
      count = 0
      for event, elem in conn:
        if event != 'end' or elem.tag != 'OrderLine': continue
        product = self.items.get(elem.find("product").get('id'), None)
        warehouse = self.locations.get(elem.find("warehouse").get('id'), None)
        organization = self.organizations.get(elem.find("organization").get("id"), None)
        if not warehouse or not product or not organization:
          # Product, location or organization are not known in frePPLe.
          # We assume that in that case you don't need to the purchase order either.
          continue
        objectid = elem.get('id')
        scheduledDeliveryDate = datetime.strptime(elem.find("scheduledDeliveryDate").text, '%Y-%m-%dT%H:%M:%S.%fZ')
        creationDate = datetime.strptime(elem.find("creationDate").text, '%Y-%m-%dT%H:%M:%S.%fZ')
        orderedQuantity = float(elem.find("orderedQuantity").text)
        deliveredQuantity = float(elem.find("deliveredQuantity").text)
        operation = u'Purchase %s @ %s' % (product, warehouse)
        deliveries.update([(product,warehouse,operation,u'%s @ %s' % (product, warehouse)),])
        if objectid in frepple_keys:
          if deliveredQuantity >= orderedQuantity:   # TODO Not the right criterion
            delete.append( (objectid,) )
          else:
            update.append( (operation, orderedQuantity-deliveredQuantity,
              creationDate, scheduledDeliveryDate, objectid) )
        else:
          idcounter += 1
          insert.append( (idcounter, operation, orderedQuantity-deliveredQuantity,
            creationDate, scheduledDeliveryDate, objectid) )
          frepple_keys.add(objectid)
        # Clean the XML hierarchy
        root.clear()
        count -= 1
        if self.verbosity > 0 and count < 0:
          count = 500
          print('.', end="")
      if self.verbosity > 0: print ('')

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
          set location_id=%%s, subcategory='openbravo', type='fixed_time', lastmodified='%s' where name=%%s" % self.date,
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
          set item_id=%%s, location_id=%%s, subcategory='openbravo', lastmodified='%s' where name=%%s" % self.date,
        [ (i[0],i[1],i[3]) for i in deliveries if i[3] in frepple_keys ])

      # Create or update flow on purchasing operation
      cursor.execute("SELECT operation_id, thebuffer_id FROM flow")
      frepple_keys = set([ i for i in cursor.fetchall()])
      cursor.executemany(
        "insert into flow \
          (operation_id,thebuffer_id,quantity,type,source,lastmodified) \
          values(%%s,%%s,1,'end','openbravo','%s')" % self.date,
        [ (i[2],i[3]) for i in deliveries if (i[2],i[3]) not in frepple_keys ])
      cursor.executemany(
        "update flow \
          set quantity=1, type='end', source='openbravo', lastmodified='%s' where operation_id=%%s and thebuffer_id=%%s" % self.date,
        [ (i[2],i[3]) for i in deliveries if (i[2],i[3]) in frepple_keys ])

      # Create purchasing operationplans
      cursor.executemany(
        "insert into operationplan \
          (id,operation_id,quantity,startdate,enddate,locked,source,lastmodified) \
          values(%%s,%%s,%%s,%%s,%%s,'1',%%s,'%s')" % self.date,
        insert
        )
      cursor.executemany(
        "update operationplan \
          set operation_id=%%s, quantity=%%s, startdate=%%s, enddate=%%s, locked='1', lastmodified='%s' \
          where source=%%s" % self.date,
        update)
      cursor.executemany(
        "delete from operationplan where source=%s",
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
  def import_processplan(self, cursor):
    transaction.enter_transaction_management(using=self.database)
    try:
      starttime = time()
      if self.verbosity > 0:
        print("Importing bills of material...")

      # Reset the current buffers
      cursor.execute("DELETE FROM suboperation where operation_id like 'Processplan %'")
      cursor.execute("DELETE FROM resourceload where operation_id like 'Processplan %'")
      cursor.execute("DELETE FROM flow where operation_id like 'Processplan %'")
      cursor.execute("UPDATE buffer SET producing_id=NULL where subcategory='openbravo'")
      cursor.execute("DELETE FROM operation where name like 'Processplan %'")

      # Pick up existing operations in frePPLe
      cursor.execute("SELECT name FROM operation")
      frepple_operations = set([i[0] for i in cursor.fetchall()])

      # Get the list of all frePPLe buffers
      cursor.execute("SELECT name, item_id, location_id FROM buffer")
      frepple_buffers = {}
      for i in cursor.fetchall():
        if i[1] in frepple_buffers:
          frepple_buffers[i[1]].append( (i[0],i[2]) )
        else:
          frepple_buffers[i[1]] = [ (i[0],i[2]) ]

      # Loop over all produced products
      query = urllib.quote("production=true and processPlan is not null")
      conn, root = self.get_data("/openbravo/ws/dal/Product?where=%s&orderBy=name&includeChildren=false" % query)
      count = 0
      for event, elem in conn:
        if event != 'end' or elem.tag != 'Product': continue
        product = self.items.get(elem.get('id'), None)
        if not product:
          continue   # Not interested if item isn't mapped to frePPLe

        # Pick up the processplan of the product
        processplan = elem.find("processPlan").get('id')
        root2 = self.get_data("/openbravo/ws/dal/ManufacturingProcessPlan/%s?includeChildren=true" % processplan)[1]

        # Create routing operation for all frePPLe buffers of this product
        # We create a routing operation in the right location
        if not product in frepple_buffers:
          # TODO A produced item which appears in a BOM but has no sales orders, purchase orders or onhand will not show up
          continue
        operations = []
        suboperations = []
        buffers_create = []
        buffers_update = []
        flows = []
        loads = []
        for name, loc in frepple_buffers[product]:
          for pp_version in root2.find('ManufacturingProcessPlan').find('manufacturingVersionList').findall('ManufacturingVersion'):
            endingDate = datetime.strptime(pp_version.find("endingDate").text, '%Y-%m-%dT%H:%M:%S.%fZ')
            if endingDate < self.current:
              continue # We have passed the validity date of this version
            documentNo = pp_version.find('documentNo').text
            routing_name = "Processplan %s - %s" % (name, documentNo)
            if routing_name in frepple_operations:
              continue  # We apparantly already added it
            frepple_operations.add(routing_name)
            operations.append( (routing_name, loc, 'routing', None) )
            flows.append( (routing_name, name, 1, 'end') )
            buffers_update.append( (routing_name,name) )
            tmp = pp_version.find('manufacturingOperationList')
            if tmp:
              for pp_operation in tmp.findall('ManufacturingOperation'):
                sequenceNumber = int(pp_operation.find('sequenceNumber').text)
                costCenterUseTime = float(pp_operation.find('costCenterUseTime').text) * 3600
                step_name = "%s - %s" % (routing_name, sequenceNumber)
                operations.append( (step_name, loc, 'fixed_time', costCenterUseTime) )
                suboperations.append( (routing_name, step_name, sequenceNumber) )
                tmp = pp_operation.find('manufacturingOperationProductList')
                if tmp:
                  for ff_operationproduct in tmp.findall('ManufacturingOperationProduct'):
                    opproduct = self.items.get(ff_operationproduct.find('product').get('id'), None)
                    if not opproduct:
                      continue # Unknown product
                    # Find the buffer
                    opbuffer = None
                    if opproduct in frepple_buffers:
                      for bname, bloc in frepple_buffers[opproduct]:
                        if bloc == loc:
                          opbuffer = bname
                          break
                    if not opbuffer:
                      opbuffer = "%s @ %s" % (opproduct,loc)
                      buffers_create.append( (opbuffer, opproduct, loc) )
                    quantity = float(ff_operationproduct.find('quantity').text)
                    productionType = ff_operationproduct.find('productionType').text
                    if productionType == '-':
                      flows.append( (step_name, opbuffer, -quantity, 'start') )
                    else:
                      flows.append( (step_name, opbuffer, quantity, 'end') )
                tmp = pp_operation.find('manufacturingOperationMachineList')
                if tmp:
                  for ff_operationmachine in tmp.findall('ManufacturingOperationMachine'):
                    machine = self.resources.get(ff_operationmachine.find('machine').get('id'), None)
                    if not machine:
                      continue # Unknown machine
                    usageCoefficient = float(ff_operationmachine.find('usageCoefficient').text)
                    loads.append( (step_name, machine, usageCoefficient) )
        count -= 1
        if self.verbosity > 0 and count < 0:
          count = 500
          print('.', end="")
      if self.verbosity > 0: print ('')

      # TODO use "decrease" and "rejected" fields on steps to compute the yield
      # TODO multiple processplans for the same item -> alternate operation

      # Execute now on the database
      cursor.executemany(
        "insert into operation \
          (name,location_id,subcategory,type,duration,lastmodified) \
          values(%%s,%%s,'openbravo',%%s,%%s,'%s')" % self.date,
        operations
        )
      cursor.executemany(
        "insert into suboperation \
          (operation_id,suboperation_id,priority,source,lastmodified) \
          values(%%s,%%s,%%s,'openbravo','%s')" % self.date,
        suboperations
        )
      cursor.executemany(
        "update buffer set producing_id=%%s, lastmodified='%s' where name=%%s" % self.date,
        buffers_update
        )
      cursor.executemany(
        "insert into buffer \
          (name,item_id,location_id,subcategory,lastmodified) \
          values(%%s,%%s,%%s,'openbravo','%s')" % self.date,
        buffers_create
        )
      cursor.executemany(
        "insert into flow \
          (operation_id,thebuffer_id,quantity,type,source,lastmodified) \
          values(%%s,%%s,%%s,%%s,'openbravo','%s')" % self.date,
        flows
        )
      cursor.executemany(
        "insert into resourceload \
          (operation_id,resource_id,quantity,source,lastmodified) \
          values(%%s,%%s,%%s,'openbravo','%s')" % self.date,
        loads
        )

      transaction.commit(using=self.database)
      if self.verbosity > 0:
        print("Inserted %d operations" % len(operations))
        print("Inserted %d suboperations" % len(suboperations))
        print("Updated %d buffers" % len(buffers_update))
        print("Created %d buffers" % len(buffers_create))
        print("Inserted %d flows" % len(flows))
        print("Inserted %d loads" % len(loads))
        print("Imported bills of material in %.2f seconds" % (time() - starttime))
    except Exception as e:
      transaction.rollback(using=self.database)
      import sys, traceback
      traceback.print_exc(file=sys.stdout)
      raise CommandError("Error importing bills of material: %s" % e)
    finally:
      transaction.commit(using=self.database)
      transaction.leave_transaction_management(using=self.database)

