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
from datetime import datetime
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

from freppledb.input.models import (
    PurchaseOrder,
    DistributionOrder,
    OperationPlan,
    Supplier,
)
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
        boundary = "**MessageBoundary**"

        odoo_db = (
            getattr(settings, "ODOO_DB", {}).get(request.database, "")
            or Parameter.getValue("odoo.db", request.database, "")
        ).strip()
        odoo_company = (
            getattr(settings, "ODOO_COMPANY", {}).get(request.database, "")
            or Parameter.getValue("odoo.company", request.database, "")
        ).strip()
        odoo_user = (
            getattr(settings, "ODOO_USER", {}).get(request.database, "")
            or Parameter.getValue("odoo.user", request.database, "")
        ).strip()
        odoo_password = (
            getattr(settings, "ODOO_PASSWORDS", {}).get(request.database, "")
            or Parameter.getValue("odoo.password", request.database, "")
        ).strip()
        odoo_url = (
            getattr(settings, "ODOO_URL", {}).get(request.database, "")
            or Parameter.getValue("odoo.url", request.database, "")
        ).strip()
        if not odoo_url.endswith("/"):
            odoo_url = odoo_url + "/"
        if (
            not odoo_db
            or not odoo_company
            or not odoo_user
            or not odoo_password
            or not odoo_url
        ):
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
        obj = []
        for rec in data:
            try:
                reference = rec.get(
                    "reference", rec.get("operationplan__reference", None)
                )
                type = rec.get("operationplan__type", rec.get("type", None))
                if not reference or not rec["quantity"]:
                    continue

                # check if some records were updated by the user
                op = OperationPlan.objects.using(request.database).get(
                    reference=reference
                )

                # date format can be "%Y-%m-%dT%H:%M:%S" if coming from sales orders
                # otherwise settings.DATETIME_INPUT_FORMATS[0]
                if rec.get("enddate"):
                    try:
                        # SO table
                        enddate = datetime.strptime(
                            rec.get("enddate"), "%Y-%m-%dT%H:%M:%S"
                        )
                    except:
                        # PO/MO/DO table
                        enddate = datetime.strptime(
                            rec.get("enddate"),
                            (
                                settings.DATETIME_INPUT_FORMATS[0]
                                if settings.DATE_STYLE_WITH_HOURS
                                else settings.DATE_INPUT_FORMATS[0]
                            ),
                        )
                else:
                    # inventory/resource detail table
                    enddate = datetime.strptime(
                        rec.get("operationplan__enddate"),
                        (
                            settings.DATETIME_INPUT_FORMATS[0]
                            if settings.DATE_STYLE_WITH_HOURS
                            else settings.DATE_INPUT_FORMATS[0]
                        ),
                    )

                if op.enddate != enddate:
                    op.enddate = enddate
                    op.dirty = True

                supplier = rec.get("supplier", rec.get("operationplan__supplier__name"))
                if op.supplier and supplier and op.supplier.name != supplier:
                    s = Supplier.objects.using(request.database).get(name=supplier)
                    op.supplier = s
                    op.dirty = True

                if op.quantity != rec["quantity"]:
                    op.quantity = rec["quantity"]
                    op.dirty = True

                if type == "PO":
                    if (
                        not op.supplier.source
                        or not (
                            op.status == "proposed"
                            or (
                                op.status in ("approved", "confirmed")
                                and op.source == "odoo_1"
                            )
                        )
                        or not op.item
                        or not op.item.source
                        or op.item.type == "make to order"
                    ):
                        continue

                    obj.append(op)
                    data_odoo.append(
                        '<operationplan ordertype="PO" id="%s" item=%s location=%s supplier=%s start="%s" end="%s" quantity="%s" location_id=%s item_id=%s criticality="%d" batch=%s status=%s remark=%s/>'
                        % (
                            op.reference,
                            quoteattr(op.item.name),
                            quoteattr(op.location.name),
                            quoteattr(op.supplier.name),
                            op.startdate,
                            op.enddate,
                            op.quantity,
                            quoteattr(op.location.subcategory or ""),
                            quoteattr(op.item.subcategory or ""),
                            int(op.criticality or 0),
                            quoteattr(op.batch or ""),
                            quoteattr(op.status),
                            quoteattr(getattr(op, "remark", None) or ""),
                        )
                    )
                elif type == "DO":
                    op = DistributionOrder.objects.using(request.database).get(
                        reference=reference
                    )
                    if (
                        not op.origin.source
                        or not op.destination.source
                        or op.status != "proposed"
                        or not op.item
                        or not op.item.source
                        or op.item.type == "make to order"
                    ):
                        continue

                    obj.append(op)
                    data_odoo.append(
                        '<operationplan status="%s" reference="%s" ordertype="DO" item=%s origin=%s destination=%s start="%s" end="%s" quantity="%s" origin_id=%s destination_id=%s item_id=%s criticality="%d" batch=%s remark=%s/>'
                        % (
                            op.status,
                            op.reference,
                            quoteattr(op.item.name),
                            quoteattr(op.origin.name),
                            quoteattr(op.destination.name),
                            op.startdate,
                            op.enddate,
                            op.quantity,
                            quoteattr(op.origin.subcategory or ""),
                            quoteattr(op.destination.subcategory or ""),
                            quoteattr(op.item.subcategory or ""),
                            int(op.criticality or 0),
                            quoteattr(op.batch or ""),
                            quoteattr(getattr(op, "remark", None) or ""),
                        )
                    )
                elif type not in ("DLVR", "STCK"):

                    if op.owner and op.owner.status in (
                        "proposed",
                        "approved",
                        "confirmed",
                    ):
                        # We are only sending the MOs with the detail of their WOs
                        op = op.owner
                    if (
                        not op.operation
                        or not op.operation.source
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

                    obj.append(op)
                    if op.operation.category == "subcontractor":
                        data_odoo.append(
                            '<operationplan ordertype="PO" id="%s" item=%s location=%s supplier=%s start="%s" end="%s" quantity="%s" location_id=%s item_id=%s criticality="%d" batch=%s remark=%s/>'
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
                                quoteattr(getattr(op, "remark", None) or ""),
                            )
                        )
                    else:
                        data_odoo.append(
                            '<operationplan ordertype="MO" reference="%s" item=%s location=%s operation=%s start="%s" end="%s" quantity="%s" location_id=%s item_id=%s criticality="%d" batch=%s status=%s remark=%s>'
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
                                quoteattr(getattr(op, "remark", None) or ""),
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
                                net_duration = wo.enddate - wo.startdate
                                if wo.plan:
                                    for w in wo.plan.get("interruptions", []):
                                        net_duration -= datetime.strptime(
                                            w[1], "%Y-%m-%d %H:%M:%S"
                                        ) - datetime.strptime(w[0], "%Y-%m-%d %H:%M:%S")
                                data_odoo.append(
                                    '<workorder operation=%s start="%s" end="%s" remark=%s net_duration="%s">'
                                    % (
                                        quoteattr(wo.operation.name),
                                        wo.startdate,
                                        wo.enddate,
                                        quoteattr(getattr(wo, "remark", None) or ""),
                                        int(net_duration.total_seconds()),
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
        if not obj:
            return HttpResponse(status=204)

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
        req = Request(
            "%sfrepple/xml/" % odoo_url,
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
            elif hasattr(i, "dirty"):
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
