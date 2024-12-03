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
import os
import time
from selenium import webdriver

from django.conf import settings
from django.contrib.staticfiles.testing import StaticLiveServerTestCase

from freppledb.common.models import User

noSelenium = settings.SELENIUM_TESTS is None


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
            cls.driver = webdriver.Firefox(options=firefox_options)
        elif settings.SELENIUM_TESTS == "chrome":
            import chromedriver_autoinstaller

            chromedriver_autoinstaller.install()
            options = webdriver.ChromeOptions()
            options.add_argument("--silent")
            if settings.SELENIUM_HEADLESS:
                options.add_argument("--headless")
            cls.driver = webdriver.Chrome(options=options)
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
        cls.driver.set_window_size(1920, 1480)
        cls.driver.implicitly_wait(10)

    @classmethod
    def tearDownClass(cls):
        browser_log = cls.driver.get_log("browser")
        if browser_log:
            print("Browser console:")
            for l in browser_log:
                print(l["message"])
        cls.driver.quit()
        time.sleep(2)
        del os.environ["FREPPLE_TEST"]
        super().tearDownClass()

    @classmethod
    def saveScreenshot(cls, name="screenshot.png"):
        cls.driver.save_screenshot(name)
