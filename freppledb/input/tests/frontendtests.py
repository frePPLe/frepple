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
from freppledb.input.models import PurchaseOrder

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
    def test_purchase_order_screen(self):
        self.open("/")
        self.login("admin", "admin")

        self.implicitlyWait(20)
        
        
        
        newQuantity = 800
        targetNavigation = "Purchasing"

        # Open purchase order screen
        purchase_menu = self.findElement(By.LINK_TEXT, targetNavigation)
        self.ActionChains().move_to_element(purchase_menu).perform()
        purchaseordermenuItem = self.findElement(
            By.CSS_SELECTOR, "#nav-menu .dropdown-menu a[href='/data/input/purchaseorder/'"
        )
        self.ActionChains().move_to_element(purchaseordermenuItem).click().perform()
        
        #interacting with purchase order table by
        purchase_table = self.findElement(By.CSS_SELECTOR, "table[id='grid']")
        purchase_table_body = purchase_table.find_element_by_css_selector("tbody")
        purchase_table_rows = purchase_table_body.find_elements_by_css_selector("tr")
        
        #changing supplier field on the chosen [0 to n-1] line
        purchase_table_supplier_column = purchase_table_rows[1].find_element_by_css_selector("td[aria-describedby='grid_supplier']")
        print("getting the supplier: %s" % purchase_table_supplier_column.text)
        self.ActionChains().move_to_element(purchase_table_supplier_column).perform()
        
        if purchase_table_supplier_column.text == "wood supplier":
            print("inside if supplier")
            self.ActionChains().move_to_element_with_offset(purchase_table_supplier_column,1,0).click().perform()# not go to the supplier page
            supplier_inputField = purchase_table_supplier_column.find_element_by_css_selector("input[name='supplier']")
            supplier_inputField.clear()
            time.sleep(3)
            supplier_inputField.send_keys("screw supplier")
            supplier_inputField.send_keys(Keys.RETURN)
            time.sleep(3)
            #return to purchase order page
            #self.findElement(By.CSS_SELECTOR,"#breadcrumbs > li > a[href='/data/input/purchaseorder/']" ).click()
        
        
        #refreshing element as table and buttons element get stale
        purchase_table = self.findElement(By.CSS_SELECTOR, "table[id='grid']")
        purchase_table_body = purchase_table.find_element_by_css_selector("tbody")
        purchase_table_rows = purchase_table_body.find_elements_by_css_selector("tr")
        
        saveButton = self.findElement(By.CSS_SELECTOR, "input[id='save']")
        
        
        #changing quantity field
        print('this the first row of table element:  --> %s' % purchase_table_rows[1].get_attribute('innerHTML'))
        time.sleep(10)
        reference = purchase_table_rows[1].get_attribute("id")
        print("this table id is: %s" % reference)
        purchase_table_quantity_column = purchase_table_rows[1].find_element_by_css_selector("td[aria-describedby='grid_quantity']")
        self.ActionChains().move_to_element(purchase_table_quantity_column).perform()
        self.assertEqual(purchase_table_quantity_column.text, "100") 
        if purchase_table_quantity_column.text == "100":
            self.ActionChains().move_to_element(purchase_table_quantity_column).click().perform()
            quantity_inputField = purchase_table_quantity_column.find_element_by_css_selector("input[id='1_quantity'")
            time.sleep(1)
            quantity_inputField.send_keys(800)
            quantity_inputField.send_keys(Keys.RETURN)
            self.assertEqual(purchase_table_quantity_column.text, "800", "the input field of quantity hasn't been modified")
        
        #changing date field
        purchase_table_enddate_column = purchase_table_rows[1].find_element_by_css_selector("td[aria-describedby='grid_enddate']")
        purchase_table_startdate_column = purchase_table_rows[1].find_element_by_css_selector("td[aria-describedby='grid_startdate']")
        self.ActionChains().move_to_element(purchase_table_enddate_column).perform()
        #print("end date column: %s" % purchase_table_enddate_column.text)
        #print("begin date column: %s" % purchase_table_startdate_column.text)
        oldEndDate = datetime.strptime(purchase_table_enddate_column.text, "%Y-%m-%d 00:00:00")
        newEndDate = oldEndDate + mainDate.timedelta(days=9)
        #print ("%s" % newEndDate)
        #print("we got in end date")
        self.ActionChains().move_to_element(purchase_table_enddate_column).click().perform()
        enddate_inputField = purchase_table_enddate_column.find_element_by_css_selector("input[id='1_enddate']")
        enddate_inputField.clear()
        enddate_inputField.send_keys(newEndDate.strftime("%Y-%m-%d 00:00:00"))
        #time.sleep(5)
        enddate_inputField.send_keys(Keys.RETURN)
        self.assertEqual(purchase_table_enddate_column.text, newEndDate.strftime("%Y-%m-%d 00:00:00"), "the input field of Receipt Date hasn't been modified")
        newdatetext= newEndDate.strftime("%Y-%m-%d 00:00:00")
        #checking if data has been saved into database after saving data
        self.ActionChains().move_to_element(saveButton).click().perform()
        time.sleep(2)
        print(PurchaseOrder.objects.get(reference=reference, enddate=newdatetext))
        for i in PurchaseOrder.objects.all().filter(reference=reference, enddate=newdatetext, quantity=newQuantity):
            print (i.reference, i.supplier.name, i.quantity)
            
        self.assertEqual(
            PurchaseOrder.objects.all().filter(reference=reference, enddate=newdatetext, supplier_id="screw supplier" , quantity=newQuantity)
            .count(),
            1,
        )

