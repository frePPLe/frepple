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
import datetime as mainDate
from datetime import datetime
import os
import time
import unittest

from django.conf import settings
from django.db.models import Q
from django.core import management
from django.utils.formats import date_format

from freppledb.common.localization import parseLocalizedDateTime
from freppledb.common.tests.seleniumsetup import SeleniumTest, noSelenium
from freppledb.common.tests.frepplePages.frepplepage import TablePage
from freppledb.input.models import (
    PurchaseOrder,
    DistributionOrder,
    ManufacturingOrder,
)
from freppledb.webservice.utils import waitTillRunning


@unittest.skipIf(noSelenium, "selenium not installed")
class PurchaseOrderScreen(SeleniumTest):
    fixtures = ["manufacturing_demo"]

    def setUp(self):
        os.environ["FREPPLE_TEST"] = "webservice"
        if "nowebservice" in os.environ:
            del os.environ["nowebservice"]
        management.call_command("runplan", env="loadplan", background=True)
        waitTillRunning(timeout=180)
        super().setUp()

    def tearDown(self):
        management.call_command("stopwebservice", force=True, wait=True)
        super().tearDown()

    def test_table_single_row_modification(self):
        newQuantity = 800
        newSupplier = "screw supplier"

        table_page = TablePage(self.driver, PurchaseOrderScreen)
        table_page.login()

        # Open purchase order screen
        table_page.go_to_target_page_by_menu("Purchasing", "purchaseorder")

        firstrow = table_page.get_table_row(rowNumber=1)
        reference = firstrow.get_attribute("id")

        supplier_content = table_page.get_content_of_row_column(firstrow, "supplier")
        supplier_inputfield = table_page.click_target_cell(supplier_content, "supplier")
        # only put existing supplier otherwise saving modification fails
        table_page.enter_text_in_inputfield(supplier_inputfield, newSupplier)

        quantity_content = table_page.get_content_of_row_column(firstrow, "quantity")
        quantity_inputfield = table_page.click_target_cell(quantity_content, "quantity")
        table_page.enter_text_in_inputfield(quantity_inputfield, newQuantity)
        self.assertEqual(
            quantity_content.text,
            "800",
            "the input field of quantity hasn't been modified",
        )

        enddate_content = table_page.get_content_of_row_column(firstrow, "enddate")
        enddate_inputdatefield = table_page.click_target_cell(
            enddate_content, "enddate"
        )

        oldEndDate = parseLocalizedDateTime(
            enddate_inputdatefield.get_attribute("value")
        )
        newEndDate = oldEndDate + mainDate.timedelta(days=9)
        table_page.enter_text_in_inputdatefield(enddate_inputdatefield, newEndDate)

        enddate_content = table_page.get_content_of_row_column(firstrow, "enddate")
        enddate_inputdatefield = table_page.click_target_cell(
            enddate_content, "enddate"
        )
        self.assertEqual(
            enddate_inputdatefield.get_attribute("value"),
            date_format(newEndDate, "DATETIME_FORMAT", False),
            "the input field of Receipt Date hasn't been modified",
        )

        # checking if data has been saved into database after saving data
        table_page.click_save_button()
        time.sleep(1)

        self.assertEqual(
            PurchaseOrder.objects.all()
            .filter(
                reference=reference,
                enddate=newEndDate,
                supplier_id=newSupplier,
                quantity=newQuantity,
            )
            .count(),
            1,
        )

    @unittest.skipIf(settings.ERP_CONNECTOR, "ERP connector app active")
    def test_table_multiple_rows_modification(self):
        table_page = TablePage(self.driver, PurchaseOrderScreen)
        table_page.login()

        # Open purchase order screen
        table_page.go_to_target_page_by_menu("Purchasing", "purchaseorder")

        rows = table_page.get_table_multiple_rows(rowNumber=2)

        table_page.multiline_checkboxes_check(targetrows=rows)

        newStatus = "completed"

        table_page.select_action(newStatus)

        q_objects = Q()
        for row in rows:
            q_objects |= Q(reference=row.get_attribute("id"))

        table_page.click_save_button()

        time.sleep(2)

        self.assertEqual(
            PurchaseOrder.objects.all().filter(q_objects, status=newStatus).count(), 2
        )


@unittest.skipIf(noSelenium, "selenium not installed")
class DistributionOrderScreen(SeleniumTest):
    fixtures = ["manufacturing_demo"]

    def setUp(self):
        os.environ["FREPPLE_TEST"] = "webservice"
        if "nowebservice" in os.environ:
            del os.environ["nowebservice"]
        management.call_command("runplan", env="loadplan", background=True)
        waitTillRunning(timeout=180)
        super().setUp()

    def tearDown(self):
        management.call_command("stopwebservice", force=True, wait=True)
        super().tearDown()

    def test_table_single_row_modification(self):
        newQuantity = 70
        newDestination = "shop 2"

        table_page = TablePage(self.driver, DistributionOrderScreen)
        table_page.login()

        # Open purchase order screen
        table_page.go_to_target_page_by_menu("Inventory", "distributionorder")

        firstrow = table_page.get_table_row(rowNumber=1)
        reference = firstrow.get_attribute("id")

        destination_content = table_page.get_content_of_row_column(
            firstrow, "destination"
        )
        destination_inputfield = table_page.click_target_cell(
            destination_content, "destination"
        )
        # only put existing destination otherwise saving modification fails ?
        table_page.enter_text_in_inputfield(destination_inputfield, newDestination)

        quantity_content = table_page.get_content_of_row_column(firstrow, "quantity")
        quantity_inputfield = table_page.click_target_cell(quantity_content, "quantity")
        table_page.enter_text_in_inputfield(quantity_inputfield, newQuantity)
        self.assertEqual(
            quantity_content.text,
            "70",
            "the input field of quantity hasn't been modified",
        )

        enddate_content = table_page.get_content_of_row_column(firstrow, "enddate")
        enddate_inputdatefield = table_page.click_target_cell(
            enddate_content, "enddate"
        )

        oldEndDate = parseLocalizedDateTime(
            enddate_inputdatefield.get_attribute("value")
        )
        newEndDate = oldEndDate + mainDate.timedelta(days=9)
        table_page.enter_text_in_inputdatefield(enddate_inputdatefield, newEndDate)

        enddate_content = table_page.get_content_of_row_column(firstrow, "enddate")
        enddate_inputdatefield = table_page.click_target_cell(
            enddate_content, "enddate"
        )
        self.assertEqual(
            enddate_inputdatefield.get_attribute("value"),
            date_format(newEndDate, "DATETIME_FORMAT", False),
            "the input field of Receipt Date hasn't been modified",
        )

        # checking if data has been saved into database after saving data
        table_page.click_save_button()
        time.sleep(1)

        self.assertEqual(
            DistributionOrder.objects.all()
            .filter(
                reference=reference,
                enddate=newEndDate,
                destination_id=newDestination,
                quantity=newQuantity,
            )
            .count(),
            1,
        )

    @unittest.skipIf(settings.ERP_CONNECTOR, "ERP connector app active")
    def test_table_multiple_rows_modification(self):
        table_page = TablePage(self.driver, DistributionOrderScreen)
        table_page.login()

        # Open purchase order screen
        table_page.go_to_target_page_by_menu("Inventory", "distributionorder")

        rows = table_page.get_table_multiple_rows(rowNumber=2)

        table_page.multiline_checkboxes_check(targetrows=rows)

        newStatus = "completed"

        table_page.select_action(newStatus)

        q_objects = Q()
        for row in rows:
            q_objects |= Q(reference=row.get_attribute("id"))

        table_page.click_save_button()
        time.sleep(2)

        self.assertEqual(
            DistributionOrder.objects.all().filter(q_objects, status=newStatus).count(),
            2,
        )


@unittest.skipIf(noSelenium, "selenium not installed")
class ManufacturingOrderScreen(SeleniumTest):
    fixtures = ["manufacturing_demo"]

    def setUp(self):
        os.environ["FREPPLE_TEST"] = "webservice"
        if "nowebservice" in os.environ:
            del os.environ["nowebservice"]
        management.call_command(
            "runplan",
            plantype=1,
            constraint="capa,mfg_lt,po_lt",
            env="supply,loadplan",
            background=True,
        )
        waitTillRunning(timeout=180)
        super().setUp()

    def tearDown(self):
        management.call_command("stopwebservice", force=True, wait=True)
        super().tearDown()

    def test_table_single_row_modification(self):
        newQuantity = 20
        newOperation = "Saw chair leg"

        table_page = TablePage(self.driver, ManufacturingOrderScreen)
        table_page.login()

        # Open purchase order screen
        table_page.go_to_target_page_by_menu("Manufacturing", "manufacturingorder")

        firstrow = table_page.get_table_row(rowNumber=1)
        reference = firstrow.get_attribute("id")

        operation_content = table_page.get_content_of_row_column(firstrow, "operation")
        operation_inputfield = table_page.click_target_cell(
            operation_content, "operation"
        )
        # only put existing operation otherwise saving modification fails
        table_page.enter_text_in_inputfield(operation_inputfield, newOperation)

        quantity_content = table_page.get_content_of_row_column(firstrow, "quantity")
        quantity_inputfield = table_page.click_target_cell(quantity_content, "quantity")
        table_page.enter_text_in_inputfield(quantity_inputfield, newQuantity)
        self.assertEqual(
            quantity_content.text,
            "20",
            "the input field of quantity hasn't been modified",
        )

        enddate_content = table_page.get_content_of_row_column(firstrow, "enddate")
        enddate_inputdatefield = table_page.click_target_cell(
            enddate_content, "enddate"
        )

        oldEndDate = parseLocalizedDateTime(
            enddate_inputdatefield.get_attribute("value")
        )
        newEndDate = oldEndDate + mainDate.timedelta(days=7)
        table_page.enter_text_in_inputdatefield(enddate_inputdatefield, newEndDate)

        enddate_content = table_page.get_content_of_row_column(firstrow, "enddate")
        enddate_inputdatefield = table_page.click_target_cell(
            enddate_content, "enddate"
        )
        self.assertEqual(
            enddate_inputdatefield.get_attribute("value"),
            date_format(newEndDate, "DATETIME_FORMAT", False),
            "the input field of Receipt Date hasn't been modified",
        )

        # checking if data has been saved into database after saving data
        table_page.click_save_button()
        time.sleep(3)

        self.assertEqual(
            ManufacturingOrder.objects.all()
            .filter(
                reference=reference,
                enddate=newEndDate,
                operation_id=newOperation,
                quantity=newQuantity,
            )
            .count(),
            1,
        )

    @unittest.skipIf(settings.ERP_CONNECTOR, "ERP connector app active")
    def test_table_multiple_rows_modification(self):
        table_page = TablePage(self.driver, ManufacturingOrderScreen)
        table_page.login()

        # Open manufacturing order screen
        table_page.go_to_target_page_by_menu("Manufacturing", "manufacturingorder")

        rows = table_page.get_table_multiple_rows(rowNumber=2)

        table_page.multiline_checkboxes_check(targetrows=rows)

        newStatus = "completed"

        table_page.select_action(newStatus)

        q_objects = Q()
        for row in rows:
            q_objects |= Q(reference=row.get_attribute("id"))

        table_page.click_save_button()

        time.sleep(2)

        self.assertEqual(
            ManufacturingOrder.objects.all()
            .filter(q_objects, status=newStatus)
            .count(),
            2,
        )
