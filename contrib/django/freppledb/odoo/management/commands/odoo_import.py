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
from optparse import make_option

from django.core import management
from django.core.management.base import BaseCommand, CommandError
from django.conf import settings
from django.db import DEFAULT_DB_ALIAS


class Command(BaseCommand):

  help = "Loads data from an Odoo instance into the frePPLe database"

  option_list = BaseCommand.option_list + (
    make_option(
      '--user', dest='user', type='string',
      help='User running the command'
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

  requires_system_checks = False

  def handle(self, **options):

    # Pick up the options
    if 'verbosity' in options:
      self.verbosity = int(options['verbosity'] or '1')
    else:
      self.verbosity = 1
    if 'database' in options:
      database = options['database'] or DEFAULT_DB_ALIAS
    else:
      database = DEFAULT_DB_ALIAS
    if database not in settings.DATABASES.keys():
      raise CommandError("No database settings known for '%s'" % self.database )

    if 'user' in options and options['user']:
      management.call_command(
        'frepple_run',
        env="odoo_read_2,noforecast,noproduction,noinventory,noevaluation",
        database=database,
        user=options['user']
        )
    else:
      management.call_command(
        'frepple_run',
        env="odoo_read_2,noforecast,noproduction,noinventory,noevaluation",
        database=database
        )
