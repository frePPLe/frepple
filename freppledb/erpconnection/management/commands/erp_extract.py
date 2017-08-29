#
# Copyright (C) 2017 by frePPLe bvba
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

import adodbapi
import csv
import os

from django.core.management.base import BaseCommand, CommandError
from django.conf import settings
from django.db import DEFAULT_DB_ALIAS

from freppledb import VERSION


class Command(BaseCommand):
  help = '''
  Extract a set of flat files from JobBoss.
  '''

  # Parameter defining the database connection
  connectionstring = 'Provider=SQLNCLI11;Server=localhost;Database=acutec;User Id=acutec;Password=acutec;'

  # Generate .csv or .cpy files:
  #  - csv files are thoroughly validated and load slower
  #  - cpy files load much faster and rely on database level validation
  #    Loading cpy files is only available in the Enterprise Edition
  ext = 'csv'
  #ext = 'cpy'

  requires_system_checks = False

  def get_version(self):
    return VERSION


  def handle(self, **options):

    # Set the destination folder
    self.destination = settings.DATABASES[DEFAULT_DB_ALIAS]['FILEUPLOADFOLDER']
    if not os.access(self.destination, os.W_OK):
      raise CommandError("Can't write to folder %s " % self.destination)

    # Open database connection
    print("Connecting to the database")
    self.conn = adodbapi.connect(self.connectionstring, timeout=600)
    self.cursor = self.conn.cursor()
    self.fk = '_id' if self.ext == 'cpy' else ''

    # Extract all files
    try:
      self.extractLocation()
      self.extractCustomer()
      self.extractItem()
      self.extractSupplier()
      self.extractResource()
      self.extractSalesOrder()
      self.extractOperation()
      self.extractSuboperation()
      self.extractOperationResource()
      self.extractOperationMaterial()
      self.extractItemSupplier()
      self.extractCalendar()
      self.extractCalendarBucket()
      self.extractBuffer()
      self.extractItemSupplier()
      self.extractCalendar()
      self.extractCalendarBucket()
    finally:
      self.cursor.close()
      self.conn.close()


  def extractLocation(self):
    '''
    Straightforward mapping JobBOSS locations to frePPLe locations.
    Only the SHOP location is actually used in the frePPLe model.
    '''
    outfilename = os.path.join(self.destination, 'location.%s' % self.ext)
    print("Start extracting locations to %s" % outfilename)
    self.cursor.execute('''
      select 
        location_id, description, current_timestamp
      from location
      ''')
    with open(outfilename, 'w', newline='') as outfile:
      outcsv = csv.writer(outfile, quoting=csv.QUOTE_MINIMAL)
      outcsv.writerow(['name', 'description', 'lastmodified'])
      outcsv.writerows(self.cursor.fetchall())


  def extractCustomer(self):
    '''
    Straightforward mapping JobBOSS customers to frePPLe customers.
    '''
    outfilename = os.path.join(self.destination, 'customer.%s' % self.ext)
    print("Start extracting customers to %s" % outfilename)
    self.cursor.execute('''
      select distinct customer, type, current_timestamp from customer
      union
      select 'N/A', null, current_timestamp
      ''')
    with open(outfilename, 'w', newline='') as outfile:
      outcsv = csv.writer(outfile, quoting=csv.QUOTE_MINIMAL)
      outcsv.writerow(['name', 'category', 'lastmodified'])
      outcsv.writerows(self.cursor.fetchall())


  def extractItem(self):
    '''
    Map active JobBOSS jobs into frePPLe items.
    '''
    outfilename = os.path.join(self.destination, 'item.%s' % self.ext)
    print("Start extracting items to %s" % outfilename)
    self.cursor.execute('''
      select job, part_number, description, customer, current_timestamp
      from job
      where status = 'Active'
      ''')
    with open(outfilename, 'w', newline='') as outfile:
      outcsv = csv.writer(outfile, quoting=csv.QUOTE_MINIMAL)
      outcsv.writerow(['name', 'subcategory', 'description', 'category', 'lastmodified'])
      outcsv.writerows(self.cursor.fetchall())


  def extractSupplier(self):
    '''
    Map active JobBOSS vendors into frePPLe suppliers.
    '''
    outfilename = os.path.join(self.destination, 'supplier.%s' % self.ext)
    print("Start extracting suppliers to %s" % outfilename)
    self.cursor.execute('''
      select vendor, name, current_timestamp
      from vendor
      where status = 'Active'
      ''')
    with open(outfilename, 'w', newline='') as outfile:
      outcsv = csv.writer(outfile, quoting=csv.QUOTE_MINIMAL)
      outcsv.writerow(['name', 'description', 'lastmodified'])
      outcsv.writerows(self.cursor.fetchall())


  def extractResource(self):
    '''
    Map JobBOSS work centers into frePPLe resources.
    Only take the top-level workcenters, and skip the inactive ones.
    '''
    outfilename = os.path.join(self.destination, 'resource.%s' % self.ext)
    print("Start extracting resources to %s" % outfilename)
    self.cursor.execute('''
      select work_center, uvtext4, department, machines, 'SHOP', 'default', current_timestamp
      from work_center
      where parent_id is null and department <> 'INACTIVE'
      union all
      select vendor, name, 'OUTSOURCED', 1, 'SHOP', 'infinite', current_timestamp
      from vendor
      where status = 'Active'
      ''')
    with open(outfilename, 'w', newline='') as outfile:
      outcsv = csv.writer(outfile, quoting=csv.QUOTE_MINIMAL)
      outcsv.writerow(['name', 'category', 'subcategory', 'maximum', 'location%s' % self.fk, 'type', 'lastmodified'])
      outcsv.writerows(self.cursor.fetchall())


  def extractSalesOrder(self):
    '''
    Map JobBOSS top level jobs into frePPLe sales orders.
    '''
    outfilename = os.path.join(self.destination, 'demand.%s' % self.ext)
    print("Start extracting demand to %s" % outfilename)
    self.cursor.execute('''
      select
        job, job, 'SHOP', coalesce(customer, 'N/A'), 'open', order_date,
        make_quantity - completed_quantity, make_quantity - completed_quantity,
        description, part_number, 10, current_timestamp
      from job
      where status = 'Active'
      and top_lvl_job = job
      and make_quantity > completed_quantity
      ''')
    with open(outfilename, 'w', newline='') as outfile:
      outcsv = csv.writer(outfile, quoting=csv.QUOTE_MINIMAL)
      outcsv.writerow([
        'name', 'item%s' % self.fk, 'location%s' % self.fk, 'customer%s' % self.fk,
        'status', 'due', 'quantity', 'minimum shipment' if self.ext == 'csv' else 'minshipment',
        'description', 'category', 'priority', 'lastmodified'
        ])
      outcsv.writerows(self.cursor.fetchall())


  def extractOperation(self):
    '''
    Map JobBOSS jobs into frePPLe operations.
    We extract a routing operation and also suboperations.
    SQL contains an ugly trick to avoid duplicate job-sequence combinations.
    '''
    outfilename = os.path.join(self.destination, 'operation.%s' % self.ext)
    print("Start extracting operations to %s" % outfilename)
    self.cursor.execute('''
      select
        job, description, part_number, null, 'routing', job,
        'SHOP', null, null, current_timestamp
      from job
      where status = 'Active'
      union all
      select
        name, description, category, subcategory, type, item,
        location, duration, duration_per, lastmodified
      from (
      select
        concat(job.job, ' - ', sequence) as name,
        null as description, null as category,
        case when vendor is not null then 'outsourced' else null end as subcategory,
        case
          when Run_Method in ('Hrs/Part', 'Min/Part', 'Parts/Hr', 'Sec/Part') then 'time_per'
          else 'fixed_time'
          end as type,
        null as item, 'SHOP' as location,
        case
          when Run_Method in ('Hrs/Part', 'Min/Part', 'Parts/Hr', 'Sec/Part') then null
          else round(run * 3600, 4)
          end as duration,
        round(case when run_method = 'Hrs/Part' then run * 3600
          when run_method = 'Min/Part' then run * 60
          when run_method = 'Parts/Hr' and run > 0 then 3600 / run
          when run_method = 'Sec/Part' and run > 0 then run
          else null end, 4) as duration_per,
        current_timestamp as lastmodified,
        row_number() over(partition by job.job, sequence order by sequence desc) as rownumber
      from job_operation
      inner join job
      on job_operation.job = job.job
      where job.status = 'Active'
      ) ops
      where rownumber = 1
      ''')
    with open(outfilename, 'w', newline='') as outfile:
      outcsv = csv.writer(outfile, quoting=csv.QUOTE_MINIMAL)
      outcsv.writerow([
        'name', 'description', 'category', 'subcategory', 'type', 'item%s' % self.fk,
        'location%s' % self.fk, 'duration', 'duration_per', 'lastmodified'
        ])
      outcsv.writerows(self.cursor.fetchall())


  def extractSuboperation(self):
    '''
    Map JobBOSS joboperations into frePPLe suboperations.
    '''
    outfilename = os.path.join(self.destination, 'suboperation.%s' % self.ext)
    print("Start extracting suboperations to %s" % outfilename)
    self.cursor.execute('''
      select
        distinct job.job, concat(job.job, ' - ', sequence), sequence, current_timestamp
      from job_operation
      inner join job
      on job_operation.job = job.job
      where job.status = 'Active'
      ''')
    with open(outfilename, 'w', newline='') as outfile:
      outcsv = csv.writer(outfile, quoting=csv.QUOTE_MINIMAL)
      outcsv.writerow([
        'operation%s' % self.fk, 'suboperation%s' % self.fk, 'priority', 'lastmodified'
        ])
      outcsv.writerows(self.cursor.fetchall())


  def extractOperationResource(self):
    '''
    Map JobBOSS joboperation workcenters into frePPLe operation-resources.
    '''
    outfilename = os.path.join(self.destination, 'operationresource.%s' % self.ext)
    print("Start extracting operationresource to %s" % outfilename)
    self.cursor.execute('''
      select
        concat(job.job, ' - ', sequence),
        coalesce(vendor.vendor, coalesce(work_center.parent_id, work_center.work_center)),
        1, current_timestamp
      from job_operation
      inner join job on job_operation.job = job.job
      left outer join work_center
        on job_operation.work_center = work_center.work_center and work_center.department <> 'INACTIVE'
      left outer join vendor on job_operation.vendor = vendor.vendor and vendor.status = 'Active'
      where job.status = 'Active'
        and (vendor.vendor is not null or work_center.work_center is not null)
      ''')
    with open(outfilename, 'w', newline='') as outfile:
      outcsv = csv.writer(outfile, quoting=csv.QUOTE_MINIMAL)
      outcsv.writerow([
        'operation%s' % self.fk, 'resource%s' % self.fk, 'quantity', 'lastmodified'
        ])
      outcsv.writerows(self.cursor.fetchall())


  def extractOperationMaterial(self):
    '''
    Map JobBOSS joboperation workcenters into frePPLe operation-materials.
    '''
    outfilename = os.path.join(self.destination, 'operationmaterial.%s' % self.ext)
    print("Start extracting operationmaterial to %s" % outfilename)
    self.cursor.execute('''
      select
        case when job_operation.sequence is null then parent_job else concat(parent_job, ' - ', sequence) end,
        component_job, 'start', -relationship_qty, current_timestamp
      from bill_of_jobs
      inner join job job_child on job_child.job = component_job
      inner join job job_parent on job_parent.job = parent_job
      left outer join job_operation on job_operation.job_operation = bill_of_jobs.job_operation
      where relationship_type = 'Component'
        and job_parent.status = 'Active'
        and job_child.status = 'Active'
      union all
      select
        case when job_max_sequence.max_sequence is null then job.job else concat(job.job, ' - ', max_sequence) end,
        job.job, 'end', 1, current_timestamp
      from job
      left outer join (
        select job, max(sequence) as max_sequence
        from job_operation
        group by job
      ) job_max_sequence on job_max_sequence.job = job.job
      where status = 'Active'
      ''')
    with open(outfilename, 'w', newline='') as outfile:
      outcsv = csv.writer(outfile, quoting=csv.QUOTE_MINIMAL)
      outcsv.writerow([
        'operation%s' % self.fk, 'item%s' % self.fk, 'type', 'quantity', 'lastmodified'
        ])
      outcsv.writerows(self.cursor.fetchall())


  def extractBuffer(self):
    '''
    Map JobBOSS operation completed into frePPLe buffer onhand.
    '''
    outfilename = os.path.join(self.destination, 'buffer.%s' % self.ext)
    print("Start extracting buffer to %s" % outfilename)
    self.cursor.execute('''
      select
        concat(job, ' @ SHOP'), job, 'SHOP',
        case when completed_quantity > order_quantity then order_quantity else completed_quantity end,
        current_timestamp
      from job
      where status = 'Active'
        and completed_quantity > 0
      ''')
    with open(outfilename, 'w', newline='') as outfile:
      outcsv = csv.writer(outfile, quoting=csv.QUOTE_MINIMAL)
      outcsv.writerow([
        'name', 'item%s' % self.fk, 'location%s' % self.fk, 'onhand', 'lastmodified'
        ])
      outcsv.writerows(self.cursor.fetchall())


  def extractItemSupplier(self):
    '''
    Extract the purchasing parameters for each item from its suppliers.
    '''
    pass


  def extractCalendar(self):
    '''
    Extract working hours calendars from the ERP system.
    '''
    outfilename = os.path.join(self.destination, 'calendar.%s' % self.ext)
    print("Start extracting calendar to %s" % outfilename)
    self.cursor.execute('''
      select 'Working hours', current_timestamp
      ''')
    with open(outfilename, 'w', newline='') as outfile:
      outcsv = csv.writer(outfile, quoting=csv.QUOTE_MINIMAL)
      outcsv.writerow([
        'name', 'lastmodified'
        ])
      outcsv.writerows(self.cursor.fetchall())


  def extractCalendarBucket(self):
    pass
