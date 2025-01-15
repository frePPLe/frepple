#
# Copyright (C) 2007-2013 by frePPLe bv
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

import base64
import json
import os
from time import sleep
import unittest

from django.conf import settings
from django.core import management
from django.db import DEFAULT_DB_ALIAS, transaction
from django.db.models import Sum, Count, Q
from django.test import TransactionTestCase

from freppledb.execute.models import Task
import freppledb.output as output
import freppledb.input as input
import freppledb.common as common
from freppledb.common.auth import getWebserviceAuthorization
from freppledb.common.models import Parameter, User, Notification


class execute_with_commands(TransactionTestCase):
    fixtures = ["demo", "initial"]

    def setUp(self):
        # Make sure the test database is used
        os.environ["FREPPLE_TEST"] = "YES"
        param = Parameter.objects.all().get_or_create(pk="plan.webservice")[0]
        param.value = "false"
        param.save()
        if not User.objects.filter(username="admin").count():
            User.objects.create_superuser("admin", "your@company.com", "admin")
        super().setUp()

    def tearDown(self):
        Notification.wait()
        del os.environ["FREPPLE_TEST"]
        super().tearDown()

    def test_run_cmd(self):
        # Empty the database tables
        self.assertNotEqual(input.models.Calendar.objects.count(), 0)
        management.call_command("empty", all=True)
        self.assertEqual(input.models.Calendar.objects.count(), 0)
        self.assertEqual(input.models.Demand.objects.count(), 0)
        self.assertEqual(output.models.Problem.objects.count(), 0)
        self.assertEqual(input.models.OperationMaterial.objects.count(), 0)
        self.assertEqual(input.models.OperationPlanResource.objects.count(), 0)
        self.assertEqual(input.models.PurchaseOrder.objects.count(), 0)
        self.assertEqual(common.models.Parameter.objects.count(), 0)

        # Create a new model
        management.call_command("createmodel", cluster="1", verbosity="0")
        self.assertNotEqual(input.models.Calendar.objects.count(), 0)
        self.assertNotEqual(input.models.Demand.objects.count(), 0)

        # Run frePPLe on the test database.
        # Since the random model generator is not generating the same model
        # across different version and platforms, we can only do a rough
        # check on the output.
        management.call_command(
            "runplan", plantype=1, constraint="capa,mfg_lt,po_lt", env="supply"
        )
        self.assertGreater(output.models.Problem.objects.count(), 8)
        self.assertGreater(input.models.OperationPlanMaterial.objects.count(), 400)
        self.assertGreater(input.models.OperationPlanResource.objects.count(), 20)
        self.assertGreater(input.models.OperationPlan.objects.count(), 300)

        # Export to CSV files
        outfolder = os.path.join(
            settings.DATABASES[DEFAULT_DB_ALIAS]["FILEUPLOADFOLDER"], "export"
        )
        if not os.path.isdir(outfolder):
            os.makedirs(outfolder)
        else:
            for file in os.listdir(outfolder):
                if file.endswith(".csv.gz"):
                    os.remove(os.path.join(outfolder, file))
        management.call_command("exporttofolder", verbosity="0")
        self.assertEqual(
            Task.objects.filter(name="exporttofolder").first().status, "100%"
        )
        count = 0
        for file in os.listdir(outfolder):
            if file.endswith(".csv.gz"):
                f = os.stat(os.path.join(outfolder, file))
                if f.st_size > 10:
                    count += 1
        self.assertGreaterEqual(count, 8)


class execute_multidb(TransactionTestCase):
    fixtures = ["demo"]

    databases = settings.DATABASES.keys()

    def setUp(self):
        os.environ["FREPPLE_TEST"] = "YES"
        param = Parameter.objects.all().get_or_create(pk="plan.webservice")[0]
        param.value = "false"
        param.save()
        super().setUp()

    def tearDown(self):
        Notification.wait()
        del os.environ["FREPPLE_TEST"]
        super().tearDown()

    def test_multidb_cmd(self):
        # Find out which databases to use
        db1 = DEFAULT_DB_ALIAS
        db2 = None
        for i in settings.DATABASES:
            if i != DEFAULT_DB_ALIAS:
                db2 = i
                break
        if not db2:
            # Only a single database is configured and we skip this test
            return

        # Check count in both databases
        count1 = input.models.PurchaseOrder.objects.all().using(db1).count()
        input.models.PurchaseOrder.objects.all().using(db2).delete()
        count2 = input.models.PurchaseOrder.objects.all().using(db2).count()
        self.assertGreater(count1, 0)
        self.assertEqual(count2, 0)
        # Erase second database
        count1 = input.models.Demand.objects.all().using(db1).count()
        management.call_command("empty", database=db2, all=True)
        count1new = input.models.Demand.objects.all().using(db1).count()
        input.models.Demand.objects.all().using(db2).delete()
        count2 = input.models.Demand.objects.all().using(db2).count()
        self.assertEqual(count1new, count1)
        self.assertEqual(count2, 0)
        # Copy the db1 into db2.
        # We need to close the transactions, since they can block the copy
        transaction.commit(using=db1)
        transaction.commit(using=db2)
        management.call_command("scenario_copy", db1, db2)
        count1 = (
            input.models.OperationPlan.objects.all()
            .filter(type="PO")
            .using(db1)
            .count()
        )
        count2 = (
            input.models.OperationPlan.objects.all()
            .filter(type="PO")
            .using(db2)
            .count()
        )
        self.assertEqual(count1, count2)
        # Run the plan on db1.
        # The count changes in db1 and not in db2.
        count1 = input.models.OperationPlanMaterial.objects.all().using(db1).count()
        management.call_command(
            "runplan",
            plantype=1,
            constraint="capa,mfg_lt,po_lt",
            env="supply",
            database=db1,
        )
        count1 = input.models.OperationPlanMaterial.objects.all().using(db1).count()
        self.assertNotEqual(count1, 0)
        # Run a plan on db2.
        # The count changes in db1 and not in db2.
        # The count in both databases is expected to be different since we run a different plan
        count1new = input.models.OperationPlanMaterial.objects.all().using(db1).count()
        management.call_command(
            "runplan", plantype=1, constraint=0, env="supply", database=db2
        )
        count1new = input.models.OperationPlanMaterial.objects.all().using(db1).count()
        count2 = input.models.OperationPlanMaterial.objects.all().using(db2).count()
        self.assertEqual(count1new, count1)
        self.assertNotEqual(count2, 0)
        self.assertNotEqual(count2, count1new)

        # Populate db2 with a backup of db1
        management.call_command("backup", database=db1)
        dumpfile = Task.objects.filter(name="backup").first().logfile
        self.assertTrue(dumpfile)
        management.call_command("scenario_release", database=db2)
        management.call_command("scenario_copy", "--dumpfile=%s" % dumpfile, db1, db2)
        self.assertEqual(
            input.models.PurchaseOrder.objects.all().using(db1).count(),
            input.models.PurchaseOrder.objects.all().using(db2).count(),
        )


class FixtureTest(TransactionTestCase):
    def test_fixture_demo(self):
        self.assertEqual(input.models.Item.objects.count(), 0)
        management.call_command("loaddata", "demo.json", verbosity=0)
        self.assertGreater(input.models.Item.objects.count(), 0)

    def test_fixture_jobshop(self):
        self.assertEqual(input.models.Item.objects.count(), 0)
        management.call_command("loaddata", "jobshop.json", verbosity=0)
        self.assertGreater(input.models.Item.objects.count(), 0)

    def test_fixture_unicode_test(self):
        self.assertEqual(input.models.Item.objects.count(), 0)
        management.call_command("loaddata", "unicode_test.json", verbosity=0)
        self.assertGreater(input.models.Item.objects.count(), 0)

    def test_fixture_parameter_test(self):
        self.assertEqual(common.models.Parameter.objects.count(), 0)
        management.call_command("loaddata", "parameters.json", verbosity=0)
        self.assertGreater(common.models.Parameter.objects.count(), 0)

    def test_fixture_flow_line_test(self):
        self.assertEqual(input.models.Item.objects.count(), 0)
        management.call_command("loaddata", "flow_line.json", verbosity=0)
        self.assertGreater(input.models.Item.objects.count(), 0)


class execute_simulation(TransactionTestCase):
    fixtures = ["demo"]

    def setUp(self):
        # Make sure the test database is used
        os.environ["FREPPLE_TEST"] = "YES"
        param = Parameter.objects.all().get_or_create(pk="plan.webservice")[0]
        param.value = "true"
        param.save()

    def tearDown(self):
        Notification.wait()
        del os.environ["FREPPLE_TEST"]

    @unittest.skip("Needs validation")
    def test_run_cmd(self):
        # Run the plan and measure the lateness
        management.call_command(
            "runplan", plantype=1, constraint="capa,mfg_lt,po_lt", env="supply"
        )
        initial_planned_late = (
            output.models.Problem.objects.all()
            .filter(name="late")
            .aggregate(count=Count("id"), lateness=Sum("weight"))
        )

        # Run the simulation.
        # The default implementation assumes the actual execution is exactly
        # matching the specified leadtime.
        management.call_command("simulation", step=7, horizon=120, verbosity=0)

        # Verify that the simulated execution is matching the original plan
        self.assertEqual(
            input.models.Demand.objects.all().filter(~Q(status="closed")).count(),
            0,
            "Some demands weren't shipped",
        )
        # TODO add comparison with initial_planned_late


class remote_commands(TransactionTestCase):
    fixtures = ["demo"]

    databases = settings.DATABASES.keys()

    def setUp(self):
        # Make sure the test database is used
        os.environ["FREPPLE_TEST"] = "YES"
        param = Parameter.objects.all().get_or_create(pk="plan.webservice")[0]
        param.value = "false"
        param.save()
        if not User.objects.filter(username="admin").count():
            User.objects.create_superuser("admin", "your@company.com", "admin")
        super().setUp()

    def tearDown(self):
        Notification.wait()
        del os.environ["FREPPLE_TEST"]
        super().tearDown()

    def test_remote_command_basic_authentication(self):
        self.remote_commands_base(
            {
                "HTTP_AUTHORIZATION": "Basic %s"
                % base64.b64encode("admin:admin".encode()).decode()
            }
        )

    def test_remote_command_jwt_authentication(self):
        self.remote_commands_base(
            {
                "HTTP_AUTHORIZATION": "Bearer %s"
                % getWebserviceAuthorization(user="admin", exp=3600),
            }
        )

    def remote_commands_base(self, headers):
        # Run a plan
        response = self.client.post(
            "/execute/api/runplan/", {"constraint": 1, "plantype": 1}, **headers
        )

        self.assertEqual(response.status_code, 200)
        taskinfo = json.loads(response.content.decode())
        taskid0 = taskinfo["taskid"]
        self.assertGreater(taskid0, 0)

        # Wait 10 seconds for the plan the finish
        cnt = 0
        while cnt <= 10:
            response = self.client.get(
                "/execute/api/status/?id=%s" % taskid0, **headers
            )
            self.assertEqual(response.status_code, 200)
            taskinfo = json.loads(response.content.decode())
            if taskinfo[str(taskid0)]["status"] == "Done":
                break
            sleep(1)
            cnt += 1
        self.assertLess(cnt, 10, "Running task taking too long")

        # Copy the plan
        db2 = None
        for i in settings.DATABASES:
            if i != DEFAULT_DB_ALIAS:
                db2 = i
                break
        if db2:
            response = self.client.post(
                "/execute/api/scenario_copy/",
                {"copy": 1, "source": DEFAULT_DB_ALIAS, "destination": db2},
                **headers,
            )
            self.assertEqual(response.status_code, 200)
            taskinfo = json.loads(response.content.decode())
            taskid2 = taskinfo["taskid"]
            self.assertEqual(taskid2, taskid0 + 1)

            # Wait for the copy the finish
            cnt = 0
            while cnt <= 20:
                response = self.client.get(
                    "/execute/api/status/?id=%s" % taskid2, **headers
                )
                self.assertEqual(response.status_code, 200)
                taskinfo = json.loads(response.content.decode())
                if taskinfo[str(taskid2)]["status"] == "Done":
                    break
                sleep(1)
                cnt += 1
            self.assertLess(cnt, 20, "Running task taking too long")

            # Generate a plan in the scenario
            response = self.client.post(
                "/%s/execute/api/runplan/" % db2,
                {"constraint": 1, "plantype": 1},
                **headers,
            )
            self.assertEqual(response.status_code, 200)
            taskinfo = json.loads(response.content.decode())
            taskid3 = taskinfo["taskid"]
            self.assertGreater(taskid3, 0)

            # Wait 10 seconds for the plan the finish
            cnt = 0
            while cnt <= 10:
                response = self.client.get(
                    "/%s/execute/api/status/?id=%s" % (db2, taskid3), **headers
                )
                self.assertEqual(response.status_code, 200)
                taskinfo = json.loads(response.content.decode())
                if taskinfo[str(taskid3)]["status"] == "Done":
                    break
                sleep(1)
                cnt += 1
            self.assertLess(cnt, 10, "Running task taking too long")

        # Empty the plan
        response = self.client.post("/execute/api/empty/", {"all": 1}, **headers)
        self.assertEqual(response.status_code, 200)
        taskinfo = json.loads(response.content.decode())
        taskid1 = taskinfo["taskid"]

        # Wait for the task to finish
        cnt = 0
        while cnt <= 20:
            response = self.client.get(
                "/execute/api/status/?id=%s" % taskid1, **headers
            )
            self.assertEqual(response.status_code, 200)
            taskinfo = json.loads(response.content.decode())
            if taskinfo[str(taskid1)]["status"] == "Done":
                break
            sleep(1)
            cnt += 1
        self.assertLess(cnt, 20, "Running task taking too long")
        sleep(4)  # Wait for the worker to die
