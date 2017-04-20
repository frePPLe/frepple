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
import csv

def read_csv_file():
  # This function reads a CSV-formatted file, creates an XML string and
  # then passes the string to Frepple for processing
  x = [ '<?xml version="1.0" encoding="UTF-8" ?><plan xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance">\n<items>' ]
  for row in csv.reader(open("items.csv", "rt")):
    x.append('<item name="%s" description="%s"/>' % (row[0],row[1]))
  x.append('</items>\n</plan>')
  frepple.readXMLdata('\n'.join(x),False,False)
  return

def read_csv_file_direct():
  # This function reads a CSV file and calls a function that accesses the
  # Frepple C++ API directly, without an intermediate XML format.
  for row in csv.reader(open("items.csv", "rt")):
    frepple.item(name=row[0], description=row[1])
  return

def create_files(cnt):
  # This function writes out 2 data files: a first one is CSV-formatted, while
  # second one is XML-formatted
  csvout = open('items.csv','w')
  xmlout = open('items.xml','w')
  try:
    xmlout.write('<?xml version="1.0" encoding="UTF-8" ?><plan xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance">\n<items>\n')
    for i in range(cnt):
      csvout.write('item%i,oper%i\n' % (i,i%100))
      xmlout.write('<item name="item%i" description="oper%i"/>\n' % (i,i%100))
    xmlout.write('</items>\n</plan>')
  finally:
    csvout.close()
    xmlout.close()
  return

def my_function(a):
  print('in my function with argument %s' % a, end="")
  return 'OK'

print('0. Initialization frePPLe version:', frepple.version)

