#
# Copyright (C) 2025 by frePPLe bv
#
# All information contained herein is, and remains the property of frePPLe.
# You are allowed to use and modify the source code, as long as the software is used
# within your company.
# You are not allowed to distribute the software, either in the form of source code
# or in the form of compiled binaries.
#

import os
import time
import unittest

from django.conf import settings
from django.core import management
from django.db import DEFAULT_DB_ALIAS, connections

from freppledb.webservice.utils import waitTillRunning
from freppledb.common.tests.seleniumsetup import SeleniumTest, noSelenium
from freppledb.forecast.tests.seleniumpages.forecastpage import ForecastTablePage


@unittest.skipUnless(
    "freppledb.forecast" in settings.INSTALLED_APPS, "App not activated"
)
@unittest.skipIf(noSelenium, "selenium not installed")
class ForecastEditorScreen(SeleniumTest):
    fixtures = ["manufacturing_demo"]

    def setUp(self):
        os.environ["FREPPLE_TEST"] = "webservice"
        if "nowebservice" in os.environ:
            del os.environ["nowebservice"]
        management.call_command("runplan", env="fcst,supply", background=True)
        waitTillRunning(timeout=180)
        super().setUp()

    def tearDown(self):
        management.call_command("stopwebservice", force=True, wait=True)
        super().tearDown()

    def test_table_forecast_override(self):
        newQuantity = 20
        month_to_override = 3
        months_to_add = 5

        forecast_table_page = ForecastTablePage(self.driver, ForecastEditorScreen)
        forecast_table_page.login()

        # Open purchase order screen
        forecast_table_page.go_to_target_page_by_menu("Sales", "forecast/editor")

        # months are numbered from 1 to n
        forecast_table_page.set_value_target_override_cell(
            month_to_override, newQuantity
        )

        forecast_table_page.click_save_forecast()
        time.sleep(1)

        with connections[DEFAULT_DB_ALIAS].cursor() as cursor:
            cursor.execute(
                """
                select sum(forecastoverride)
                from forecastplan
                where item_id = (select name from item where lvl = 0)
                  and location_id = (select name from location where lvl = 0)
                  and customer_id = (select name from customer where lvl = 0)
                """
            )
            self.assertEqual(cursor.fetchone()[0], newQuantity)

            # months are numbered from 1 to n
        forecast_table_page.set_value_target_override_cell(1, 0)

        frominput = forecast_table_page.get_startdate_input()

        # monthsadded represent months added from the first month on if its value is n the range size is n+1
        (
            newstartdate,
            newenddate,
            timerange,
        ) = forecast_table_page.update_forecast_override_time_range(
            frominput, monthsadded=months_to_add, overridevalue=200
        )
        time.sleep(1)

        self.assertEqual(
            newstartdate.strftime("%Y-%m-%d"),
            forecast_table_page.get_startdate_input().get_attribute("value"),
            "input startdate either is not updated or its value is wrong",
        )
        self.assertEqual(
            newenddate.strftime("%Y-%m-%d"),
            forecast_table_page.get_enddate_input().get_attribute("value"),
            "input enddate either is not updated or its value is wrong",
        )

        self.assertNotEqual(
            newstartdate, newenddate, "start date and enddate must be different"
        )

        forecast_table_page.click_apply_override_forecast_edit_button()
        time.sleep(1)
        forecast_table_page.click_save_forecast()
        time.sleep(1)

        with connections[DEFAULT_DB_ALIAS].cursor() as cursor:
            cursor.execute(
                """
                select count(forecastoverride)
                from forecastplan
                where item_id = (select name from item where lvl = 0)
                  and location_id = (select name from location where lvl = 0)
                  and customer_id = (select name from customer where lvl = 0)
                  and forecastoverride > 0
                """
            )

            self.assertEqual(cursor.fetchone()[0], timerange)
