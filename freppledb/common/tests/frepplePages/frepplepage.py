#
# Copyright (C) 2013 by frePPLe bv
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
from freppledb.common.tests.frepplePages.freppleelement import BasePageElement #in here, import the class containing all the elements from your target page 
from freppledb.common.tests.frepplePages.frepplelocators import TableLocators, BasePageLocators #here, we should find all the locators for your target page
#from freppledb.common.tests.seleniumsetup import SeleniumTest
import selenium
from django.db.models.functions.window import RowNumber


### Special page for common actions only

class SupplierEditInputElement(BasePageElement):
    locator = 'input[id=id_name]'


"""class PurchaseOrderTableSelectActionMenuElement(BasePageElement):
    select_action_statuses = ("proposed","approved","confirmed","completed","closed")"""

class BasePage(object):
    NAV_MENU_LEFT = ("Sales", "Inventory", "Capacity", "Purchasing", "Manufacturing", "Admin", "My Reports", "Help")
    
    def __init__(self, driver, selenium):
        self.driver = driver
        self.selenium = selenium
    
    def login(self, selenium):
        selenium.open("/")
        selenium.login("admin", "admin")

        selenium.implicitlyWait(20)
        
    def go_to_target_page_by_menu(self,menu_item, submenu_item):
        (menuby, menulocator) = BasePageLocators.mainMenuLinkLocator(menu_item)
        self.menuitem = self.selenium.findElement(self,menuby, menulocator)
        self.selenium.ActionChains(self).move_to_element(self.menuitem).perform()
        
        (submenuby, submenulocator) = BasePageLocators.subMenuItemLocator(submenu_item)
        self.submenuitem = self.selenium.findElement(self,submenuby, submenulocator)
        self.selenium.ActionChains(self).move_to_element(self.submenuitem).click().perform()
    
    def go_home_with_breadcrumbs(self):
        pass
    
    def go_back_to_page_with_breadcrumbs(self, targetPageName):
        pass
    #most common actions go here like opening a menu, clicking a save button, clicking undo


#create a table page class
#for all interactions with table
#ability to choose a specific table to interact with
#selecting a cell, updating a cell, reading value of a cell
class TablePage(BasePage):
    #purchase order page action method come here
    
    #declaring variable that will contain the retrieved table
    table = None
    
    def get_table(self):
        self.table = self.driver.find_element(*TableLocators.TABLE_DEFAULT)
        return self.table
    
    def get_table_row(self, rowNumber):
        table = self.get_table()
        #body = self.driver.find_element(*TableLocators.TABLE_BODY)
        rows = table.find_elements(*TableLocators.TABLE_ROWS)
        return rows[rowNumber]
        #print("in table body : %s " % rows[rowNumber].get_attribute("innerHTML"))
    
    def get_content_of_row_column(self, rowNumber, columnName):
        row = self.get_table_row(rowNumber)
        content = row.find_element(*TableLocators.tablecolumns[columnName])
        return content
    
    def get_content_of_row_column(self, rowElement , columnName):
        content = rowElement.find_element(*TableLocators.tablecolumns[columnName])
        return content
    
    #def is_title_matches(self): # change to current url
    #    return "Purchase orders" in self.driver.title
    
    def click_save_button(self):
        save_button = self.driver.find_element(*TableLocators.TABLE_SAVE_BUTTON)
        save_button.click()
    
    def click_undo_button(self):
        undo_button = self.driver.find_element(*TableLocators.TABLE_UNDO_BUTTON)
        undo_button.click()
    
    def select_action(self,actionToPerform): # method that will select an action from the select action dropdown
        select = self.driver.find_element(*TableLocators.TABLE_SELECT_ACTION);
        select.click()
        select_menu = self.driver.find_element(*TableLocators.TABLE_SELECT_ACTION_MENU)
        select_action = self.driver.find_element(*TableLocators.actionLocator(actionToPerform))
        select_action.click()
    
    def multiline_checkboxes_check(self, number_of_line, checkbox_column): # method that will check a certain number of checkboxes in the checkbox column
        
        if(number_of_line <= 8):
            pass
    
    def click_target_row_colum(self, target_row, target_column): # method that clicks of the table cell at the targeted row and column
        pass
    


