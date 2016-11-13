#
# Copyright (C) 2007-2016 by frePPLe bvba
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
import base64
import email
import jwt
import os
import time
from urllib.request import urlopen, HTTPError, Request
from xml.sax.saxutils import quoteattr

from django.utils.http import urlencode

from django.db import DEFAULT_DB_ALIAS
from django.conf import settings
from django.utils.translation import ugettext_lazy as _

from freppledb.common.models import Parameter
from freppledb.common.commands import PlanTaskRegistry, PlanTask


@PlanTaskRegistry.register
class OdooReadData(PlanTask):
  '''
  This function connects to a URL, authenticates itself using HTTP basic
  authentication, and then reads data from the URL.
  The data from the source must adhere to frePPLe's official XML schema,
  as defined in the schema files bin/frepple.xsd and bin/frepple_core.xsd.

  The mode is pass as an argument:
    - Mode 1:
      This mode returns all data that is loaded with every planning run.
    - Mode 2:
      This mode returns data that is loaded that changes infrequently and
      can be transferred during automated scheduled runs at a quiet moment.
  Which data elements belong to each category is determined in the Odoo
  addon module and can vary between implementations.
  '''

  description = "Load Odoo data"
  sequence = 150
  label = ('odoo_read_1', _("Read Odoo data"))

  @classmethod
  def getWeight(cls, database=DEFAULT_DB_ALIAS, **kwargs):
    for i in range(5):
      if ("odoo_read_%s" % i) in os.environ:
        cls.mode = i
        for idx in (100, 101, 110):
          stdLoad = PlanTaskRegistry.getTask(sequence=idx)
          if stdLoad:
            stdLoad.filter = "source is null or source<>'odoo_%s'" % cls.mode
            stdLoad.description = "Load non-Odoo data"
        return 1
    else:
      return -1

  @classmethod
  def run(cls, database=DEFAULT_DB_ALIAS, **kwargs):
    import frepple
    
    # Uncomment the following lines to bypass the connection to odoo and use
    # a XML flat file alternative. This can be useful for debugging.
    #with open("my_path/my_data_file.xml", 'rb') as f:
    #  frepple.readXMLdata(f.read().decode('utf-8'), False, False)
    #  frepple.printsize()
    #  return
    
    odoo_user = Parameter.getValue("odoo.user", database)

    if settings.ODOO_PASSWORDS.get(database) == '':
      odoo_password = Parameter.getValue("odoo.password", database)
    else:
      odoo_password = settings.ODOO_PASSWORDS.get(database)

    odoo_db = Parameter.getValue("odoo.db", database)
    odoo_url = Parameter.getValue("odoo.url", database)
    odoo_company = Parameter.getValue("odoo.company", database)
    ok = True
    if not odoo_user:
      print("Missing or invalid parameter odoo.user")
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
    odoo_language = Parameter.getValue("odoo.language", database, 'en_US')
    if not ok:
      raise Exception("Odoo connector not configured correctly")

    # Connect to the odoo URL to GET data
    url = "%sfrepple/xml?%s" % (odoo_url, urlencode({
        'database': odoo_db,
        'language': odoo_language,
        'company': odoo_company,
        'mode': cls.mode
        }))
    try:
      request = Request(url)
      encoded = base64.encodestring(('%s:%s' % (odoo_user, odoo_password)).encode('utf-8'))[:-1]
      request.add_header("Authorization", "Basic %s" % encoded.decode('ascii'))
    except HTTPError as e:
      print("Error connecting to odoo at %s: %s" % (url, e))
      raise e

    # Download and parse XML data
    with urlopen(request) as f:
      frepple.readXMLdata(f.read().decode('utf-8'), False, False)
    frepple.printsize()


@PlanTaskRegistry.register
class OdooSaveStatic(PlanTask):
  description = "Save static model"
  sequence = 150
  label = ('odoo_read_1', _("Read Odoo data"))

  @classmethod
  def getWeight(cls, database=DEFAULT_DB_ALIAS, **kwargs):
    for i in range(5):
      if ("odoo_read_%s" % i) in os.environ:
        cls.mode = i
        cls.description = "Save static model of source odoo_%s" % cls.mode
        return 1
    else:
      return -1

  @classmethod
  def run(cls, database=DEFAULT_DB_ALIAS, **kwargs):
    from freppledb.execute.export_database_static import exportStaticModel
    exportStaticModel(database=database, source='odoo_%s' % cls.mode).run()


@PlanTaskRegistry.register
class OdooWritePlan(PlanTask):
  '''
  Uploads operationplans to odoo.
    - Sends all operationplans, meeting the criteria:
      a) locked = False
         The operationplans with locked equal to true are input to the plan,
         and not output.
      b) operationplan produces into a buffer whose source field is 'odoo'.
         Only those results are of interest to odoo.
    - We upload the following info in XML form:
       - id: frePPLe generated unique identifier
       - operation
       - start
       - end
       - quantity
       - location: This is the odoo id of the location, as stored in
         buffer.location.subcategory.
       - item: This is the odoo id of the produced item and its uom_id, as
         stored in buffer.item.subcategory.
       - criticality: 0 indicates a critical operationplan, 999 indicates a
         redundant operationplan.
    - The XML file uploaded is not exactly the standard XML of frePPLe, but a
      slight variation that fits odoo better.
    - Filter expressions are evaluated to limit the plan data that is
      automatically exported.
        - odoo.filter_export_purchase_order
        - odoo.filter_export_manufacturing_order
        - odoo.filter_export_distribution_order
    - This code doesn't interprete any of the results. An odoo addon module
      will need to read the content, and take appropriate actions in odoo:
      such as creating purchase orders, manufacturing orders, work orders,
      project tasks, etc...
  '''

  description = "Write results to Odoo"
  sequence = 450
  label = ('odoo_write', _("Write results to Odoo"))

  @classmethod
  def getWeight(cls, database=DEFAULT_DB_ALIAS, **kwargs):
    if 'odoo_write' in os.environ:
      return 1
    else:
      return -1

  @classmethod
  def run(cls, database=DEFAULT_DB_ALIAS, **kwargs):
    import frepple
    odoo_user = Parameter.getValue("odoo.user", database)
    odoo_password = Parameter.getValue("odoo.password", database)
    odoo_db = Parameter.getValue("odoo.db", database)
    odoo_url = Parameter.getValue("odoo.url", database)
    odoo_company = Parameter.getValue("odoo.company", database)
    ok = True
    if not odoo_user:
      print("Missing or invalid parameter odoo.user")
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
    odoo_language = Parameter.getValue("odoo.language", database, 'en_US')
    if not ok:
      raise Exception("Odoo connector not configured correctly")
    boundary = email.generator._make_boundary()

    # Generator function
    # We generate output in the multipart/form-data format.
    # We send the connection parameters as well as a file with the planning
    # results in XML-format.
    def publishPlan():
      yield '--%s\r' % boundary
      yield 'Content-Disposition: form-data; name="webtoken"\r'
      yield '\r'
      yield '%s\r' % jwt.encode({
        'exp': round(time.time()) + 600,
        'user': odoo_user,
        },
        settings.DATABASES[database].get('SECRET_WEBTOKEN_KEY', settings.SECRET_KEY),
        algorithm='HS256').decode('ascii')
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
        if not b or not b.source or not b.source.startswith('odoo') or i.locked:
          continue
        yield '<operationplan id="%s" operation=%s start="%s" end="%s" quantity="%s" location=%s item=%s criticality="%d"/>' % (
          i.id, quoteattr(i.operation.name),
          i.start, i.end, i.quantity,
          quoteattr(b.location.subcategory), quoteattr(b.item.subcategory),
          int(i.criticality)
          )
      yield '</operationplans>'
      yield '</plan>'
      yield '--%s--\r' % boundary
      yield '\r'

    # Connect to the odoo URL to POST data
    try:
      body = '\n'.join(publishPlan()).encode('utf-8')
      size = len(body)
      encoded = base64.encodestring(('%s:%s' % (odoo_user, odoo_password)).encode('utf-8'))
      req = Request(
        "%sfrepple/xml/" % odoo_url,
        data=body,
        headers={
          'Authorization': "Basic %s" % encoded.decode('ascii')[:-1],
          'Content-Type': 'multipart/form-data; boundary=%s' % boundary,
          'Content-length': size
          }
        )

      # Posting the data and displaying the server response
      print("Uploading %d bytes of planning results to odoo" % size)
      with urlopen(req) as f:
        msg = f.read()
        print("Odoo response: %s" % msg.decode('utf-8'))

    except HTTPError as e:
      print("Error connecting to odoo", e.read())
      raise e
