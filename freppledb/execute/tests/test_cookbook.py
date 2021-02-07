#
# Copyright (C) 2007-2013 by frePPLe bv
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

import os.path

from django.conf import settings
from django.core import management
from django.http.response import StreamingHttpResponse
from django.test import TransactionTestCase

from freppledb.common.models import User, Notification
import freppledb.input


class cookbooktest(TransactionTestCase):
    def setUp(self):
        os.environ["FREPPLE_TEST"] = "YES"
        if not User.objects.filter(username="admin").count():
            User.objects.create_superuser("admin", "your@company.com", "admin")
        super().setUp()

    def tearDown(self):
        Notification.wait()
        del os.environ["FREPPLE_TEST"]
        super().tearDown()

    def loadExcel(self, *filepath):
        # Login
        self.client.login(username="admin", password="admin")
        try:
            with open(os.path.join(*filepath), "rb") as myfile:
                response = self.client.post(
                    "/execute/launch/importworkbook/", {"spreadsheet": myfile}
                )
                if not isinstance(response, StreamingHttpResponse):
                    raise Exception("expected a streaming response")
                for rec in response.streaming_content:
                    rec
        except Exception as e:
            self.fail("Can't load excel file: %s" % e)
        self.assertEqual(response.status_code, 200)
        self.client.logout()

    def assertOperationplans(self, *resultpath):
        opplans = sorted(
            [
                "%s,%s,%s,%s%s"
                % (
                    i.name,
                    i.startdate,
                    i.enddate,
                    round(i.quantity, 1),
                    ",%s " % i.batch if i.batch else "",
                )
                for i in freppledb.input.models.OperationPlan.objects.order_by(
                    "name", "startdate", "quantity", "batch"
                ).only("name", "startdate", "enddate", "quantity", "batch")
            ],
            key=lambda s: s.lower(),
        )
        row = 0
        maxrow = len(opplans)
        with open(os.path.join(*resultpath), "r") as f:
            for line in f:
                if not line.strip():
                    continue
                if row >= maxrow or opplans[row].strip() != line.strip():
                    print("Got:")
                    for i in opplans:
                        print("  ", i.strip())
                    if row < maxrow:
                        self.fail(
                            "Difference in expected results on line %s" % (row + 1)
                        )
                    else:
                        self.fail("Less output rows than expected")
                row += 1
        if row != maxrow:
            print("Got:")
            for i in opplans:
                print("  ", i.strip())
            self.fail("More output rows than expected")

    def test_calendar_working_hours(self):
        self.loadExcel(
            settings.FREPPLE_HOME,
            "..",
            "doc",
            "examples",
            "calendar",
            "calendar-working-hours.xlsx",
        )
        management.call_command("runplan", plantype=1, constraint=15, env="supply")
        self.assertOperationplans(
            settings.FREPPLE_HOME,
            "..",
            "doc",
            "examples",
            "calendar",
            "calendar-working-hours.expect",
        )

    def test_resource_type(self):
        self.loadExcel(
            settings.FREPPLE_HOME,
            "..",
            "doc",
            "examples",
            "resource",
            "resource-type.xlsx",
        )
        management.call_command("runplan", plantype=1, constraint=15, env="supply")
        self.assertOperationplans(
            settings.FREPPLE_HOME,
            "..",
            "doc",
            "examples",
            "resource",
            "resource-type.expect",
        )

    def test_resource_skills(self):
        self.loadExcel(
            settings.FREPPLE_HOME,
            "..",
            "doc",
            "examples",
            "resource",
            "resource-skills.xlsx",
        )
        management.call_command("runplan", plantype=1, constraint=15, env="supply")
        self.assertOperationplans(
            settings.FREPPLE_HOME,
            "..",
            "doc",
            "examples",
            "resource",
            "resource-skills.expect",
        )

    def test_resource_tool(self):
        self.loadExcel(
            settings.FREPPLE_HOME,
            "..",
            "doc",
            "examples",
            "resource",
            "resource-tool.xlsx",
        )
        management.call_command("runplan", plantype=1, constraint=15, env="supply")
        self.assertOperationplans(
            settings.FREPPLE_HOME,
            "..",
            "doc",
            "examples",
            "resource",
            "resource-tool.expect",
        )

    def test_demand_priorities(self):
        self.loadExcel(
            settings.FREPPLE_HOME,
            "..",
            "doc",
            "examples",
            "demand",
            "demand-priorities.xlsx",
        )
        management.call_command("runplan", plantype=1, constraint=15, env="supply")
        self.assertOperationplans(
            settings.FREPPLE_HOME,
            "..",
            "doc",
            "examples",
            "demand",
            "demand-priorities.expect",
        )

    def test_demand_policies(self):
        self.loadExcel(
            settings.FREPPLE_HOME,
            "..",
            "doc",
            "examples",
            "demand",
            "demand-policies.xlsx",
        )
        management.call_command("runplan", plantype=1, constraint=15, env="supply")
        self.assertOperationplans(
            settings.FREPPLE_HOME,
            "..",
            "doc",
            "examples",
            "demand",
            "demand-policies.expect",
        )

    def test_operation_type(self):
        self.loadExcel(
            settings.FREPPLE_HOME,
            "..",
            "doc",
            "examples",
            "operation",
            "operation-type.xlsx",
        )
        management.call_command("runplan", plantype=1, constraint=15, env="supply")
        self.assertOperationplans(
            settings.FREPPLE_HOME,
            "..",
            "doc",
            "examples",
            "operation",
            "operation-type.expect",
        )

    def test_operation_posttime(self):
        self.loadExcel(
            settings.FREPPLE_HOME,
            "..",
            "doc",
            "examples",
            "operation",
            "operation-posttime.xlsx",
        )
        management.call_command("runplan", plantype=1, constraint=15, env="supply")
        self.assertOperationplans(
            settings.FREPPLE_HOME,
            "..",
            "doc",
            "examples",
            "operation",
            "operation-posttime.expect",
        )

    def test_operation_autofence(self):
        self.loadExcel(
            settings.FREPPLE_HOME,
            "..",
            "doc",
            "examples",
            "operation",
            "operation-autofence.xlsx",
        )
        management.call_command("runplan", plantype=1, constraint=15, env="supply")
        self.assertOperationplans(
            settings.FREPPLE_HOME,
            "..",
            "doc",
            "examples",
            "operation",
            "operation-autofence.expect",
        )

    def test_operation_routing(self):
        self.loadExcel(
            settings.FREPPLE_HOME,
            "..",
            "doc",
            "examples",
            "operation",
            "operation-routing.xlsx",
        )
        management.call_command("runplan", plantype=1, constraint=15, env="supply")
        self.assertOperationplans(
            settings.FREPPLE_HOME,
            "..",
            "doc",
            "examples",
            "operation",
            "operation-routing.expect",
        )

    def test_make_to_order(self):
        self.loadExcel(
            settings.FREPPLE_HOME,
            "..",
            "doc",
            "examples",
            "buffer",
            "make-to-order.xlsx",
        )
        management.call_command("runplan", plantype=1, constraint=15, env="supply")
        self.assertOperationplans(
            settings.FREPPLE_HOME,
            "..",
            "doc",
            "examples",
            "buffer",
            "make-to-order.expect",
        )

    def test_buffer_transfer_batch(self):
        self.loadExcel(
            settings.FREPPLE_HOME,
            "..",
            "doc",
            "examples",
            "buffer",
            "transfer-batch.xlsx",
        )
        management.call_command("runplan", plantype=1, constraint=15, env="supply")
        self.assertOperationplans(
            settings.FREPPLE_HOME,
            "..",
            "doc",
            "examples",
            "buffer",
            "transfer-batch.expect",
        )

    def test_supplier_capacity(self):
        self.loadExcel(
            settings.FREPPLE_HOME,
            "..",
            "doc",
            "examples",
            "supplier",
            "supplier-capacity.xlsx",
        )
        management.call_command("runplan", plantype=1, constraint=15, env="supply")
        self.assertOperationplans(
            settings.FREPPLE_HOME,
            "..",
            "doc",
            "examples",
            "supplier",
            "supplier-capacity.expect",
        )

    def test_alternate_materials(self):
        self.loadExcel(
            settings.FREPPLE_HOME,
            "..",
            "doc",
            "examples",
            "buffer",
            "alternate-materials.xlsx",
        )
        management.call_command("runplan", plantype=1, constraint=15, env="supply")
        self.assertOperationplans(
            settings.FREPPLE_HOME,
            "..",
            "doc",
            "examples",
            "buffer",
            "alternate-materials.expect",
        )

    def test_resource_efficiency(self):
        self.loadExcel(
            settings.FREPPLE_HOME,
            "..",
            "doc",
            "examples",
            "resource",
            "resource-efficiency.xlsx",
        )
        management.call_command("runplan", plantype=1, constraint=15, env="supply")
        self.assertOperationplans(
            settings.FREPPLE_HOME,
            "..",
            "doc",
            "examples",
            "resource",
            "resource-efficiency.expect",
        )

    def test_operation_alternate(self):
        self.loadExcel(
            settings.FREPPLE_HOME,
            "..",
            "doc",
            "examples",
            "operation",
            "operation-alternate.xlsx",
        )
        management.call_command("runplan", plantype=1, constraint=15, env="supply")
        self.assertOperationplans(
            settings.FREPPLE_HOME,
            "..",
            "doc",
            "examples",
            "operation",
            "operation-alternate.expect",
        )

    def test_resource_alternate(self):
        self.loadExcel(
            settings.FREPPLE_HOME,
            "..",
            "doc",
            "examples",
            "resource",
            "resource-alternate.xlsx",
        )
        management.call_command("runplan", plantype=1, constraint=15, env="supply")
        self.assertOperationplans(
            settings.FREPPLE_HOME,
            "..",
            "doc",
            "examples",
            "resource",
            "resource-alternate.expect",
        )
