#
# Copyright (C) 2007-2019 by frePPLe bv
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
import unittest
import time
import datetime as mainDate
from datetime import datetime

from freppledb.common.tests.seleniumsetup import SeleniumTest
from freppledb.common.tests.frepplePages.frepplepage import TablePage
from freppledb.input.models import PurchaseOrder
from django.db.models import Q

try:
    from selenium.common.exceptions import NoSuchElementException
    from selenium.webdriver.common.action_chains import ActionChains
    from selenium.webdriver.common.by import By
    from selenium.webdriver.common.keys import Keys
    from selenium.webdriver.support import expected_conditions

    noSelenium = False
except ImportError:
    noSelenium = True

## page only for non-recurring actions within the app
## each unit test represent a screen
class PurchaseOrderScreen(SeleniumTest):
    fixtures = ["manufacturing_demo"]
    
    @unittest.skipIf(noSelenium, "selenium not installed")
    def test_table_single_row_modification(self):
        
        newQuantity = 800
        newSupplier = "screw supplier"
        
        table_page = TablePage(self.driver, SeleniumTest)
        table_page.login(self)
        
        # Open purchase order screen
        table_page.go_to_target_page_by_menu("Purchasing","purchaseorder")
        
        purchase_order_table = table_page.get_table()
        
        firstrow = table_page.get_table_row(rowNumber = 1)
        reference = firstrow.get_attribute("id")
        
        supplier_content = table_page.get_content_of_row_column(firstrow,"supplier")
        supplier_inputfield = table_page.click_target_cell(supplier_content, "supplier")
        #only put existing supplier otherwise saving modification fails
        table_page.enter_text_in_inputfield(supplier_inputfield, newSupplier)
        
        quantity_content = table_page.get_content_of_row_column(firstrow,"quantity")
        quantity_inputfield = table_page.click_target_cell(quantity_content, "quantity")
        table_page.enter_text_in_inputfield(quantity_inputfield, newQuantity)
        self.assertEqual(quantity_content.text, "800", "the input field of quantity hasn't been modified")
        
        enddate_content = table_page.get_content_of_row_column(firstrow,"enddate")
        enddate_inputdatefield = table_page.click_target_cell(enddate_content, "enddate")
        
        oldEndDate = datetime.strptime(enddate_inputdatefield.get_attribute("value"), "%Y-%m-%d 00:00:00")
        newEndDate = oldEndDate + mainDate.timedelta(days=9)
        newdatetext = table_page.enter_text_in_inputdatefield(enddate_inputdatefield, newEndDate)
        
        enddate_content = table_page.get_content_of_row_column(firstrow,"enddate")
        enddate_inputdatefield = table_page.click_target_cell(enddate_content, "enddate")
        self.assertEqual(enddate_inputdatefield.get_attribute("value"), newEndDate.strftime("%Y-%m-%d 00:00:00"), "the input field of Receipt Date hasn't been modified")
        
        
        #checking if data has been saved into database after saving data
        table_page.click_save_button()
        time.sleep(1)
        
        self.assertEqual(
            PurchaseOrder.objects.all().filter(reference=reference, enddate=newdatetext, supplier_id=newSupplier , quantity=newQuantity)
            .count(),
            1,
        )
    
    @unittest.skipIf(noSelenium, "selenium not installed")
    def test_table_multiple_rows_modification(self):
        
        table_page = TablePage(self.driver, SeleniumTest)
        table_page.login(self)
        
        # Open purchase order screen
        table_page.go_to_target_page_by_menu("Purchasing","purchaseorder")
        
        purchase_order_table = table_page.get_table()
        
        rows = table_page.get_table_multiple_rows(rowNumber = 2)
        
        table_page.multiline_checkboxes_check(targetrows=rows)
        
        references = []
        newStatus = "completed"
        q_objects = Q()
        
        table_page.select_action(newStatus)
        
        for row in rows:
            references.append(row.get_attribute("id"))
            
        table_page.click_save_button()
        
        time.sleep(2)
        for reference in references:
            
            q_objects |= Q(reference=reference)
            
        
        
        self.assertEqual(
            PurchaseOrder.objects.all().filter(q_objects,status=newStatus)
            .count(),
            2,
        )
        
        
    
    
    

