#
# Copyright (C) 2016 by frePPLe bvba
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
import json
import jwt
import time
from urllib.request import urlopen, HTTPError, Request
from xml.sax.saxutils import quoteattr

from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse, HttpResponseServerError
from django.utils.translation import ugettext_lazy as _
from django.views.decorators.csrf import csrf_protect

from freppledb.input.models import PurchaseOrder, DistributionOrder, OperationPlan
from freppledb.common.models import Parameter

import logging
logger = logging.getLogger(__name__)


@login_required
@csrf_protect
def Upload(request):
  try:
    # Prepare a message for odoo
    boundary = email.generator._make_boundary()
    odoo_db = Parameter.getValue("odoo.db", request.database)
    odoo_company = Parameter.getValue("odoo.company", request.database)
    odoo_user = Parameter.getValue("odoo.user", request.database)
    odoo_password = settings.ODOO_PASSWORDS.get(request.database, None)
    if not odoo_password:
      odoo_password = Parameter.getValue("odoo.password", request.database)
    if not odoo_db or not odoo_company or not odoo_user or not odoo_password:
      return HttpResponseServerError(_("Invalid configuration parameters"))
    data_odoo = [
      '--%s' % boundary,
      'Content-Disposition: form-data; name="webtoken"\r',
      '\r',
      '%s\r' % jwt.encode({
        'exp': round(time.time()) + 600,
        'user': odoo_user,
        },
        settings.DATABASES[request.database].get('SECRET_WEBTOKEN_KEY', settings.SECRET_KEY),
        algorithm='HS256').decode('ascii'),
      '--%s\r' % boundary,
      'Content-Disposition: form-data; name="database"',
      '',
      odoo_db,
      '--%s' % boundary,
      'Content-Disposition: form-data; name="language"',
      '',
      Parameter.getValue("odoo.language", request.database, 'en_US'),
      '--%s' % boundary,
      'Content-Disposition: form-data; name="company"',
      '',
      odoo_company,
      '--%s' % boundary,
      'Content-Disposition: form-data; name="mode"',
      '',
      '2',   # Marks incremental export
      '--%s' % boundary,
      'Content-Disposition: file; name="frePPLe plan"; filename="frepple_plan.xml"',
      'Content-Type: application/xml',
      '',
      '<?xml version="1.0" encoding="UTF-8" ?>',
      '<plan xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"><operationplans>'
      ]

    # Validate records which exist in the database
    data = json.loads(request.body.decode('utf-8'))
    data_ok = False
    obj = []
    for rec in data:
      try:
        if rec['type'] == 'PO':
          po = PurchaseOrder.objects.using(request.database).get(id=rec['id'])
          if not po.supplier.source or po.status != 'proposed' or not po.item.source:
            continue
          data_ok = True
          obj.append(po)
          data_odoo.append(
            '<operationplan ordertype="PO" id="%s" item=%s location=%s supplier=%s start="%s" end="%s" quantity="%s" location_id=%s item_id=%s criticality="%d"/>' % (
            po.id, quoteattr(po.item.name), quoteattr(po.location.name), 
            quoteattr(po.supplier.name), po.startdate, po.enddate, po.quantity,
            quoteattr(po.location.subcategory), quoteattr(po.item.subcategory),
            int(po.criticality)
            ))
        elif rec['type'] == 'DO':
          do = DistributionOrder.objects.using(request.database).get(id=rec['id'])
          if not do.origin.source or do.status != 'proposed' or not do.item.source:
            continue
          data_ok = True
          obj.append(do)
          data_odoo.append(
            '<operationplan ordertype="DO" id="%s" item=%s origin=%s location=%s start="%s" end="%s" quantity="%s" location_id=%s item_id=%s criticality="%d"/>' % (
            do.id, quoteattr(do.item.name), quoteattr(do.origin.name), 
            quoteattr(do.location.name), do.startdate, do.enddate, do.quantity,
            quoteattr(do.location.subcategory), quoteattr(do.item.subcategory),
            int(do.criticality)
            ))
        else:
          op = OperationPlan.objects.using(request.database).get(id=rec['id'])
          if not op.operation.source or op.status != 'proposed':
            continue
          data_ok = True
          obj.append(op)
          data_odoo.append(
            '<operationplan ordertype="MO" id="%s" item=%s location=%s operation=%s start="%s" end="%s" quantity="%s" location_id=%s item_id=%s criticality="%d"/>' % (
              op.id, quoteattr(op.operation.item.name),
              quoteattr(op.operation.location.name), quoteattr(op.operation.name),
              op.startdate, op.enddate, op.quantity,
              quoteattr(op.operation.location.subcategory), quoteattr(op.operation.item.subcategory),
              int(op.criticality)
            ))
      except:
        pass
    if not data_ok:
      return HttpResponseServerError(_("No proposed data records selected"))

    # Send the data to Odoo
    data_odoo.append('</operationplans></plan>')
    data_odoo.append('--%s--' % boundary)
    data_odoo.append('')
    body = '\n'.join(data_odoo).encode('utf-8')
    size = len(body)
    encoded = base64.encodestring(('%s:%s' % (odoo_user, odoo_password)).encode('utf-8'))
    logger.debug("Uploading %d bytes of planning results to Odoo" % size)
    req = Request(
      "%sfrepple/xml/" % Parameter.getValue("odoo.url", request.database),
      data=body,
      headers={
        'Authorization': "Basic %s" % encoded.decode('ascii')[:-1],
        'Content-Type': 'multipart/form-data; boundary=%s' % boundary,
        'Content-length': size
        }
      )

    # Read the response
    with urlopen(req) as f:
      msg = f.read()
      logger.debug("Odoo response: %s" % msg.decode('utf-8'))
    for i in obj:
      i.status = "approved"
      i.source = "odoo_1"
      i.save(using=request.database)
    return HttpResponse("OK")

  except HTTPError:
    logger.error("Can't connect to the Odoo server")
    return HttpResponseServerError("Can't connect to the odoo server")

  except Exception as e:
    logger.error(e)
    return HttpResponseServerError("internal server error")
