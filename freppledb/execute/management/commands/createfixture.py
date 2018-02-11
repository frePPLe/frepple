#
# Copyright (C) 2007-2017 by frePPLe bvba
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

import codecs
import json

from django.core.management.base import BaseCommand, CommandError
from django.db import connections, DEFAULT_DB_ALIAS
from django.conf import settings

from freppledb import VERSION


class Command(BaseCommand):

  help = '''
  This command dumps the content of the database in a fixture format file.
  '''

  requires_system_checks = False


  def get_version(self):
    return VERSION


  def add_arguments(self, parser):
    parser.add_argument(
      '--database', default=DEFAULT_DB_ALIAS,
      help='Nominates a specific database to load data from and export results into'
      )
    parser.add_argument(
      'output', help='file name to write the data to'
      )


  @staticmethod
  def extractTable(database, file, table, model):
    cursor = connections[database].cursor()

    # First retrieve the column names from that table
    sql = '''
    select column_name, data_type
    from information_schema.columns
    where table_name = %s and column_name <> 'lastmodified'
    '''
    cursor.execute(sql, (table,))
    nb_of_rows = cursor.rowcount

    # Then build a sql request like this
    #(select col1, col2, col3... from table) t
    sql = 'select '
    row = 0
    column = [[0 for x in range(2)] for y in range(nb_of_rows)]
    for columns in cursor.fetchall():
      #keep a copy of the result in the array column
      column[row][0]=columns[0]
      column[row][1]=columns[1]
      row = row + 1
      if columns[1] == "interval":
        sql = sql + "case when extract(epoch from %s)<0 then 0 else extract(epoch from %s) end as %s" % (columns[0], columns[0], columns[0])
      else:
        sql = sql + columns[0]
      if row < nb_of_rows:
        sql = sql + ", "
      else:
        sql = sql + " from %s" % table
    cursor.execute(sql)
    nb_of_rows = cursor.rowcount

    # Then start writing into the file
    row=0
    for i in cursor:
      row = row+1
      firstLoop = True
      for j in range(0,len(column)):
        columnName=column[j][0]
        value = i[j]
        # Make sure value is not None
        if value == None:
          continue
        if (firstLoop):
          firstLoop = False
          file.write("{\"model\": \"%s\", \"fields\": {" % (model))
        else:
          file.write(",")
        if column[j][1] in set(['numeric','integer']):
          file.write("\"%s\":%s" % (columnName,value))
        elif column[j][1] == 'jsonb':
          file.write("\"%s\":%s" % (columnName, json.dumps(value)))
        elif column[j][1] == 'boolean' and value:
          file.write("\"%s\":true" % (columnName))
        elif column[j][1] == 'boolean' and not value:
          file.write("\"%s\":false" % (columnName))
        else:
          file.write("\"%s\":\"%s\"" % (columnName,value))
      file.write("}}")
      if (row < nb_of_rows):
        file.write(",\n")
    return nb_of_rows


  def handle(self, *args, **options):
    # Pick up the options
    database = options['database']
    if database not in settings.DATABASES:
      raise CommandError("No database settings known for '%s'" % database )
    with codecs.open(options['output'], "w","utf-8") as file_object:
      #open the square bracket
      file_object.write("[\n")
      n = Command.extractTable(database,file_object, 'calendar', 'input.calendar')
      if n>0:
        file_object.write(",\n")
      n = Command.extractTable(database,file_object, 'calendarbucket', 'input.calendarbucket')
      if n>0:
        file_object.write(",\n")
      n = Command.extractTable(database,file_object, 'location', 'input.location')
      if n>0:
        file_object.write(",\n")
      n = Command.extractTable(database,file_object, 'customer', 'input.customer')
      if n>0:
        file_object.write(",\n")
      n = Command.extractTable(database,file_object, 'item', 'input.item')
      if n>0:
        file_object.write(",\n")
      n = Command.extractTable(database,file_object, 'operation', 'input.operation')
      if n>0:
        file_object.write(",\n")
      n = Command.extractTable(database,file_object, 'suboperation', 'input.suboperation')
      if n>0:
        file_object.write(",\n")
      n = Command.extractTable(database,file_object, 'buffer', 'input.buffer')
      if n>0:
        file_object.write(",\n")
      n = Command.extractTable(database,file_object, 'resource', 'input.resource')
      if n>0:
        file_object.write(",\n")
      n = Command.extractTable(database,file_object, 'skill', 'input.skill')
      if n>0:
        file_object.write(",\n")
      n = Command.extractTable(database,file_object, 'resourceskill', 'input.resourceskill')
      if n>0:
        file_object.write(",\n")
      n = Command.extractTable(database,file_object, 'operationmaterial', 'input.operationmaterial')
      if n>0:
        file_object.write(",\n")
      n = Command.extractTable(database,file_object, 'operationresource', 'input.operationresource')
      if n>0:
        file_object.write(",\n")
      n = Command.extractTable(database,file_object, 'supplier', 'input.supplier')
      if n>0:
        file_object.write(",\n")
      n = Command.extractTable(database,file_object, 'itemsupplier', 'input.itemsupplier')
      if n>0:
        file_object.write(",\n")
      n = Command.extractTable(database,file_object, 'itemdistribution', 'input.itemdistribution')
      if n>0:
        file_object.write(",\n")
      n = Command.extractTable(database,file_object, 'demand', 'input.demand')
      if n>0:
        file_object.write(",\n")
      n = Command.extractTable(database,file_object, 'common_parameter', 'common.parameter')
      if n>0:
        file_object.write(",\n")
      n = Command.extractTable(database,file_object, 'common_bucket', 'common.bucket')
      if n>0:
        file_object.write(",\n")
      n = Command.extractTable(database,file_object, 'common_bucketdetail', 'common.bucketdetail')
      if n>0:
        file_object.write(",\n")
      n = Command.extractTable(database,file_object, 'common_preference', 'common.userpreference')
      if n>0:
        file_object.write(",\n")
      n = Command.extractTable(database,file_object, 'operationplan', 'input.operationplan')
      if n>0:
        file_object.write(",\n")
      n = Command.extractTable(database,file_object, 'operationplanmaterial', 'input.operationplanmaterial')
      if n>0:
        file_object.write(",\n")
      n = Command.extractTable(database,file_object, 'operationplanresource', 'input.operationplanresource')
      if n>0:
        file_object.write(",\n")
      n = Command.extractTable(database,file_object, 'out_resourceplan', 'output.resourcesummary')
      if n>0:
        file_object.write(",\n")
      n = Command.extractTable(database,file_object, 'out_problem', 'output.problem')
      #close the square bracket
      file_object.write("\n]")
