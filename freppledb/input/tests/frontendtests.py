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
