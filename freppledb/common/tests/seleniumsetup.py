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
import os
import time

from django.conf import settings
from django.contrib.staticfiles.testing import StaticLiveServerTestCase

from freppledb.common.models import User

try:
    from selenium import webdriver

    noSelenium = False
except ImportError:
    noSelenium = True


class SeleniumTest(StaticLiveServerTestCase):
    def setUp(self):
        # Login
        if not User.objects.filter(username="admin").count():
            User.objects.create_superuser("admin", "your@company.com", "admin")
        super().setUp()

    @classmethod
    def setUpClass(cls):
        for db in settings.DATABASES:
            # Avoid leaking persistent connections
            settings.DATABASES[db]["CONN_MAX_AGE"] = 0
        os.environ["FREPPLE_TEST"] = "YES"
        super().setUpClass()
        if settings.SELENIUM_TESTS == "firefox":
            firefox_options = webdriver.FirefoxOptions()
            if settings.SELENIUM_HEADLESS:
                firefox_options.add_argument("--headless")
            cls.driver = webdriver.Firefox(firefox_options=firefox_options)
        elif settings.SELENIUM_TESTS == "chrome":
            options = webdriver.ChromeOptions()
            options.add_argument("--silent")
            if settings.SELENIUM_HEADLESS:
                options.add_argument("--headless")
            cls.driver = webdriver.Chrome(chrome_options=options)
        elif settings.SELENIUM_TESTS == "edge":
            from msedge.selenium_tools import Edge, EdgeOptions

            options = EdgeOptions()
            options.use_chromium = True
            options.add_argument("--silent")
            if settings.SELENIUM_HEADLESS:
                options.add_argument("--headless")
            cls.driver = Edge(options=options)
        else:
            raise Exception("Invalid setting SELENIUM_TESTS")
        cls.driver.set_window_size(1080, 800)
        cls.driver.implicitly_wait(10)

    @classmethod
    def tearDownClass(cls):
        cls.driver.quit()
        time.sleep(2)
        del os.environ["FREPPLE_TEST"]
        super().tearDownClass()
