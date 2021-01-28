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
    
    def mainMenuLinkLocator (targetLink):
        return (By.LINK_TEXT, targetLink)
    def subMenuItemLocator(targetItem):
        return (By.CSS_SELECTOR, "#nav-menu  .dropdown-menu a[href*='%s']" % targetItem)


#table page locators go here
class TableLocators(object):
    TABLE_DEFAULT = (By.CSS_SELECTOR, "table[id='grid']")
    TABLE_BODY = (By.CSS_SELECTOR, "tbody")
    TABLE_ROWS = (By.CSS_SELECTOR, "tr")
    TABLE_SAVE_BUTTON = (By.CSS_SELECTOR, 'input[id="save"]')
    TABLE_UNDO_BUTTON = (By.CSS_SELECTOR, 'input[id="undo"]')
    TABLE_SELECT_ACTION = (By.CSS_SELECTOR, 'button[id="actions1"]')
    TABLE_SELECT_ACTION_MENU = (By.CSS_SELECTOR, 'ul[id="actionsul"]')
    
    tablecolumns = {
        "supplier" : (By.CSS_SELECTOR, 'td[aria-describedby="grid_supplier"]'),
        "quantity" : (By.CSS_SELECTOR, 'td[aria-describedby="grid_quantity"]'),
        "startdate" : (By.CSS_SELECTOR, 'td[aria-describedby="grid_startdate"]'),
        "enddate" : (By.CSS_SELECTOR, 'td[aria-describedby="grid_enddate"]'),
    }
    
    tablecolumnsinput = {
        "supplier" : (By.CSS_SELECTOR, 'input[name="supplier"]'),
        "quantity" : (By.CSS_SELECTOR, 'input[id="1_quantity"]'),
        "startdate" : (By.CSS_SELECTOR, 'input[id="1_startdate"]'),
        "enddate" : (By.CSS_SELECTOR, 'input[id="1_enddate"]'),
        
    }
    
    def actionLocator(actionTofind):
        return (By.CSS_SELECTOR, "li>a[name='"+actionTofind+"'")
