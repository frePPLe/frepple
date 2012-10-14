#
# Copyright (C) 2007-2012 by Johan De Taeye, frePPLe bvba
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

# file : $URL$
# revision : $LastChangedRevision$  $LastChangedBy$
# date : $LastChangedDate$

from optparse import make_option

from django.core.management.base import BaseCommand, CommandError
from django.core.management.color import no_style
from django.db import connections, transaction, DEFAULT_DB_ALIAS
from django.conf import settings
from django.utils.translation import ugettext as _

from freppledb.execute.models import log
from freppledb import VERSION


class Command(BaseCommand):
  help = '''
  This command empties the contents of all data tables in the frePPLe database.

  The results are similar to the 'flush input output' command, with the
  difference that some tables are not emptied and some performance related
  tweaks.
  Another difference is that the initial_data fixture is not loaded.
  '''
  option_list = BaseCommand.option_list + (
    make_option('--user', dest='user', type='string',
      help='User running the command'),
    make_option('--nonfatal', action="store_true", dest='nonfatal',
      default=False, help='Dont abort the execution upon an error'),
    make_option('--database', action='store', dest='database',
      default=DEFAULT_DB_ALIAS, help='Nominates a specific database to delete data from'),
    )

  requires_model_validation = False

  def get_version(self):
    return VERSION

  def handle(self, **options):
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
    if 'database' in options: database = options['database'] or DEFAULT_DB_ALIAS
    else: database = DEFAULT_DB_ALIAS
    if not database in settings.DATABASES.keys():
      raise CommandError("No database settings known for '%s'" % database )

    transaction.enter_transaction_management(using=database)
    transaction.managed(True, using=database)
    try:
      # Logging message
      log(category='ERASE', theuser=user,
        message=_('Start erasing the database')).save(using=database)

      # Create a database connection
      cursor = connections[database].cursor()

      # Delete all records from the tables.
      # We split the tables in groups to speed things up in postgreSQL.
      cursor.execute('update common_preference set horizonbuckets = null')
      transaction.commit(using=database)
      tables = [ 
        ['out_demandpegging'],
        ['out_problem','out_resourceplan','out_constraint'],
        ['out_loadplan','out_flowplan','out_operationplan'], 
        ['out_demand','out_forecast'],    # TODO Table may not exist!
        ['demand','forecastdemand','forecast','customer',
         'setuprule','setupmatrix','resourceload','resource',
         'flow','buffer','operationplan','item',
         'suboperation','operation',
         'location','calendarbucket','calendar'],
        ['common_parameter','common_bucketdetail','common_bucket'],
        ['common_comment','django_admin_log'],
        ]
      for group in tables:
        sql_list = connections[database].ops.sql_flush(no_style(), group, [] )
        for sql in sql_list:
          cursor.execute(sql)
          transaction.commit(using=database)

      # SQLite specials
      if settings.DATABASES[database]['ENGINE'] == 'django.db.backends.sqlite3':
        cursor.execute('vacuum')   # Shrink the database file

      # Logging message
      log(category='ERASE', theuser=user,
        message=_('Finished erasing the database')).save(using=database)

    except Exception as e:
      try: log(category='ERASE', theuser=user,
        message=u'%s: %s' % (_('Failed erasing the database'),e)).save(using=database)
      except: pass
      if nonfatal: raise e
      else: raise CommandError(e)

    finally:
      transaction.commit(using=database)
      settings.DEBUG = tmp_debug
      transaction.leave_transaction_management(using=database)
