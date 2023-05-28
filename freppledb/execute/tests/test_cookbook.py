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

import os.path
import unittest

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

    def loadExcel(self, *filepath, webservice=False):
        # Login
        if webservice:
            os.environ["FREPPLE_TEST"] = "webservice"
            if "nowebservice" in os.environ:
                del os.environ["nowebservice"]
        else:
            os.environ["FREPPLE_TEST"] = "YES"
        if not User.objects.filter(username="admin").count():
            User.objects.create_superuser("admin", "your@company.com", "admin")
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
        if webservice:
            management.call_command("stopwebservice", wait=True, force=True)

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

    def test_operation_dependency(self):
        self.loadExcel(
            settings.FREPPLE_HOME,
            "..",
            "doc",
            "examples",
            "operation",
            "operation-dependency.xlsx",
        )
        management.call_command("runplan", plantype=1, constraint=15, env="supply")
        self.assertOperationplans(
            settings.FREPPLE_HOME,
            "..",
            "doc",
            "examples",
            "operation",
            "operation-dependency.expect",
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

    @unittest.skipUnless(
        "freppledb.forecast" in settings.INSTALLED_APPS, "App not activated"
    )
    def test_forecast_netting(self):
        """
        TODO Ideally this should be moved to the forecasting app.
        """
        self.loadExcel(
            settings.FREPPLE_HOME,
            "..",
            "doc",
            "examples",
            "forecasting",
            "forecast-netting.xlsx",
            webservice=True,
        )
        management.call_command(
            "runplan", plantype=1, constraint=15, env="fcst,supply,nowebservice"
        )
        self.assertOperationplans(
            settings.FREPPLE_HOME,
            "..",
            "doc",
            "examples",
            "forecasting",
            "forecast-netting.expect",
        )

    @unittest.skipUnless(
        "freppledb.forecast" in settings.INSTALLED_APPS, "App not activated"
    )
    def test_middle_out_forecast(self):
        """
        TODO Ideally this should be moved to the forecasting app.
        """
        self.loadExcel(
            settings.FREPPLE_HOME,
            "..",
            "doc",
            "examples",
            "forecasting",
            "middle-out-forecast.xlsx",
            webservice=True,
        )
        management.call_command(
            "runplan", plantype=1, constraint=15, env="fcst,supply,nowebservice"
        )
        self.assertOperationplans(
            settings.FREPPLE_HOME,
            "..",
            "doc",
            "examples",
            "forecasting",
            "middle-out-forecast.expect",
        )

    @unittest.skipUnless(
        "freppledb.forecast" in settings.INSTALLED_APPS, "App not activated"
    )
    def test_forecast_method(self):
        """
        TODO Ideally this should be moved to the forecasting app.
        """
        self.loadExcel(
            settings.FREPPLE_HOME,
            "..",
            "doc",
            "examples",
            "forecasting",
            "forecast-method.xlsx",
            webservice=True,
        )
        management.call_command(
            "runplan", plantype=1, constraint=15, env="fcst,supply,nowebservice"
        )
        self.assertOperationplans(
            settings.FREPPLE_HOME,
            "..",
            "doc",
            "examples",
            "forecasting",
            "forecast-method.expect",
        )

    @unittest.skip("Temporarily disabled - intermittent failures")
    def test_forecast_with_missing_data(self):
        """
        TODO Ideally this should be moved to the forecasting app.
        """
        self.loadExcel(
            settings.FREPPLE_HOME,
            "..",
            "doc",
            "examples",
            "forecasting",
            "forecast-with-missing-data.xlsx",
            webservice=True,
        )
        management.call_command(
            "runplan", plantype=1, constraint=15, env="fcst,supply,nowebservice"
        )
        self.assertOperationplans(
            settings.FREPPLE_HOME,
            "..",
            "doc",
            "examples",
            "forecasting",
            "forecast-with-missing-data.expect",
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
