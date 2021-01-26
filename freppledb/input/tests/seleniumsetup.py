import time

from django.conf import settings
from django.contrib.staticfiles.testing import StaticLiveServerTestCase

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
    
    def implicitlyWait(cls, wait):
        cls.driver.implicitly_wait(wait)
