#
# Copyright (C) 2015 by frePPLe bvba
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
import json
from datetime import datetime
from io import StringIO
import urllib
from uuid import uuid4
from xml.etree.cElementTree import iterparse

from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse
from django.utils.translation import ugettext_lazy as _
from django.views.decorators.csrf import csrf_protect

from freppledb.common.models import Parameter
from freppledb.openbravo.utils import get_data, post_data
from freppledb.input.models import PurchaseOrder, DistributionOrder, Supplier, Item, Location


openbravo_organization_ids = {}


@login_required
@csrf_protect
def Upload(request):
  '''
  TODO we are doing lots of round trips to the database and openbravo to
  read the configuration. There is considerable overhead in this.
  '''
  # Decode the data received from the client
  data = json.loads(request.body.decode('utf-8'))

  # Validate records which exist in the database
  cleaned_records = []
  for rec in data:
    try:
      if rec['type'] == 'PO':
        obj = PurchaseOrder.objects.using(request.database).get(id=rec['id'])
        obj.supplier = Supplier.objects.using(request.database).get(name=rec.get('origin') or rec.get('supplier'))
        if not obj.supplier.source:
          continue
      else:
        obj = DistributionOrder.objects.using(request.database).get(id=rec['id'])
        #obj.destination = Location.objects.using(request.database).get(name=rec['destination'])
        #obj.origin = Location.object.using(request.database).get(name=rec['origin'])
      if obj.item.name != rec['item']:
        obj.item = Item.objects.using(request.database).get(name=rec['item'])
      if obj.status == 'proposed' and obj.item.source:
        # Copy edited values on the database object. Changes aren't saved yet.
        obj.startdate = datetime.strptime(rec['startdate'], "%Y-%m-%d %H:%M:%S")
        obj.enddate = datetime.strptime(rec['enddate'], "%Y-%m-%d %H:%M:%S")
        obj.quantity = abs(float(rec['quantity']))
        obj.status = 'approved'
        cleaned_records.append(obj)
    except:
      pass
  if not cleaned_records:
    return HttpResponse(content=_("No proposed data records selected"), status=500)

  # Read the configuration data from the database.
  openbravo_user = Parameter.getValue("openbravo.user", request.database)
  # Passwords in djangosettings file are preferably used
  if settings.OPENBRAVO_PASSWORDS.get(request.database) == '':
    openbravo_password = Parameter.getValue("openbravo.password", request.database)
  else:
    openbravo_password = settings.OPENBRAVO_PASSWORDS.get(request.database)
  openbravo_host = Parameter.getValue("openbravo.host", request.database)
  openbravo_organization = Parameter.getValue("openbravo.organization", request.database)
  exportPurchasingPlan = Parameter.getValue("openbravo.exportPurchasingPlan", request.database, default="false")

  # Look up the id of the Openbravo organization id
  if request.database not in openbravo_organization_ids:
    query = urllib.parse.quote("name='%s'" % openbravo_organization)
    data = get_data(
      "/openbravo/ws/dal/Organization?where=%s&includeChildren=false" % query,
      openbravo_host, openbravo_user, openbravo_password
      )
    conn = iterparse(StringIO(data), events=('start', 'end'))
    for event, elem in conn:
      if event == 'end' and elem.tag == 'Organization':
        openbravo_organization_ids[request.database] = elem.get('id')
        break
    if request.database not in openbravo_organization_ids:
      return HttpResponse(content="Can't find organization id in Openbravo", status=500)

  # Build the data content to send
  body = [
    #'<?xml version="1.0" encoding="UTF-8"?>',
    '<ob:Openbravo xmlns:ob="http://www.openbravo.com">',
    ]
  now = datetime.now().strftime('%Y/%m/%d %H:%M:%S')
  if exportPurchasingPlan:
    identifier = uuid4().hex
    url = "/openbravo/ws/dal/MRPPurchasingRun"
    body.append('''<MRPPurchasingRun id="%s">
      <organization id="%s" entity-name="Organization" identifier="%s"/>
      <active>true</active>
      <name>FREPPLE %s</name>
      <description>Incremental export triggered by %s</description>
      <timeHorizon>365</timeHorizon>
      <timeHorizon>365</timeHorizon>
      <safetyLeadTime>0</safetyLeadTime>
      <mRPPurchasingRunLineList>''' % (
        identifier, openbravo_organization_ids[request.database],
        openbravo_organization, now, request.user.username
      ))
    for obj in cleaned_records:
      identifier2 = uuid4().hex
      businessPartner = ''
      if isinstance(obj, PurchaseOrder):
        transaction_type = 'PO'
        if obj.supplier and obj.supplier.source:
          businessPartner = '<businessPartner id="%s"/>' % obj.supplier.source
          # TODO: where to store the destination of a purchase order
      else:
        transaction_type = 'MF'  # TODO Is this right?
        # TODO: where to store the source and destination of a stock transfer order
      # Possible transaction types in Openbravo are:
      #  - SO (Pending Sales Order)
      #  - PO (Pending Purchase Order)
      #  - WR (Pending Work Requirement)
      #  - SF (Sales Forecast)
      #  - MF (Material Requirement)
      #  - UD (User defined)
      #  - WP (Suggested Work Requirement)
      #  - MP (Suggested Material Requirement)
      #  - PP (Suggested Purchase Order)
      #  - ST (Stock)
      #  - MS (Minimum Stock): Minimum or security stock
      body.append('''<MRPPurchasingRunLine id="%s">
          <active>true</active>
          <purchasingPlan id="%s" entity-name="MRPPurchasingRun"/>
          <product id="%s" entity-name="Product"/>
          <quantity>%s</quantity>
          <requiredQuantity>%s</requiredQuantity>
          <plannedDate>%s.0Z</plannedDate>
          <plannedOrderDate>%s.0Z</plannedOrderDate>
          <transactionType>%s</transactionType>
          %s
          <fixed>true</fixed>
          <completed>false</completed>
        </MRPPurchasingRunLine>
        ''' % (
        identifier2, identifier, obj.item.source, obj.quantity,
        obj.quantity, datetime.strftime(obj.enddate, "%Y-%m-%d %H:%M:%S"),
        datetime.strftime(obj.startdate, "%Y-%m-%d %H:%M:%S"), transaction_type,
        businessPartner
        ))
    body.append('''</mRPPurchasingRunLineList>
      </MRPPurchasingRun>
      </ob:Openbravo>
      ''')
  else:
    raise Exception("Incremental export as a requisition not implemented yet") # TODO
  xmldoc = '\n'.join(body).encode(encoding='utf_8')

  try:
    # Send the data to openbravo
    post_data(xmldoc, url, openbravo_host, openbravo_user, openbravo_password)

    # Now save the changed status also in our database
    for obj in cleaned_records:
      obj.save(using=request.database)

    return HttpResponse("OK")
  except Exception as e:
    # Something went wrong in the connection
    return HttpResponse(content=str(e), status=500)
