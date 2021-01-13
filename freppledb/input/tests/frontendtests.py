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

from freppledb.common.tests import SeleniumTest

try:
    from selenium.common.exceptions import NoSuchElementException
    from selenium.webdriver.common.action_chains import ActionChains
    from selenium.webdriver.common.by import By
    from selenium.webdriver.support import expected_conditions

    noSelenium = False
except ImportError:
    noSelenium = True


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

        # Open purchase order screen
        purchase_menu = self.findElement(By.LINK_TEXT, "Purchasing")
        self.ActionChains().move_to_element(purchase_menu).perform()
        purchaseordermenuItem = self.findElement(
            By.CSS_SELECTOR, "#nav-menu .dropdown-menu a[href='/data/input/purchaseorder/'"
        )
        self.ActionChains().move_to_element(purchaseordermenuItem).click().perform()
        
        #interacting with purchase order table by
        purchase_table = self.findElement(By.CSS_SELECTOR, "table[id='grid']")
        purchase_table_body = purchase_table.find_element_by_tag_name("tbody")
        purchase_table_rows = purchase_table_body.find_elements_by_css_selector("tr:not(first-child)")
        
        #changing quantity field
        purchase_table_quantity_column = purchase_table_rows[0].find_element_by_css_selector("td[aria-describedby='grid_quantity']")
        self.ActionChains().move_to_element(purchase_table_quantity_column).perform()
        #self.assertEqual(purchase_table_quantity_column.text, 500) 
        if (purchase_table_quantity_column.text is 500) or (purchase_table_quantity_column.text is ""):
            self.ActionChains().move_to_element(purchase_table_quantity_column).click().perform()
            quantity_inputField = purchase_table_quantity_column.find_element_by_css_selector("#1_quantity")
            quantity_inputField.send_keys(800)
        
        #TODO: replace all self.findElement into element.find_element
        #changing date field
        purchase_table_enddate_column = self.findElement(purchase_table_rows[0], By.CSS_SELECTOR, "td[aria-describedby='grid_enddate']")
        self.ActionChains().move_to_element(purchase_table_enddate_column).perform()
        
        if (purchase_table_enddate_column.text is 500) or (purchase_table_enddate_column.text is ""):
            self.ActionChains().move_to_element(purchase_table_enddate_column).click().perform()
            quantity_inputField = self.findElement(purchase_table_enddate_column, By.CSS_SELECTOR, "#1_enddate")
            quantity_inputField.send_keys(800)
        #changing supplier field on the chosen [0 to n-1] line
        purchase_table_supplier_column = self.findElement(purchase_table_rows[0], By.CSS_SELECTOR, "td[aria-describedby='grid_supplier']")
        self.ActionChains().move_to_element(purchase_table_supplier_column).perform()
        
        if (purchase_table_supplier_column.text is 500) or (purchase_table_supplier_column.text is ""):
            self.ActionChains().move_to_element(purchase_table_supplier_column).click().perform()
            quantity_inputField = self.findElement(purchase_table_supplier_column, By.CSS_SELECTOR, "#1_supplier")
        #checking if data has been saved into database after saving data
