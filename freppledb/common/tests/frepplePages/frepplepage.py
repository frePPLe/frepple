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

from freppledb.common.tests.frepplePages.freppleelement import (
    BasePageElement,
)
from freppledb.common.tests.frepplePages.frepplelocators import (
    TableLocators,
    BasePageLocators,
)

import time

from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.common.action_chains import ActionChains

from django.conf import settings
from django.utils.formats import date_format

### Special page for common actions only


class SupplierEditInputElement(BasePageElement):
    locator = "input[id=id_name]"


class BasePage:
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

    def __init__(self, driver, testclass):
        self.driver = driver
        self.testclass = testclass

    def login(self, user="admin", password="admin"):
        self.open("/")
        if (
            "freppledb.common.middleware.AutoLoginAsAdminUser"
            not in settings.MIDDLEWARE
        ):
            self.driver.find_element(By.NAME, "username").send_keys(user)
            self.driver.find_element(By.NAME, "password").send_keys(password)
            self.driver.find_element(By.CSS_SELECTOR, "[type='submit']").click()

    def wait(self, timing):
        return WebDriverWait(self.driver, timing)

    def go_to_target_page_by_menu(self, menu_item, submenu_item):
        (menuby, menulocator) = BasePageLocators.mainMenuLinkLocator(menu_item)
        self.menuitem = self.driver.find_element(menuby, menulocator)
        ActionChains(self.driver).move_to_element(self.menuitem).perform()

        (submenuby, submenulocator) = BasePageLocators.subMenuItemLocator(submenu_item)
        self.submenuitem = self.driver.find_element(submenuby, submenulocator)
        time.sleep(1)
        ActionChains(self.driver).move_to_element(self.submenuitem).click().perform()
        time.sleep(1)

    def open(self, url):
        return self.driver.get("%s%s" % (self.testclass.live_server_url, url))


# create a table page class
# for all interactions with table
# ability to choose a specific table to interact with
# selecting a cell, updating a cell, reading value of a cell
class TablePage(BasePage):
    # purchase order page action method come here

    # declaring variable that will contain the retrieved table
    table = None

    def get_table(self):
        if not self.table:
            self.table = self.driver.find_element(*TableLocators.TABLE_DEFAULT)
        return self.table

    def get_table_row(self, rowNumber):
        return self.get_table().find_elements(*TableLocators.TABLE_ROWS)[rowNumber]

    def get_table_multiple_rows(self, rowNumber):
        return self.get_table().find_elements(*TableLocators.TABLE_ROWS)[
            1 : rowNumber + 1
        ]

    def get_item_reference_in_target_row(self, targetrow):
        return targetrow.get_attribute("id")

    def get_content_of_row_column(self, rowElement, columnName):
        return rowElement.find_element(*TableLocators.tablecolumns[columnName])

    def click_target_row_colum(
        self, rowElement, columnNameLocator
    ):  # method that clicks of the table cell at the targeted row and column
        targetTableCell = self.get_content_of_row_column(rowElement, columnNameLocator)
        ActionChains(self.driver).move_to_element_with_offset(
            targetTableCell, 1, 1
        ).click().perform()
        inputfield = targetTableCell.find_element(
            *TableLocators.tablecolumnsinput[columnNameLocator]
        )
        return inputfield

    def click_target_cell(
        self, targetcellElement, columnNameLocator
    ):  # method that clicks of the table cell at the targeted row and column
        ActionChains(self.driver).move_to_element_with_offset(
            targetcellElement, 10, 10
        ).click().perform()
        return targetcellElement.find_element(
            *TableLocators.tablecolumnsinput[columnNameLocator]
        )

    def enter_text_in_inputfield(self, targetinputfield, text):
        targetinputfield.clear()
        time.sleep(0.3)
        targetinputfield.send_keys(text)
        time.sleep(0.3)
        targetinputfield.send_keys(Keys.RETURN)
        time.sleep(0.3)

    def enter_text_in_inputdatefield(
        self, targetinputdatefield, newdate, withTime=True
    ):
        if withTime:
            val = date_format(newdate, "DATETIME_FORMAT", use_l10n=False)
        else:
            val = newdate.strftime("%m-%d-%Y")
        targetinputdatefield.clear()
        time.sleep(0.3)
        targetinputdatefield.send_keys(val)
        time.sleep(0.3)
        targetinputdatefield.send_keys(Keys.RETURN)
        time.sleep(0.3)
        return val

    def click_save_button(self):
        save_button = self.driver.find_element(*TableLocators.TABLE_SAVE_BUTTON)
        ActionChains(self.driver).move_to_element(save_button).click().perform()

    def click_undo_button(self):
        undo_button = self.driver.find_element(*TableLocators.TABLE_UNDO_BUTTON)
        ActionChains(self.driver).move_to_element(undo_button).click().perform()

    def select_action(self, actionToPerform):
        # method that will select an action from the select action dropdown
        select = self.driver.find_element(*TableLocators.TABLE_SELECT_ACTION)
        ActionChains(self.driver).move_to_element(select).click().perform()
        time.sleep(1)
        select_menu = self.driver.find_element(*TableLocators.TABLE_SELECT_ACTION_MENU)
        select_action = select_menu.find_element(
            *TableLocators.actionLocator(actionToPerform)
        )
        ActionChains(self.driver).move_to_element(select_action).perform()
        select_action.click()

    def multiline_checkboxes_check(self, targetrows):
        # method that will check a certain number of checkboxes in the checkbox column
        for row in targetrows:
            checkbox = row.find_element(*TableLocators.tablecolumnsinput["checkbox"])
            ActionChains(self.driver).key_down(Keys.CONTROL).move_to_element(
                checkbox
            ).click().perform()
            time.sleep(0.3)
