#
# Copyright (C) 2019 by frePPLe bv
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

import http
import json
import os
import time
from urllib.parse import urlencode
from xml.etree import ElementTree
import unittest

from django.conf import settings
from django.core import management
from django.db import connection, DEFAULT_DB_ALIAS
from django.test import TransactionTestCase

from freppledb.common.auth import getWebserviceAuthorization
from freppledb.input.models import Item, Location, Customer


@unittest.skipUnless(
    "freppledb.webservice" in settings.INSTALLED_APPS, "App not activated"
)
class WebServiceTest(TransactionTestCase):
    def setUp(self):
        os.environ["FREPPLE_TEST"] = "webservice"
        if "nowebservice" in os.environ:
            del os.environ["nowebservice"]
        self.token = "Bearer %s" % getWebserviceAuthorization(user="admin", exp=600)

    def getData(self, url, **kwargs):
        conn = http.client.HTTPConnection(
            settings.DATABASES[DEFAULT_DB_ALIAS]["TEST"]["FREPPLE_PORT"]
        )
        for fmt in ["xml", "json"]:
            args = {"format": fmt}
            if kwargs:
                args.update(kwargs)
            conn.request(
                "GET", url, urlencode(args), headers={"Authorization": self.token}
            )
            resp = conn.getresponse()
            self.assertEqual(resp.status, http.HTTPStatus.OK)
            if fmt == "xml":
                answer = ElementTree.fromstring(resp.read())
            elif fmt == "json":
                answer = json.loads(resp.read())
        return answer

    def tearDown(self):
        management.call_command("stopwebservice", force=True, wait=True)
        del os.environ["FREPPLE_TEST"]

    def test_triggers(self):
        # A first item needs to exists, otherwise the web service doesn't start
        Item(name="first item").save()

        # Bring up the webservice
        management.call_command("runwebservice", wait=True, forcerestart=True)

        # Create items in the database.
        for i in range(9):
            Item(name="item %s" % i).save()

        # Check the webservice has loaded them (through the trigger)
        time.sleep(1)
        self.assertEqual(len(self.getData("/item/")["items"]), 10)

        # Delete an item
        Item(name="item 6").delete()
        time.sleep(1)
        self.assertEqual(len(self.getData("/item/")["items"]), 9)

        # Delete all items
        with connection.cursor() as cursor:
            cursor.execute("truncate table item cascade")

        # Check the web service sees the truncate (through the trigger)
        time.sleep(1)
        self.assertEqual(self.getData("/item/"), {})

        # Location
        for i in range(10):
            Location(name="location %s" % i).save()
        time.sleep(1)
        self.assertEqual(len(self.getData("/location/")["locations"]), 10)
        Location(name="location 6").delete()
        time.sleep(1)
        self.assertEqual(len(self.getData("/location/")["locations"]), 9)
        with connection.cursor() as cursor:
            cursor.execute("truncate table location cascade")
        time.sleep(1)
        self.assertEqual(self.getData("/location/"), {})

        # Customer
        for i in range(10):
            Customer(name="customer %s" % i).save()
        time.sleep(1)
        self.assertEqual(len(self.getData("/customer/")["customers"]), 10)
        Customer(name="customer 6").delete()
        time.sleep(1)
        self.assertEqual(len(self.getData("/customer/")["customers"]), 9)
        with connection.cursor() as cursor:
            cursor.execute("truncate table customer cascade")
        time.sleep(1)
        self.assertEqual(self.getData("/customer/"), {})

    def test_get_urls(self):

        # Load data and start the web service
        management.call_command("loaddata", "manufacturing_demo", verbosity=0)
        management.call_command("runwebservice", wait=True, forcerestart=True)

        # Test various URLs on the web service
        self.assertTrue(self.getData("/"))
        self.assertTrue(self.getData("/customer/"))
        self.assertTrue(self.getData("/buffer/"))
        self.assertTrue(self.getData("/resource/"))
        self.assertTrue(self.getData("/location/"))
        self.assertTrue(self.getData("/item/"))
        self.assertTrue(self.getData("/calendar/"))
        self.assertTrue(self.getData("/operation/"))
        self.assertTrue(self.getData("/supplier/"))
        self.assertFalse(self.getData("/setupmatrix/"))
        self.assertTrue(self.getData("/problem/", type="plan"))
        # TODO Following calls shouldn't return empty. The iterator fields on the plan are missing.
        self.assertFalse(self.getData("/itemsupplier/"))
        self.assertFalse(self.getData("/itemdistribution/"))
        self.assertFalse(self.getData("/resourceskill/"))
        self.assertFalse(self.getData("/flow/"))
        self.assertFalse(self.getData("/load/"))
