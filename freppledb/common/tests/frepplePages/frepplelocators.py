#
# Copyright (C) 2013 by frePPLe bv
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
from selenium.webdriver.common.by import By


class BasePageLocators:
    NAVIGATOR_BREADCUMBS_HOME = (By.CSS_SELECTOR, "#breadcrumbs > li > a[href='/']")
    NAVIGATOR_BREADCUMBS_PURCHASE_ORDERS = (
        By.CSS_SELECTOR,
        "#breadcrumbs > li > a[href='/data/input/purchaseorder/']",
    )

    @staticmethod
    def mainMenuLinkLocator(targetLink):
        return (By.LINK_TEXT, targetLink)

    @staticmethod
    def subMenuItemLocator(targetItem):
        return (By.CSS_SELECTOR, "#nav-menu  .dropdown-menu a[href*='%s']" % targetItem)


class TableLocators:
    TABLE_DEFAULT = (By.CSS_SELECTOR, "table[id='grid']")
    TABLE_BODY = (By.CSS_SELECTOR, "tbody")
    TABLE_ROWS = (By.CSS_SELECTOR, "tr")
    TABLE_SAVE_BUTTON = (By.CSS_SELECTOR, 'button[id="save"]')
    TABLE_UNDO_BUTTON = (By.CSS_SELECTOR, 'button[id="undo"]')
    TABLE_SELECT_ACTION = (By.CSS_SELECTOR, 'button[id="actions1"]')
    TABLE_SELECT_ACTION_MENU = (By.CSS_SELECTOR, 'ul[id="actionsul"]')

    tablecolumns = {
        "supplier": (By.CSS_SELECTOR, 'td[aria-describedby="grid_supplier"]'),
        "quantity": (By.CSS_SELECTOR, 'td[aria-describedby="grid_quantity"]'),
        "startdate": (By.CSS_SELECTOR, 'td[aria-describedby="grid_startdate"]'),
        "enddate": (By.CSS_SELECTOR, 'td[aria-describedby="grid_enddate"]'),
        "status": (By.CSS_SELECTOR, 'td[aria-describedby="grid_status"]'),
        "destination": (By.CSS_SELECTOR, 'td[aria-describedby="grid_destination"]'),
        "operation": (By.CSS_SELECTOR, 'td[aria-describedby="grid_operation"]'),
    }

    tablecolumnsinput = {
        "supplier": (By.CSS_SELECTOR, 'input[name="supplier"]'),
        "quantity": (By.CSS_SELECTOR, 'input[id="1_quantity"]'),
        "startdate": (By.CSS_SELECTOR, 'input[id="1_startdate"]'),
        "enddate": (By.CSS_SELECTOR, 'input[id="1_enddate"]'),
        "destination": (By.CSS_SELECTOR, 'input[id="1_destination"]'),
        "operation": (By.CSS_SELECTOR, 'input[id="1_operation"]'),
        "checkbox": (By.CSS_SELECTOR, 'input[type="checkbox"]'),
    }

    @staticmethod
    def actionLocator(actionTofind):
        return (By.CSS_SELECTOR, "li>a[name='" + actionTofind + "']")
