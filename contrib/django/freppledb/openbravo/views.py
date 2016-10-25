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
from freppledb.openbravo.utils import get_data
from freppledb.input.models import PurchaseOrder, DistributionOrder, OperationPlan
from freppledb.input.models import Operation, Supplier, Item, Location


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
  cleaned_MO_records = []
  for rec in data:
    try:
      if rec['type'] == 'PO':
        # Purchase orders
        obj = PurchaseOrder.objects.using(request.database).get(id=rec['id'])
        obj.supplier = Supplier.objects.using(request.database).get(name=rec.get('origin') or rec.get('supplier'))
        if obj.item.name != rec['item']:
          obj.item = Item.objects.using(request.database).get(name=rec['item'])
        if not obj.supplier.source or not obj.item.source or obj.status != 'proposed':
          continue
        obj.startdate = datetime.strptime(rec['startdate'], "%Y-%m-%d %H:%M:%S")
        obj.enddate = datetime.strptime(rec['enddate'], "%Y-%m-%d %H:%M:%S")
        obj.quantity = abs(float(rec['quantity']))
        obj.status = 'approved'
        cleaned_records.append(obj)
      elif rec['type'] == 'OP':
        # Manufacturing orders
        obj = OperationPlan.objects.using(request.database).get(id=rec['id'])
        if obj.operation.name != rec['operation']:
          obj.operation = Operation.objects.using(request.database).get(name=rec['operation'])
        if not obj.operation.source or obj.status != 'proposed':
          continue
        obj.startdate = datetime.strptime(rec['startdate'], "%Y-%m-%d %H:%M:%S")
        obj.enddate = datetime.strptime(rec['enddate'], "%Y-%m-%d %H:%M:%S")
        obj.quantity = abs(float(rec['quantity']))
        obj.status = 'approved'
        cleaned_MO_records.append(obj)
      elif rec['type'] == 'DO':
        # Distribution orders
        obj = DistributionOrder.objects.using(request.database).get(id=rec['id'])
        #obj.destination = Location.objects.using(request.database).get(name=rec['destination'])
        #obj.origin = Location.object.using(request.database).get(name=rec['origin'])
        if obj.item.name != rec['item']:
          obj.item = Item.objects.using(request.database).get(name=rec['item'])
        if not obj.item.source or obj.status != 'proposed':
          continue
        obj.startdate = datetime.strptime(rec['startdate'], "%Y-%m-%d %H:%M:%S")
        obj.enddate = datetime.strptime(rec['enddate'], "%Y-%m-%d %H:%M:%S")
        obj.quantity = abs(float(rec['quantity']))
        obj.status = 'approved'
        cleaned_records.append(obj)
      else:
        raise Exception("Unknown transaction type")
    except:
      pass
  if not cleaned_records and not cleaned_MO_records:
    return HttpResponse(content=_("No proposed data records selected"), status=500)

  # Read the configuration data from the database.
  openbravo_user = Parameter.getValue("openbravo.user", request.database)
  # Passwords in djangosettings file are preferably used
  openbravo_password = settings.OPENBRAVO_PASSWORDS.get(request.database, None)
  if not openbravo_password:
    openbravo_password = Parameter.getValue("openbravo.password", request.database)
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
  now = datetime.now().strftime('%Y/%m/%d %H:%M:%S')

  # Export manufacturing orders
  # This export requires the advanced warehousing functionality from openbravo.
  # Details on this web service can be found on:
  #    http://wiki.openbravo.com/wiki/Modules:Advanced_Warehouse_Operations
  if cleaned_MO_records:
    body = [
      #'<?xml version="1.0" encoding="UTF-8"?>',
      '<ob:Openbravo xmlns:ob="http://www.openbravo.com" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance">',
      ]
    for obj in cleaned_MO_records:
      body.append('''<ManufacturingWorkRequirement>
          <organization id="%s" entity-name="Organization" identifier="%s"/>
          <active>true</active>
          <processPlan id="%s" entity-name="ManufacturingProcessPlan"/>
          <quantity>%s</quantity>
          <startingDate>%s</startingDate>
          <endingDate>%s</endingDate>
          <closed>false</closed>
          <insertProductsAndorPhases>false</insertProductsAndorPhases>
          <processed>false</processed>
          <includePhasesWhenInserting>true</includePhasesWhenInserting>
          <processQuantity>0</processQuantity>
          <processUnit xsi:nil="true"/>
          <conversionRate xsi:nil="true"/>
          <createworkrequirement>false</createworkrequirement>
          <closedStat>false</closedStat>
          </ManufacturingWorkRequirement>''' % (
            openbravo_organization_ids[request.database],
            openbravo_organization, obj.operation.source,
            obj.quantity, datetime.strftime(obj.startdate, "%Y-%m-%d %H:%M:%S"),
            datetime.strftime(obj.enddate, "%Y-%m-%d %H:%M:%S")
            ))
    body.append("</ob:Openbravo>")
    try:
      # Send the data to openbravo
      get_data(
        "/ws/org.openbravo.warehouse.advancedwarehouseoperations.manufacturing.AddWorkRequirementsWS",
        openbravo_host, openbravo_user, openbravo_password,
        method="PUT",
        xmldoc='\n'.join(body),
        headers={'DoProcess': 'true'}
        )
      # Now save the changed status also in our database
      for obj in cleaned_MO_records:
        obj.save(using=request.database)

    except Exception as e:
      # Something went wrong in the connection
      return HttpResponse(content=str(e), status=500)


  # Build the distribution and purchase orders
  if cleaned_records:
    body = [
      #'<?xml version="1.0" encoding="UTF-8"?>',
      '<ob:Openbravo xmlns:ob="http://www.openbravo.com">',
      ]
    if exportPurchasingPlan:
      identifier = uuid4().hex
      url = "/ws/dal/MRPPurchasingRun"
      body.append('''<MRPPurchasingRun id="%s">
        <organization id="%s" entity-name="Organization" identifier="%s"/>
        <active>true</active>
        <name>FREPPLE %s</name>
        <description>Incremental export triggered by %s</description>
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

    try:
      # Send the data to openbravo
      get_data(
        url, openbravo_host, openbravo_user, openbravo_password,
        method="POST", xmldoc='\n'.join(body)
        )

      # Now save the changed status also in our database
      for obj in cleaned_records:
        obj.save(using=request.database)

      return HttpResponse("OK")
    except Exception as e:
      # Something went wrong in the connection
      return HttpResponse(content=str(e), status=500)

  # Exported everything successfully
  return HttpResponse("OK")
