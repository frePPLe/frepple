#
# Copyright (C) 2007-2013 by frePPLe bvba
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

from django.conf import settings
from django.core.management.base import BaseCommand, CommandError
from six.moves import input


class Command(BaseCommand):
  help = '''
    Create the PostgreSQL databases for frePPLe.

    The data
    '''

  def add_arguments(self, parser):
    super(Command, self).add_arguments(parser)
    parser.add_argument(
      '--database', default=None,
      help='Specify the database to recreate. When left unspecified all database will be created.'
      )
    parser.add_argument(
      '--noinput', action='store_false',
      dest='interactive', default=True,
      help='Tells frePPLe to NOT prompt the user for input of any kind.'
      )
    parser.add_argument(
      '--user', action='store', dest='user', default=None,
      help="Use a different user than defined in settings.py to create the database. "
           "This user must have the rights to drop and create databases."
      )
    parser.add_argument(
      '--password', action='store', dest='password', default=None,
      help='Use a different password than defined in settings.py to create the database.'
      )


  def handle(self, *args, **options):
    # Get the list of databases to create
    databaselist = options['database']
    if databaselist:
      if databaselist in settings.DATABASES:
        databaselist = [databaselist]
      else:
        raise CommandError("No database settings known for '%s'" % databaselist)
    else:
      databaselist = settings.DATABASES.keys()

    for database in databaselist:
      # Connect to the database
      import psycopg2
      user = options['user'] or settings.DATABASES[database].get('USER', '')
      password = options['password'] or settings.DATABASES[database].get('PASSWORD', '')
      conn_params = {'database': 'template1'}
      if user:
        conn_params['user'] = user
      if password:
        conn_params['password'] = password
      database_host = settings.DATABASES[database].get('HOST', None)
      if database_host:
        conn_params['host'] = database_host
      database_port = settings.DATABASES[database].get('PORT', None)
      if database_port:
        conn_params['port'] = database_port
      database_name = settings.DATABASES[database].get('NAME', None)
      if not database_name:
        raise CommandError("No database name specified")

      with psycopg2.connect(**conn_params) as connection:
        connection.set_isolation_level(0)  # autocommit false
        with connection.cursor() as cursor:
          # Check if the database exists
          cursor.execute("SELECT count(*) AS result FROM pg_database where datname = '%s'" % database_name)
          database_exists = cursor.fetchone()[0]

          if database_exists:
            # Confirm the destruction of the database
            if options['interactive']:
              confirm = input(
                "\nThe database %s is about to be IRREVERSIBLY destroyed and recreated.\n"
                "ALL data currently in the database will be lost.\n"
                "Are you sure you want to do this?\n"
                "\n"
                "Type 'yes' to continue, or 'no' to cancel: " % database_name
                )
              if confirm != 'yes':
                print("Skipping drop and create of database %s" % database_name)

            # Close current connections
            try:
              cursor.execute(
                '''
                SELECT pg_terminate_backend(pg_stat_activity.pid)
                FROM pg_stat_activity
                WHERE pg_stat_activity.datname = '%s'
                ''' % database_name
              )
            except psycopg2.ProgrammingError as e:
              raise CommandError(str(e))

            # Drop the database
            try:
              sql = 'drop database "%s"' % database_name
              print("Executing SQL statement:", sql)
              cursor.execute(sql)
            except psycopg2.ProgrammingError as e:
              raise CommandError(str(e))

          # Create the database
          try:
            sql = "create database \"%s\" encoding = 'UTF8'" % database_name
            if settings.DEFAULT_TABLESPACE:
              sql += ' TABLESPACE = %s' % settings.DEFAULT_TABLESPACE
            print("Executing SQL statement:", sql)
            cursor.execute(sql)
          except psycopg2.ProgrammingError as e:
            raise CommandError(str(e))
