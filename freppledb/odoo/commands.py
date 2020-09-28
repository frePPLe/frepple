#
# Copyright (C) 2007-2016 by frePPLe bv
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
import logging
from urllib.request import urlopen, HTTPError, Request
from xml.sax.saxutils import quoteattr

from django.utils.http import urlencode

from django.db import DEFAULT_DB_ALIAS
from django.conf import settings
from django.utils.translation import gettext_lazy as _

from freppledb.common.models import Parameter
from freppledb.common.commands import (
    PlanTaskRegistry,
    PlanTask,
    PlanTaskParallel,
    PlanTaskSequence,
)
from freppledb.input.commands import LoadTask

logger = logging.getLogger(__name__)


@PlanTaskRegistry.register
class OdooReadData(PlanTask):
    """
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
    """

    description = "Load Odoo data"
    sequence = 119
    label = ("odoo_read_1", _("Read Odoo data"))

    @classmethod
    def getWeight(cls, database=DEFAULT_DB_ALIAS, **kwargs):
        for i in range(5):
            if ("odoo_read_%s" % i) in os.environ:
                cls.mode = i
                for stdLoad in PlanTaskRegistry.reg.steps:
                    if isinstance(stdLoad, (PlanTaskParallel, PlanTaskSequence)):
                        continue
                    if issubclass(stdLoad, LoadTask):
                        stdLoad.filter = (
                            "(source is null or source<>'odoo_%s')" % cls.mode
                        )
                        stdLoad.description += " - non-odoo source"
                PlanTaskRegistry.addArguments(exportstatic=True, source="odoo_%s" % i)
                return 1
        return -1

    @classmethod
    def run(cls, database=DEFAULT_DB_ALIAS, **kwargs):
        import frepple

        # Uncomment the following lines to bypass the connection to odoo and use
        # a XML flat file alternative. This can be useful for debugging.
        # with open("my_path/my_data_file.xml", 'rb') as f:
        #  frepple.readXMLdata(f.read().decode('utf-8'), False, False)
        #  frepple.printsize()
        #  return

        odoo_user = Parameter.getValue("odoo.user", database)
        odoo_password = settings.ODOO_PASSWORDS.get(database, None)
        if not settings.ODOO_PASSWORDS.get(database):
            odoo_password = Parameter.getValue("odoo.password", database)
        odoo_db = Parameter.getValue("odoo.db", database)
        odoo_url = Parameter.getValue("odoo.url", database).strip()
        if not odoo_url.endswith("/"):
            odoo_url = odoo_url + "/"

        odoo_company = Parameter.getValue("odoo.company", database)
        ok = True

        # Set debugFile=PathToXmlFile if you want frePPLe to read that file
        # rather than the data at url
        # else leave it to False
        debugFile = False  # "c:/temp/frepple_data.xml"

        if not odoo_user and not debugFile:
            logger.error("Missing or invalid parameter odoo.user")
            ok = False
        if not odoo_password and not debugFile:
            logger.error("Missing or invalid parameter odoo.password")
            ok = False
        if not odoo_db and not debugFile:
            logger.error("Missing or invalid parameter odoo.db")
            ok = False
        if not odoo_url and not debugFile:
            logger.error("Missing or invalid parameter odoo.url")
            ok = False
        if not odoo_company and not debugFile:
            logger.error("Missing or invalid parameter odoo.company")
            ok = False
        odoo_language = Parameter.getValue("odoo.language", database, "en_US")
        if not ok and not debugFile:
            raise Exception("Odoo connector not configured correctly")

        # Connect to the odoo URL to GET data
        try:
            loglevel = int(Parameter.getValue("odoo.loglevel", database, "0"))
        except Exception:
            loglevel = 0

        if not debugFile:
            url = "%sfrepple/xml?%s" % (
                odoo_url,
                urlencode(
                    {
                        "database": odoo_db,
                        "language": odoo_language,
                        "company": odoo_company,
                        "mode": cls.mode,
                    }
                ),
            )
            try:
                request = Request(url)
                encoded = base64.encodestring(
                    ("%s:%s" % (odoo_user, odoo_password)).encode("utf-8")
                )[:-1]
                request.add_header(
                    "Authorization", "Basic %s" % encoded.decode("ascii")
                )
            except HTTPError as e:
                logger.error("Error connecting to odoo at %s: %s" % (url, e))
                raise e

            # Download and parse XML data
            with urlopen(request) as f:
                frepple.readXMLdata(f.read().decode("utf-8"), False, False, loglevel)
        else:
            # Download and parse XML data
            with open(debugFile) as f:
                frepple.readXMLdata(f.read(), False, False, loglevel)

        # Hierarchy correction: Count how many items/locations/customers have no owner
        # If we find 2+ then we use All items/All customers/All locations as root
        # otherwise we assume that the hierarchy is correct
        rootItem = None
        for r in frepple.items():
            if r.owner is None:
                if not rootItem:
                    rootItem = r
                else:
                    rootItem = None
                    break
        rootLocation = None
        for r in frepple.locations():
            if r.owner is None:
                if not rootLocation:
                    rootLocation = r
                else:
                    rootLocation = None
                    break
        rootCustomer = None
        for r in frepple.customers():
            if r.owner is None:
                if not rootCustomer:
                    rootCustomer = r
                else:
                    rootCustomer = None
                    break

        if not rootItem:
            rootItem = frepple.item_mts(name="All items", source="odoo_%s" % cls.mode)
            for r in frepple.items():
                if r.owner is None and r != rootItem:
                    r.owner = rootItem
        if not rootLocation:
            rootLocation = frepple.location(
                name="All locations", source="odoo_%s" % cls.mode
            )

            for r in frepple.locations():
                if r.owner is None and r != rootLocation:
                    r.owner = rootLocation
        if not rootCustomer:
            rootCustomer = frepple.customer(
                name="All customers", source="odoo_%s" % cls.mode
            )
            if rootCustomer:
                print("%s" % rootCustomer.name)
            for r in frepple.customers():
                if r.owner is None and r != rootCustomer:
                    print("Assigning root customer to %s" % r.name)
                    r.owner = rootCustomer
                    print("%s %s" % (r.name, r.owner.name))


@PlanTaskRegistry.register
class OdooWritePlan(PlanTask):
    """
  Uploads operationplans to odoo.
    - Sends all operationplans, meeting the criteria:
      a) status = 'proposed' or 'approved'
         Other operationplans are input to the plan, and not output.
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
    - This code doesn't interpret any of the results. An odoo addon module
      will need to read the content, and take appropriate actions in odoo:
      such as creating purchase orders, manufacturing orders, work orders,
      project tasks, etc...
  """

    description = "Write results to Odoo"
    sequence = 390
    label = ("odoo_write", _("Write results to Odoo"))

    @classmethod
    def getWeight(cls, database=DEFAULT_DB_ALIAS, **kwargs):
        if "odoo_write" in os.environ:
            return 1
        else:
            return -1

    @classmethod
    def run(cls, database=DEFAULT_DB_ALIAS, **kwargs):
        import frepple

        odoo_user = Parameter.getValue("odoo.user", database)
        odoo_password = settings.ODOO_PASSWORDS.get(database, None)
        if not settings.ODOO_PASSWORDS.get(database):
            odoo_password = Parameter.getValue("odoo.password", database)
        odoo_db = Parameter.getValue("odoo.db", database)
        odoo_url = Parameter.getValue("odoo.url", database)
        odoo_company = Parameter.getValue("odoo.company", database)
        ok = True
        if not odoo_user:
            logger.error("Missing or invalid parameter odoo.user")
            ok = False
        if not odoo_password:
            logger.error("Missing or invalid parameter odoo.password")
            ok = False
        if not odoo_db:
            logger.error("Missing or invalid parameter odoo.db")
            ok = False
        if not odoo_url:
            logger.error("Missing or invalid parameter odoo.url")
            ok = False
        if not odoo_company:
            logger.error("Missing or invalid parameter odoo.company")
            ok = False
        odoo_language = Parameter.getValue("odoo.language", database, "en_US")
        if not ok:
            raise Exception("Odoo connector not configured correctly")
        boundary = email.generator._make_boundary()

        # Generator function
        # We generate output in the multipart/form-data format.
        # We send the connection parameters as well as a file with the planning
        # results in XML-format.
        # TODO respect the parameters odoo.filter_export_purchase_order, odoo.filter_export_manufacturing_order, odoo.filter_export_distribution_order
        # these are python expressions - attack-sensitive evaluation!
        def publishPlan(cls):
            yield "--%s\r" % boundary
            yield 'Content-Disposition: form-data; name="webtoken"\r'
            yield "\r"
            yield "%s\r" % jwt.encode(
                {"exp": round(time.time()) + 600, "user": odoo_user},
                settings.DATABASES[database].get(
                    "SECRET_WEBTOKEN_KEY", settings.SECRET_KEY
                ),
                algorithm="HS256",
            ).decode("ascii")
            yield "--%s\r" % boundary
            yield 'Content-Disposition: form-data; name="database"\r'
            yield "\r"
            yield "%s\r" % odoo_db
            yield "--%s\r" % boundary
            yield 'Content-Disposition: form-data; name="language"\r'
            yield "\r"
            yield "%s\r" % odoo_language
            yield "--%s\r" % boundary
            yield 'Content-Disposition: form-data; name="company"\r'
            yield "\r"
            yield "%s\r" % odoo_company
            yield "--%s\r" % boundary
            yield 'Content-Disposition: file; name="frePPLe plan"; filename="frepple_plan.xml"\r'
            yield "Content-Type: application/xml\r"
            yield "\r"
            yield '<?xml version="1.0" encoding="UTF-8" ?>'
            yield '<plan xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance">'
            # Export relevant operationplans
            yield "<operationplans>"
            for i in frepple.operationplans():
                if i.ordertype == "PO":
                    if (
                        not i.item
                        or not i.item.source
                        or not i.item.source.startswith("odoo")
                        or i.status not in ("proposed", "approved")
                    ):
                        continue
                    cls.exported.append(i)
                    yield '<operationplan id="%s" ordertype="PO" item=%s location=%s supplier=%s start="%s" end="%s" quantity="%s" location_id=%s item_id=%s criticality="%d"/>' % (
                        i.id,
                        quoteattr(i.item.name),
                        quoteattr(i.location.name),
                        quoteattr(i.supplier.name),
                        i.start,
                        i.end,
                        i.quantity,
                        quoteattr(i.location.subcategory),
                        quoteattr(i.item.subcategory),
                        int(i.criticality),
                    )
                elif i.ordertype == "MO":
                    if (
                        not i.operation
                        or not i.operation.source
                        or not i.operation.item
                        or not i.operation.source.startswith("odoo")
                        or i.status not in ("proposed", "approved")
                    ):
                        continue
                    cls.exported.append(i)
                    res = set()
                    try:
                        for j in i.loadplans:
                            res.add(j.resource.name)
                    except Exception:
                        pass
                    demand = {}
                    demand_str = ""
                    for d in i.pegging_demand:
                        demand[d.demand] = d.quantity
                        demand_str += "%s:%s, " % (d.demand, d.quantity)
                    if demand_str:
                        demand_str = demand_str[:-2]
                    yield '<operationplan id="%s" ordertype="MO" item=%s location=%s operation=%s start="%s" end="%s" quantity="%s" location_id=%s item_id=%s criticality="%d" resource=%s demand=%s/>' % (
                        i.id,
                        quoteattr(i.operation.item.name),
                        quoteattr(i.operation.location.name),
                        quoteattr(i.operation.name),
                        i.start,
                        i.end,
                        i.quantity,
                        quoteattr(i.operation.location.subcategory),
                        quoteattr(i.operation.item.subcategory),
                        int(i.criticality),
                        quoteattr(",".join(res)),
                        quoteattr(demand_str),
                    )
            yield "</operationplans>"
            yield "</plan>"
            yield "--%s--\r" % boundary
            yield "\r"

        # Connect to the odoo URL to POST data
        try:
            cls.exported = []
            body = "\n".join(publishPlan(cls)).encode("utf-8")
            size = len(body)
            encoded = base64.encodestring(
                ("%s:%s" % (odoo_user, odoo_password)).encode("utf-8")
            )
            req = Request(
                "%sfrepple/xml/" % odoo_url,
                data=body,
                headers={
                    "Authorization": "Basic %s" % encoded.decode("ascii")[:-1],
                    "Content-Type": "multipart/form-data; boundary=%s" % boundary,
                    "Content-length": size,
                },
            )

            # Posting the data and displaying the server response
            logger.info("Uploading %d bytes of planning results to odoo" % size)
            with urlopen(req) as f:
                msg = f.read()
                logger.info("Odoo response: %s" % msg.decode("utf-8"))

            # Mark the exported operations as approved
            for i in cls.exported:
                i.status = "approved"
            del cls.exported

        except HTTPError as e:
            logger.error("Error connecting to odoo %s" % e.read())
