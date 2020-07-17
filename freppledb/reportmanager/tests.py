#
# Copyright (C) 2020 by frePPLe bv
#
# All information contained herein is, and remains the property of frePPLe.
# You are allowed to use and modify the source code, as long as the software is used
# within your company.
# You are not allowed to distribute the software, either in the form of source code
# or in the form of compiled binaries.
#

import json
from urllib.parse import quote

from django.test import TransactionTestCase

from freppledb.common.tests import checkResponse
from .models import SQLReport, SQLColumn


class ReportManagerTest(TransactionTestCase):

    fixtures = ["demo"]

    def setUp(self):
        # Login
        self.client.login(username="admin", password="admin")

    def test_create_and_edit(self):
        # Create a report
        self.assertEqual(SQLReport.objects.all().count(), 0)
        response = self.client.get("/reportmanager/schema/")
        checkResponse(self, response)
        response = self.client.post(
            "/reportmanager/",
            {
                "sql": "select name, cost, description from item",
                "save": "true",
                "name": "test report",
                "public": "false",
                "description": "my description",
            },
            HTTP_X_REQUESTED_WITH="XMLHttpRequest",
        )
        checkResponse(self, response)
        self.assertEqual(SQLReport.objects.all().count(), 1)
        self.assertEqual(SQLColumn.objects.all().count(), 3)
        report = SQLReport.objects.all()[0]
        self.assertEqual(report.name, "test report")
        self.assertEqual(report.sql, "select name, cost, description from item")
        self.assertEqual(report.description, "my description")
        self.assertEqual(report.public, False)

        # Retrieve report data
        response = self.client.get("/reportmanager/%s/" % report.id)
        checkResponse(self, response)
        response = self.client.get("/reportmanager/%s/?format=json" % report.id)
        self.assertContains(response, '"records":7,')
        response = self.client.get("/reportmanager/%s/?format=csv" % report.id)
        checkResponse(self, response)
        response = self.client.get("/reportmanager/%s/?format=spreadsheet" % report.id)
        checkResponse(self, response)

        # Retrieve filtered and sorted report data
        response = self.client.get("/reportmanager/%s/" % report.id)
        checkResponse(self, response)
        fltr = quote(
            json.dumps(
                {
                    "groupOp": "AND",
                    "rules": [{"field": "name", "op": "cn", "data": "e"}],
                }
            )
        )
        response = self.client.get(
            "/reportmanager/%s/?format=json&_search=true&filters=%s&searchField=&searchString=&searchOper="
            % (report.id, fltr)
        )
        self.assertContains(response, '"records":1,')
        response = self.client.get(
            "/reportmanager/%s/?format=csv&name__cn=a" % (report.id)
        )
        cnt = 0
        for _ in response:
            cnt += 1
        self.assertEqual(cnt, 5)

        # Edit report
        response = self.client.post(
            "/reportmanager/%s/" % report.id,
            {
                "id": report.id,
                "save": "true",
                "sql": "select name, category, subcategory, cost, description from item",
                "name": report.name,
                "public": report.public,
            },
            HTTP_X_REQUESTED_WITH="XMLHttpRequest",
        )
        answer = json.loads(response.content.decode("utf-8"))
        self.assertEqual(answer["status"], "ok")
        response = self.client.post(
            "/reportmanager/%s/" % report.id,
            {
                "id": report.id,
                "save": "true",
                "sql": "a very bad SQL statement",
                "name": report.name,
                "public": report.public,
            },
            HTTP_X_REQUESTED_WITH="XMLHttpRequest",
        )
        answer = json.loads(response.content.decode("utf-8"))
        self.assertNotEqual(answer["status"], "ok")

        # Delete a report
        response = self.client.post(
            "/reportmanager/",
            {"id": report.id, "delete": "true"},
            HTTP_X_REQUESTED_WITH="XMLHttpRequest",
        )
        checkResponse(self, response)
        self.assertEqual(SQLReport.objects.all().count(), 0)
        self.assertEqual(SQLColumn.objects.all().count(), 0)
