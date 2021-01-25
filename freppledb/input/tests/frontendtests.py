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

from freppledb.common.tests import SeleniumTest
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
class SeleniumTestScreen1(SeleniumTest):
    fixtures = ["manufacturing_demo"]
    
    @unittest.skipIf(noSelenium, "selenium not installed")
    def test_preferences(self):
        self.open("/")
        self.login("admin", "admin")

        # Open preferences form
        usermenu = self.findElement(By.CSS_SELECTOR, "#nav-menu .navbar-right")
        self.ActionChains().move_to_element(usermenu).perform()
        prefmenuitem = self.findElement(
            By.CSS_SELECTOR, "#nav-menu .navbar-right a[href='/preferences/'"
        )
        self.ActionChains().move_to_element(prefmenuitem).click().perform()
    
    
    @unittest.skipIf(noSelenium, "selenium not installed")
    def test_purchase_order_screen(self):
        self.open("/")
        self.login("admin", "admin")

        self.implicitlyWait(20)
        
        
        newEndDate = "2021-01-22 00:00:00"
        newQuantity = 800
        targetNavigation = "Purchasing"
        newSupplier = "Brazilian wood supplier"

        # Open purchase order screen
        purchase_menu = self.findElement(By.LINK_TEXT, targetNavigation)
        self.ActionChains().move_to_element(purchase_menu).perform()
        purchaseordermenuItem = self.findElement(
            By.CSS_SELECTOR, "#nav-menu .dropdown-menu a[href='/data/input/purchaseorder/'"
        )
        self.ActionChains().move_to_element(purchaseordermenuItem).click().perform()
        
        saveButton = self.findElement(By.CSS_SELECTOR, "input[id='save']")
        
        #interacting with purchase order table by
        purchase_table = self.findElement(By.CSS_SELECTOR, "table[id='grid']")
        purchase_table_body = purchase_table.find_element_by_css_selector("tbody")
        purchase_table_rows = purchase_table_body.find_elements_by_css_selector("tr")
        
        #changing supplier field on the chosen [0 to n-1] line
        purchase_table_supplier_column = purchase_table_rows[1].find_element_by_css_selector("td[aria-describedby='grid_supplier']")
        print("getting the supplier: %s" % purchase_table_supplier_column.text)
        self.ActionChains().move_to_element(purchase_table_supplier_column).perform()
        
        if purchase_table_supplier_column.text == "wood supplier":
            self.ActionChains().move_to_element(purchase_table_supplier_column).click().perform()# go to the supplier page
            supplier_inputField = self.findElement(By.CSS_SELECTOR, "input[id='id_name']")
            supplier_inputField.clear()
            supplier_inputField.send_keys(newSupplier)
            supplier_inputField.send_keys(Keys.RETURN)
            #return to purchase order page
            self.findElement(By.CSS_SELECTOR,"#breadcrumbs > li > a[href='/data/input/purchaseorder/']" ).click()
        time.sleep(60)
        #changing quantity field
        #print('this the first row of table element:  --> %s' % purchase_table_rows[1].get_attribute('innerHTML'))
        reference = purchase_table_rows[1].get_attribute("id")
        print("this table id is: %s" % reference)
        purchase_table_quantity_column = purchase_table_rows[1].find_element_by_css_selector("td[aria-describedby='grid_quantity']")
        self.ActionChains().move_to_element(purchase_table_quantity_column).perform()
        self.assertEqual(purchase_table_quantity_column.text, "100") 
        if purchase_table_quantity_column.text == "100":
            self.ActionChains().move_to_element(purchase_table_quantity_column).click().perform()
            quantity_inputField = purchase_table_quantity_column.find_element_by_css_selector("input[id='1_quantity'")
            quantity_inputField.send_keys(800)
            quantity_inputField.send_keys(Keys.RETURN)
            self.assertEqual(purchase_table_quantity_column.text, "800", "the input field of quantity hasn't been modified")
        
        #changing date field
        purchase_table_enddate_column = purchase_table_rows[1].find_element_by_css_selector("td[aria-describedby='grid_enddate']")
        self.ActionChains().move_to_element(purchase_table_enddate_column).perform()
        
        if purchase_table_enddate_column.text == "2021-01-14 00:00:00":
            self.ActionChains().move_to_element(purchase_table_enddate_column).click().perform()
            enddate_inputField = purchase_table_enddate_column.find_element_by_css_selector("input[id='1_enddate']")
            enddate_inputField.clear()
            enddate_inputField.send_keys(newEndDate)
            enddate_inputField.send_keys(Keys.RETURN)
            self.assertEqual(purchase_table_enddate_column.text, newEndDate, "the input field of Receipt Date hasn't been modified")
        
        #checking if data has been saved into database after saving data
        self.ActionChains().move_to_element(saveButton).click().perform()
        time.sleep(10)
        self.assertEqual(
            PurchaseOrder.objects.all()
            .filter(reference=reference, enddate=newEndDate, supplier=newSupplier , quantity=newQuantity)
            .count(),
            1,
        )
        
    
    @unittest.skipIf(noSelenium, "selenium not installed")
    def test_supplier_screen(self):
        self.open("/")
        self.login("admin", "admin")

        self.implicitlyWait(20)
        
        targetNavigation = "Purchasing"
        
        
        purchase_menu = self.findElement(By.LINK_TEXT, targetNavigation)
        self.ActionChains().move_to_element(purchase_menu).perform()
        purchaseordermenuItem = self.findElement(
            By.CSS_SELECTOR, "#nav-menu .dropdown-menu a[href='/data/input/purchaseorder/'"
        )
        
        self.ActionChains().move_to_element(purchaseordermenuItem).click().perform()
        
        saveButton = self.findElement(By.CSS_SELECTOR, "input[id='save']")
        
        #interacting with purchase order table by
        purchase_table = self.findElement(By.CSS_SELECTOR, "table[id='grid']")
        purchase_table_body = purchase_table.find_element_by_tag_name("tbody")
        purchase_table_rows = purchase_table_body.find_elements_by_css_selector("tr")
