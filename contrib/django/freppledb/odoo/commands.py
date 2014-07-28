#
# Copyright (C) 2007-2013 by Johan De Taeye, frePPLe bvba
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

from __future__ import print_function
import os, inspect
from datetime import datetime, timedelta
from time import time
try:
  from urllib2 import urlopen, HTTPError
except:
  from urllib.request import urlopen, HTTPError
from xml.sax.saxutils import quoteattr

from django.utils.http import urlencode

from django.db import connections, transaction, DEFAULT_DB_ALIAS
from django.conf import settings

from freppledb.common.models import Parameter
from freppledb.input.models import Item, Customer
from freppledb.execute.commands import printWelcome, logProgress, createPlan, exportPlan

import frepple


def odoo_read(db = DEFAULT_DB_ALIAS):
  odoo_user = Parameter.getValue("odoo.user", db)
  odoo_password = Parameter.getValue("odoo.password", db)
  odoo_db = Parameter.getValue("odoo.db", db)
  odoo_url = Parameter.getValue("odoo.url", db)
  odoo_company = Parameter.getValue("odoo.company", db)
  ok = True
  if not odoo_user:
    print("Missing or invalid odoo.user parameter")
    ok = False
  if not odoo_password:
    print("Missing or invalid parameter odoo.password")
    ok = False
  if not odoo_db:
    print("Missing or invalid parameter odoo.db")
    ok = False
  if not odoo_url:
    print("Missing or invalid parameter odoo.url")
    ok = False
  if not odoo_company:
    print("Missing or invalid parameter odoo.company")
    ok = False
  odoo_language = Parameter.getValue("odoo.language", db, 'en_US')
  if not ok:
    print("Skipping data import from odoo")
    return

  # Connect to odoo
  try:
    f = urlopen("%s/frepple/xml/?%s" % (odoo_url, urlencode({
          'database': odoo_db, 'user': odoo_user, 'password': odoo_password,
          'language': odoo_language, 'company': odoo_company
          })))
  except HTTPError as e:
    print("Error connecting to odoo", e.read())
    raise e

  # Download and parse XML data
  frepple.readXMLdata(f.read().decode('ascii','ignore'), False, False)


def odoo_write(db = DEFAULT_DB_ALIAS):
  print("Exporting to odoo")


if __name__ == "__main__":
  # Select database
  try: db = os.environ['FREPPLE_DATABASE'] or DEFAULT_DB_ALIAS
  except: db = DEFAULT_DB_ALIAS

  # Use the test database if we are running the test suite
  if 'FREPPLE_TEST' in os.environ:
    settings.DATABASES[db]['NAME'] = settings.DATABASES[db]['TEST_NAME']
    if 'TEST_CHARSET' in os.environ:
      settings.DATABASES[db]['CHARSET'] = settings.DATABASES[db]['TEST_CHARSET']
    if 'TEST_COLLATION' in os.environ:
      settings.DATABASES[db]['COLLATION'] = settings.DATABASES[db]['TEST_COLLATION']
    if 'TEST_USER' in os.environ:
      settings.DATABASES[db]['USER'] = settings.DATABASES[db]['TEST_USER']

  printWelcome(database=db)
  logProgress(1, db)
  from freppledb.execute.load import loadData
  print("\nStart loading data from the database at", datetime.now().strftime("%H:%M:%S"))
  frepple.printsize()
  if 'odoo_read' in os.environ:
    # Use input data from the frePPLe database and Odoo
    loadData(database=db, filter="source is null or source<>'odoo'").run()
    frepple.printsize()
    logProgress(10, db)
    print("\nStart loading data from odoo at", datetime.now().strftime("%H:%M:%S"))
    odoo_read(db)
  else:
    # Use input data from the frePPLe database
    loadData(database=db, filter=None).run()
    frepple.printsize()
  logProgress(33, db)

  print("\nStart plan generation at", datetime.now().strftime("%H:%M:%S"))
  createPlan(db)
  frepple.printsize()
  logProgress(66, db)

  if 'odoo_read' in os.environ:
    print("\nStart exporting static model to the database at", datetime.now().strftime("%H:%M:%S"))
    from freppledb.execute.export_database_static import exportStaticModel
    exportStaticModel(database=db, source='odoo').run()

  print("\nStart exporting plan to the database at", datetime.now().strftime("%H:%M:%S"))
  exportPlan(db)

  if 'odoo_write' in os.environ:
    print("\nStart exporting plan to odoo at", datetime.now().strftime("%H:%M:%S"))
    odoo_write(db)

  #print("\nStart saving the plan to flat files at", datetime.now().strftime("%H:%M:%S"))
  #from freppledb.execute.export_file_plan import exportfrepple as export_plan_to_file
  #export_plan_to_file()

  #print("\nStart saving the plan to an XML file at", datetime.now().strftime("%H:%M:%S"))
  #frepple.saveXMLfile("output.1.xml","PLANDETAIL")
  #frepple.saveXMLfile("output.2.xml","PLAN")
  #frepple.saveXMLfile("output.3.xml","STANDARD")

  #print("Start deleting model data at", datetime.now().strftime("%H:%M:%S"))
  #frepple.erase(True)
  #frepple.printsize()

  print("\nFinished planning at", datetime.now().strftime("%H:%M:%S"))
  logProgress(100, db)
