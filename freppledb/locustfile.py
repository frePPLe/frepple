#
# Copyright (C) 2024 by frePPLe bv
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
from locust import FastHttpUser, task, between

from django.conf import settings

# Initialize django
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "freppledb.settings")
import django

django.setup()


class FreppleUser(FastHttpUser):
    host = "http://localhost:8000"
    wait_time = between(1, 5)
    default_headers = {
        "accept-encoding": "gzip, deflate, br, zstd",
        "accept-language": "en",
    }

    @task(10)
    def common(self):
        self.client.get("/inbox/")

    @task(10)
    def productionplannner(self):
        self.client.get("/data/input/demand/")
        self.client.get(
            "/data/input/demand/?format=json&rows=100&page=1",
        )

    @task(10)
    def materialplannner(self):
        self.client.get("/buffer/")
        self.client.get(
            "/buffer/?format=json&rows=100&page=1",
        )

    @task(1)
    def executionscreen(self):
        self.client.get("/execute/")
        self.client.get(
            "/execute/?format=json&rows=100&page=1",
        )

    if "freppledb.forecast" in settings.INSTALLED_APPS:

        @task(1)
        def demandplanner(self):
            self.client.get("/forecast/")
            self.client.get(
                "/forecast/?format=json&rows=100&page=1",
            )
            self.client.get("/forecast/editor/")
            self.client.get("/forecast/locationtree/?measure=forecasttotal")
            self.client.get("/forecast/customertree/?measure=forecasttotal")
            self.client.get("/forecast/itemtree/?measure=forecasttotal")
            self.client.get(
                "/forecast/detail/?measure=forecasttotal&item=&location=&customer="
            )
