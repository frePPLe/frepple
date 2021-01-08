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

import time

from django.conf import settings
from django.contrib.staticfiles.testing import StaticLiveServerTestCase
from django.db import DEFAULT_DB_ALIAS
from django.http.response import StreamingHttpResponse
from django.test import TestCase

from freppledb.common.models import User

try:
    from selenium import webdriver
    from selenium.common.exceptions import NoSuchElementException
    from selenium.webdriver.common.action_chains import ActionChains
    from selenium.webdriver.common.by import By
    from selenium.webdriver.support.ui import WebDriverWait
    from selenium.webdriver.support import expected_conditions

    noSelenium = False
except ImportError:
    noSelenium = True


def checkResponse(testcase, response):
    if isinstance(response, StreamingHttpResponse):
        for rec in response.streaming_content:
            rec
    testcase.assertEqual(response.status_code, 200)


class SeleniumTest(StaticLiveServerTestCase):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        if settings.SELENIUM_TESTS == "firefox":
            firefox_options = webdriver.FirefoxOptions()
            # firefox_options.add_argument("--headless")
            cls.driver = webdriver.Firefox(firefox_options=firefox_options)
        elif settings.SELENIUM_TESTS == "chrome":
            options = webdriver.ChromeOptions()
            options.add_argument("--silent")
            # options.add_argument("--headless")
            cls.driver = webdriver.Chrome(chrome_options=options)
        else:
            raise Exception("Invalid setting SELENIUM_TESTS")
        cls.driver.set_window_size(1080, 800)
        cls.driver.implicitly_wait(10)

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        cls.driver.quit()
        time.sleep(2)

    def open(self, url):
        return self.driver.get("%s%s" % (self.live_server_url, url))

    def login(self, user, password):
        if (
            "freppledb.common.middleware.AutoLoginAsAdminUser"
            not in settings.MIDDLEWARE
        ):
            self.findElement(By.NAME, "username").send_keys(user)
            self.findElement(By.NAME, "password").send_keys(password)
            self.findElement(By.CSS_SELECTOR, "[type='submit']").click()

    def findElement(self, by, locator):
        try:
            return self.driver.find_element(by, locator)
        except NoSuchElementException:
            self.fail("Element %s not found by %s" % (locator, by))

    def ActionChains(self):
        return ActionChains(self.driver)


class DataLoadTest(TestCase):
    def setUp(self):
        # Login
        self.client.login(username="admin", password="admin")

    def test_common_parameter(self):
        response = self.client.get("/data/common/parameter/?format=json")
        if not isinstance(response, StreamingHttpResponse):
            raise Exception("expected a streaming response")
        for i in response.streaming_content:
            if b'"records":' in i:
                return
        self.fail("Didn't find expected number of parameters")


class UserPreferenceTest(TestCase):
    def test_get_set_preferences(self):
        user = User.objects.all().get(username="admin")
        before = user.getPreference("test")
        self.assertIsNone(before)
        user.setPreference("test", {"a": 1, "b": "c"})
        after = user.getPreference("test")
        self.assertEqual(after, {"a": 1, "b": "c"})
