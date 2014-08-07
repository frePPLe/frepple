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
import base64
import mimetools
import os
from datetime import datetime
try:
  from urllib2 import urlopen, HTTPError, Request
except:
  from urllib.request import urlopen, HTTPError, Request
from xml.sax.saxutils import quoteattr

from django.utils.http import urlencode

from django.db import DEFAULT_DB_ALIAS
from django.conf import settings

from freppledb.common.models import Parameter
from freppledb.execute.commands import printWelcome, logProgress, createPlan, exportPlan

import frepple


def odoo_read(db=DEFAULT_DB_ALIAS):
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

  # Connect to the odoo URL to GET data
  try:
    request = Request("%s/frepple/xml/?%s" % (odoo_url, urlencode({
      'database': odoo_db, 'language': odoo_language, 'company': odoo_company
      })))
    encoded = base64.encodestring('%s:%s' % (odoo_user, odoo_password)).replace('\n', '')
    request.add_header("Authorization", "Basic %s" % encoded)
    f = urlopen(request)
  except HTTPError as e:
    print("Error connecting to odoo", e.read())
    raise e

  # Download and parse XML data
  frepple.readXMLdata(f.read().decode('ascii','ignore'), False, False)


def odoo_write(db=DEFAULT_DB_ALIAS):
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
    print("Skipping data export from odoo")
    return
  boundary = mimetools.choose_boundary()

  # Generator function
  # We generate output in the multipart/form-data format.
  # We send the connection parameters as well as a file with the planning
  # results in XML-format.
  def publishPlan():
    yield '--%s\r' % boundary
    yield 'Content-Disposition: form-data; name="database"\r'
    yield '\r'
    yield '%s\r' % odoo_db
    yield '--%s\r' % boundary
    yield 'Content-Disposition: form-data; name="language"\r'
    yield '\r'
    yield '%s\r' % odoo_language
    yield '--%s\r' % boundary
    yield 'Content-Disposition: form-data; name="company"\r'
    yield '\r'
    yield '%s\r' % odoo_company
    yield '--%s\r' % boundary
    yield 'Content-Disposition: file; name="frePPLe plan"; filename="frepple_plan.xml"\r'
    yield 'Content-Type: application/xml\r'
    yield '\r'
    yield '<?xml version="1.0" encoding="UTF-8" ?>'
    yield '<plan xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance">'
    # Export relevant operationplans
    yield '<operationplans>'
    for i in frepple.operationplans():
      b = None
      for j in i.flowplans:
        if j.quantity > 0:
          b = j.flow.buffer
      if not b or b.source != 'odoo' or i.locked:
        continue
      yield '<operationplan id="%s" operation=%s start="%s" end="%s" quantity="%s" location=%s item=%s/>' % (
        i.id, quoteattr(i.operation.name),
        i.start, i.end, i.quantity,
        quoteattr(b.location.subcategory), quoteattr(b.item.subcategory),
        )
    yield '</operationplans>'
    yield '</plan>'
    yield '--%s--\r' % boundary
    yield '\r'

  # Connect to the odoo URL to POST data
  try:
    req = Request("%s/frepple/xml/" % odoo_url)
    body = '\n'.join(publishPlan())
    size = len(body)
    encoded = base64.encodestring('%s:%s' % (odoo_user, odoo_password)).replace('\n', '')
    req.add_header("Authorization", "Basic %s" % encoded)
    req.add_header("Content-Type", 'multipart/form-data; boundary=%s' % boundary)
    req.add_header('Content-length', size)
    req.add_data(body)

    # Posting the data
    print("Uploading %d bytes of planning results to odoo" % size)
    req.get_data()

    # Display the server response, which can contain error messages
    print("Odoo response:")
    for i in urlopen(req):
      print(i, end="")

  except HTTPError as e:
    print("Error connecting to odoo", e.read())
    raise e


if __name__ == "__main__":
  # Select database
  try:
    db = os.environ['FREPPLE_DATABASE'] or DEFAULT_DB_ALIAS
  except:
    db = DEFAULT_DB_ALIAS

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
  frepple.printsize()
  if 'odoo_read' in os.environ:
    # Use input data from the frePPLe database and Odoo
    print("\nStart loading data from the database with filter \"source <> 'odoo'\" at", datetime.now().strftime("%H:%M:%S"))
    loadData(database=db, filter="source is null or source<>'odoo'").run()
    frepple.printsize()
    logProgress(10, db)
    print("\nStart loading data from odoo at", datetime.now().strftime("%H:%M:%S"))
    odoo_read(db)
    frepple.printsize()
  else:
    # Use input data from the frePPLe database
    print("\nStart loading data from the database at", datetime.now().strftime("%H:%M:%S"))
    loadData(database=db, filter=None).run()
    frepple.printsize()
  logProgress(33, db)

  print("\nStart plan generation at", datetime.now().strftime("%H:%M:%S"))
  createPlan(db)
  frepple.printsize()
  logProgress(66, db)

  if 'odoo_read' in os.environ:
    print("\nStart exporting static model to the database with filter \"source = 'odoo'\" at", datetime.now().strftime("%H:%M:%S"))
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
