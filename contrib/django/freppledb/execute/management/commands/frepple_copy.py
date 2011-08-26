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

# file : $URL$
# revision : $LastChangedRevision$  $LastChangedBy$
# date : $LastChangedDate$

import os, shutil
from optparse import make_option
from datetime import datetime

from django.core.management.base import BaseCommand, CommandError
from django.conf import settings
from django.db import transaction
from django.utils.translation import ugettext as _

from freppledb.execute.models import log, Scenario


class Command(BaseCommand):
  help = '''
  This command copies the contents of a database into another.
  The original data in the destination database are lost.

  To use this command the following prerequisites need to be met:
    * MySQL:
        - mysqldump and mysql need to be in the path
    * PostgreSQL:
       - pg_dump and psql need to be in the path
       - The passwords need to be specified upfront in a file ~/.pgpass
    * SQLite:
       - none
    * Oracle:
       - impdp and expdp need to be in the path
       - The DBA has to create a server side directory and grant rights to it:
           CREATE OR REPLACE DIRECTORY dump_dir AS 'c:\temp';
           GRANT READ, WRITE ON DIRECTORY dump_dir TO usr1;
           GRANT READ, WRITE ON DIRECTORY dump_dir TO usr2;
       - If the schemas reside on different servers, the DB will need to
         create a database link.
         If the database are on the same server, you might still use the database
         link to avoid create a temporary dump file.
       - Can't run multiple copies in parallel!
       - For oracle, this script probably requires a bit of changing to optimize
         it for your particular usage.
  '''
  option_list = BaseCommand.option_list + (
    make_option('--user', dest='user', type='string',
      help='User running the command'),
    make_option('--nonfatal', action="store_true", dest='nonfatal',
      default=False, help='Dont abort the execution upon an error'),
    make_option('--force', action="store_true", dest='force',
      default=False, help='Overwrite scenarios already in use'),
    make_option('--description', dest='description', type='string',
      help='Description of the destination scenario'),
    )
  args = 'source_database destination_database'

  requires_model_validation = False

  def get_version(self):
    return settings.FREPPLE_VERSION

  @transaction.commit_manually
  def handle(self, *args, **options):
    # Make sure the debug flag is not set!
    # When it is set, the django database wrapper collects a list of all sql
    # statements executed and their timings. This consumes plenty of memory
    # and cpu time.
    tmp_debug = settings.DEBUG
    settings.DEBUG = False

    # Pick up options
    if 'user' in options: user = options['user'] or ''
    else: user = ''
    nonfatal = False
    if 'nonfatal' in options: nonfatal = options['nonfatal']
    force = False
    if 'force' in options: force = options['force']
    test = 'FREPPLE_TEST' in os.environ

    # Synchronize the scenario table with the settings
    Scenario.syncWithSettings()

    # Validate the arguments
    destinationscenario = None
    try:
      if len(args) != 2:
        raise CommandError("Command takes exactly 2 arguments.")
      source = args[0]
      try:
        sourcescenario = Scenario.objects.get(pk=source)
      except:
        raise CommandError("No source database defined with name '%s'" % source)
      destination = args[1]
      try:
        destinationscenario = Scenario.objects.get(pk=destination)
      except:
        raise CommandError("No destination database defined with name '%s'" % destination)
      if source == destination:
        raise CommandError("Can't copy a schema on itself")
      if settings.DATABASES[source]['ENGINE'] != settings.DATABASES[destination]['ENGINE']:
        raise CommandError("Source and destination scenarios have a different engine")
      if sourcescenario.status != u'In use':
        raise CommandError("Source scenario is not in use")
      if destinationscenario.status != u'Free' and not force:
        raise CommandError("Destination scenario is not free")

      # Logging message (Always logging in the default database)
      log(category='COPY', theuser=user,
        message=_("Start copying database '%(source)s' to '%(destination)s'" %
          {'source':source, 'destination':destination} )).save()
      destinationscenario.status = u'Busy'
      destinationscenario.save()
      transaction.commit()

      # Copying the data
      if settings.DATABASES[source]['ENGINE'] == 'django.db.backends.postgresql_psycopg2':
        ret = os.system("pg_dump -c -U%s -Fp %s%s%s | psql -U%s %s%s%s" % (
          settings.DATABASES[source]['USER'],
          settings.DATABASES[source]['HOST'] and ("-h %s " % settings.DATABASES[source]['HOST']) or '',
          settings.DATABASES[source]['PORT'] and ("-p %s " % settings.DATABASES[source]['PORT']) or '',
          test and settings.DATABASES[source]['TEST_NAME'] or settings.DATABASES[source]['NAME'],
          settings.DATABASES[destination]['USER'],
          settings.DATABASES[destination]['HOST'] and ("-h %s " % settings.DATABASES[destination]['HOST']) or '',
          settings.DATABASES[destination]['PORT'] and ("-p %s " % settings.DATABASES[destination]['PORT']) or '',
          test and settings.DATABASES[destination]['TEST_NAME'] or settings.DATABASES[destination]['NAME'],
          ))
        if ret: raise Exception('Exit code of the database copy command is %d' % ret)
      elif settings.DATABASES[source]['ENGINE'] == 'django.db.backends.sqlite3':
        # A plain copy of the database file
        if test:
          shutil.copy2(settings.DATABASES[source]['TEST_NAME'], settings.DATABASES[destination]['TEST_NAME'])
        else:
          shutil.copy2(settings.DATABASES[source]['NAME'], settings.DATABASES[destination]['NAME'])
      elif settings.DATABASES[source]['ENGINE'] == 'django.db.backends.mysql':
        ret = os.system("mysqldump %s --password=%s --user=%s %s%s--quick --compress --extended-insert --add-drop-table | mysql %s --password=%s --user=%s %s%s" % (
          test and settings.DATABASES[source]['TEST_NAME'] or settings.DATABASES[source]['NAME'],
          settings.DATABASES[source]['PASSWORD'],
          settings.DATABASES[source]['USER'],
          settings.DATABASES[source]['HOST'] and ("--host=%s " % settings.DATABASES[source]['HOST']) or '',
          settings.DATABASES[source]['PORT'] and ("--port=%s " % settings.DATABASES[source]['PORT']) or '',
          test and settings.DATABASES[destination]['TEST_NAME'] or settings.DATABASES[destination]['NAME'],
          settings.DATABASES[destination]['PASSWORD'],
          settings.DATABASES[destination]['USER'],
          settings.DATABASES[destination]['HOST'] and ("--host=%s " % settings.DATABASES[destination]['HOST']) or '',
          settings.DATABASES[destination]['PORT'] and ("--port=%s " % settings.DATABASES[destination]['PORT']) or '',
          ))
        if ret: raise Exception('Exit code of the database copy command is %d' % ret)
      elif settings.DATABASES[source]['ENGINE'] == 'django.db.backends.oracle':
        try:
          try: os.unlink('c:\\temp\\frepple.dmp')
          except: pass
          ret = os.system("expdp %s/%s@//%s:%s/%s schemas=%s directory=dump_dir nologfile=Y dumpfile=frepple.dmp" % (
            test and settings.DATABASES[source]['TEST_USER'] or settings.DATABASES[source]['USER'],
            settings.DATABASES[source]['PASSWORD'],
            settings.DATABASES[source]['HOST'],
            settings.DATABASES[source]['PORT'],
            test and settings.DATABASES[source]['TEST_NAME'] or settings.DATABASES[source]['NAME'],
            test and settings.DATABASES[source]['TEST_USER'] or settings.DATABASES[source]['USER'],
            ))
          if ret: raise Exception('Exit code of the database export command is %d' % ret)
          ret = os.system("impdp %s/%s@//%s:%s/%s remap_schema=%s:%s table_exists_action=replace directory=dump_dir nologfile=Y dumpfile=frepple.dmp" % (
            test and settings.DATABASES[destination]['TEST_USER'] or settings.DATABASES[destination]['USER'],
            settings.DATABASES[destination]['PASSWORD'],
            settings.DATABASES[destination]['HOST'],
            settings.DATABASES[destination]['PORT'],
            test and settings.DATABASES[destination]['TEST_NAME'] or settings.DATABASES[destination]['NAME'],
            test and settings.DATABASES[source]['TEST_USER'] or settings.DATABASES[source]['USER'],
            test and settings.DATABASES[destination]['TEST_USER'] or settings.DATABASES[destination]['USER'],
            ))
          if ret: raise Exception('Exit code of the database import command is %d' % ret)
        finally:
          try: os.unlink('c:\\temp\\frepple.dmp')
          except: pass
      else:
        raise Exception('Copy command not supported for database engine %s' % settings.DATABASES[source]['ENGINE'])

      # Logging message
      log(category='COPY', theuser=user,
        message=_("Finished copying database '%(source)s' to '%(destination)s'" %
          {'source':source, 'destination':destination} )).save()

      # Update the scenario table
      destinationscenario.status = 'In use'
      destinationscenario.lastrefresh = datetime.today()
      if 'description' in options:
        destinationscenario.description = options['description']
      else:
        destinationscenario.description = "Copied from scenario '%s'" % source
      destinationscenario.save()

    except Exception, e:
      try: log(category='COPY', theuser=user,
        message=_("Failed copying database '%(source)s' to '%(destination)s'" %
          {'source':source, 'destination':destination} )).save()
      except: pass
      if destinationscenario and destinationscenario.status == u'Busy':
        destinationscenario.status = u'Free'
        destinationscenario.save()
      if nonfatal: raise e
      else: raise CommandError(e)

    finally:
      transaction.commit()
      settings.DEBUG = tmp_debug
