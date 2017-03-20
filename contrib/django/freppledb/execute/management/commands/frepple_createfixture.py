#
# Copyright (C) 2007-2017 by frePPLe bvba
#
# All information contained herein is, and remains the property of frePPLe.
# You are allowed to use and modify the source code, as long as the software is used
# within your company.
# You are not allowed to distribute the software, either in the form of source code
# or in the form of compiled binaries.
#
import codecs,json
from optparse import make_option

from django.core.management.base import BaseCommand, CommandError
from django.db import connections, DEFAULT_DB_ALIAS
from django.conf import settings

from freppledb import VERSION

class Command(BaseCommand):

  help = '''
  This command dumps the content of the database in a fixture format file.
  '''
  option_list = BaseCommand.option_list + (

    make_option(
      '--database', action='store', dest='database', default=DEFAULT_DB_ALIAS,
      help='Nominates a specific database to load data from and export results into'
      ),
  )
  args = 'output json file'


  requires_system_checks = False

  def get_version(self):
    return VERSION

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
    results = cursor.fetchall()
    row=0
    for i in results:
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
        elif column[j][1] == 'json':
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
    if 'database' in options:
      database = options['database'] or DEFAULT_DB_ALIAS
    else:
      database = DEFAULT_DB_ALIAS
    if database not in settings.DATABASES:
      raise CommandError("No database settings known for '%s'" % database )
    file_object  = codecs.open(args[0], "w","utf-8")
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
