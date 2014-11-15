#
# Copyright (C) 2010-2013 by Johan De Taeye, frePPLe bvba
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
from optparse import make_option

from django.core.management.base import BaseCommand, CommandError
from django.db import connections, DEFAULT_DB_ALIAS
from django.conf import settings

#TODO handling of suboperations!!!


class Command(BaseCommand):
  help = "Generates output in the DOT language to visualize the network"

  option_list = BaseCommand.option_list + (
    make_option(
      '--database', action='store', dest='database',
      default=DEFAULT_DB_ALIAS, help='Nominates a specific database to graph'
      ),
    )

  requires_model_validation = False

  def handle(self, **options):
    try:

      # Pick up the options
      if 'database' in options:
        database = options['database'] or DEFAULT_DB_ALIAS
      else:
        database = DEFAULT_DB_ALIAS
      if not database in settings.DATABASES:
        raise CommandError("No database settings known for '%s'" % database )

      # Create a database connection
      cursor = connections[database].cursor()

      # Header
      print('digraph G {')
      print('rankdir=LR;')
      print('graph [bgcolor=white];')
      print('edge [color=black];')
      print('node[style=filled,fontsize=8,label=""];')

      # Buffers
      print('subgraph buffers {')
      print('  node[shape=triangle,color=red];')
      cursor.execute('select name from buffer')
      for row in cursor.fetchall():
        print('  "B%s" [label="%s",tooltip="%s"];' % (row[0], row[0], row[0]))
      print('}')

      # Resources
      print('subgraph resources {')
      print('	 node[shape=circle,color=blue];')
      cursor.execute('select name from resource')
      for row in cursor.fetchall():
        print('  "R%s" [label="%s",tooltip="%s"];' % (row[0], row[0], row[0]))
      print('}')

      # Operations
      # TODO shows only 1 level of suboperations
      print('subgraph operations {')
      print('	 node[shape=rectangle,color=green];')
      cursor.execute('''
         select name, suboperation_id
         from operation
         left join suboperation
         on name = operation_id
         where name not in (select suboperation_id from suboperation)
         order by name, suboperation.priority
         ''')
      previous = None
      needs_closure = 0
      for o, s in cursor.fetchall():
        if o != previous and needs_closure > 0:
          needs_closure -= 1
          print('  }')
        if s is None:
          print('  "O%s" [label="%s",tooltip="%s"];' % (o, o, o))
        else:
          if o != previous:
            print('  subgraph "cluster_O%s" {' % o)
            print('    label="%s";' % o)
            print('    tooltip="%s";' % o)
            print('    fontsize=8;')
            previous = o
            needs_closure += 1
          print('    "O%s" [label="%s",tooltip="%s"];' % (s, s, s))
      print('}')

      # Flows
      print('subgraph flows {')
      print('  edge[weight=100];')
      cursor.execute('select operation_id, thebuffer_id, quantity from flow')
      for o, b, q in cursor.fetchall():
        if q > 0:
          print('  "O%s"->"B%s";' % (o, b))
        else:
          print('  "B%s"->"O%s";' % (b, o))
      print('}')

      # Loads
      print('subgraph loads {')
      print('  edge[style=dashed,dir=none,weight=100];')
      cursor.execute('select operation_id, resource_id from resourceload')
      for o, r in cursor.fetchall():
        print('  "O%s"->"R%s";' % (o, r))
      print('}')

      # Footer
      print('}')

    except Exception as e:
      raise CommandError(e)
