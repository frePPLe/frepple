#
# Copyright (C) 2007-2019 by frePPLe bvba
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

import os
from rest_framework.test import APIClient, APITestCase, APIRequestFactory
import tempfile

from django.core import management
from django.http.response import StreamingHttpResponse
from django.test import TestCase, TransactionTestCase

from freppledb.common.models import User, Bucket, BucketDetail, Parameter
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
)


class DataLoadTest(TestCase):

    fixtures = ["demo"]

    def setUp(self):
        # Login
        self.client.login(username="admin", password="admin")

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
        self.assertContains(response, '"records":0,')
        response = self.client.get("/data/input/purchaseorder/?format=json")
        self.assertContains(response, '"records":4,')
        response = self.client.get("/data/input/resource/?format=json")
        self.assertContains(response, '"records":3,')
        response = self.client.get("/data/input/suboperation/?format=json")
        self.assertContains(response, '"records":0,')

    def test_csv_upload(self):
        self.assertEqual(
            [(i.name, i.category or u"") for i in Location.objects.all()],
            [
                (u"All locations", u""),
                (u"factory 1", u""),
                (u"factory 2", u""),
            ],  # Test result is different in Enterprise Edition
        )
        try:
            data = tempfile.NamedTemporaryFile(mode="w+b")
            data.write(b"name,category\n")
            data.write(b"factory 3,cat1\n")
            data.write(b"factory 4,\n")
            data.seek(0)
            response = self.client.post("/data/input/location/", {"csv_file": data})
            for rec in response.streaming_content:
                rec
            self.assertEqual(response.status_code, 200)
        finally:
            data.close()
        self.assertEqual(
            [(i.name, i.category or u"") for i in Location.objects.order_by("name")],
            [
                (u"All locations", u""),
                (u"factory 1", u""),
                (u"factory 2", u""),
                (u"factory 3", u"cat1"),
                (u"factory 4", u""),
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
                "shipping_date_0": "2019-01-01",
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

    def tearDown(self):
        if os.path.exists("workbook.xlsx"):
            os.remove("workbook.xlsx")

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
        management.call_command("empty")
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
            for rec in response.streaming_content:
                rec
            self.assertEqual(response.status_code, 200)

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

    def test_workbook_english(self):
        self.run_workbook("en")

    def test_workbook_chinese(self):
        self.run_workbook("zh-cn")

    def test_workbook_dutch(self):
        self.run_workbook("nl")

    def test_workbook_french(self):
        self.run_workbook("fr")

    def test_workbook_japanese(self):
        self.run_workbook("ja")

    def test_workbook_portuguese(self):
        self.run_workbook("pt")

    def test_workbook_brazilian_portuguese(self):
        self.run_workbook("pt-br")

    def test_workbook_hebrew(self):
        self.run_workbook("he")


class freppleREST(APITestCase):

    fixtures = ["demo"]

    # Default request format is multipart
    factory = APIRequestFactory(enforce_csrf_checks=True)

    def setUp(self):
        # Login
        self.client = APIClient()
        self.client.login(username="admin", password="admin")

    def test_api_listpages_getapi(self):
        response = self.client.get("/api/")
        self.assertEqual(response.status_code, 200)

        response = self.client.get("/api/input/demand/")
        self.assertEqual(response.status_code, 200)

        response = self.client.get("/api/input/item/")
        self.assertEqual(response.status_code, 200)

        response = self.client.get("/api/input/customer/")
        self.assertEqual(response.status_code, 200)

        response = self.client.get("/api/input/location/")
        self.assertEqual(response.status_code, 200)

        response = self.client.get("/api/input/buffer/")
        self.assertEqual(response.status_code, 200)

        response = self.client.get("/api/input/resource/")
        self.assertEqual(response.status_code, 200)

        response = self.client.get("/api/input/skill/")
        self.assertEqual(response.status_code, 200)

        response = self.client.get("/api/input/resourceskill/")
        self.assertEqual(response.status_code, 200)

        response = self.client.get("/api/input/setupmatrix/")
        self.assertEqual(response.status_code, 200)

        response = self.client.get("/api/input/purchaseorder/")
        self.assertEqual(response.status_code, 200)

        response = self.client.get("/api/input/supplier/")
        self.assertEqual(response.status_code, 200)

        response = self.client.get("/api/input/itemsupplier/")
        self.assertEqual(response.status_code, 200)

        response = self.client.get("/api/input/distributionorder/")
        self.assertEqual(response.status_code, 200)

        response = self.client.get("/api/input/itemdistribution/")
        self.assertEqual(response.status_code, 200)

        response = self.client.get("/api/input/manufacturingorder/")
        self.assertEqual(response.status_code, 200)

        response = self.client.get("/api/input/calendar/")
        self.assertEqual(response.status_code, 200)

        response = self.client.get("/api/input/calendarbucket/")
        self.assertEqual(response.status_code, 200)

        response = self.client.get("/api/input/operation/")
        self.assertEqual(response.status_code, 200)

        response = self.client.get("/api/input/operationmaterial/")
        self.assertEqual(response.status_code, 200)

        response = self.client.get("/api/input/operationresource/")
        self.assertEqual(response.status_code, 200)

        response = self.client.get("/api/input/suboperation/")
        self.assertEqual(response.status_code, 200)

        response = self.client.get("/api/common/parameter/")
        self.assertEqual(response.status_code, 200)

        response = self.client.get("/api/common/bucket/")
        self.assertEqual(response.status_code, 200)

        response = self.client.get("/api/common/bucketdetail/")
        self.assertEqual(response.status_code, 200)

    def test_api_demand(self):
        response = self.client.get("/api/input/demand/")
        self.assertEqual(response.status_code, 200)
        response = self.client.options("/api/input/demand/")
        self.assertEqual(response.status_code, 200)
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
        self.assertEqual(response.status_code, 200)
        self.assertEqual(Demand.objects.filter(name="Order UFO 25").count(), 1)
        # Demand OPTIONS
        response = self.client.options("/api/input/demand/Order UFO 25/")
        self.assertEqual(response.status_code, 200)
        # Demand GET JSON tests
        response = self.client.get("/api/input/demand/Order UFO 26/", format="json")
        self.assertEqual(response.status_code, 200)
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
        self.assertEqual(response.status_code, 200)
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
        self.assertEqual(response.status_code, 200)
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
        self.assertEqual(response.status_code, 200)
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
        self.assertEqual(response.status_code, 200)
        recordsnumber = Customer.objects.count()
        self.assertEqual(
            Customer.objects.count(), 3
        )  # Different between Enterprise Edition and Community Edition
        response = self.client.options("/api/input/customer/")
        self.assertEqual(response.status_code, 200)
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
        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            Customer.objects.filter(name="Customer near Area 51").count(), 1
        )
        # Customer OPTIONS
        response = self.client.options("/api/input/customer/Customer near Area 51/")
        self.assertEqual(response.status_code, 200)
        # Customer GET JSON tests
        response = self.client.get(
            "/api/input/customer/Customer near Area 52/", format="json"
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            Customer.objects.filter(name="Customer near Area 52").count(), 1
        )
        # Customer PUT MULTIPART tests
        data = {"name": "Customer near Area 51", "description": "Patch multipart"}
        response = self.client.patch("/api/input/customer/Customer near Area 51/", data)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(Customer.objects.count(), recordsnumber + 4)
        self.assertEqual(
            Customer.objects.filter(description="Patch multipart").count(), 1
        )
        # Customer PUT JSON tests
        data = {"name": "Customer near Area 52", "description": "Patch json"}
        response = self.client.patch(
            "/api/input/customer/Customer near Area 52/", data, format="json"
        )
        self.assertEqual(response.status_code, 200)
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
        self.assertEqual(response.status_code, 200)
        self.assertEqual(Customer.objects.count(), recordsnumber + 4)
        self.assertEqual(Customer.objects.filter(source="Put json").count(), 1)

        # Customer bulk filtered GET test
        response = self.client.get(
            "/api/input/customer/?name__contains=Area", format="json"
        )
        self.assertEqual(response.status_code, 200)
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
