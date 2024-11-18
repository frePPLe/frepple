#
# Copyright (C) 2007-2016 by frePPLe bv
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
from datetime import datetime
import base64
import gzip

from html.parser import HTMLParser
import os
import json
import logging
from urllib.request import urlopen, HTTPError, Request

from django.db import DEFAULT_DB_ALIAS, connections
from django.conf import settings
from django.contrib.auth.models import Group, Permission
from django.utils.http import urlencode
from django.utils.translation import get_supported_language_variant

from freppledb.common.models import Parameter, User
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

        odoo_user = (
            getattr(settings, "ODOO_USER", {}).get(database, None)
            or Parameter.getValue("odoo.user", database)
        ).strip()
        odoo_password = (
            getattr(settings, "ODOO_PASSWORDS", {}).get(database, None)
            or Parameter.getValue("odoo.password", database)
        ).strip()
        odoo_db = (
            getattr(settings, "ODOO_DB", {}).get(database, None)
            or Parameter.getValue("odoo.db", database, None)
        ).strip()
        odoo_url = (
            getattr(settings, "ODOO_URL", {}).get(database, None)
            or Parameter.getValue("odoo.url", database, "")
        ).strip()
        if not odoo_url.endswith("/"):
            odoo_url = odoo_url + "/"
        odoo_company = (
            getattr(settings, "ODOO_COMPANY", {}).get(database, None)
            or Parameter.getValue("odoo.company", database, None)
        ).strip()
        singlecompany = (
            getattr(settings, "ODOO_SINGLECOMPANY", {}).get(database, None)
            or Parameter.getValue("odoo.singlecompany", database, "false")
        ).strip()
        odoo_language = (
            getattr(settings, "ODOO_SINGLECOMPANY", {}).get(database, None)
            or Parameter.getValue("odoo.language", database, "en_US")
        ).strip()
        odoo_delta = Parameter.getValue("odoo.delta", database, "999")

        # Set the environment variable FREPPLE_ODOO_DEBUGFILE if you want frePPLe
        # to read that file rather than the data at url.
        debugFile = os.environ.get("FREPPLE_ODOO_DEBUGFILE", False)

        ok = True
        if not odoo_user and not debugFile:
            logger.error("Missing or invalid parameter odoo.user")
            ok = False
        if not odoo_password and not debugFile:
            logger.error("Missing or invalid parameter odoo.password")
            ok = False
        if not odoo_url and not debugFile:
            logger.error("Missing or invalid parameter odoo.url")
            ok = False
        if not odoo_company and not debugFile:
            logger.error("Missing or invalid parameter odoo.company")
            ok = False
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

        # Disable the automatic creation of inventory consumption & production until we have
        # read all odoo data. When odoo data is available we don't create extra ones
        # but take the odoo data as input.
        frepple.settings.suppressFlowplanCreation = True

        if not debugFile:
            args = {
                "language": odoo_language,
                "company": odoo_company,
                "mode": cls.mode,
                "singlecompany": singlecompany,
                "version": frepple.version,
                "delta": odoo_delta,
                "apps": (
                    "freppledb.shelflife"
                    if "freppledb.shelflife" in settings.INSTALLED_APPS
                    else ""
                ),
            }
            if odoo_db:
                args["database"] = odoo_db
            url = "%sfrepple/xml?%s" % (odoo_url, urlencode(args))
            response = None
            try:
                request = Request(url)
                encoded = base64.encodebytes(
                    ("%s:%s" % (odoo_user, odoo_password)).encode("utf-8")
                )[:-1]
                request.add_header(
                    "Authorization", "Basic %s" % encoded.decode("ascii")
                )
                request.add_header("Accept-Encoding", "gzip")

                # Download and parse XML data
                with urlopen(request) as response:
                    if response.info().get("Content-Encoding") == "gzip":
                        frepple.readXMLdata(
                            gzip.decompress(response.read())
                            .decode(encoding="utf-8", errors="ignore")
                            .translate({ord(i): None for i in "\f\v\b"}),
                            False,
                            False,
                            loglevel,
                        )
                    else:
                        frepple.readXMLdata(
                            response.read()
                            .decode(encoding="utf-8", errors="ignore")
                            .translate({ord(i): None for i in "\f\v\b"}),
                            False,
                            False,
                            loglevel,
                        )

            except HTTPError as e:
                print("Error connecting to odoo at %s" % url)
                if not response:
                    raise e
                if response.info().get("Content-Encoding") == "gzip":
                    odoo_data = gzip.decompress(e.read())
                else:
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
                    odoo_msg.feed(
                        odoo_data.decode("utf-8", errors="ignore").translate(
                            {ord(i): None for i in "\f\v\b"}
                        )
                    )
                raise e

        else:
            # Parse XML data file
            with open(debugFile, encoding="utf-8") as f:
                frepple.readXMLdata(
                    f.read().translate({ord(i): None for i in "\f\v\b"}),
                    False,
                    False,
                    loglevel,
                )

        # All predefined inventory detail records are now loaded.
        # We now create any missing ones.
        frepple.settings.suppressFlowplanCreation = False

        # Freeze the date of the extract (in memory and in database)
        frepple.settings.current = datetime.now()
        with connections[database].cursor() as cursor:
            cursor.execute(
                """
                insert into common_parameter
                (name, value) values ('currentdate', %s)
                on conflict(name)
                do update set value = excluded.value
                """,
                (frepple.settings.current.strftime("%Y-%m-%d %H:%M:%S"),),
            )

        # Synchronize users
        if hasattr(frepple.settings, "users"):
            try:
                odoo_group, created = Group.objects.using(database).get_or_create(
                    name="Odoo users"
                )
                if created:
                    # Newly odoo user group. Assign all permissions by default.
                    for p in Permission.objects.using(database).all():
                        odoo_group.permissions.add(p)
                odoo_users = [
                    u.username
                    for u in odoo_group.user_set.all().using(database).only("username")
                ]
                users = {}
                for u in User.objects.using(database).all():
                    users[u.username] = u
                for usr_data in json.loads(frepple.settings.users):
                    user = users.get(usr_data[1], None)
                    if not user:
                        # Create a new user
                        user = User.objects.create_user(
                            username=usr_data[1],
                            email=usr_data[1],
                            first_name=usr_data[0],
                            # Note: users can navigate from odoo into frepple with
                            # a webtoken. No password is ever needed.
                            # A user can still use the password reset feature if they
                            # still prefer to log in directly into frepple.
                            # So, we can set a random password here that nobody will ever
                            # need to know.
                            password=User.objects.make_random_password(),
                        )
                        user._state.db = database
                    if user.username in odoo_users:
                        odoo_users.remove(user.username)
                    else:
                        user.groups.add(odoo_group)
                    user.is_active = True
                    if len(usr_data) >= 2:
                        # Only the odoo addon for odoo >= 18 sends the user information
                        try:
                            user.language = get_supported_language_variant(
                                str(usr_data[2]).lower().replace("_", "-")
                            )
                        except Exception:
                            user.language = settings.LANGUAGE_CODE
                        user.save(
                            using=database, update_fields=["is_active", "language"]
                        )
                        if database != DEFAULT_DB_ALIAS:
                            user.save(
                                using=DEFAULT_DB_ALIAS,
                                update_fields=["is_active", "language"],
                            )
                    else:
                        user.save(using=database, update_fields=["is_active"])
                        if database != DEFAULT_DB_ALIAS:
                            user.save(
                                using=DEFAULT_DB_ALIAS, update_fields=["is_active"]
                            )

                # Remove users that no longer have access rights
                for o in odoo_users:
                    users[o].groups.remove(odoo_group)
            except Exception as e:
                print("Error synchronizing odoo users:", e)

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


@PlanTaskRegistry.register
class OdooDeltaChangeSource(PlanTask):
    """
    This class updates the source field of the sales order table to
    make sure odoo.delta parameter is handled correctly.
    if odoo.delta >= 999, we are pulling the entire demand history and
    the source field of the sales order table shouldn't be modified (it should be odoo_1)
    if odoo.delta < 999, we need to modify the source field from odoo_1 to demand history
    to make sure clean static doesn't delete the records we haven't pulled.
    """

    description = "Update sales order source"
    sequence = 307

    @classmethod
    def getWeight(cls, database=DEFAULT_DB_ALIAS, **kwargs):
        return (
            1
            if kwargs.get("exportstatic", False)
            and "odoo_" in kwargs.get("source", False)
            and float(Parameter.getValue("odoo.delta", database, "999")) < 999
            else -1
        )

    @classmethod
    def run(cls, database=DEFAULT_DB_ALIAS, **kwargs):
        with connections[database].cursor() as cursor:
            cursor.execute(
                """
                update demand set source = 'demand history' where source = %s;
                """,
                (kwargs.get("source", None),),
            )
            logger.info(
                "Updated source field of %d sales order records" % (cursor.rowcount,)
            )
