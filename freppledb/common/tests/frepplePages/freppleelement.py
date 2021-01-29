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
from selenium.webdriver.support.ui import WebDriverWait

class BasePageElement(object):
    # Base page that is initialized on every page object class.
    
    def __set__(self, obj, value):
        #Sets the text to the value supplied
        
        driver = self.driver
        WebDriverWait(driver, 100).until(
            lambda driver : driver.find_element_by_css_selector(self.locator)
        )
        
        driver.find_element_by_css_selector(self.locator).clear()
        driver.find_element_by_css_selector(self.locator).send_keys(value)
    
    def __get__(self, obj, owner):
        #Gets the text of the specified object
        
        driver = obj.driver
        WebDriverWait(driver, 100).until(
            lambda driver : driver.find_element_by_css_selector(self.locator)
        )