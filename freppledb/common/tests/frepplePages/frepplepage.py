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
from freppledb.common.tests.frepplePages.freppleelement import (
    BasePageElement,
)  # in here, import the class containing all the elements from your target page
from freppledb.common.tests.frepplePages.frepplelocators import (
    TableLocators,
    BasePageLocators,
)  # here, we should find all the locators for your target page

import selenium
import time
from django.db.models.functions.window import RowNumber

try:
    from selenium.common.exceptions import NoSuchElementException
    from selenium.webdriver.common.action_chains import ActionChains
    from selenium.webdriver.common.by import By
    from selenium.webdriver.common.keys import Keys
    from selenium.webdriver.support import expected_conditions as EC

    noSelenium = False
except ImportError:
    noSelenium = True


### Special page for common actions only


class SupplierEditInputElement(BasePageElement):
    locator = "input[id=id_name]"


"""class PurchaseOrderTableSelectActionMenuElement(BasePageElement):
    select_action_statuses = ("proposed","approved","confirmed","completed","closed")"""


class BasePage(object):
    NAV_MENU_LEFT = (
        "Sales",
        "Inventory",
        "Capacity",
        "Purchasing",
        "Manufacturing",
        "Admin",
        "My Reports",
        "Help",
    )

    def __init__(self, driver, selenium):
        self.driver = driver
        self.selenium = selenium

    def login(self, selenium):
        selenium.open("/")
        selenium.login("admin", "admin")

        selenium.implicitlyWait(20)

    def ActionChains(self):
        return self.selenium.ActionChains(self)

    def wait(self, timing):
        return self.selenium.wait(self, timing)

    def go_to_target_page_by_menu(self, menu_item, submenu_item):
        (menuby, menulocator) = BasePageLocators.mainMenuLinkLocator(menu_item)
        self.menuitem = self.selenium.findElement(self, menuby, menulocator)
        self.selenium.ActionChains(self).move_to_element(self.menuitem).perform()

        (submenuby, submenulocator) = BasePageLocators.subMenuItemLocator(submenu_item)
        self.submenuitem = self.selenium.findElement(self, submenuby, submenulocator)
        self.selenium.ActionChains(self).move_to_element(
            self.submenuitem
        ).click().perform()

    def go_home_with_breadcrumbs(self):
        pass

    def go_back_to_page_with_breadcrumbs(self, targetPageName):
        pass

    # most common actions go here like opening a menu, clicking a save button, clicking undo


# create a table page class
# for all interactions with table
# ability to choose a specific table to interact with
# selecting a cell, updating a cell, reading value of a cell
class TablePage(BasePage):
    # purchase order page action method come here

    # declaring variable that will contain the retrieved table
    table = None

    def get_table(self):
        self.table = self.driver.find_element(*TableLocators.TABLE_DEFAULT)
        return self.table

    def get_table_row(self, rowNumber):
        table = self.get_table()
        rows = table.find_elements(*TableLocators.TABLE_ROWS)
        return rows[rowNumber]

    def get_table_multiple_rows(self, rowNumber):
        table = self.get_table()
        rows = table.find_elements(*TableLocators.TABLE_ROWS)
        return rows[1 : rowNumber + 1]

    def get_item_reference_in_target_row(self, targetrow):
        reference = targetrow.get_attribute("id")
        return reference

    def get_content_of_row_column(self, rowElement, columnName):
        content = rowElement.find_element(*TableLocators.tablecolumns[columnName])
        return content

    def click_target_row_colum(
        self, rowElement, columnNameLocator
    ):  # method that clicks of the table cell at the targeted row and column
        targetTableCell = self.get_content_of_row_column(rowElement, columnNameLocator)
        self.ActionChains().move_to_element_with_offset(
            targetTableCell, 1, 0
        ).click().perform()
        inputfield = targetTableCell.find_element(
            *TableLocators.tablecolumnsinput[columnNameLocator]
        )
        return inputfield

    def click_target_cell(
        self, targetcellElement, columnNameLocator
    ):  # method that clicks of the table cell at the targeted row and column
        self.ActionChains().move_to_element_with_offset(
            targetcellElement, 1, 0
        ).click().perform()
        inputfield = targetcellElement.find_element(
            *TableLocators.tablecolumnsinput[columnNameLocator]
        )
        return inputfield

    def enter_text_in_inputfield(self, targetinputfield, text):
        targetinputfield.clear()
        time.sleep(0.3)
        targetinputfield.send_keys(text)
        time.sleep(0.3)
        targetinputfield.send_keys(Keys.RETURN)
        time.sleep(0.3)

    def enter_text_in_inputdatefield(self, targetinputdatefield, newdate):
        targetinputdatefield.clear()
        time.sleep(0.3)
        targetinputdatefield.send_keys(newdate.strftime("%Y-%m-%d 00:00:00"))
        time.sleep(0.3)
        targetinputdatefield.send_keys(Keys.RETURN)
        time.sleep(0.3)
        return newdate.strftime("%Y-%m-%d 00:00:00")

    # def is_title_matches(self): # change to current url
    #    return "Purchase orders" in self.driver.title

    def click_save_button(self):
        save_button = self.driver.find_element(*TableLocators.TABLE_SAVE_BUTTON)
        self.ActionChains().move_to_element(save_button).click().perform()

    def click_undo_button(self):
        undo_button = self.driver.find_element(*TableLocators.TABLE_UNDO_BUTTON)
        self.ActionChains().move_to_element(undo_button).click().perform()

    def select_action(
        self, actionToPerform
    ):  # method that will select an action from the select action dropdown
        select = self.driver.find_element(*TableLocators.TABLE_SELECT_ACTION)
        self.ActionChains().move_to_element(select).click().perform()
        select_menu = self.driver.find_element(*TableLocators.TABLE_SELECT_ACTION_MENU)
        select_action = select_menu.find_element(
            *TableLocators.actionLocator(actionToPerform)
        )
        select_action.click()

    def multiline_checkboxes_check(
        self, targetrows
    ):  # method that will check a certain number of checkboxes in the checkbox column

        for row in targetrows:
            checkbox = row.find_element(*TableLocators.tablecolumnsinput["checkbox"])
            self.ActionChains().move_to_element(checkbox).click().perform()
