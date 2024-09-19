#
# Copyright (C) 2016 by frePPLe bv
#
# Permission is hereby granted, free of charge, to any person obtaining
# a copy of this software and associated documentation files (the
# "Software"), to deal in the Software without restriction, including
# without limitation the rights to use, copy, modify, merge, publish,
# distribute, sublicense, and/or sell copies of the Software, and to
# permit persons to whom the Software is furnished to do so, subject to
# the following conditions:
#
# The above copyright notice and this permission notice shall be
# included in all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND,
# EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF
# MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND
# NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE
# LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION
# OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION
# WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.
#

import base64
import email
from html.parser import HTMLParser
import json
import jwt
import time
from urllib.request import urlopen, HTTPError, Request, URLError
from xml.sax.saxutils import quoteattr

from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse, HttpResponseServerError, HttpResponseNotAllowed
from django.utils.translation import gettext_lazy as _
from django.views.decorators.csrf import csrf_protect

from freppledb.input.models import PurchaseOrder, DistributionOrder, OperationPlan
from freppledb.common.models import Parameter

import logging

logger = logging.getLogger(__name__)


@login_required
@csrf_protect
def Upload(request):
    if request.method != "POST":
        return HttpResponseNotAllowed("Only POST requests are allowed")
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
        token = jwt.encode(
            {"exp": round(time.time()) + 600, "user": odoo_user},
            settings.DATABASES[request.database].get(
                "SECRET_WEBTOKEN_KEY", settings.SECRET_KEY
            ),
            algorithm="HS256",
        )
        if not isinstance(token, str):
            token = token.decode("ascii")
        data_odoo = [
            "--%s" % boundary,
            'Content-Disposition: form-data; name="webtoken"\r',
            "\r",
            "%s\r" % token,
            "--%s\r" % boundary,
            'Content-Disposition: form-data; name="database"',
            "",
            odoo_db,
            "--%s" % boundary,
            'Content-Disposition: form-data; name="language"',
            "",
            Parameter.getValue("odoo.language", request.database, "en_US"),
            "--%s" % boundary,
            'Content-Disposition: form-data; name="company"',
            "",
            odoo_company,
            "--%s" % boundary,
            'Content-Disposition: form-data; name="mode"',
            "",
            "2",  # Marks incremental export
            "--%s" % boundary,
            'Content-Disposition: form-data; name="actual_user"',
            "",
            request.user.username,
            "--%s" % boundary,
            'Content-Disposition: file; name="frePPLe plan"; filename="frepple_plan.xml"',
            "Content-Type: application/xml",
            "",
            '<?xml version="1.0" encoding="UTF-8" ?>',
            '<plan xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"><operationplans>',
        ]

        # Validate records which exist in the database
        data = json.loads(request.body.decode("utf-8"))
        data_ok = False
        obj = []
        for rec in data:
            try:
                if not "reference" in rec:
                    continue
                elif rec.get("type", None) == "PO":
                    po = PurchaseOrder.objects.using(request.database).get(
                        reference=rec["reference"]
                    )
                    if (
                        not po.supplier.source
                        or not (
                            po.status == "proposed"
                            or (
                                po.status in ("approved", "confirmed")
                                and po.source == "odoo_1"
                            )
                        )
                        or not po.item
                        or not po.item.source
                        or po.item.type == "make to order"
                    ):
                        continue
                    data_ok = True
                    obj.append(po)
                    data_odoo.append(
                        '<operationplan ordertype="PO" id="%s" item=%s location=%s supplier=%s start="%s" end="%s" quantity="%s" location_id=%s item_id=%s criticality="%d" batch=%s status=%s/>'
                        % (
                            po.reference,
                            quoteattr(po.item.name),
                            quoteattr(po.location.name),
                            quoteattr(po.supplier.name),
                            po.startdate,
                            po.enddate,
                            po.quantity,
                            quoteattr(po.location.subcategory or ""),
                            quoteattr(po.item.subcategory or ""),
                            int(po.criticality),
                            quoteattr(po.batch or ""),
                            quoteattr(po.status),
                        )
                    )
                elif rec.get("type", None) == "DO":
                    do = DistributionOrder.objects.using(request.database).get(
                        reference=rec["reference"]
                    )
                    if (
                        not do.origin.source
                        or not do.destination.source
                        or do.status != "proposed"
                        or not do.item
                        or not do.item.source
                        or do.item.type == "make to order"
                    ):
                        continue
                    data_ok = True
                    obj.append(do)
                    data_odoo.append(
                        '<operationplan status="%s" reference="%s" ordertype="DO" item=%s origin=%s destination=%s start="%s" end="%s" quantity="%s" origin_id=%s destination_id=%s item_id=%s criticality="%d" batch=%s/>'
                        % (
                            do.status,
                            do.reference,
                            quoteattr(do.item.name),
                            quoteattr(do.origin.name),
                            quoteattr(do.destination.name),
                            do.startdate,
                            do.enddate,
                            do.quantity,
                            quoteattr(do.origin.subcategory or ""),
                            quoteattr(do.destination.subcategory or ""),
                            quoteattr(do.item.subcategory or ""),
                            int(do.criticality or 0),
                            quoteattr(do.batch or ""),
                        )
                    )
                else:
                    op = OperationPlan.objects.using(request.database).get(
                        reference=rec["reference"]
                    )
                    if op.owner and op.owner.status in (
                        "proposed",
                        "approved",
                        "confirmed",
                    ):
                        # We are only sending the MOs with the detail of their WOs
                        op = op.owner
                    if (
                        not op.operation.source
                        or not (
                            op.status == "proposed"
                            or (
                                op.status in ("approved", "confirmed")
                                and op.source == "odoo_1"
                            )
                        )
                        or op in obj
                        or not op.item
                        or (op.item.type == "make to order" and op.status == "proposed")
                        or not op.location
                        or not op.operation
                    ):
                        continue
                    data_ok = True
                    obj.append(op)
                    if op.operation.category == "subcontractor":
                        data_odoo.append(
                            '<operationplan ordertype="PO" id="%s" item=%s location=%s supplier=%s start="%s" end="%s" quantity="%s" location_id=%s item_id=%s criticality="%d" batch=%s/>'
                            % (
                                op.reference,
                                quoteattr(op.item.name),
                                quoteattr(op.location.name),
                                quoteattr(op.operation.subcategory or ""),
                                op.startdate,
                                op.enddate,
                                op.quantity,
                                quoteattr(op.location.subcategory or ""),
                                quoteattr(op.item.subcategory or ""),
                                int(op.criticality or 0),
                                quoteattr(op.batch or ""),
                            )
                        )
                    else:
                        data_odoo.append(
                            '<operationplan ordertype="MO" reference="%s" item=%s location=%s operation=%s start="%s" end="%s" quantity="%s" location_id=%s item_id=%s criticality="%d" batch=%s status=%s>'
                            % (
                                op.reference,
                                quoteattr(op.operation.item.name),
                                quoteattr(op.operation.location.name),
                                quoteattr(op.operation.name),
                                op.startdate,
                                op.enddate,
                                op.quantity,
                                quoteattr(op.operation.location.subcategory or ""),
                                quoteattr(op.operation.item.subcategory or ""),
                                int(op.criticality or 0),
                                quoteattr(op.batch or ""),
                                quoteattr(op.status),
                            )
                        )
                        wolist = [
                            i
                            for i in op.xchildren.using(request.database)
                            .all()
                            .order_by("operation__priority")
                        ]
                        if wolist:
                            for wo in wolist:
                                data_odoo.append(
                                    '<workorder operation=%s start="%s" end="%s">'
                                    % (
                                        quoteattr(wo.operation.name),
                                        wo.startdate,
                                        wo.enddate,
                                    )
                                )
                                for wores in wo.resources.using(request.database).all():
                                    if (
                                        wores.resource.source
                                        and wores.resource.source.startswith("odoo")
                                    ):
                                        data_odoo.append(
                                            '<resource name=%s id=%s quantity="%s"/>'
                                            % (
                                                quoteattr(wores.resource.name),
                                                quoteattr(
                                                    wores.resource.category or ""
                                                ),
                                                wores.quantity,
                                            )
                                        )
                                data_odoo.append("</workorder>")
                        else:
                            for opplanres in op.resources.using(request.database).all():
                                if (
                                    opplanres.resource.source
                                    and opplanres.resource.source.startswith("odoo")
                                ):
                                    data_odoo.append(
                                        "<resource name=%s id=%s/>"
                                        % (
                                            quoteattr(opplanres.resource.name),
                                            quoteattr(
                                                opplanres.resource.category or ""
                                            ),
                                        )
                                    )
                        data_odoo.append("</operationplan>")

            except Exception as e:
                logger.error("Exception during odoo export: %s" % e)
        if not data_ok:
            return HttpResponseServerError(_("No proposed data records selected"))

        # Send the data to Odoo
        data_odoo.append("</operationplans></plan>")
        data_odoo.append("--%s--" % boundary)
        data_odoo.append("")
        body = "\n".join(data_odoo).encode("utf-8")
        size = len(body)
        encoded = base64.encodebytes(
            ("%s:%s" % (odoo_user, odoo_password)).encode("utf-8")
        )
        logger.debug("Uploading %d bytes of planning results to Odoo" % size)
        url = Parameter.getValue("odoo.url", request.database)
        req = Request(
            "%s%sfrepple/xml/"
            % (
                url,
                "/" if not url.endswith("/") else "",
            ),
            data=body,
            headers={
                "Authorization": "Basic %s" % encoded.decode("ascii")[:-1],
                "Content-Type": "multipart/form-data; boundary=%s" % boundary,
                "Content-length": size,
            },
        )

        # Read the response
        with urlopen(req) as f:
            msg = f.read()
            logger.debug("Odoo response: %s" % msg.decode("utf-8"))
        for i in obj:
            if i.status == "proposed":
                i.status = "approved"
                i.source = "odoo_1"
                i.save(using=request.database)
        return HttpResponse("OK")

    except HTTPError as e:
        odoo_data = e.read()
        if odoo_data:

            class OdooMsgParser(HTMLParser):
                def handle_data(self, data):
                    if "Error processing data" in data:
                        self.echo = True
                        logger.error("Odoo stack trace:")
                    elif hasattr(self, "echo"):
                        logger.error("Odoo: %s" % data)

            odoo_msg = OdooMsgParser()
            odoo_msg.feed(odoo_data.decode("utf-8"))
        return HttpResponseServerError("Internal server error %s on odoo side" % e.code)

    except URLError:
        logger.error("Can't connect to the Odoo server")
        return HttpResponseServerError("Can't connect to the odoo server")

    except Exception as e:
        logger.error(e)
        return HttpResponseServerError("Internal server error on frepple side")
