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
from freppleelement import BasePageElement #in here, import the class containing all the elements from your target page 
from frepplelocators import PurchaseOrderPageLocators #here, we should find all the locators for your target page


### Special page for common actions only

class SupplierEditInputElement(BasePageElement):
    locator = 'input[id=id_name]'


"""class PurchaseOrderTableSelectActionMenuElement(BasePageElement):
    select_action_statuses = ("proposed","approved","confirmed","completed","closed")"""

class BasePage(object):
    NAV_MENU_LEFT = ("Sales", "Inventory", "Capacity", "Purchasing", "Manufacturing", "Admin", "My Reports", "Help")
    
    
    def __init__(self, driver):
        self.driver = driver
    
    def login(self):
        pass
    
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
    purchase_order_table_element = PurchaseOrderTableElement()
    
    def is_title_matches(self): # change to current url
        return "Purchase orders" in self.driver.title
    
    def click_save_button(self):
        save_button = self.driver.find_element(*PurchaseOrderPageLocators.PURCHASE_ORDER_TABLE_SAVE_BUTTON)
        save_button.click()
    
    def click_undo_button(self):
        undo_button = self.driver.find_element(*PurchaseOrderPageLocators.PURCHASE_ORDER_TABLE_UNDO_BUTTON)
        undo_button.click()
    
    def select_action(self,actionToPerform): # method that will select an action from the select action dropdown
        select = self.driver.find_element(*PurchaseOrderPageLocators.PURCHASE_ORDER_TABLE_SELECT_ACTION);
        select.click()
        select_menu = self.driver.find_element(*PurchaseOrderPageLocators.PURCHASE_ORDER_TABLE_SELECT_ACTION_MENU)
        select_action = self.driver.find_element(*PurchaseOrderPageLocators.actionLocator(actionToPerform))
        select_action.click()
    
    def multiline_checkboxes_check(self, number_of_line, checkbox_column): # method that will check a certain number of checkboxes in the checkbox column
        max_number_checkboxes = 8;
        if(number_of_line <= 8):
            
    
    def click_target_row_colum(self, target_row, target_column): # method that clicks of the table cell at the targeted row and column
        pass
    


