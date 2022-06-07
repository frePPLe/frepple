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

from html.parser import HTMLParser
import os
import logging
from urllib.request import urlopen, HTTPError, Request

from django.utils.http import urlencode

from django.db import DEFAULT_DB_ALIAS, connections
from django.conf import settings

from freppledb.common.models import Parameter
from freppledb.common.commands import (
    PlanTaskRegistry,
    PlanTask,
    PlanTaskParallel,
    PlanTaskSequence,
)
from freppledb.input.commands import (
    LoadTask,
    loadOperationPlans,
    loadOperationPlanMaterials,
)

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
    sequence = 70

    @classmethod
    def getWeight(cls, database=DEFAULT_DB_ALIAS, **kwargs):
        for i in range(5):
            if ("odoo_read_%s" % i) in os.environ:
                cls.mode = i
                if (
                    Parameter.getValue(
                        "odoo.allowSharedOwnership", database=database, default="false"
                    ).lower()
                    == "true"
                ):
                    for stdLoad in PlanTaskRegistry.reg.steps:
                        if isinstance(stdLoad, (PlanTaskParallel, PlanTaskSequence)):
                            continue
                        if issubclass(stdLoad, LoadTask):
                            if stdLoad in (
                                loadOperationPlans,
                                loadOperationPlanMaterials,
                            ):
                                stdLoad.filter = "false"
                            else:
                                stdLoad.filter = (
                                    "(source is null or source<>'odoo_%s')" % cls.mode
                                )
                            stdLoad.description += " - non-odoo source"
                    PlanTaskRegistry.addArguments(
                        exportstatic=True, source="odoo_%s" % i
                    )
                else:
                    PlanTaskRegistry.addArguments(
                        exportstatic=True, source="odoo_%s" % i, skipLoad=True
                    )
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
        odoo_db = Parameter.getValue("odoo.db", database, None)
        odoo_url = Parameter.getValue("odoo.url", database, "").strip()
        if not odoo_url.endswith("/"):
            odoo_url = odoo_url + "/"

        odoo_company = Parameter.getValue("odoo.company", database, None)
        singlecompany = Parameter.getValue("odoo.singlecompany", database, "false")
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

        with connections[database].cursor() as cursor:
            cursor.execute(
                """
                select coalesce(max(reference::bigint), 0) as max_reference
                from operationplan
                where reference ~ '^[0-9]*$'
                and char_length(reference) <= 9
                """
            )
            d = cursor.fetchone()
            frepple.settings.id = d[0] + 1

        if not debugFile:
            url = "%sfrepple/xml?%s" % (
                odoo_url,
                urlencode(
                    {
                        "database": odoo_db,
                        "language": odoo_language,
                        "company": odoo_company,
                        "mode": cls.mode,
                        "singlecompany": singlecompany,
                    }
                ),
            )
            try:
                request = Request(url)
                encoded = base64.encodebytes(
                    ("%s:%s" % (odoo_user, odoo_password)).encode("utf-8")
                )[:-1]
                request.add_header(
                    "Authorization", "Basic %s" % encoded.decode("ascii")
                )

                # Download and parse XML data
                with urlopen(request) as f:
                    frepple.readXMLdata(
                        f.read().decode("utf-8"), False, False, loglevel
                    )

            except HTTPError as e:
                print("Error connecting to odoo at %s" % url)
                odoo_data = e.read()
                if odoo_data:

                    class OdooMsgParser(HTMLParser):
                        def handle_data(self, data):
                            if "Error generating frePPLe XML data" in data:
                                self.echo = True
                                print("Odoo stack trace:")
                            elif hasattr(self, "echo"):
                                print("Odoo:", data)

                    odoo_msg = OdooMsgParser()
                    odoo_msg.feed(odoo_data.decode("utf-8"))
                raise e

        else:
            # Parse XML data file
            with open(debugFile, encoding="utf-8") as f:
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
            for r in frepple.customers():
                if r.owner is None and r != rootCustomer:
                    r.owner = rootCustomer
