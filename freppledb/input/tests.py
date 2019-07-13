#
# Copyright (C) 2007-2013 by frePPLe bvba
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
import tempfile

from django.test import TestCase

from freppledb.input.models import Location, Supplier, Item, Operation
from freppledb.input.models import PurchaseOrder, ManufacturingOrder, DistributionOrder


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
        self.assertContains(response, '"records":4,')

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
