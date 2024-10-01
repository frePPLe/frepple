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
import time

try:
    os.environ["LOCUST_SKIP_MONKEY_PATCH"] = "1"
    import gevent
    from locust import FastHttpUser, task, between
    from locust.env import Environment
    from locust.log import setup_logging
    import locust.stats

    locust_installed = True
except ImportError:
    # Skip of locust isn't installed
    locust_installed = False

from django.conf import settings
from django.core.management.base import BaseCommand
from django.db import DEFAULT_DB_ALIAS

from freppledb import __version__


if locust_installed:

    class Command(BaseCommand):
        help = """
        This command generates a stress test load on the frepple webserver.

        You need to have the locust python library installed
        """

        requires_system_checks = []

        def get_version(self):
            return __version__

        def add_arguments(self, parser):
            parser.add_argument(
                "--users", help="Number of users", type=int, default=10
            ),
            parser.add_argument(
                "--server",
                help="URL of the server to test.",
                default="http://localhost:8000",
            )

        def handle(self, **options):
            locust.stats.CONSOLE_STATS_INTERVAL_SEC = 30

            user_classes = [MaterialPlanner, ProductionPlanner]
            if "freppledb.forecast" in settings.INSTALLED_APPS:
                user_classes.append(DemandPlanner)
            setup_logging("INFO")
            env = Environment(user_classes=user_classes)
            runner = env.create_local_runner()
            web_ui = env.create_web_ui("127.0.0.1", 8089)

            print("")
            print("Open your browser on http://127.0.0.1:8089/ to control your test.")
            print("")

            env.events.init.fire(environment=env, runner=runner, web_ui=web_ui)
            env.runner.start(options["users"], spawn_rate=100)
            gevent.spawn(locust.stats.stats_history, env.runner)
            gevent.spawn_later(30, locust.stats.stats_printer(env.stats))
            env.runner.greenlet.join()

        @staticmethod
        def getHTML(request):
            return None

    class freppleUser(FastHttpUser):
        host = "http://localhost:8000"
        wait_time = between(1, 5)
        default_headers = {
            "accept-encoding": "gzip, deflate, br, zstd",
            "accept-language": "en",
        }

    class MaterialPlanner(freppleUser):
        @task(10)
        def common(self):
            self.client.get("/inbox/")

        @task(10)
        def materialplannner(self):
            self.client.get("/buffer/")
            self.client.get(
                "/buffer/?format=json&rows=100&page=1", name="/buffer/?format=json"
            )

    class ProductionPlanner(freppleUser):
        @task(10)
        def SalesOrderList(self):
            self.client.get("/data/input/demand/")
            self.client.get(
                "/data/input/demand/?format=json&rows=100&page=1",
                name="/data/input/demand/?format=json",
            )

        @task(10)
        def ResourceReport(self):
            self.client.get("/resource/")
            self.client.get(
                "/resource/?format=json&rows=100&page=1", name="/resource/?format=json"
            )

        @task(1)
        def ExecutionScreen(self):
            self.client.get("/execute/")
            self.client.get(
                "/execute/?format=json&rows=100&page=1", name="/execute/?format=json"
            )

    class DemandPlanner(freppleUser):
        @task(1)
        def Forecastditor(self):
            self.client.get("/forecast/")
            self.client.get(
                "/forecast/?format=json&rows=100&page=1", name="/forecast/?format=json"
            )
            self.client.get("/forecast/editor/")
            self.client.get("/forecast/locationtree/?measure=forecasttotal")
            self.client.get("/forecast/customertree/?measure=forecasttotal")
            self.client.get("/forecast/itemtree/?measure=forecasttotal")
            self.client.get(
                "/forecast/detail/?measure=forecasttotal&item=&location=&customer=",
                name="/forecast/detail/",
            )
