#
# Copyright (C) 2016 by frePPLe bvba
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

from django.core import management
from django.core.management.base import BaseCommand, CommandError
from django.conf import settings
from django.db import DEFAULT_DB_ALIAS

from freppledb import VERSION


class Command(BaseCommand):

  help = "Loads data from an Odoo instance into the frePPLe database"

  requires_system_checks = False


  def get_version(self):
    return VERSION


  def add_arguments(self, parser):
    parser.add_argument(
      '--user', help='User running the command'
      )
    parser.add_argument(
      '--database', default=DEFAULT_DB_ALIAS,
      help='Nominates the frePPLe database to load'
      )
    parser.add_argument(
      '--task', type=int,
      help='Task identifier (generated automatically if not provided)'
      )


  def handle(self, **options):

    # Pick up the options
    self.verbosity = int(options['verbosity'])
    database = options['database']
    if database not in settings.DATABASES.keys():
      raise CommandError("No database settings known for '%s'" % self.database)
    if options['user']:
      management.call_command(
        'frepple_run',
        env="odoo_read_2",
        database=database,
        user=options['user']
        )
    else:
      management.call_command(
        'frepple_run',
        env="odoo_read_2",
        database=database
        )
