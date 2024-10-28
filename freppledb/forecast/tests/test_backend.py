#
# Copyright (C) 2023 by frePPLe bv
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

from datetime import date, datetime, timedelta
from decimal import Decimal
import os
from rest_framework.test import APIClient, APITransactionTestCase, APIRequestFactory
import unittest

from django.conf import settings
from django.core import management
from django.db import transaction
from django.test import TransactionTestCase
from django.db import DEFAULT_DB_ALIAS, connections

from freppledb.common.models import Parameter, User
from freppledb.common.tests import checkResponse
from freppledb.input.models import Item, Location, Customer

if "freppledb.forecast" in settings.INSTALLED_APPS:
    from freppledb.forecast.models import Forecast, ForecastPlan


@unittest.skipUnless(
    "freppledb.forecast" in settings.INSTALLED_APPS, "App not activated"
)
class ForecastEdit(TransactionTestCase):
    fixtures = ["demo"]

    def setUp(self):
        os.environ["FREPPLE_TEST"] = "YES"

    def tearDown(self):
        del os.environ["FREPPLE_TEST"]

    @unittest.skip("Temporarily disabled - being revised")
    def test_input_edit(self):
        # Generate the forecast
        ForecastPlan.objects.all().delete()
        self.assertEqual(ForecastPlan.objects.all().count(), 0)
        management.call_command("runplan", env="fcst")
        recs = ForecastPlan.objects.all().count()
        self.assertGreater(recs, 0)

        # Create a quantity override at an aggregate level
        bcktst = date(2014, 1, 1)
        bcktnd = date(2014, 2, 1)
        fcstpln1 = ForecastPlan.objects.get(
            item__name="All products",
            location__name="All locations",
            customer__name="All customers",
            startdate=bcktst,
        )
        self.assertEqual(fcstpln1.forecastoverride, None)
        self.assertEqual(fcstpln1.forecastoverridevalue, None)
        self.assertEqual(fcstpln1.forecasttotal, 140)
        self.assertEqual(fcstpln1.forecasttotalvalue, 14000)
        with transaction.atomic():
            Forecast.updatePlan(
                item=Item.objects.get(name="All products"),
                location=Location.objects.get(name="All locations"),
                customer=Customer.objects.get(name="All customers"),
                startdate=bcktst,
                enddate=bcktnd,
                forecastoverride=Decimal(100),
                ordersadjustment=None,
                units=True,
            )
        fcstpln1 = ForecastPlan.objects.get(
            item__name="product",
            location__name="factory 1",
            customer__name="Customer near factory 1",
            startdate=bcktst,
        )
        self.assertEqual(fcstpln1.forecastoverride, None)
        self.assertEqual(fcstpln1.forecastoverridevalue, None)
        self.assertEqual(fcstpln1.forecasttotal, 50)
        self.assertEqual(fcstpln1.forecasttotalvalue, 5000)
        fcstpln2 = ForecastPlan.objects.get(
            item__name="product",
            location__name="All locations",
            customer__name="All customers",
            startdate=bcktst,
        )
        self.assertEqual(fcstpln2.forecastoverride, None)
        self.assertEqual(fcstpln2.forecastoverridevalue, None)
        self.assertEqual(fcstpln2.forecasttotal, 100)
        self.assertEqual(fcstpln2.forecasttotalvalue, 10000)
        fcstpln3 = ForecastPlan.objects.get(
            item__name="All products",
            location__name="All locations",
            customer__name="All customers",
            startdate=bcktst,
        )
        self.assertEqual(fcstpln3.forecastoverride, 100)
        self.assertEqual(fcstpln3.forecastoverridevalue, 10000)
        self.assertEqual(fcstpln3.forecasttotal, 100)
        self.assertEqual(fcstpln3.forecasttotalvalue, 10000)

        # Update a quantity override at the lower level
        bcktst = date(2014, 1, 1)
        bcktnd = date(2014, 2, 1)
        with transaction.atomic():
            Forecast.updatePlan(
                forecast=Forecast.objects.get(name="product - region 1"),
                startdate=bcktst,
                enddate=bcktnd,
                forecastoverride=Decimal(100),
                ordersadjustment=None,
                units=True,
            )
        fcstpln1 = ForecastPlan.objects.get(
            item__name="product",
            location__name="factory 1",
            customer__name="Customer near factory 1",
            startdate=bcktst,
        )
        self.assertEqual(fcstpln1.forecastoverride, 100)
        self.assertEqual(fcstpln1.forecastoverridevalue, 10000)
        self.assertEqual(fcstpln1.forecasttotal, 100)
        self.assertEqual(fcstpln1.forecasttotalvalue, 10000)
        fcstpln2 = ForecastPlan.objects.get(
            item__name="product",
            location__name="All locations",
            customer__name="All customers",
            startdate=bcktst,
        )
        self.assertEqual(fcstpln2.forecastoverride, None)
        self.assertEqual(fcstpln2.forecastoverridevalue, None)
        self.assertEqual(fcstpln2.forecasttotal, 150)
        self.assertEqual(fcstpln2.forecasttotalvalue, 15000)
        fcstpln3 = ForecastPlan.objects.get(
            item__name="All products",
            location__name="All locations",
            customer__name="All customers",
            startdate=bcktst,
        )
        self.assertEqual(fcstpln3.forecastoverride, 100)
        self.assertEqual(fcstpln3.forecastoverridevalue, 10000)
        self.assertEqual(fcstpln3.forecasttotal, 150)
        self.assertEqual(fcstpln3.forecasttotalvalue, 15000)

        # Create a quantity override at the lower level
        bcktst = date(2014, 2, 1)
        bcktnd = date(2014, 3, 1)
        fcstpln3_before = ForecastPlan.objects.get(
            item__name="All products",
            location__name="All locations",
            customer__name="All customers",
            startdate=bcktst,
        )
        with transaction.atomic():
            Forecast.updatePlan(
                forecast=Forecast.objects.get(name="product2 - region 1"),
                startdate=bcktst,
                enddate=bcktnd,
                forecastoverride=Decimal(100),
                ordersadjustment=None,
                units=True,
            )
        fcstpln1 = ForecastPlan.objects.get(
            item__name="product2",
            location__name="factory 1",
            customer__name="Customer near factory 1",
            startdate=bcktst,
        )
        self.assertEqual(fcstpln1.forecastoverride, 100)
        self.assertEqual(fcstpln1.forecastoverridevalue, 5000)
        self.assertEqual(fcstpln1.forecasttotal, 100)
        self.assertEqual(fcstpln1.forecasttotalvalue, 5000)
        fcstpln2 = ForecastPlan.objects.get(
            item__name="product2",
            location__name="All locations",
            customer__name="All customers",
            startdate=bcktst,
        )
        self.assertEqual(fcstpln2.forecastoverride, None)
        self.assertEqual(fcstpln2.forecastoverridevalue, None)
        self.assertEqual(fcstpln2.forecasttotal, 100)
        self.assertEqual(fcstpln2.forecasttotalvalue, 5000)
        fcstpln3 = ForecastPlan.objects.get(
            item__name="All products",
            location__name="All locations",
            customer__name="All customers",
            startdate=bcktst,
        )
        self.assertEqual(fcstpln3.forecastoverride, None)
        self.assertEqual(fcstpln3.forecastoverridevalue, None)
        self.assertEqual(fcstpln3.forecasttotal, fcstpln3_before.forecasttotal + 100)
        self.assertEqual(
            fcstpln3.forecasttotalvalue, fcstpln3_before.forecasttotalvalue + 5000
        )

        # TODO Create a value override at an aggregate level

        # TODO Update a value override at the lower level

        # TODO Create a value override at the lower level

        # Reset all overrides by setting to null the override at root level
        bcktst = date(2014, 1, 1)
        with transaction.atomic():
            Forecast.updatePlan(
                item=Item.objects.get(name="All products"),
                location=Location.objects.get(name="All locations"),
                customer=Customer.objects.get(name="All customers"),
                startdate=bcktst,
                enddate=bcktnd,
                forecastoverride=None,
                ordersadjustment=None,
                units=True,
            )
        # Make sure there are no overrides left in the models
        for fp in ForecastPlan.objects.all().filter(startdate=bcktst):
            self.assertEqual(fp.forecastoverride, None)
            self.assertEqual(fp.forecastoverridevalue, None)
        bcktst = date(2014, 2, 1)
        with transaction.atomic():
            Forecast.updatePlan(
                item=Item.objects.get(name="All products"),
                location=Location.objects.get(name="All locations"),
                customer=Customer.objects.get(name="All customers"),
                startdate=bcktst,
                enddate=bcktnd,
                forecastoverride=None,
                ordersadjustment=None,
                units=True,
            )
        # Make sure there are no overrides left in the models
        for fp in ForecastPlan.objects.all().filter(startdate=bcktst):
            self.assertEqual(fp.forecastoverride, None)
            self.assertEqual(fp.forecastoverridevalue, None)

        # Redo the same tests as above but this time using values rather than units.
        # Create a quantity override at an aggregate level
        bcktst = date(2014, 1, 1)
        bcktnd = date(2014, 2, 1)
        fcstpln1 = ForecastPlan.objects.get(
            item__name="All products",
            location__name="All locations",
            customer__name="All customers",
            startdate=bcktst,
        )
        self.assertEqual(fcstpln1.forecastoverride, None)
        self.assertEqual(fcstpln1.forecastoverridevalue, None)
        self.assertEqual(fcstpln1.forecasttotal, 140)
        self.assertEqual(fcstpln1.forecasttotalvalue, 14000)
        with transaction.atomic():
            Forecast.updatePlan(
                item=Item.objects.get(name="All products"),
                location=Location.objects.get(name="All locations"),
                customer=Customer.objects.get(name="All customers"),
                startdate=bcktst,
                enddate=bcktnd,
                forecastoverride=Decimal(10000),
                ordersadjustment=None,
                units=False,
            )
        fcstpln1 = ForecastPlan.objects.get(
            item__name="product",
            location__name="factory 1",
            customer__name="Customer near factory 1",
            startdate=bcktst,
        )
        self.assertEqual(fcstpln1.forecastoverride, None)
        self.assertEqual(fcstpln1.forecastoverridevalue, None)
        self.assertEqual(fcstpln1.forecasttotal, 50)
        self.assertEqual(fcstpln1.forecasttotalvalue, 5000)
        fcstpln2 = ForecastPlan.objects.get(
            item__name="product",
            location__name="All locations",
            customer__name="All customers",
            startdate=bcktst,
        )
        self.assertEqual(fcstpln2.forecastoverride, None)
        self.assertEqual(fcstpln2.forecastoverridevalue, None)
        self.assertEqual(fcstpln2.forecasttotal, 100)
        self.assertEqual(fcstpln2.forecasttotalvalue, 10000)
        fcstpln3 = ForecastPlan.objects.get(
            item__name="All products",
            location__name="All locations",
            customer__name="All customers",
            startdate=bcktst,
        )
        self.assertEqual(fcstpln3.forecastoverride, 100)
        self.assertEqual(fcstpln3.forecastoverridevalue, 10000)
        self.assertEqual(fcstpln3.forecasttotal, 100)
        self.assertEqual(fcstpln3.forecasttotalvalue, 10000)

        # Update a quantity override at the lower level
        bcktst = date(2014, 1, 1)
        bcktnd = date(2014, 2, 1)
        with transaction.atomic():
            Forecast.updatePlan(
                forecast=Forecast.objects.get(name="product - region 1"),
                startdate=bcktst,
                enddate=bcktnd,
                forecastoverride=Decimal(10000),
                ordersadjustment=None,
                units=False,
            )
        fcstpln1 = ForecastPlan.objects.get(
            item__name="product",
            location__name="factory 1",
            customer__name="Customer near factory 1",
            startdate=bcktst,
        )
        self.assertEqual(fcstpln1.forecastoverride, 100)
        self.assertEqual(fcstpln1.forecastoverridevalue, 10000)
        self.assertEqual(fcstpln1.forecasttotal, 100)
        self.assertEqual(fcstpln1.forecasttotalvalue, 10000)
        fcstpln2 = ForecastPlan.objects.get(
            item__name="product",
            location__name="All locations",
            customer__name="All customers",
            startdate=bcktst,
        )
        self.assertEqual(fcstpln2.forecastoverride, None)
        self.assertEqual(fcstpln2.forecastoverridevalue, None)
        self.assertEqual(fcstpln2.forecasttotal, 150)
        self.assertEqual(fcstpln2.forecasttotalvalue, 15000)
        fcstpln3 = ForecastPlan.objects.get(
            item__name="All products",
            location__name="All locations",
            customer__name="All customers",
            startdate=bcktst,
        )
        self.assertEqual(fcstpln3.forecastoverride, 100)
        self.assertEqual(fcstpln3.forecastoverridevalue, 10000)
        self.assertEqual(fcstpln3.forecasttotal, 150)
        self.assertEqual(fcstpln3.forecasttotalvalue, 15000)

        # Create a quantity override at the lower level
        bcktst = date(2014, 2, 1)
        bcktnd = date(2014, 3, 1)
        fcstpln3_before = ForecastPlan.objects.get(
            item__name="All products",
            location__name="All locations",
            customer__name="All customers",
            startdate=bcktst,
        )
        with transaction.atomic():
            Forecast.updatePlan(
                forecast=Forecast.objects.get(name="product2 - region 1"),
                startdate=bcktst,
                enddate=bcktnd,
                forecastoverride=Decimal(5000),
                ordersadjustment=None,
                units=False,
            )
        fcstpln1 = ForecastPlan.objects.get(
            item__name="product2",
            location__name="factory 1",
            customer__name="Customer near factory 1",
            startdate=bcktst,
        )
        self.assertEqual(fcstpln1.forecastoverride, 100)
        self.assertEqual(fcstpln1.forecastoverridevalue, 5000)
        self.assertEqual(fcstpln1.forecasttotal, 100)
        self.assertEqual(fcstpln1.forecasttotalvalue, 5000)
        fcstpln2 = ForecastPlan.objects.get(
            item__name="product2",
            location__name="All locations",
            customer__name="All customers",
            startdate=bcktst,
        )
        self.assertEqual(fcstpln2.forecastoverride, None)
        self.assertEqual(fcstpln2.forecastoverridevalue, None)
        self.assertEqual(fcstpln2.forecasttotal, 100)
        self.assertEqual(fcstpln2.forecasttotalvalue, 5000)
        fcstpln3 = ForecastPlan.objects.get(
            item__name="All products",
            location__name="All locations",
            customer__name="All customers",
            startdate=bcktst,
        )
        self.assertEqual(fcstpln3.forecastoverride, None)
        self.assertEqual(fcstpln3.forecastoverridevalue, None)
        self.assertEqual(fcstpln3.forecasttotal, fcstpln3_before.forecasttotal + 100)
        self.assertEqual(
            fcstpln3.forecasttotalvalue, fcstpln3_before.forecasttotalvalue + 5000
        )


@unittest.skipUnless(
    "freppledb.forecast" in settings.INSTALLED_APPS, "App not activated"
)
class ReportTest(TransactionTestCase):
    fixtures = ["distribution_demo"]

    def setUp(self):
        os.environ["FREPPLE_TEST"] = "YES"
        param = Parameter.objects.all().get_or_create(pk="plan.webservice")[0]
        param.value = "false"
        param.save()

        # Login
        if not User.objects.filter(username="admin").count():
            User.objects.create_superuser("admin", "your@company.com", "admin")
        self.client.login(username="admin", password="admin")

    def tearDown(self):
        del os.environ["FREPPLE_TEST"]

    def testForecastReports(self):
        management.call_command("runplan", env="fcst")

        # Forecast table
        response = self.client.get("/data/forecast/forecast/", follow=True)
        checkResponse(self, response)
        response = self.client.get("/data/forecast/forecast/?format=json", follow=True)
        ok = False
        for i in response.streaming_content:
            if b'"records":' in i:
                ok = True
                break
        if not ok:
            self.fail("Invalid response")
        checkResponse(self, response)
        response = self.client.get("/data/forecast/forecast/?format=csvlist")
        checkResponse(self, response)
        self.assertTrue(
            response.__getitem__("Content-Type").startswith("text/csv; charset=")
        )
        response = self.client.get("/data/forecast/forecast/?format=csvtable")
        checkResponse(self, response)
        self.assertTrue(
            response.__getitem__("Content-Type").startswith("text/csv; charset=")
        )
        response = self.client.get("/data/forecast/forecast/?format=csvlist")
        checkResponse(self, response)
        self.assertTrue(
            response.__getitem__("Content-Type").startswith("text/csv; charset=")
        )
        response = self.client.get("/data/forecast/forecast/?format=spreadsheettable")
        checkResponse(self, response)
        self.assertTrue(
            response.__getitem__("Content-Type").startswith(
                "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            )
        )

        # Forecast report
        fcst = Forecast.objects.all()[0]
        response = self.client.get("/forecast/?format=spreadsheettable")
        checkResponse(self, response)
        self.assertTrue(
            response.__getitem__("Content-Type").startswith(
                "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            )
        )
        response = self.client.get("/forecast/?format=spreadsheetlist")
        checkResponse(self, response)
        self.assertTrue(
            response.__getitem__("Content-Type").startswith(
                "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            )
        )
        response = self.client.get("/forecast/?format=csvtable")
        checkResponse(self, response)
        self.assertTrue(
            response.__getitem__("Content-Type").startswith("text/csv; charset=")
        )
        response = self.client.get("/forecast/?format=csvlist")
        checkResponse(self, response)
        self.assertTrue(
            response.__getitem__("Content-Type").startswith("text/csv; charset=")
        )
        response = self.client.get("/forecast/%s/" % fcst.name)
        checkResponse(self, response)
        response = self.client.get("/forecast/%s/?format=spreadsheettable" % fcst.name)
        checkResponse(self, response)
        self.assertTrue(
            response.__getitem__("Content-Type").startswith(
                "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            )
        )
        response = self.client.get("/forecast/%s/?format=csvtable" % fcst.name)
        checkResponse(self, response)
        self.assertTrue(
            response.__getitem__("Content-Type").startswith("text/csv; charset=")
        )
        response = self.client.get("/forecast/%s/?format=csvlist" % fcst.name)
        checkResponse(self, response)
        self.assertTrue(
            response.__getitem__("Content-Type").startswith("text/csv; charset=")
        )

        # Forecast editor
        response = self.client.get("/forecast/itemtree/", {"units": "unit"})
        checkResponse(self, response)
        response = self.client.get("/forecast/itemtree/", {"units": "value"})
        checkResponse(self, response)
        response = self.client.get("/forecast/locationtree/", {"units": "unit"})
        checkResponse(self, response)
        response = self.client.get("/forecast/locationtree/", {"units": "value"})
        checkResponse(self, response)
        response = self.client.get("/forecast/customertree/", {"units": "unit"})
        checkResponse(self, response)
        response = self.client.get("/forecast/customertree/", {"units": "value"})
        checkResponse(self, response)
        response = self.client.get(
            "/forecast/itemtree/", {"units": "unit", "item": fcst.item.name}
        )
        checkResponse(self, response)
        response = self.client.get(
            "/forecast/itemtree/", {"units": "value", "item": fcst.item.name}
        )
        checkResponse(self, response)
        response = self.client.get(
            "/forecast/locationtree/", {"units": "unit", "location": fcst.location.name}
        )
        checkResponse(self, response)
        response = self.client.get(
            "/forecast/locationtree/",
            {"units": "value", "location": fcst.location.name},
        )
        checkResponse(self, response)
        response = self.client.get(
            "/forecast/customertree/", {"units": "unit", "customer": fcst.customer.name}
        )
        checkResponse(self, response)
        response = self.client.get(
            "/forecast/customertree/",
            {"units": "value", "customer": fcst.customer.name},
        )
        checkResponse(self, response)
        response = self.client.get(
            "/forecast/detail/",
            {
                "units": "value",
                "item": fcst.item.name,
                "customer": fcst.customer.name,
                "location": fcst.location.name,
            },
        )
        checkResponse(self, response)
        response = self.client.get(
            "/forecast/detail/",
            {
                "units": "unit",
                "item": fcst.item.name,
                "customer": fcst.customer.name,
                "location": fcst.location.name,
            },
        )
        checkResponse(self, response)


@unittest.skipUnless(
    "freppledb.forecast" in settings.INSTALLED_APPS, "App not activated"
)
class ForecastSimulation(TransactionTestCase):
    fixtures = ["distribution_demo"]

    def setUp(self):
        os.environ["FREPPLE_TEST"] = "YES"

        # Freeze the current date to get reproducible test results.
        # Otherwise, the loaddata command adjusts the data to the current date.
        cursor = connections[DEFAULT_DB_ALIAS].cursor()
        self.now = datetime(2019, 1, 1)
        offset = (self.now - datetime.now()).days
        cursor.execute(
            "update common_parameter set value=%s where name = 'currentdate'",
            (self.now.strftime("%Y-%m-%d %H:%M:%S"),),
        )
        cursor.execute("update demand set due = due + %s * interval '1 day'", (offset,))

    def tearDown(self):
        del os.environ["FREPPLE_TEST"]

    def test_forecast_simulation(self):
        management.call_command("createbuckets")
        management.call_command("forecast_simulation")
        # This SQL is the same as used in the forecast accuracy widget
        cursor = connections[DEFAULT_DB_ALIAS].cursor()
        cursor.execute(
            """
            select common_bucketdetail.name, 100 * sum( fcst * abs(fcst - orders) / abs(fcst + orders) * 2) / greatest(sum(fcst),1)
            from
            (
            select
              startdate,
              greatest(coalesce((value->>'forecasttotal')::numeric,0),0) fcst,
              greatest(coalesce((value->>'orderstotal')::numeric,0) + coalesce((value->>'ordersadjustment')::numeric,0),0) orders
            from forecastplan
            inner join forecast
              on forecastplan.item_id = forecast.item_id
              and forecastplan.location_id = forecast.location_id
              and forecastplan.customer_id = forecast.customer_id
              and forecast.planned = true
            where startdate < %s
              and startdate > %s - interval '%s month'
            ) recs
            inner join common_parameter
              on common_parameter.name = 'forecast.calendar'
            inner join common_bucketdetail
              on common_bucketdetail.bucket_id = common_parameter.value
              and common_bucketdetail.startdate = recs.startdate
            where fcst > 0 or orders > 0
            group by common_bucketdetail.name, recs.startdate
            order by recs.startdate asc
            """,
            (self.now, self.now, 12),
        )
        errorSum = 0
        for i in cursor.fetchall():
            errorSum = errorSum + i[1]
        self.assertAlmostEqual(
            first=errorSum, second=Decimal(405.74), delta=Decimal(5.0)
        )
