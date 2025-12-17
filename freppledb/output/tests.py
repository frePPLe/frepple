#
# Copyright (C) 2007-2013 by frePPLe bv
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

from django.test import TestCase

from freppledb.common.tests import checkResponse


class OutputTest(TestCase):
    fixtures = ["demo"]

    def setUp(self):
        # Login
        self.client.login(username="admin", password="admin")

    # Buffer
    def test_output_buffer(self):
        response = self.client.get("/buffer/?format=json")
        self.assertContains(response, '"records":0,')
        self.assertEqual(response.status_code, 200)
        response = self.client.get("/buffer/?format=csvtable")
        checkResponse(self, response)
        self.assertTrue(
            response.__getitem__("Content-Type").startswith("text/csv; charset=")
        )
        response = self.client.get("/buffer/?format=csvlist")
        checkResponse(self, response)
        self.assertTrue(
            response.__getitem__("Content-Type").startswith("text/csv; charset=")
        )
        response = self.client.get("/buffer/?format=spreadsheettable")
        checkResponse(self, response)
        self.assertTrue(
            response.__getitem__("Content-Type").startswith(
                "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            )
        )
        response = self.client.get("/data/input/operationplanmaterial/?format=json")
        checkResponse(self, response)

    # Resource
    def test_output_resource(self):
        response = self.client.get("/resource/?format=json")
        self.assertContains(response, '"records":3,')
        self.assertEqual(response.status_code, 200)
        response = self.client.get("/resource/?format=csvtable")
        checkResponse(self, response)
        self.assertTrue(
            response.__getitem__("Content-Type").startswith("text/csv; charset=")
        )
        response = self.client.get("/resource/?format=spreadsheetlist")
        checkResponse(self, response)
        self.assertTrue(
            response.__getitem__("Content-Type").startswith(
                "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            )
        )
        response = self.client.get("/data/input/operationplanresource/?format=json")
        checkResponse(self, response)

    # Demand
    def test_output_demand(self):
        response = self.client.get("/demand/")
        self.assertContains(response, "Demand report")
        self.assertEqual(response.status_code, 200)
        response = self.client.get("/demand/?format=csvlist")
        checkResponse(self, response)
        self.assertTrue(
            response.__getitem__("Content-Type").startswith("text/csv; charset=")
        )
        response = self.client.get("/demand/?format=spreadsheettable")
        checkResponse(self, response)
        self.assertTrue(
            response.__getitem__("Content-Type").startswith(
                "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            )
        )

    # Manufacturing orders
    def test_output_manufacturing_orders(self):
        response = self.client.get("/operation/?format=json")
        self.assertContains(response, '"records":0,')
        self.assertEqual(response.status_code, 200)
        response = self.client.get("/operation/?format=csvtable")
        checkResponse(self, response)
        self.assertTrue(
            response.__getitem__("Content-Type").startswith("text/csv; charset=")
        )
        response = self.client.get("/operation/?format=spreadsheetlist")
        checkResponse(self, response)
        self.assertTrue(
            response.__getitem__("Content-Type").startswith(
                "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            )
        )

    # Purchase orders
    def test_output_purchase_orders(self):
        response = self.client.get("/purchase/?format=json")
        self.assertContains(response, '"records":4,')
        self.assertEqual(response.status_code, 200)
        response = self.client.get("/purchase/?format=csvtable")
        checkResponse(self, response)
        self.assertTrue(
            response.__getitem__("Content-Type").startswith("text/csv; charset=")
        )
        response = self.client.get("/purchase/?format=spreadsheetlist")
        checkResponse(self, response)
        self.assertTrue(
            response.__getitem__("Content-Type").startswith(
                "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            )
        )

    # Distribution orders
    def test_output_distribution_orders(self):
        response = self.client.get("/distribution/?format=json")
        self.assertContains(response, '"records":0,')
        self.assertEqual(response.status_code, 200)
        response = self.client.get("/distribution/?format=csvtable")
        checkResponse(self, response)
        self.assertTrue(
            response.__getitem__("Content-Type").startswith("text/csv; charset=")
        )
        response = self.client.get("/distribution/?format=spreadsheetlist")
        checkResponse(self, response)
        self.assertTrue(
            response.__getitem__("Content-Type").startswith(
                "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            )
        )

    # Problem
    def test_output_problem(self):
        response = self.client.get("/problem/?format=json")
        self.assertContains(response, '"records":0,')
        self.assertEqual(response.status_code, 200)
        response = self.client.get("/problem/?format=csvlist")
        checkResponse(self, response)
        self.assertTrue(
            response.__getitem__("Content-Type").startswith("text/csv; charset=")
        )
        response = self.client.get("/problem/?format=spreadsheetlist")
        checkResponse(self, response)
        self.assertTrue(
            response.__getitem__("Content-Type").startswith(
                "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            )
        )

    # Pegging
    def test_output_pegging(self):
        response = self.client.get("/demandpegging/Demand%2001/?format=json")
        self.assertContains(response, '"records":1,')
        checkResponse(self, response)

    # Constraint
    def test_output_constraint(self):
        response = self.client.get("/constraint/?format=json")
        self.assertContains(response, '"records":0,')
        self.assertEqual(response.status_code, 200)
        response = self.client.get("/constraint/?format=csvlist")
        checkResponse(self, response)
        self.assertTrue(
            response.__getitem__("Content-Type").startswith("text/csv; charset=")
        )
        response = self.client.get("/constraint/?format=spreadsheetlist")
        checkResponse(self, response)
        self.assertTrue(
            response.__getitem__("Content-Type").startswith(
                "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            )
        )

