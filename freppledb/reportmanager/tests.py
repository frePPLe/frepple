#
# Copyright (C) 2020 by frePPLe bv
#
# This library is free software; you can redistribute it and/or modify it
# under the terms of the GNU Affero General Public License as published
# by the Free Software Foundation; either version 3 of the License, or
#
# This library is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU Affero
# General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public
# License along with this program.  If not, see <http://www.gnu.org/licenses/>.
#

import json
from urllib.parse import quote

from django.test import TransactionTestCase

from freppledb.common.models import User
from freppledb.common.tests import checkResponse
from .models import SQLReport, SQLColumn


class ReportManagerTest(TransactionTestCase):

    fixtures = ["demo"]

    def setUp(self):
        # Login
        if not User.objects.filter(username="admin").count():
            User.objects.create_superuser("admin", "your@company.com", "admin")
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
