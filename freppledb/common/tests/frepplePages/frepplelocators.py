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
from selenium.webdriver.common.by import By
#common action's element locators go here
class BasePageLocators(object):
    NAVIGATOR_BREADCUMBS_HOME = (By.CSS_SELECTOR, "#breadcrumbs > li > a[href='/']")
    NAVIGATOR_BREADCUMBS_PURCHASE_ORDERS = (By.CSS_SELECTOR, "#breadcrumbs > li > a[href='/data/input/purchaseorder/']")
#table page locators go here
#Change class into Table Page Locators
class TableLocators(object):
    TABLE_DEFAULT = (By.CSS_SELECTOR, "table[id='grid']")
    PURCHASE_ORDER_TABLE_BODY = (By.CSS_SELECTOR, "tbody")
    PURCHASE_ORDER_TABLE_ROWS = (By.CSS_SELECTOR, "tr")
    #PURCHASE_ORDER_TABLE_SUPPLIER_COLUMN = (By.CSS_SELECTOR, 'td[aria-describedby="grip_supplier"]')
    PURCHASE_ORDER_TABLE_SAVE_BUTTON = (By.CSS_SELECTOR, 'input[id="save"]')
    PURCHASE_ORDER_TABLE_UNDO_BUTTON = (By.CSS_SELECTOR, 'input[id="undo"]')
    PURCHASE_ORDER_TABLE_SELECT_ACTION = (By.CSS_SELECTOR, 'button[id="actions1"]')
    PURCHASE_ORDER_TABLE_SELECT_ACTION_MENU = (By.CSS_SELECTOR, 'ul[id="actionsul"]')
    
    def actionLocator(actionTofind):
        return (By.CSS_SELECTOR, "li>a[name='"+actionTofind+"'")

class SupplierPageLocators(object):
    pass