#
# Copyright (C) 2011-2016 by frePPLe bvba
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

import psycopg2
import os

from _datetime import datetime
from optparse import make_option
from django.conf import settings
from django.db import DEFAULT_DB_ALIAS
from django.core.management.base import BaseCommand, CommandError

from freppledb.common.models import User
from freppledb import VERSION
from freppledb.execute.models import Task
from django.contrib.admin.models import LogEntry

class Command(BaseCommand):
  help = "Exports tables from the frePPLe database to CSV files in a folder"
  option_list = BaseCommand.option_list + (
    make_option(
      '--user', dest='user', type='string',
      help='User running the command'
      ),
    make_option(
      '--database', action='store', dest='database', default=DEFAULT_DB_ALIAS,
      help='Nominates a specific database to load the data into'
      ),
    make_option(
      '--task', dest='task', type='int',
      help='Task identifier (generated automatically if not provided)'
      )
  )

  requires_system_checks = False

  statements = [
      ("purchaseorder.csv", 
        '''COPY 
        (select source, lastmodified, id, status , reference, quantity, 
        to_char(startdate,'YYYY-MM-DD HH24:MI:SS') as startdate, 
        to_char(enddate,'YYYY-MM-DD HH24:MI:SS') as enddate, criticality, 
        owner_id, item_id, location_id, supplier_id from operationplan 
        where status='proposed' and type='PO') 
        TO STDOUT WITH CSV HEADER'''
        ),
      ("distributionorder.csv", 
        '''COPY 
        (select source, lastmodified, id, status, reference, quantity, 
        to_char(startdate,'YYYY-MM-DD HH24:MI:SS') as startdate, 
        to_char(enddate,'YYYY-MM-DD HH24:MI:SS') as enddate, criticality,
        plan, destination_id, item_id, origin_id from operationplan 
        where status='proposed' and type='DO') 
        TO STDOUT WITH CSV HEADER'''
        ),
      ("manufacturingorder.csv", 
       '''COPY 
       (select source, lastmodified, id , status ,reference ,quantity,
       to_char(startdate,'YYYY-MM-DD HH24:MI:SS') as startdate, 
       to_char(enddate,'YYYY-MM-DD HH24:MI:SS') as enddate, 
       criticality, operation_id, owner_id, plan, item_id
       from operationplan where status='proposed' and type='MO')
       TO STDOUT WITH CSV HEADER'''
       )
      ]

  def get_version(self):
    return VERSION

  def handle(self, *args, **options):
    # Pick up the options
    if 'database' in options:
      self.database = options['database'] or DEFAULT_DB_ALIAS
    else:
      self.database = DEFAULT_DB_ALIAS
    if self.database not in settings.DATABASES:
      raise CommandError("No database settings known for '%s'" % self.database )

    if 'user' in options and options['user']:
      try:
        self.user = User.objects.all().using(self.database).get(username=options['user'])
      except:
        raise CommandError("User '%s' not found" % options['user'] )
    else:
      self.user = None

    now = datetime.now()

    task = None
    self.logfile = None
    errors = 0
    try:
      # Initialize the task
      if 'task' in options and options['task']:
        try:
          task = Task.objects.all().using(self.database).get(pk=options['task'])
        except:
          raise CommandError("Task identifier not found")
        if task.started or task.finished or task.status != "Waiting" or task.name != 'export to folder':
          raise CommandError("Invalid task identifier")
        task.status = '0%'
        task.started = now
      else:
        task = Task(name='export to folder', submitted=now, started=now, status='0%', user=self.user)
      task.arguments = ' '.join(['"%s"' % i for i in args])
      task.save(using=self.database)

       # Execute
      if os.path.isdir(settings.DATABASES[self.database]['FILEUPLOADFOLDER']):

        # Open the logfile
        self.logfile = open(os.path.join(settings.DATABASES[self.database]['FILEUPLOADFOLDER'], 'exporttofolder.log'), "a")
        print("%s Started export to folder\n" % datetime.now(), file=self.logfile)

        #Define our connection string
        conn_string = "host='localhost' dbname='"+settings.DATABASES[self.database]['NAME']+"' user='"+settings.DATABASES[self.database]['USER']+"' password='"+settings.DATABASES[self.database]['PASSWORD']+"'"

        conn = psycopg2.connect(conn_string)

        cursor = conn.cursor()

        task.status = '0%'
        task.save(using=self.database)

        i=0
        cnt = len(self.statements)

        for filename, sqlquery in self.statements:
          print("%s Started export of %s" % (datetime.now(),filename), file=self.logfile)

          try:
            csv_datafile = open(os.path.join(settings.DATABASES[self.database]['FILEUPLOADFOLDER'], filename), "w")

            cursor.copy_expert(sqlquery,csv_datafile)

            csv_datafile.close()
            i += 1

          except Exception as e:
            errors += 1
            print("%s Failed to export to %s" % (datetime.now(),filename), file=self.logfile)
            if task:
              task.message = '%s' % e
            conn = psycopg2.connect(conn_string)
            cursor = conn.cursor()

          task.status = str(int(i/cnt*100))+'%'
          task.save(using=self.database)

        conn.close()
        print("%s Exported %s file(s)\n" % (datetime.now(),cnt-errors), file=self.logfile)

      else:
        errors += 1
        print("%s Failed, folder does not exist" % datetime.now(), file=self.logfile)
        task.message = "Destination folder does not exist"
        task.save(using=self.database)

    except Exception as e:
      print("%s Failed" % datetime.now(), file=self.logfile)
      errors += 1
      if task:
        task.message = '%s' % e

    finally:
      if task:
        if not errors:
          task.status = '100%'
          task.message = "Exported %s data files" % (cnt)
        else:
          task.status = 'Failed'
          #task.message = "Exported %s data files, %s failed" % (cnt-errors, errors)
        task.finished = datetime.now()
        task.save(using=self.database)

      if self.logfile:
        print('%s End of export to folder\n' % datetime.now(), file=self.logfile)
        self.logfile.close()