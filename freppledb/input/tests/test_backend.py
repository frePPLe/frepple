#
# Copyright (C) 2007-2019 by frePPLe bv
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

from datetime import date
from itertools import chain
import os
import random
from rest_framework.test import APIClient, APITestCase, APIRequestFactory
import tempfile
from time import sleep
from unittest import skipUnless

from django.conf import settings
from django.contrib.auth.models import Permission
from django.contrib.contenttypes.models import ContentType
from django.core import management
from django.http.response import StreamingHttpResponse
from django.test import TestCase, TransactionTestCase
from django.utils import translation
from django.utils.formats import date_format

from freppledb.common.dataload import parseCSVdata
from freppledb.common.models import (
    User,
    Bucket,
    BucketDetail,
    Parameter,
    Comment,
    Follower,
    Notification,
    NotificationFactory,
)
from freppledb.common.tests import checkResponse
from freppledb.input.models import (
    Buffer,
    Calendar,
    CalendarBucket,
    Customer,
    Demand,
    DistributionOrder,
    Item,
    ItemDistribution,
    ItemSupplier,
    Location,
    ManufacturingOrder,
    Operation,
    OperationMaterial,
    OperationPlanMaterial,
    OperationPlanResource,
    OperationResource,
    PurchaseOrder,
    Resource,
    ResourceSkill,
    SetupMatrix,
    Skill,
    SubOperation,
    Supplier,
    WorkOrder,
)


class DataLoadTest(TestCase):
    fixtures = ["demo"]

    def setUp(self):
        os.environ["FREPPLE_TEST"] = "YES"
        self.client.login(username="admin", password="admin")
        super().setUp()

    def tearDown(self):
        Notification.wait()
        del os.environ["FREPPLE_TEST"]
        super().tearDown()

    def test_demo_data(self):
        response = self.client.get("/data/input/customer/?format=json")
        self.assertContains(response, '"records":3,')
        response = self.client.get("/data/input/operationmaterial/?format=json")
        self.assertContains(response, '"records":13,')
        response = self.client.get("/data/input/buffer/?format=json")
        self.assertContains(response, '"records":8,')
        response = self.client.get("/data/input/calendar/?format=json")
        self.assertContains(response, '"records":4,')
        response = self.client.get("/data/input/calendarbucket/?format=json")
        self.assertContains(response, '"records":5,')
        response = self.client.get("/data/input/demand/?format=json")
        self.assertContains(response, '"records":14,')
        response = self.client.get("/data/input/item/?format=json")
        self.assertContains(response, '"records":7,')
        response = self.client.get("/data/input/operationresource/?format=json")
        self.assertContains(response, '"records":3,')
        response = self.client.get("/data/input/location/?format=json")
        self.assertContains(response, '"records":3,')
        response = self.client.get("/data/input/operation/?format=json")
        self.assertContains(response, '"records":9,')
        response = self.client.get("/data/input/manufacturingorder/?format=json")
        self.assertContains(response, '"records":1,')
        response = self.client.get("/data/input/workorder/?format=json")
        self.assertContains(response, '"records":0,')
        response = self.client.get("/data/input/purchaseorder/?format=json")
        self.assertContains(response, '"records":4,')
        response = self.client.get("/data/input/resource/?format=json")
        self.assertContains(response, '"records":3,')
        response = self.client.get("/data/input/suboperation/?format=json")
        self.assertContains(response, '"records":0,')
        response = self.client.get(
            "/data/input/calendardetail/Working%20Days/?format=json"
        )
        self.assertContains(response, '"records":1,')
        response = self.client.get("/data/input/calendardetail/Working%20Days/")
        checkResponse(self, response)

    def test_csv_upload(self):
        self.assertEqual(
            [(i.name, i.category or "") for i in Location.objects.all()],
            [
                ("All locations", ""),
                ("factory 1", ""),
                ("factory 2", ""),
            ],  # Test result is different in Enterprise Edition
        )
        try:
            data = tempfile.NamedTemporaryFile(mode="w+b")
            data.write(b"name,category\n")
            data.write(b"factory 3,cat1\n")
            data.write(b"factory 4,\n")
            data.seek(0)
            response = self.client.post("/data/input/location/", {"csv_file": data})
            checkResponse(self, response)
        finally:
            data.close()
        self.assertEqual(
            [(i.name, i.category or "") for i in Location.objects.order_by("name")],
            [
                ("All locations", ""),
                ("factory 1", ""),
                ("factory 2", ""),
                ("factory 3", "cat1"),
                ("factory 4", ""),
            ],  # Test result is different in Enterprise Edition
        )

    def test_forms(self):
        item = Item.objects.all()[0].name
        loc1 = Location.objects.all()[0].name
        loc2 = Location.objects.all()[1].name
        sup = Supplier.objects.all()[0].name
        oper = Operation.objects.all()[0].name

        # Create a PO
        response = self.client.post(
            "/data/input/purchaseorder/add/",
            {
                "reference": "test PO",
                "item": item,
                "location": loc1,
                "supplier": sup,
                "quantity": 1,
                "status": "confirmed",
            },
        )
        self.assertEqual(response.status_code, 302)
        self.assertEqual(
            PurchaseOrder.objects.all()
            .filter(reference="test PO", status="confirmed", quantity=1.0)
            .count(),
            1,
        )

        # Create a MO
        response = self.client.post(
            "/data/input/manufacturingorder/add/",
            {
                "reference": "test MO",
                "operation": oper,
                "quantity": 1,
                "status": "confirmed",
            },
        )
        self.assertEqual(response.status_code, 302)
        self.assertEqual(
            ManufacturingOrder.objects.all()
            .filter(
                reference="test MO", status="confirmed", quantity=1.0, operation=oper
            )
            .count(),
            1,
        )

        # Create a DO
        response = self.client.post(
            "/data/input/distributionorder/add/",
            {
                "reference": "test DO",
                "origin": loc1,
                "destination": loc2,
                "quantity": 1,
                "status": "confirmed",
                "shipping_date_0": date_format(
                    date(2019, 1, 1), format="DATE_FORMAT", use_l10n=False
                ),
                "shipping_date_1": "00:00:00",
            },
        )
        self.assertEqual(response.status_code, 302)
        self.assertEqual(
            DistributionOrder.objects.all()
            .filter(
                reference="test DO",
                status="confirmed",
                quantity=1.0,
                origin=loc1,
                destination=loc2,
            )
            .count(),
            1,
        )


class ExcelTest(TransactionTestCase):
    fixtures = ["demo"]

    def setUp(self):
        # Login
        if not User.objects.filter(username="admin").count():
            User.objects.create_superuser("admin", "your@company.com", "admin")
        self.client.login(username="admin", password="admin")
        os.environ["FREPPLE_TEST"] = "YES"
        super().setUp()

    def tearDown(self):
        Notification.wait()
        del os.environ["FREPPLE_TEST"]
        if os.path.exists("workbook.xlsx"):
            os.remove("workbook.xlsx")
        translation.activate(settings.LANGUAGE_CODE)
        super().tearDown()

    def run_workbook(self, language):
        # Change the language preference
        self.client.post(
            "/preferences/", {"pagesize": 100, "language": language, "theme": "orange"}
        )

        # Initial size
        countBuffer = Buffer.objects.count()
        countCalendarBucket = CalendarBucket.objects.count()
        countCalendar = Calendar.objects.count()
        countCustomer = Customer.objects.count()
        countDemand = Demand.objects.count()
        countOperationMaterial = OperationMaterial.objects.count()
        countItem = Item.objects.count()
        countItemSupplier = ItemSupplier.objects.count()
        countItemDistribution = ItemDistribution.objects.count()
        countOperationResource = OperationResource.objects.count()
        countLocation = Location.objects.count()
        countPurchaseOrder = PurchaseOrder.objects.count()
        countDistributionOrder = DistributionOrder.objects.count()
        countManufacturingOrder = ManufacturingOrder.objects.count()
        countWorkOrder = WorkOrder.objects.count()
        countOperation = Operation.objects.count()
        countResourceSkill = ResourceSkill.objects.count()
        countResource = Resource.objects.count()
        countSetupMatrix = SetupMatrix.objects.count()
        countSkill = Skill.objects.count()
        countSubOperation = SubOperation.objects.count()
        countSupplier = Supplier.objects.count()
        countBucket = Bucket.objects.count()
        countBucketDetail = BucketDetail.objects.count()
        countParameter = Parameter.objects.count()
        self.assertTrue(countDemand > 0)

        # Export workbook
        response = self.client.post(
            "/execute/launch/exportworkbook/",
            {
                "entities": [
                    "input.demand",
                    "input.item",
                    "input.customer",
                    "input.location",
                    "input.buffer",
                    "input.resource",
                    "input.skill",
                    "input.resourceskill",
                    "input.setupmatrix",
                    "input.purchaseorder",
                    "input.supplier",
                    "input.itemsupplier",
                    "input.distributionorder",
                    "input.itemdistribution",
                    "input.operationmaterial",
                    "input.manufacturingorder",
                    "input.workorder",
                    "input.calendar",
                    "input.calendarbucket",
                    "input.operation",
                    "input.operationplanmaterial",
                    "input.operationresource",
                    "input.suboperation",
                    "common.parameter",
                    "common.bucket",
                    "common.bucketdetail",
                ]
            },
        )
        with open("workbook.xlsx", "wb") as f:
            f.write(response.content)

        # Erase the database
        management.call_command("empty", all=True)
        self.assertEqual(Buffer.objects.count(), 0)
        self.assertEqual(CalendarBucket.objects.count(), 0)
        self.assertEqual(Calendar.objects.count(), 0)
        self.assertEqual(Customer.objects.count(), 0)
        self.assertEqual(Demand.objects.count(), 0)
        self.assertEqual(OperationMaterial.objects.count(), 0)
        self.assertEqual(Item.objects.count(), 0)
        self.assertEqual(ItemDistribution.objects.count(), 0)
        self.assertEqual(ItemSupplier.objects.count(), 0)
        self.assertEqual(OperationResource.objects.count(), 0)
        self.assertEqual(Location.objects.count(), 0)
        self.assertEqual(PurchaseOrder.objects.count(), 0)
        self.assertEqual(DistributionOrder.objects.count(), 0)
        self.assertEqual(ManufacturingOrder.objects.count(), 0)
        self.assertEqual(WorkOrder.objects.count(), 0)
        self.assertEqual(OperationPlanResource.objects.count(), 0)
        self.assertEqual(OperationPlanMaterial.objects.count(), 0)
        self.assertEqual(Operation.objects.count(), 0)
        self.assertEqual(ResourceSkill.objects.count(), 0)
        self.assertEqual(Resource.objects.count(), 0)
        self.assertEqual(SetupMatrix.objects.count(), 0)
        self.assertEqual(Skill.objects.count(), 0)
        self.assertEqual(SubOperation.objects.count(), 0)
        self.assertEqual(Supplier.objects.count(), 0)
        self.assertEqual(Bucket.objects.count(), 0)
        self.assertEqual(BucketDetail.objects.count(), 0)
        self.assertEqual(Parameter.objects.count(), 0)

        # Import the same workbook again
        with open("workbook.xlsx", "rb") as f:
            response = self.client.post(
                "/execute/launch/importworkbook/", {"spreadsheet": f}
            )
            if not isinstance(response, StreamingHttpResponse):
                raise Exception("expected a streaming response")
            checkResponse(self, response)

        # Verify the new content is identical
        self.assertEqual(Buffer.objects.count(), countBuffer)
        self.assertEqual(CalendarBucket.objects.count(), countCalendarBucket)
        self.assertEqual(Calendar.objects.count(), countCalendar)
        self.assertEqual(Customer.objects.count(), countCustomer)
        self.assertEqual(Demand.objects.count(), countDemand)
        self.assertEqual(OperationMaterial.objects.count(), countOperationMaterial)
        self.assertEqual(Item.objects.count(), countItem)
        self.assertEqual(ItemDistribution.objects.count(), countItemDistribution)
        self.assertEqual(ItemSupplier.objects.count(), countItemSupplier)
        self.assertEqual(OperationResource.objects.count(), countOperationResource)
        self.assertEqual(Location.objects.count(), countLocation)
        self.assertEqual(PurchaseOrder.objects.count(), countPurchaseOrder)
        self.assertEqual(DistributionOrder.objects.count(), countDistributionOrder)
        self.assertEqual(ManufacturingOrder.objects.count(), countManufacturingOrder)
        self.assertEqual(WorkOrder.objects.count(), countWorkOrder)
        self.assertEqual(Operation.objects.count(), countOperation)
        self.assertEqual(ResourceSkill.objects.count(), countResourceSkill)
        self.assertEqual(Resource.objects.count(), countResource)
        self.assertEqual(SetupMatrix.objects.count(), countSetupMatrix)
        self.assertEqual(Skill.objects.count(), countSkill)
        self.assertEqual(SubOperation.objects.count(), countSubOperation)
        self.assertEqual(Supplier.objects.count(), countSupplier)
        self.assertEqual(Bucket.objects.count(), countBucket)
        self.assertEqual(BucketDetail.objects.count(), countBucketDetail)
        self.assertEqual(Parameter.objects.count(), countParameter)

    def test_workbook_brazilian_portuguese(self):
        self.run_workbook("pt-br")

    def test_workbook_chinese(self):
        self.run_workbook("zh-cn")

    def test_workbook_dutch(self):
        self.run_workbook("nl")

    def test_workbook_english(self):
        self.run_workbook("en")

    def test_workbook_french(self):
        self.run_workbook("fr")

    def test_workbook_hebrew(self):
        self.run_workbook("he")

    def test_workbook_croation(self):
        self.run_workbook("hr")

    def test_workbook_italian(self):
        self.run_workbook("it")

    def test_workbook_japanese(self):
        self.run_workbook("ja")

    def test_workbook_portuguese(self):
        self.run_workbook("pt")

    def test_workbook_russian(self):
        self.run_workbook("ru")

    def test_workbook_ukrainian(self):
        self.run_workbook("uk")

    def test_workbook_spanish(self):
        self.run_workbook("es")

    def test_workbook_taiwanese(self):
        self.run_workbook("zh-tw")


class freppleREST(APITestCase):
    fixtures = ["demo"]

    # Default request format is multipart
    factory = APIRequestFactory(enforce_csrf_checks=True)

    def setUp(self):
        # Login
        self.client = APIClient()
        self.client.login(username="admin", password="admin")
        os.environ["FREPPLE_TEST"] = "YES"
        super().setUp()

    def tearDown(self):
        Notification.wait()
        del os.environ["FREPPLE_TEST"]
        super().tearDown()

    def test_api_listpages_getapi(self):
        response = self.client.get("/api/")
        checkResponse(self, response)

        response = self.client.get("/api/input/demand/")
        checkResponse(self, response)

        response = self.client.get("/api/input/item/")
        checkResponse(self, response)

        response = self.client.get("/api/input/customer/")
        checkResponse(self, response)

        response = self.client.get("/api/input/location/")
        checkResponse(self, response)

        response = self.client.get("/api/input/buffer/")
        checkResponse(self, response)

        response = self.client.get("/api/input/resource/")
        checkResponse(self, response)

        response = self.client.get("/api/input/skill/")
        checkResponse(self, response)

        response = self.client.get("/api/input/resourceskill/")
        checkResponse(self, response)

        response = self.client.get("/api/input/setupmatrix/")
        checkResponse(self, response)

        response = self.client.get("/api/input/purchaseorder/")
        checkResponse(self, response)

        response = self.client.get("/api/input/supplier/")
        checkResponse(self, response)

        response = self.client.get("/api/input/itemsupplier/")
        checkResponse(self, response)

        response = self.client.get("/api/input/distributionorder/")
        checkResponse(self, response)

        response = self.client.get("/api/input/itemdistribution/")
        checkResponse(self, response)

        response = self.client.get("/api/input/manufacturingorder/")
        checkResponse(self, response)

        response = self.client.get("/api/input/workorder/")
        checkResponse(self, response)

        response = self.client.get("/api/input/calendar/")
        checkResponse(self, response)

        response = self.client.get("/api/input/calendarbucket/")
        checkResponse(self, response)

        response = self.client.get("/api/input/operation/")
        checkResponse(self, response)

        response = self.client.get("/api/input/operationmaterial/")
        checkResponse(self, response)

        response = self.client.get("/api/input/operationresource/")
        checkResponse(self, response)

        response = self.client.get("/api/input/suboperation/")
        checkResponse(self, response)

        response = self.client.get("/api/common/parameter/")
        checkResponse(self, response)

        response = self.client.get("/api/common/bucket/")
        checkResponse(self, response)

        response = self.client.get("/api/common/bucketdetail/")
        checkResponse(self, response)

    def test_api_demand(self):
        response = self.client.get("/api/input/demand/")
        checkResponse(self, response)
        response = self.client.options("/api/input/demand/")
        checkResponse(self, response)
        recordsnumber = Demand.objects.count()
        data = {
            "name": "Order UFO 25",
            "description": None,
            "category": None,
            "subcategory": None,
            "item": "product",
            "customer": "Customer near factory 1",
            "location": "factory 1",
            "due": "2013-12-01T00:00:00",
            "status": "closed",
            "operation": None,
            "quantity": "110.0000",
            "priority": 1,
            "minshipment": None,
            "maxlateness": None,
        }
        response = self.client.post("/api/input/demand/", data, format="json")
        self.assertEqual(response.status_code, 201)
        self.assertEqual(Demand.objects.count(), recordsnumber + 1)
        self.assertEqual(Demand.objects.filter(name="Order UFO 25").count(), 1)
        data = {
            "name": "Order UFO 26",
            "description": None,
            "category": None,
            "subcategory": None,
            "item": "product",
            "customer": "Customer near factory 1",
            "location": "factory 1",
            "due": "2013-12-01T00:00:00",
            "status": "closed",
            "operation": None,
            "quantity": "220.0000",
            "priority": 1,
            "minshipment": None,
            "maxlateness": None,
        }
        response = self.client.post("/api/input/demand/", data, format="json")
        self.assertEqual(response.status_code, 201)
        self.assertEqual(Demand.objects.count(), recordsnumber + 2)
        self.assertEqual(Demand.objects.filter(name="Order UFO 26").count(), 1)

        data = [
            {
                "name": "Order UFO 27",
                "description": None,
                "category": "TEST DELETE",
                "subcategory": None,
                "item": "product",
                "location": "factory 1",
                "customer": "Customer near factory 1",
                "due": "2013-12-01T00:00:00",
                "status": "closed",
                "operation": None,
                "quantity": "220.0000",
                "priority": 1,
                "minshipment": None,
                "maxlateness": None,
            },
            {
                "name": "Order UFO 28",
                "description": None,
                "category": "TEST DELETE",
                "subcategory": None,
                "item": "product",
                "customer": "Customer near factory 1",
                "location": "factory 1",
                "due": "2013-12-01T00:00:00",
                "status": "closed",
                "operation": None,
                "quantity": "220.0000",
                "priority": 1,
                "minshipment": None,
                "maxlateness": None,
            },
        ]
        response = self.client.post("/api/input/demand/", data, format="json")
        self.assertEqual(response.status_code, 201)
        self.assertEqual(Demand.objects.count(), recordsnumber + 4)
        self.assertEqual(Demand.objects.filter(category="TEST DELETE").count(), 2)

        # Demand GET MULTIPART
        response = self.client.get("/api/input/demand/Order UFO 25/")
        checkResponse(self, response)
        self.assertEqual(Demand.objects.filter(name="Order UFO 25").count(), 1)
        # Demand OPTIONS
        response = self.client.options("/api/input/demand/Order UFO 25/")
        checkResponse(self, response)
        # Demand GET JSON tests
        response = self.client.get("/api/input/demand/Order UFO 26/", format="json")
        checkResponse(self, response)
        self.assertEqual(Demand.objects.filter(name="Order UFO 26").count(), 1)
        # Demand PUT MULTIPART tests
        data = {
            "name": "Order UFO 25",
            "description": "Put multipart",
            "category": None,
            "subcategory": None,
            "item": "product",
            "customer": "Customer near factory 1",
            "location": "factory 1",
            "due": "2013-12-01T00:00:00",
            "status": "closed",
            "operation": None,
            "quantity": "110.0000",
            "priority": 1,
            "minshipment": None,
            "maxlateness": None,
        }
        response = self.client.put(
            "/api/input/demand/Order UFO 25/", data, format="json"
        )
        checkResponse(self, response)
        self.assertEqual(Demand.objects.count(), 18)
        self.assertEqual(Demand.objects.filter(description="Put multipart").count(), 1)
        # Demand PUT JSON tests
        data = {
            "name": "Order UFO 26",
            "description": "Put json",
            "category": None,
            "subcategory": None,
            "item": "product",
            "customer": "Customer near factory 1",
            "location": "factory 1",
            "due": "2013-12-01T00:00:00",
            "status": "closed",
            "operation": None,
            "quantity": "110.0000",
            "priority": 1,
            "minshipment": None,
            "maxlateness": None,
        }
        response = self.client.put(
            "/api/input/demand/Order UFO 26/", data, format="json"
        )
        checkResponse(self, response)
        self.assertEqual(Demand.objects.count(), recordsnumber + 4)
        self.assertEqual(Demand.objects.filter(description="Put json").count(), 1)
        # Demand PUT FORM tests
        data = {
            "name": "Order UFO 26",
            "description": "Put form",
            "category": None,
            "subcategory": None,
            "item": "product",
            "customer": "Customer near factory 1",
            "location": "factory 1",
            "due": "2013-12-01T00:00:00",
            "status": "closed",
            "operation": None,
            "quantity": "110.0000",
            "priority": 1,
            "minshipment": None,
            "maxlateness": None,
        }
        response = self.client.put(
            "/api/input/demand/Order UFO 26/", data, format="json"
        )
        checkResponse(self, response)
        self.assertEqual(Demand.objects.count(), recordsnumber + 4)
        self.assertEqual(Demand.objects.filter(description="Put form").count(), 1)

        # Demand DELETE tests
        response = self.client.delete("/api/input/demand/Order UFO 26/", format="form")
        self.assertEqual(response.status_code, 204)
        response = self.client.delete("/api/input/demand/Order UFO 25/", format="json")
        self.assertEqual(response.status_code, 204)
        response = self.client.delete("/api/input/demand/Demand 01/", format="api")
        self.assertEqual(response.status_code, 204)
        response = self.client.delete(
            "/api/input/demand/?category=TEST DELETE", format="api"
        )
        self.assertEqual(response.status_code, 204)
        self.assertEqual(Customer.objects.filter(category="TEST DELETE").count(), 0)

    def test_api_customer(self):
        response = self.client.get("/api/input/customer/")
        checkResponse(self, response)
        recordsnumber = Customer.objects.count()
        self.assertEqual(
            Customer.objects.count(), 3
        )  # Different between Enterprise Edition and Community Edition
        response = self.client.options("/api/input/customer/")
        checkResponse(self, response)
        data = {"name": "Customer near Area 51"}
        response = self.client.post("/api/input/customer/", data)
        self.assertEqual(response.status_code, 201)
        self.assertEqual(Customer.objects.count(), recordsnumber + 1)
        self.assertEqual(
            Customer.objects.filter(name="Customer near Area 51").count(), 1
        )
        data = {"name": "Customer near Area 52"}
        response = self.client.post("/api/input/customer/", data, format="json")
        self.assertEqual(response.status_code, 201)
        self.assertEqual(Customer.objects.count(), recordsnumber + 2)
        self.assertEqual(
            Customer.objects.filter(name="Customer near Area 52").count(), 1
        )
        data = [
            {"name": "Customer near Area 99", "source": "TEST DELETE"},
            {"name": "Customer near Area 100", "source": "TEST DELETE"},
        ]
        response = self.client.post("/api/input/customer/", data, format="json")
        self.assertEqual(response.status_code, 201)
        self.assertEqual(Customer.objects.count(), recordsnumber + 4)
        self.assertEqual(Customer.objects.filter(source="TEST DELETE").count(), 2)

        # Customer GET MULTIPART
        response = self.client.get("/api/input/customer/Customer near Area 51/")
        checkResponse(self, response)
        self.assertEqual(
            Customer.objects.filter(name="Customer near Area 51").count(), 1
        )
        # Customer OPTIONS
        response = self.client.options("/api/input/customer/Customer near Area 51/")
        checkResponse(self, response)
        # Customer GET JSON tests
        response = self.client.get(
            "/api/input/customer/Customer near Area 52/", format="json"
        )
        checkResponse(self, response)
        self.assertEqual(
            Customer.objects.filter(name="Customer near Area 52").count(), 1
        )
        # Customer PUT MULTIPART tests
        data = {"name": "Customer near Area 51", "description": "Patch multipart"}
        response = self.client.patch("/api/input/customer/Customer near Area 51/", data)
        checkResponse(self, response)
        self.assertEqual(Customer.objects.count(), recordsnumber + 4)
        self.assertEqual(
            Customer.objects.filter(description="Patch multipart").count(), 1
        )
        # Customer PUT JSON tests
        data = {"name": "Customer near Area 52", "description": "Patch json"}
        response = self.client.patch(
            "/api/input/customer/Customer near Area 52/", data, format="json"
        )
        checkResponse(self, response)
        self.assertEqual(Customer.objects.count(), recordsnumber + 4)
        self.assertEqual(Customer.objects.filter(description="Patch json").count(), 1)

        # Customer PUT FORM tests
        data = {
            "name": "Customer near Area 52",
            "description": "Patch json",
            "category": None,
            "subcategory": None,
            "source": "Put json",
            "lastmodified": "2015-12-04T10:18:40.048861",
        }

        response = self.client.patch(
            "/api/input/customer/Customer near Area 52/", data, format="json"
        )
        checkResponse(self, response)
        self.assertEqual(Customer.objects.count(), recordsnumber + 4)
        self.assertEqual(Customer.objects.filter(source="Put json").count(), 1)

        # Customer bulk filtered GET test
        response = self.client.get(
            "/api/input/customer/?name__contains=Area", format="json"
        )
        checkResponse(self, response)
        self.assertEqual(Customer.objects.filter(name__contains="Area").count(), 4)

        # Customer DELETE tests
        # Bulk "contains" filtered DELETE
        response = self.client.delete(
            "/api/input/customer/?name__contains=Area 5", format="form"
        )
        self.assertEqual(response.status_code, 204)
        self.assertEqual(Customer.objects.filter(name__contains="Area").count(), 2)
        # Single DELETE
        response = self.client.delete(
            "/api/input/customer/Customer near factory 1/", format="api"
        )
        self.assertEqual(response.status_code, 204)
        # Bulk filtered DELETE
        response = self.client.delete(
            "/api/input/customer/?source=TEST DELETE", format="json"
        )
        self.assertEqual(response.status_code, 204)
        self.assertEqual(Customer.objects.filter(source="TEST DELETE").count(), 0)


class NotificationTest(TransactionTestCase):
    def setUp(self):
        os.environ["FREPPLE_TEST"] = "YES"
        if not User.objects.filter(username="admin").count():
            User.objects.create_superuser("admin", "your@company.com", "admin")
        super().setUp()

    def tearDown(self):
        Notification.wait()
        del os.environ["FREPPLE_TEST"]
        super().tearDown()

    def test_follow_item(self):
        sleep(3)
        user = User.objects.create_user(
            username="test user",
            email="tester@yourcompany.com",
            password="big_secret12345",
        )
        user.user_permissions.add(
            *Permission.objects.filter(
                codename__in=("view_item", "view_supplier", "view_purchaseorder")
            )
        )
        Follower(
            user=user,
            content_type=ContentType.objects.get(model="item"),
            object_pk="test item",
        ).save()
        for _ in parseCSVdata(
            Item, [["name", "category"], ["test item", "test category"]], user=user
        ):
            pass
        for _ in parseCSVdata(
            Item, [["name", "category"], ["test item", "new test category"]], user=user
        ):
            pass
        for _ in parseCSVdata(Supplier, [["name"], ["test supplier"]], user=user):
            pass
        for _ in parseCSVdata(
            ItemSupplier,
            [["supplier", "item"], ["test supplier", "test item"]],
            user=user,
        ):
            pass
        for _ in parseCSVdata(
            PurchaseOrder,
            [
                ["reference", "supplier", "item", "quantity", "enddate"],
                ["PO 1", "test supplier", "test item", "10", "2020-12-31"],
            ],
            user=user,
        ):
            pass
        item = Item.objects.get(name="test item")
        Comment(
            content_object=item,
            object_repr=str(item),
            user=user,
            comment="test comment",
            type="comment",
        ).save()

        # Check what notifications we got
        Notification.wait()
        NotificationFactory.start()
        self.assertEqual(Notification.objects.count(), 5)

    def test_performance(self):
        # Admin user follows all items
        user = User.objects.get(username="admin")
        Follower(
            user=user,
            content_type=ContentType.objects.get(model="item"),
            object_pk="all",
            type="M",  # The test email backend doesn't send email, so we can't check it
        ).save()

        items = [["item %s" % cnt] for cnt in range(1000)]

        # Create 2 users. Each user follows all 1000 items.
        for cnt in range(2):
            u = User.objects.create_user(
                username="user%s" % cnt,
                email="user%s" % cnt,
                password="big_secret12345",
            )
            u.user_permissions.add(
                *Permission.objects.filter(codename__in=("view_item", "view_demand"))
            )
            for i in items:
                Follower(
                    user=u,
                    content_type=ContentType.objects.get(model="item"),
                    object_pk=i[0],
                ).save()
        self.assertEqual(User.objects.count(), 3)
        self.assertEqual(Follower.objects.count(), 2001)

        # Upload CSV data with 1000 items
        # print("start items", datetime.now())
        errors = 0
        for _ in parseCSVdata(Item, chain([["name"]], items), user=user):
            errors += 1
        self.assertEqual(Item.objects.count(), 1000)

        # Upload CSV data with 1000 customers
        # print("start customers", datetime.now())
        customers = [["customer %s" % cnt, "test"] for cnt in range(1000)]
        for _ in parseCSVdata(
            Customer, chain([["name", "category"]], customers), user=user
        ):
            errors += 1
        self.assertEqual(Customer.objects.count(), 1000)

        # Upload CSV data with 1000 locations
        # print("start locations", datetime.now())
        locations = [["location %s" % cnt, "test"] for cnt in range(1000)]
        for _ in parseCSVdata(
            Location, chain([["name", "category"]], locations), user=user
        ):
            errors += 1
        self.assertEqual(Location.objects.count(), 1000)

        # Upload CSV data with 1000 demands
        # print("start demands", datetime.now())
        demands = [
            [
                "demand %s" % cnt,
                random.choice(items)[0],
                random.choice(customers)[0],
                random.choice(locations)[0],
                1,
                "2020-01-01",
            ]
            for cnt in range(1000)
        ]
        for _ in parseCSVdata(
            Demand,
            chain(
                [["name", "item", "customer", "location", "quantity", "due"]], demands
            ),
            user=user,
        ):
            errors += 1
        self.assertEqual(Demand.objects.count(), 1000)
        self.assertEqual(errors, 4)

        # The Loading is finished now, but the notifications aren't ready yet. It takes
        # longer to process all notifications and send emails by the worker.
        #
        # The real performance test is to run with and without the followers.
        # The load process should take the same time with or without the followers.
        # The time required for the notification worker instead grows with the number of
        # followers that need to be checked.
        # print("END DATA LOAD", datetime.now())
        Notification.wait()
        # print("END NOTIFICATON WORKERS", datetime.now())

        self.assertEqual(Comment.objects.count(), 4000)
        self.assertEqual(Notification.objects.count(), 6000)


@skipUnless("freppledb.forecast" in settings.INSTALLED_APPS, "App not activated")
class ManufacturingDemoTest(TransactionTestCase):
    fixtures = ["manufacturing_demo"]

    def setUp(self):
        # Make sure the test database is used
        os.environ["FREPPLE_TEST"] = "YES"

    def tearDown(self):
        del os.environ["FREPPLE_TEST"]

    def test_plan(self):
        from freppledb.forecast.models import ForecastPlan
        from freppledb.input.models import OperationPlan

        # Run frePPLe on the test database.
        ForecastPlan.objects.all().delete()
        OperationPlan.objects.filter(status="proposed").delete()
        management.call_command(
            "runplan",
            plantype=1,
            constraint="capa,mfg_lt,po_lt",
            env="fcst,invplan,supply",
        )
        self.assertGreater(ForecastPlan.objects.all().count(), 0)
        self.assertGreater(OperationPlan.objects.filter(status="proposed").count(), 0)
