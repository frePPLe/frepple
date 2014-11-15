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
from optparse import make_option
import base64
from datetime import datetime, timedelta, date
from time import time
from xml.etree.cElementTree import iterparse
import http.client
import urllib
from io import StringIO

from django.core.management.base import BaseCommand, CommandError
from django.db import transaction, connections, DEFAULT_DB_ALIAS
from django.conf import settings

from freppledb.common.models import Parameter
from freppledb.execute.models import Task


class Command(BaseCommand):

  help = "Loads data from an Openbravo instance into the frePPLe database"

  option_list = BaseCommand.option_list + (
    make_option(
      '--user', dest='user', type='string',
      help='User running the command'
      ),
    make_option(
      '--delta', action='store', dest='delta', type="float", default='3650',
      help='Number of days for which we extract changed openbravo data'
      ),
    make_option(
      '--database', action='store', dest='database',
      default=DEFAULT_DB_ALIAS, help='Nominates the frePPLe database to load'
      ),
    make_option(
      '--task', dest='task', type='int',
      help='Task identifier (generated automatically if not provided)'
      ),
    )

  requires_model_validation = False

  def handle(self, **options):

    # Pick up the options
    if 'verbosity' in options:
      self.verbosity = int(options['verbosity'] or '1')
    else:
      self.verbosity = 1
    if 'user' in options:
      user = options['user']
    else:
      user = ''
    if 'database' in options:
      self.database = options['database'] or DEFAULT_DB_ALIAS
    else:
      self.database = DEFAULT_DB_ALIAS
    if not self.database in settings.DATABASES.keys():
      raise CommandError("No database settings known for '%s'" % self.database )
    if 'delta' in options:
      self.delta = float(options['delta'] or '3650')
    else:
      self.delta = 3650

    # Pick up configuration parameters
    self.openbravo_user = Parameter.getValue("openbravo.user", self.database)
    self.openbravo_password = Parameter.getValue("openbravo.password", self.database)
    self.openbravo_host = Parameter.getValue("openbravo.host", self.database)
    if not self.openbravo_user:
      raise CommandError("Missing or invalid parameter openbravo_user")
    if not self.openbravo_password:
      raise CommandError("Missing or invalid parameter openbravo_password")
    if not self.openbravo_host:
      raise CommandError("Missing or invalid parameter openbravo_host")

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
        try:
          task = Task.objects.all().using(self.database).get(pk=options['task'])
        except:
          raise CommandError("Task identifier not found")
        if task.started or task.finished or task.status != "Waiting" or task.name != 'Openbravo import':
          raise CommandError("Invalid task identifier")
        task.status = '0%'
        task.started = now
      else:
        task = Task(
          name='Openbravo import', submitted=now, started=now, status='0%',
          user=user, arguments="--delta=%s" % self.delta
          )
      task.save(using=self.database)
      transaction.commit(using=self.database)

      # Create a database connection to the frePPLe database
      cursor = connections[self.database].cursor()

      # Dictionaries for the mapping between openbravo ids and frepple names
      self.organizations = {}
      self.locations = {}
      self.organization_location = {}
      self.customers = {}
      self.items = {}
      self.locators = {}
      self.resources = {}
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
      self.import_approvedvendors(cursor)
      task.status = '70%'
      task.save(using=self.database)
      self.import_purchaseorders(cursor)
      task.status = '80%'
      task.save(using=self.database)
      transaction.commit(using=self.database)
      self.import_productbom(cursor)
      task.status = '90%'
      task.save(using=self.database)
      self.import_processplan(cursor)
      task.status = '95%'
      task.save(using=self.database)
      self.import_workInProgress(cursor)

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
      if task:
        task.save(using=self.database)
      try:
        transaction.commit(using=self.database)
      except:
        pass
      settings.DEBUG = tmp_debug
      transaction.set_autocommit(ac, using=self.database)


  def get_data(self, url):
    # Send the request
    webservice = http.client.HTTP(self.openbravo_host)
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
    if statuscode != http.client.OK:
      raise Exception(statusmessage)
    if self.verbosity > 2:
      res = webservice.getfile().read()
      print('Request: ', url)
      print('Response status: ', statuscode, statusmessage, header)
      print('Response content: ', res)
      conn = iter(iterparse(StringIO(res), events=('start', 'end')))
    else:
      conn = iter(iterparse(webservice.getfile(), events=('start', 'end')))
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
      conn, root = self.get_data("/openbravo/ws/dal/Organization?includeChildren=false")
      count = 0
      for event, elem in conn:
        if event != 'end' or elem.tag != 'Organization':
          continue
        searchkey = elem.find("searchKey").text
        objectid = elem.get('id')
        self.organizations[objectid] = searchkey
        count += 1
        # Clean the XML hierarchy
        root.clear()
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
  #        - 'openbravo' -> subcategory
  def import_customers(self, cursor):
    transaction.enter_transaction_management(using=self.database)
    try:
      starttime = time()
      if self.verbosity > 0:
        print("Importing customers...")

      # Get existing records
      cursor.execute("SELECT name, subcategory, source FROM customer")
      frepple_keys = {}
      for i in cursor.fetchall():
        if i[1] == 'openbravo':
          frepple_keys[i[0]] = i[2]
        else:
          frepple_keys[i[0]] = None
      unused_keys = frepple_keys.copy()

      # Retrieve businesspartners
      insert = []
      update = []
      query = urllib.quote("customer=true")
      conn, root = self.get_data("/openbravo/ws/dal/BusinessPartner?where=%s&orderBy=name&includeChildren=false" % query)
      count = 0
      for event, elem in conn:
        if event != 'end' or elem.tag != 'BusinessPartner':
          continue
        organization = self.organizations.get(elem.find("organization").get("id"), None)
        if not organization:
          continue
        searchkey = elem.find("searchKey").text
        name = elem.find("name").text
        unique_name = u'%s %s' % (searchkey, name)
        objectid = elem.get('id')
        description = elem.find("description").text
        self.customers[objectid] = unique_name
        if unique_name in frepple_keys:
          update.append( (description, objectid, unique_name) )
        else:
          insert.append( (description, unique_name, objectid) )
        unused_keys.pop(unique_name, None)
        # Clean the XML hierarchy
        root.clear()
        count -= 1
        if self.verbosity > 0 and count < 0:
          count = 500
          print('.', end="")
      if self.verbosity > 0:
        print ('')

      # Create records
      cursor.executemany(
        "insert into customer \
          (description,name,source,subcategory,lastmodified) \
          values (%%s,%%s,%%s,'openbravo','%s')" % self.date,
        insert
        )

      # Update records
      cursor.executemany(
        "update customer \
          set description=%%s,source=%%s,subcategory='openbravo',lastmodified='%s' \
          where name=%%s" % self.date,
        update
        )

      # Delete records
      delete = [ (i,) for i, j in unused_keys.items() if j ]
      cursor.executemany(
        'update customer set owner_id=null where owner_id=%s',
        delete
        )
      cursor.executemany(
        'update demand set customer_id=null where customer_id=%s',
        delete
        )
      cursor.executemany(
        'delete from customer where name=%s',
        delete
        )

      transaction.commit(using=self.database)
      if self.verbosity > 0:
        print("Inserted %d new customers" % len(insert))
        print("Updated %d existing customers" % len(update))
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
  #   - mapped fields openbravo -> frePPLe item
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

      # Get existing items
      cursor.execute("SELECT name, subcategory, source FROM item")
      frepple_keys = {}
      for i in cursor.fetchall():
        if i[1] == 'openbravo':
          frepple_keys[i[0]] = i[2]
        else:
          frepple_keys[i[0]] = None
      unused_keys = frepple_keys.copy()

      # Get all items from Openbravo
      insert = []
      update = []
      delete = []
      conn, root = self.get_data("/openbravo/ws/dal/Product?orderBy=name&includeChildren=false")
      count = 0
      for event, elem in conn:
        if event != 'end' or elem.tag != 'Product':
          continue
        organization = self.organizations.get(elem.find("organization").get("id"), None)
        if not organization:
          continue
        searchkey = elem.find("searchKey").text
        name = elem.find("name").text
        # A product name which consists of the searchkey and the name fields
        # is the default.
        # If you want a shorter item name, use the following lines instead:
        # unique_name = searchkey
        # description = name
        unique_name = u'%s %s' % (searchkey, name)
        description = elem.find("description").text
        objectid = elem.get('id')
        self.items[objectid] = unique_name
        unused_keys.pop(unique_name, None)
        if unique_name in frepple_keys:
          update.append( (description, objectid, unique_name) )
        else:
          insert.append( (unique_name, description, objectid) )
        # Clean the XML hierarchy
        root.clear()
        count -= 1
        if self.verbosity > 0 and count < 0:
          count = 500
          print('.', end="")
      if self.verbosity > 0:
        print ('')

      # Create new items
      cursor.executemany(
        "insert into item \
          (name,description,subcategory,source,lastmodified) \
          values (%%s,%%s,'openbravo',%%s,'%s')" % self.date,
        insert
        )

      # Update existing items
      cursor.executemany(
        "update item \
          set description=%%s, subcategory='openbravo', source=%%s, lastmodified='%s' \
          where name=%%s" % self.date,
        update
        )

      # Delete inactive items
      delete = [ (i,) for i, j in unused_keys.items() if j ]
      cursor.executemany("delete from demand where item_id=%s", delete)
      cursor.executemany(
        "delete from flow \
        where thebuffer_id in (select name from buffer where item_id=%s)",
        delete
        )
      cursor.executemany("delete from buffer where item_id=%s", delete)
      cursor.executemany("delete from item where name=%s", delete)

      transaction.commit(using=self.database)
      if self.verbosity > 0:
        print("Inserted %d new products" % len(insert))
        print("Updated %d existing products" % len(update))
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
  #   - We're also trying to create a mapping between an organization and its main
  #     warehouse location. This mapping is used to map manufacturing work requirements
  #     to a location where it'll happen.
  #     Manufacturing work requirements are linked with an organization in Openbravo,
  #     not with a warehouse.
  #     The mapping organization - warehouse we're making here is not a strict and
  #     foolproof way.
  #   - meeting the criterion:
  #        - %active = True
  #   - mapped fields Openbravo -> frePPLe location
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
      frepple_keys = {}
      for i in cursor.fetchall():
        if i[1] == 'openbravo':
          frepple_keys[i[0]] = i[2]
        else:
          frepple_keys[i[0]] = None
      unused_keys = frepple_keys.copy()

      # Get locations
      locations = []
      query = urllib.quote("active=true")
      conn, root = self.get_data("/openbravo/ws/dal/Warehouse?where=%s&orderBy=name&includeChildren=false" % query)
      count = 0
      for event, elem in conn:
        if event != 'end' or elem.tag != 'Warehouse':
          continue
        organization = self.organizations.get(elem.find("organization").get("id"), None)
        if not organization:
          continue
        searchkey = elem.find("searchKey").text
        name = elem.find("name").text
        # A product name which consists of the searchkey field is the default.
        # If you want a longer more descriptive item name, use the following lines instead
        # unique_name = u'%s %s' % (searchkey, name)
        # description = elem.find("description").text
        unique_name = searchkey
        description = name
        objectid = elem.get('id')
        self.locations[objectid] = unique_name
        locations.append( (description, objectid, unique_name) )
        self.locations[objectid] = unique_name
        unused_keys.pop(unique_name, None)
        if organization in self.organization_location:
          print (
            "Warning: Organization '%s' is already associated with '%s'. Ignoring association with '%s'"
            % (organization, self.organization_location[organization], unique_name)
            )
        else:
          self.organization_location[organization] = unique_name

        # Clean the XML hierarchy
        root.clear()
        count -= 1
        if self.verbosity > 0 and count < 0:
          count = 500
          print('.', end="")
      if self.verbosity > 0:
        print ('')

      # Remove deleted or inactive locations
      delete = [ (i,) for i, j in unused_keys.items() if j ]
      cursor.executemany(
        "update buffer \
        set location_id=null \
        where location_id=%s",
        delete
        )
      cursor.executemany(
        "update resource \
        set location_id=null \
        where location_id=%s",
        delete
        )
      cursor.executemany(
        "update location \
        set owner_id=null \
        where owner_id=%s",
        delete
        )

      # Create or update locations
      cursor.executemany(
        "insert into location \
          (description, source, subcategory, name, lastmodified) \
          values (%%s,%%s,'openbravo',%%s,'%s')" % self.date,
        [ i for i in locations if i[2] not in frepple_keys ]
        )
      cursor.executemany(
        "update location \
          set description=%%s, subcategory='openbravo', source=%%s, lastmodified='%s' \
          where name=%%s" % self.date,
        [ i for i in locations if i[2] not in frepple_keys ]
        )

      # Get a mapping of all locators to their warehouse
      conn, root = self.get_data("/openbravo/ws/dal/Locator")
      for event, elem in conn:
        if event != 'end' or elem.tag != 'Locator':
          continue
        warehouse = elem.find("warehouse").get('id')
        objectid = elem.get('id')
        self.locators[objectid] = warehouse
        root.clear()

      transaction.commit(using=self.database)
      if self.verbosity > 0:
        print("Processed %d locations" % len(locations))
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
  #          Note that the field scheduledDeliveryDate on the order line is hidden by default.
  #          Only the field scheduledDeliveryDate on the order is visible by default.
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
      query = urllib.quote("(updated>'%s' or salesOrder.updated>'%s') and salesOrder.salesTransaction=true and (salesOrder.documentStatus='CO' or salesOrder.documentStatus='CL')" % (self.delta, self.delta))
      conn, root = self.get_data("/openbravo/ws/dal/OrderLine?where=%s&orderBy=salesOrder.creationDate&includeChildren=false" % query)
      count = 0
      for event, elem in conn:
        if event != 'end' or elem.tag != 'OrderLine':
          continue
        organization = self.organizations.get(elem.find("organization").get("id"), None)
        product = self.items.get(elem.find("product").get('id'), None)
        warehouse = self.locations.get(elem.find("warehouse").get('id'), None)
        businessPartner = self.customers.get(elem.find("businessPartner").get('id'), None)
        if not warehouse or not product or not businessPartner or not organization:
          # Product, customer, location or organization are not known in frePPLe.
          # We assume that in that case you don't need to the demand either.
          root.clear()
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
        deliveries.update([
          (product, warehouse, operation, u'%s @ %s' % (product, warehouse))
          ])
        if unique_name in frepple_keys:
          update.append((
            objectid, closed and orderedQuantity or orderedQuantity - deliveredQuantity,
            product, closed and 'closed' or 'open', scheduledDeliveryDate,
            businessPartner, operation, unique_name
            ))
        else:
          insert.append((
            objectid, closed and orderedQuantity or orderedQuantity - deliveredQuantity,
            product, closed and 'closed' or 'open', scheduledDeliveryDate,
            businessPartner, operation, unique_name
            ))
          frepple_keys.add(unique_name)
        # Clean the XML hierarchy
        root.clear()
        count -= 1
        if self.verbosity > 0 and count < 0:
          count = 500
          print('.', end="")
      if self.verbosity > 0:
        print ('')

      # Create or update delivery operations
      cursor.execute("SELECT name FROM operation where name like 'Ship %'")
      frepple_keys = set([ i[0] for i in cursor.fetchall()])
      cursor.executemany(
        "insert into operation \
          (name,location_id,subcategory,type,lastmodified) \
          values (%%s,%%s,'openbravo','fixed_time','%s')" % self.date,
        [ (i[2], i[1]) for i in deliveries if i[2] not in frepple_keys ])
      cursor.executemany(
        "update operation \
          set location_id=%%s, subcategory='openbravo', type='fixed_time', lastmodified='%s' where name=%%s" % self.date,
        [ (i[1], i[2]) for i in deliveries if i[2] in frepple_keys ])

      # Create or update delivery buffers
      cursor.execute("SELECT name FROM buffer")
      frepple_keys = set([ i[0] for i in cursor.fetchall()])
      cursor.executemany(
        "insert into buffer \
          (name,item_id,location_id,subcategory,lastmodified) \
          values(%%s,%%s,%%s,'openbravo','%s')" % self.date,
        [ (i[3], i[0], i[1]) for i in deliveries if i[3] not in frepple_keys ])
      cursor.executemany(
        "update buffer \
          set item_id=%%s, location_id=%%s, subcategory='openbravo', lastmodified='%s' where name=%%s" % self.date,
        [ (i[0], i[1], i[3]) for i in deliveries if i[3] in frepple_keys ])

      # Create or update flow on delivery operation
      cursor.execute("SELECT operation_id, thebuffer_id FROM flow")
      frepple_keys = set([ i for i in cursor.fetchall()])
      cursor.executemany(
        "insert into flow \
          (operation_id,thebuffer_id,quantity,type,source,lastmodified) \
          values(%%s,%%s,-1,'start','openbravo','%s')" % self.date,
        [ (i[2], i[3]) for i in deliveries if (i[2], i[3]) not in frepple_keys ])
      cursor.executemany(
        "update flow \
          set quantity=-1, type='start', source='openbravo', lastmodified='%s' where operation_id=%%s and thebuffer_id=%%s" % self.date,
        [ (i[2], i[3]) for i in deliveries if (i[2], i[3]) in frepple_keys ])

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
  #   - Manufacturing machines are associated with any location in Openbravo.
  #     You should assign a location in frePPLe to assure that the user interface
  #     working.
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
        if i[1] == 'openbravo':
          self.resources[i[2]] = i[0]
        frepple_keys.add(i[0])
      unused_keys = frepple_keys.copy()
      insert = []
      update = []
      conn, root = self.get_data("/openbravo/ws/dal/ManufacturingMachine?orderBy=name&includeChildren=false")
      count = 0
      for event, elem in conn:
        if event != 'end' or elem.tag != 'ManufacturingMachine':
          continue
        organization = self.organizations.get(elem.find("organization").get("id"), None)
        if not organization:
          continue
        unique_name = elem.get('identifier')
        objectid = elem.get('id')
        if unique_name in frepple_keys:
          update.append( (objectid, unique_name) )
        else:
          insert.append( (unique_name, objectid) )
        unused_keys.discard(unique_name)
        self.resources[objectid] = unique_name
        # Clean the XML hierarchy
        root.clear()
        count -= 1
        if self.verbosity > 0 and count < 0:
          count = 500
          print('.', end="")
      if self.verbosity > 0:
        print ('')

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
      delete = [ (i,) for i in unused_keys ]
      cursor.executemany('delete from resourceskill where resource_id=%s', delete)
      cursor.executemany('delete from resourceload where resource_id=%s', delete)
      cursor.executemany('update resource set owner_id where owner_id=%s', delete)
      cursor.executemany('delete from resource where name=%s', delete)
      transaction.commit(using=self.database)
      if self.verbosity > 0:
        print("Inserted %d new machines" % len(insert))
        print("Updated %d existing machines" % len(update))
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
        if event != 'end' or elem.tag != 'MaterialMgmtStorageDetail':
          continue
        organization = self.organizations.get(elem.find("organization").get("id"), None)
        if not organization:
          continue
        onhand = elem.find("quantityOnHand").text
        locator = elem.find("storageBin").get('id')
        product = elem.find("product").get('id')
        item = self.items.get(product, None)
        location = self.locations.get(self.locators[locator], None)
        if not item or not location:
          root.clear()
          continue
        buffer_name = "%s @ %s" % (item, location)
        if buffer_name in frepple_buffers:
          if frepple_buffers[buffer_name] == 'openbravo':
            # Existing buffer marked as openbravo buffer
            increment.append( (onhand, buffer_name) )
          else:
            # Existing buffer marked as a non-openbravo buffer
            update.append( (onhand, buffer_name) )
            frepple_buffers[buffer_name] = 'openbravo'
        elif item and location:
          # New buffer
          insert.append( (buffer_name, self.items[product], self.locations[self.locators[locator]], onhand) )
          frepple_buffers[buffer_name] = 'openbravo'
        # Clean the XML hierarchy
        root.clear()
        count -= 1
        if self.verbosity > 0 and count < 0:
          count = 500
          print('.', end="")
      if self.verbosity > 0:
        print ('')

      cursor.executemany(
        "insert into buffer \
          (name,item_id,location_id,onhand,subcategory,lastmodified) \
          values(%%s,%%s,%%s,%%s,'openbravo','%s')" % self.date,
        insert)
      cursor.executemany(
        "update buffer \
          set onhand=%%s, subcategory='openbravo', lastmodified='%s' \
          where name=%%s" % self.date,
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


  # Load approved vendors
  #   - exctracting approvedvendor records
  #   - creating a purchasing buffer in each warehouse
  #   - NOT supported are situations with multiple approved vendors per part.
  #     Only the first record is used.
  #   - meeting the criterion:
  #        - %product already exists in frePPLe
  #        - %product.purchase = true
  #        - %currentVendor = true
  #   - mapped fields openbravo -> frePPLe buffer
  #        - %product @ %warehouse -> name
  #        - %warehouse -> location
  #        - %product -> item
  #        - 'openbravo' -> subcategory
  #   - mapped fields openbravo -> frePPLe operation
  #        - 'Purchase ' %product ' @ ' %warehouse -> name
  #        - %businessPartner -> category
  #        - 'fixed_time' -> type
  #        - %purchasingLeadTime -> duration
  #        - %minimumOrderQty ->sizeminimum
  #        - %quantityPerPackage -> sizemultiple
  #        - 'openbravo' -> subcategory
  #   - mapped fields openbravo -> frePPLe flow
  #        - 'Purchase ' %product ' @ ' %warehouse -> operation
  #        - %product ' @ ' %warehouse -> buffer
  #        - 1 -> quantity
  #        - 'end' -> type
  def import_approvedvendors(self, cursor):
    transaction.enter_transaction_management(using=self.database)
    try:
      starttime = time()
      if self.verbosity > 0:
        print("Importing approved vendors...")
      cursor.execute("SELECT name, subcategory, source FROM operation where name like 'Purchase %'")
      frepple_keys = {}
      for i in cursor.fetchall():
        if i[1] == 'openbravo':
          frepple_keys[i[0]] = i[2]
        else:
          frepple_keys[i[0]] = None
      unused_keys = frepple_keys.copy()
      purchasing = []
      warehouses = self.locations.values()
      query = urllib.quote("product.purchase=true and currentVendor=true")
      conn, root = self.get_data("/openbravo/ws/dal/ApprovedVendor?where=%s&orderBy=product&includeChildren=false" % query)
      count = 0
      prevproduct = None
      for event, elem in conn:
        if event != 'end' or elem.tag != 'ApprovedVendor':
          continue
        objectid = elem.get('id')
        product = self.items.get(elem.find('product').get('id'), None)
        if not product:
          root.clear()
          continue
        if product == prevproduct:
          # TODO there could be multiple supplier for an item
          print("Warning: Multiple approved vendors for a part are not supported. Skipping record")
          continue
        prevproduct = product
        businessPartner = elem.find('businessPartner').get('identifier')[:settings.CATEGORYSIZE]
        purchasingLeadTime = elem.find("purchasingLeadTime").text
        minimumOrderQty = elem.find("minimumOrderQty").text
        quantityPerPackage = elem.find("quantityPerPackage").text
        for wh in warehouses:
          operation = "Purchase %s @ %s" % (product, wh)
          unused_keys.pop(operation, None)
          purchasing.append((
            operation, "%s @ %s" % (product, wh), product, wh, businessPartner,
            purchasingLeadTime, minimumOrderQty, quantityPerPackage, objectid
            ))
        # Clean the XML hierarchy
        root.clear()
        count -= 1
        if self.verbosity > 0 and count < 0:
          count = 500
          print('.', end="")
      if self.verbosity > 0:
        print ('')

      # Remove deleted operations
      cursor.executemany(
        "update buffer \
        set producing_id=null \
        where producing_id=%s",
        [ (i,) for i, j in unused_keys.items() if j ]
        )
      cursor.executemany(
        "delete from flow \
        where operation_id=%s \
        and not exists (select 1 from operationplan where operation_id=flow.operation_id)",
        [ (i,) for i, j in unused_keys.items() if j ]
        )
      cursor.executemany(
        "delete from operation \
        where name=%s \
        and not exists (select 1 from operationplan where operation_id=operation.name)",
        [ (i,) for i, j in unused_keys.items() if j ]
        )

      # Create or update purchasing operations
      cursor.executemany(
        "insert into operation \
          (name,location_id,category,duration,sizeminimum,sizemultiple,subcategory,type,lastmodified,source) \
          values (%%s,%%s,%%s,%%s,%%s,%%s,'openbravo','fixed_time','%s',%%s)" % self.date,
        [
          (i[0], i[3], i[4], i[5], i[6], i[7], i[8])
          for i in purchasing
          if i[0] not in frepple_keys
        ])
      cursor.executemany(
        "update operation \
          set source=%%s, location_id=%%s, category=%%s, duration=%%s, sizeminimum=%%s, \
          sizemultiple=%%s, subcategory='openbravo', type='fixed_time', lastmodified='%s' where name=%%s" % self.date,
        [
          (i[8], i[3], i[4], i[5], i[6], i[7], i[0])
          for i in purchasing
          if i[0] in frepple_keys
        ])

      # Create or update buffers
      cursor.execute("SELECT name FROM buffer")
      frepple_keys = set([ i[0] for i in cursor.fetchall() ])
      cursor.executemany(
        "insert into buffer \
          (producing_id,name,item_id,location_id,subcategory,lastmodified,source) \
          values (%%s,%%s,%%s,%%s,'openbravo','%s',%%s)" % self.date,
        [ (i[0], i[1], i[2], i[3], i[8]) for i in purchasing if i[1] not in frepple_keys ]
        )
      cursor.executemany(
        "update buffer \
          set producing_id=%%s, source=%%s, item_id=%%s, location_id=%%s, \
          subcategory='openbravo', lastmodified='%s' \
          where name=%%s" % self.date,
        [ (i[0], i[8], i[2], i[3], i[1]) for i in purchasing if i[1] in frepple_keys ]
        )

      # Create or update flows
      cursor.execute("SELECT operation_id, thebuffer_id FROM flow")
      frepple_keys = set([ i for i in cursor.fetchall() ])
      cursor.executemany(
        "insert into flow \
          (operation_id,thebuffer_id,quantity,type,source,lastmodified) \
          values(%%s,%%s,1,'end','openbravo','%s')" % self.date,
        [ (i[0], i[1]) for i in purchasing if (i[0], i[1]) not in frepple_keys ]
        )
      cursor.executemany(
        "update flow \
          set quantity=1, type='end', source='openbravo', lastmodified='%s' \
          where operation_id=%%s and thebuffer_id=%%s" % self.date,
        [ (i[0], i[1]) for i in purchasing if (i[0], i[1]) in frepple_keys ]
        )

      transaction.commit(using=self.database)
      if self.verbosity > 0:
        print("Processed %d approved vendors" % len(purchasing))
        print("Imported approved vendors in %.2f seconds" % (time() - starttime))
    except Exception as e:
      transaction.rollback(using=self.database)
      raise CommandError("Error importing approved vendors: %s" % e)
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
      cursor.execute("SELECT source \
         FROM operationplan \
         where source is not null \
           and operation_id like 'Purchase %'")
      frepple_keys = set([ i[0] for i in cursor.fetchall()])
      cursor.execute("SELECT max(id) FROM operationplan")
      idcounter = cursor.fetchone()[0] or 1

      # Get the list of all open purchase orders
      insert = []
      update = []
      delete = []
      deliveries = set()
      query = urllib.quote("updated>'%s' and salesOrder.salesTransaction=false and salesOrder.documentType.name<>'RTV Order'" % self.delta)
      conn, root = self.get_data("/openbravo/ws/dal/OrderLine?where=%s&orderBy=salesOrder.creationDate&includeChildren=false" % query)
      count = 0
      for event, elem in conn:
        if event != 'end' or elem.tag != 'OrderLine':
          continue
        product = self.items.get(elem.find("product").get('id'), None)
        warehouse = self.locations.get(elem.find("warehouse").get('id'), None)
        organization = self.organizations.get(elem.find("organization").get("id"), None)
        scheduledDeliveryDate = elem.find("scheduledDeliveryDate").text
        if not warehouse or not product or not organization or not scheduledDeliveryDate:
          # Product, location or organization are not known in frePPLe.
          # Or there is no scheduled delivery date.
          # We assume that in that case you don't need to the purchase order either.
          root.clear()
          continue
        objectid = elem.get('id')
        scheduledDeliveryDate = datetime.strptime(scheduledDeliveryDate, '%Y-%m-%dT%H:%M:%S.%fZ')
        creationDate = datetime.strptime(elem.find("creationDate").text, '%Y-%m-%dT%H:%M:%S.%fZ')
        orderedQuantity = float(elem.find("orderedQuantity").text or 0)
        deliveredQuantity = float(elem.find("deliveredQuantity").text or 0)
        operation = u'Purchase %s @ %s' % (product, warehouse)
        deliveries.update([
          (product, warehouse, operation, u'%s @ %s' % (product, warehouse))
          ])
        if objectid in frepple_keys:
          if deliveredQuantity >= orderedQuantity:   # TODO Not the right criterion
            delete.append( (objectid,) )
          else:
            update.append((
              operation, orderedQuantity - deliveredQuantity,
              creationDate, scheduledDeliveryDate, objectid
              ))
        else:
          idcounter += 1
          insert.append((
            idcounter, operation, orderedQuantity - deliveredQuantity,
            creationDate, scheduledDeliveryDate, objectid
            ))
          frepple_keys.add(objectid)
        # Clean the XML hierarchy
        root.clear()
        count -= 1
        if self.verbosity > 0 and count < 0:
          count = 500
          print('.', end="")
      if self.verbosity > 0:
        print ('')

      # Create or update procurement operations
      cursor.execute("SELECT name FROM operation where name like 'Purchase %'")
      frepple_keys = set([ i[0] for i in cursor.fetchall()])
      cursor.executemany(
        "insert into operation \
          (name,location_id,subcategory,type,lastmodified) \
          values (%%s,%%s,'openbravo','fixed_time','%s')" % self.date,
        [ (i[2], i[1]) for i in deliveries if i[2] not in frepple_keys ])
      cursor.executemany(
        "update operation \
          set location_id=%%s, subcategory='openbravo', type='fixed_time', lastmodified='%s' where name=%%s" % self.date,
        [ (i[1], i[2]) for i in deliveries if i[2] in frepple_keys ])

      # Create or update purchasing buffers
      cursor.execute("SELECT name FROM buffer")
      frepple_keys = set([ i[0] for i in cursor.fetchall()])
      cursor.executemany(
        "insert into buffer \
          (name,item_id,location_id,subcategory,lastmodified) \
          values(%%s,%%s,%%s,'openbravo','%s')" % self.date,
        [ (i[3], i[0], i[1]) for i in deliveries if i[3] not in frepple_keys ])
      cursor.executemany(
        "update buffer \
          set item_id=%%s, location_id=%%s, subcategory='openbravo', lastmodified='%s' where name=%%s" % self.date,
        [ (i[0], i[1], i[3]) for i in deliveries if i[3] in frepple_keys ])

      # Create or update flow on purchasing operation
      cursor.execute("SELECT operation_id, thebuffer_id FROM flow")
      frepple_keys = set([ i for i in cursor.fetchall()])
      cursor.executemany(
        "insert into flow \
          (operation_id,thebuffer_id,quantity,type,source,lastmodified) \
          values(%%s,%%s,1,'end','openbravo','%s')" % self.date,
        [ (i[2], i[3]) for i in deliveries if (i[2], i[3]) not in frepple_keys ])
      cursor.executemany(
        "update flow \
          set quantity=1, type='end', source='openbravo', lastmodified='%s' where operation_id=%%s and thebuffer_id=%%s" % self.date,
        [ (i[2], i[3]) for i in deliveries if (i[2], i[3]) in frepple_keys ])

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


  # Load work in progress operationplans
  #   - extracting manufacturingWorkRequirement objects
  #   - meeting the criterion:
  #        - %operation already exists in frePPLe
  #   - mapped fields openbravo -> frePPLe operationplan
  #        - %product @ %warehouse -> name
  #        - %warehouse -> location
  #        - %product -> item
  #        - 'openbravo' -> subcategory
  def import_workInProgress(self, cursor):
    transaction.enter_transaction_management(using=self.database)
    try:
      starttime = time()
      if self.verbosity > 0:
        print("Importing manufacturing work requirement ...")

      # Find all known operationplans in frePPLe
      cursor.execute("SELECT source \
         FROM operationplan \
         where source is not null \
           and operation_id like 'Processplan %'")
      frepple_keys = set([ i[0] for i in cursor.fetchall()])
      unused_keys = frepple_keys.copy()
      cursor.execute("SELECT max(id) FROM operationplan")
      idcounter = cursor.fetchone()[0] or 1

      # Create index of all operations
      cursor.execute("SELECT name, source, location_id \
        FROM operation \
        WHERE subcategory='openbravo' \
          and source is not null")
      frepple_operations = { (i[1], i[2]): i[0] for i in cursor.fetchall() }

      # Get the list of all open work requirements
      insert = []
      update = []
      query = urllib.quote("closed=false")
      conn, root = self.get_data("/openbravo/ws/dal/ManufacturingWorkRequirement?where=%s" % query)
      count = 0
      for event, elem in conn:
        if event != 'end' or elem.tag != 'ManufacturingWorkRequirement':
          continue
        objectid = elem.get('id')
        quantity = float(elem.find("quantity").text)
        organization = self.organizations.get(elem.find("organization").get("id"), None)
        location = self.organization_location.get(organization, None)
        if not location:
          continue
        processPlan = frepple_operations.get( (elem.find("processPlan").get('id'), location), None)
        if not processPlan:
          continue
        startingDate = datetime.strptime(elem.find("startingDate").text, '%Y-%m-%dT%H:%M:%S.%fZ')
        endingDate = datetime.strptime(elem.find("endingDate").text, '%Y-%m-%dT%H:%M:%S.%fZ')
        if objectid in frepple_keys:
          update.append( (processPlan, quantity, startingDate, endingDate, objectid) )
        else:
          idcounter += 1
          insert.append( (idcounter, processPlan, quantity, startingDate, endingDate, objectid) )
        unused_keys.discard(objectid)
        # Clean the XML hierarchy
        root.clear()
        count -= 1
        if self.verbosity > 0 and count < 0:
          count = 500
          print('.', end="")
      if self.verbosity > 0:
        print ('')

      # Delete closed/canceled/deleted work requirements
      deleted = [ (i,) for i in unused_keys ]
      cursor.executemany("delete from operationplan where source=%s", deleted)

      # Create or update operationplans
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
        update
        )

      transaction.commit(using=self.database)
      if self.verbosity > 0:
        print("Inserted %d operationplans" % len(insert))
        print("Updated %d operationplans" % len(update))
        print("Deleted %d operationplans" % len(deleted))
        print("Imported manufacturing work requirements in %.2f seconds" % (time() - starttime))
    except Exception as e:
      transaction.rollback(using=self.database)
      raise CommandError("Error importing manufacturing work requirements: %s" % e)
    finally:
      transaction.commit(using=self.database)
      transaction.leave_transaction_management(using=self.database)


  # Importing productboms
  #   - extracting productBOM object for all Products with
  #
  def import_productbom(self, cursor):
    transaction.enter_transaction_management(using=self.database)
    try:
      starttime = time()
      if self.verbosity > 0:
        print("Importing product boms...")

      # Reset the current operations
      cursor.execute("DELETE FROM operationplan where operation_id like 'Product BOM %'")  # TODO allow incremental load!
      cursor.execute("DELETE FROM suboperation where operation_id like 'Product BOM %'")
      cursor.execute("DELETE FROM resourceload where operation_id like 'Product BOM %'")
      cursor.execute("DELETE FROM flow where operation_id like 'Product BOM %'")
      cursor.execute("UPDATE buffer SET producing_id=NULL where subcategory='openbravo' and producing_id like 'Product BOM %'")
      cursor.execute("DELETE FROM operation where name like 'Product BOM %'")

      # Get the list of all frePPLe buffers
      cursor.execute("SELECT name, item_id, location_id FROM buffer")
      frepple_buffers = {}
      frepple_keys = set()
      for i in cursor.fetchall():
        if i[1] in frepple_buffers:
          frepple_buffers[i[1]].append( (i[0], i[2]) )
        else:
          frepple_buffers[i[1]] = [ (i[0], i[2]) ]
        frepple_keys.add(i[0])

      # Loop over all productboms
      query = urllib.quote("product.billOfMaterials=true")
      conn, root = self.get_data("/openbravo/ws/dal/ProductBOM?where=%s&includeChildren=false" % query)
      count = 0
      operations = set()
      buffers = set()
      flows = {}
      for event, elem in conn:
        if event != 'end' or elem.tag != 'ProductBOM':
          continue
        bomquantity = float(elem.find("bOMQuantity").text)
        organization = self.organizations.get(elem.find("organization").get("id"), None)
        product = self.items.get(elem.find("product").get("id"), None)
        bomproduct = self.items.get(elem.find("bOMProduct").get("id"), None)
        if not product or not organization or not bomproduct or not product in frepple_buffers:
          # Rejecting uninteresting records
          root.clear()
          continue
        for name, loc in frepple_buffers[product]:
          operation = "Product BOM %s @ %s" % (product, loc)
          buf = "%s @ %s" % (bomproduct, loc)
          operations.add( (operation, loc, name) )
          if not buf in frepple_keys:
            buffers.add( (buf, bomproduct, loc) )
          flows[ (operation, name, 'end') ] = 1
          t = (operation, buf, 'start')
          if t in flows:
            flows[t] -= bomquantity
          else:
            flows[t] = -bomquantity
        # Clean the XML hierarchy
        root.clear()
        count -= 1
        if self.verbosity > 0 and count < 0:
          count = 500
          print('.', end="")
      if self.verbosity > 0:
        print ('')

      # Execute now on the database
      cursor.executemany(
        "insert into operation \
          (name,location_id,subcategory,type,duration,lastmodified) \
          values(%%s,%%s,'openbravo','fixed_time',0,'%s')" % self.date,
        [ (i[0], i[1]) for i in operations ]
        )
      cursor.executemany(
        "update buffer set producing_id=%%s, lastmodified='%s' where name=%%s" % self.date,
        [ (i[0], i[2]) for i in operations ]
        )
      cursor.executemany(
        "insert into buffer \
          (name,item_id,location_id,subcategory,lastmodified) \
          values(%%s,%%s,%%s,'openbravo','%s')" % self.date,
        buffers
        )
      cursor.executemany(
        "insert into flow \
          (operation_id,thebuffer_id,type,quantity,source,lastmodified) \
          values(%%s,%%s,%%s,%%s,'openbravo','%s')" % self.date,
        [ (i[0], i[1], i[2], j) for i, j in flows.items() ]
        )

      transaction.commit(using=self.database)
      if self.verbosity > 0:
        print("Inserted %d operations" % len(operations))
        print("Created %d buffers" % len(buffers))
        print("Inserted %d flows" % len(flows))
        print("Imported product boms in %.2f seconds" % (time() - starttime))
    except Exception as e:
      transaction.rollback(using=self.database)
      import sys
      import traceback
      traceback.print_exc(file=sys.stdout)
      raise CommandError("Error importing product boms: %s" % e)
    finally:
      transaction.commit(using=self.database)
      transaction.leave_transaction_management(using=self.database)


  # Importing processplans
  #   - extracting ManufacturingProcessPlan objects for all
  #     Products with production=true and processplan <> null
  #   - Not supported yet:
  #        - date effectivity with start date in the future
  #        - multiple processplans simultaneously effective
  #        - phantom boms
  #        - subproducts
  #        - routings
  #
  def import_processplan(self, cursor):
    transaction.enter_transaction_management(using=self.database)
    try:
      starttime = time()
      if self.verbosity > 0:
        print("Importing processplans...")

      # Reset the current operations
      cursor.execute("DELETE FROM operationplan where operation_id like 'Processplan %'")  # TODO allow incremental load!
      cursor.execute("DELETE FROM suboperation where operation_id like 'Processplan %'")
      cursor.execute("DELETE FROM resourceload where operation_id like 'Processplan %'")
      cursor.execute("DELETE FROM flow where operation_id like 'Processplan %'")
      cursor.execute("UPDATE buffer SET producing_id=NULL where subcategory='openbravo' and producing_id like 'Processplan %'")
      cursor.execute("DELETE FROM operation where name like 'Processplan %'")

      # Pick up existing operations in frePPLe
      cursor.execute("SELECT name FROM operation")
      frepple_operations = set([i[0] for i in cursor.fetchall()])

      # Get the list of all frePPLe buffers
      cursor.execute("SELECT name, item_id, location_id FROM buffer")
      frepple_buffers = {}
      for i in cursor.fetchall():
        if i[1] in frepple_buffers:
          frepple_buffers[i[1]].append( (i[0], i[2]) )
        else:
          frepple_buffers[i[1]] = [ (i[0], i[2]) ]

      # Get a dictionary with all process plans
      processplans = {}
      conn, root = self.get_data("/openbravo/ws/dal/ManufacturingProcessPlan?includeChildren=true")
      for event, elem in conn:
        if event != 'end' or elem.tag != 'ManufacturingProcessPlan':
          continue
        processplans[elem.get('id')] = elem

      # Loop over all produced products
      query = urllib.quote("production=true and processPlan is not null")
      conn, root = self.get_data("/openbravo/ws/dal/Product?where=%s&orderBy=name&includeChildren=false" % query)
      count = 0
      operations = []
      suboperations = []
      buffers_create = []
      buffers_update = []
      flows = {}
      loads = []
      for event, elem in conn:
        if event != 'end' or elem.tag != 'Product':
          continue
        product = self.items.get(elem.get('id'), None)
        if not product or not product in frepple_buffers:
          # TODO A produced item which appears in a BOM but has no sales orders, purchase orders or onhand will not show up.
          # If WIP exists on a routing, it could thus happen that the operation was not created.
          # A buffer in the middle of a BOM may thus be missing.
          root.clear()
          continue   # Not interested if item isn't mapped to frePPLe

        # Pick up the processplan of the product
        processplan = elem.find("processPlan").get('id')
        root2 = processplans[processplan]

        # Create routing operation for all frePPLe buffers of this product
        # We create a routing operation in the right location
        for name, loc in frepple_buffers[product]:
          tmp0 = root2.find('manufacturingVersionList')
          if not tmp0:
            continue
          for pp_version in tmp0.findall('ManufacturingVersion'):
            endingDate = datetime.strptime(pp_version.find("endingDate").text, '%Y-%m-%dT%H:%M:%S.%fZ')
            if endingDate < self.current:
              continue  # We have passed the validity date of this version
            documentNo = pp_version.find('documentNo').text
            routing_name = "Processplan %s - %s - %s" % (name, documentNo, loc)
            if routing_name in frepple_operations:
              continue  # We apparantly already added it
            frepple_operations.add(routing_name)
            operations.append( (routing_name, loc, 'routing', None, processplan) )
            #flows[ (routing_name, name, 'end') ] = 1
            buffers_update.append( (routing_name, name) )
            tmp1 = pp_version.find('manufacturingOperationList')
            if tmp1:
              steps = set()
              for pp_operation in tmp1.findall('ManufacturingOperation'):
                objectid = pp_operation.get('id')
                sequenceNumber = int(pp_operation.find('sequenceNumber').text)
                if sequenceNumber in steps:
                  print ("Warning: duplicate sequence number %s in processplan %s" % (sequenceNumber, routing_name))
                  while sequenceNumber in steps:
                    sequenceNumber += 1
                steps.add(sequenceNumber)
                costCenterUseTime = float(pp_operation.find('costCenterUseTime').text) * 3600
                step_name = "%s - %s" % (routing_name, sequenceNumber)
                operations.append( (step_name, loc, 'fixed_time', costCenterUseTime, objectid) )
                suboperations.append( (routing_name, step_name, sequenceNumber) )
                tmp2 = pp_operation.find('manufacturingOperationProductList')
                if tmp2:
                  for ff_operationproduct in tmp2.findall('ManufacturingOperationProduct'):
                    quantity = float(ff_operationproduct.find('quantity').text)
                    productionType = ff_operationproduct.find('productionType').text
                    opproduct = self.items.get(ff_operationproduct.find('product').get('id'), None)
                    if not opproduct:
                      continue  # Unknown product
                    # Find the buffer
                    opbuffer = None
                    if opproduct in frepple_buffers:
                      for bname, bloc in frepple_buffers[opproduct]:
                        if bloc == loc:
                          opbuffer = bname
                          break
                    if not opbuffer:
                      opbuffer = "%s @ %s" % (opproduct, loc)
                      buffers_create.append( (opbuffer, opproduct, loc) )
                      if not opproduct in frepple_buffers:
                        frepple_buffers[opproduct] = [ (opbuffer, loc) ]
                      else:
                        frepple_buffers[opproduct].append( (opbuffer, loc) )
                    if productionType == '-':
                      flow_key = (step_name, opbuffer, 'start')
                      if flow_key in flows:
                        flows[flow_key] -= quantity
                      else:
                        flows[flow_key] = -quantity
                    else:
                      flow_key = (step_name, opbuffer, 'end')
                      if flow_key in flows:
                        flows[flow_key] += quantity
                      else:
                        flows[flow_key] = quantity
                tmp4 = pp_operation.find('manufacturingOperationMachineList')
                if tmp4:
                  for ff_operationmachine in tmp4.findall('ManufacturingOperationMachine'):
                    machine = self.resources.get(ff_operationmachine.find('machine').get('id'), None)
                    if not machine:
                      continue  # Unknown machine
                    loads.append( (step_name, machine, 1) )
        # Clean the XML hierarchy
        root.clear()
        count -= 1
        if self.verbosity > 0 and count < 0:
          count = 500
          print('.', end="")
      if self.verbosity > 0:
        print ('')

      # TODO use "decrease" and "rejected" fields on steps to compute the yield
      # TODO multiple processplans for the same item -> alternate operation

      # Execute now on the database
      cursor.executemany(
        "insert into operation \
          (name,location_id,subcategory,type,duration,source,lastmodified) \
          values(%%s,%%s,'openbravo',%%s,%%s,%%s,'%s')" % self.date,
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
          (operation_id,thebuffer_id,type,quantity,source,lastmodified) \
          values(%%s,%%s,%%s,%%s,'openbravo','%s')" % self.date,
        [ (i[0], i[1], i[2], j) for i, j in flows.items() ]
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
        print("Imported processplans in %.2f seconds" % (time() - starttime))
    except Exception as e:
      transaction.rollback(using=self.database)
      import sys
      import traceback
      traceback.print_exc(file=sys.stdout)
      raise CommandError("Error importing processplans: %s" % e)
    finally:
      transaction.commit(using=self.database)
      transaction.leave_transaction_management(using=self.database)
