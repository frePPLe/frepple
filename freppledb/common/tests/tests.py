#
# Copyright (C) 2007-2019 by frePPLe bv
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

from django.http.response import StreamingHttpResponse
from django.test import TestCase

from freppledb.common.models import User, Scenario


def checkResponse(testcase, response):
    if isinstance(response, StreamingHttpResponse):
        for rec in response.streaming_content:
            rec
    testcase.assertEqual(response.status_code, 200)


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


class AppsAndAboutTest(TestCase):
    def setUp(self):
        os.environ["FREPPLE_TEST"] = "YES"
        Scenario.syncWithSettings()
        self.client.login(username="admin", password="admin")
        super().setUp()

    def tearDown(self):
        del os.environ["FREPPLE_TEST"]
        super().tearDown()

    def test_app_and_about_screen(self):
        response = self.client.get("/apps/")
        self.assertEqual(response.status_code, 200)
        response = self.client.get("/about/")
        self.assertEqual(response.status_code, 200)
