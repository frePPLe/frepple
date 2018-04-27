#
# Copyright (C) 2007-2013 by frePPLe bvba
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

import base64
import json
import os
from time import sleep

from django.conf import settings
from django.core import management
from django.db import DEFAULT_DB_ALIAS, transaction
from django.db.models import Sum, Count, Q
from django.test import TransactionTestCase

import freppledb.output as output
import freppledb.input as input
import freppledb.common as common
from freppledb.common.models import Parameter, User


class execute_with_commands(TransactionTestCase):
  fixtures = ["demo"]

  def setUp(self):
    # Make sure the test database is used
    os.environ['FREPPLE_TEST'] = "YES"
    param = Parameter.objects.all().get_or_create(pk='plan.webservice')[0]
    param.value = 'false'
    param.save()

  def tearDown(self):
    del os.environ['FREPPLE_TEST']

  def test_run_cmd(self):
    # Empty the database tables
    self.assertNotEqual(input.models.Calendar.objects.count(), 0)
    management.call_command('empty')
    self.assertEqual(input.models.Calendar.objects.count(), 0)
    self.assertEqual(input.models.Demand.objects.count(), 0)
    self.assertEqual(output.models.Problem.objects.count(), 0)
    self.assertEqual(input.models.OperationMaterial.objects.count(), 0)
    self.assertEqual(input.models.OperationPlanResource.objects.count(), 0)
    self.assertEqual(input.models.PurchaseOrder.objects.count(), 0)
    self.assertEqual(common.models.Parameter.objects.count(), 0)

    # Create a new model
    management.call_command('createmodel', cluster='1', verbosity='0')
    self.assertNotEqual(input.models.Calendar.objects.count(), 0)
    self.assertNotEqual(input.models.Demand.objects.count(), 0)

    # Run frePPLe on the test database.
    # Since the random model generator is not generating the same model
    # across different version and platforms, we can only do a rough
    # check on the output.
    management.call_command('runplan', plantype=1, constraint=15, env='supply')
    self.assertTrue(output.models.Problem.objects.count() > 100)
    self.assertTrue(input.models.OperationPlanMaterial.objects.count() > 400)
    self.assertTrue(input.models.OperationPlanResource.objects.count() > 20)
    self.assertTrue(input.models.OperationPlan.objects.count() > 300)


class execute_multidb(TransactionTestCase):

  fixtures = ['demo']

  def setUp(self):
    os.environ['FREPPLE_TEST'] = "YES"
    param = Parameter.objects.all().get_or_create(pk='plan.webservice')[0]
    param.value = 'false'
    param.save()

  def tearDown(self):
    del os.environ['FREPPLE_TEST']

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
    count1 = input.models.OperationPlanMaterial.objects.all().using(db1).count()
    input.models.OperationPlanMaterial.objects.all().using(db2).delete()
    count2 = input.models.OperationPlanMaterial.objects.all().using(db2).count()
    self.assertGreater(count1, 140)
    self.assertEqual(count2, 0)
    # Erase second database
    count1 = input.models.Demand.objects.all().using(db1).count()
    management.call_command('empty', database=db2)
    count1new = input.models.Demand.objects.all().using(db1).count()
    input.models.Demand.objects.all().using(db2).delete()
    count2 = input.models.Demand.objects.all().using(db2).count()
    self.assertEqual(count1new, count1)
    self.assertEqual(count2, 0)
    # Copy the db1 into db2.
    # We need to close the transactions, since they can block the copy
    transaction.commit(using=db1)
    transaction.commit(using=db2)
    management.call_command('scenario_copy', db1, db2)
    count1 = input.models.OperationPlan.objects.all().filter(type='PO').using(db1).count()
    count2 = input.models.OperationPlan.objects.all().filter(type='PO').using(db2).count()
    self.assertEqual(count1, count2)
    # Run the plan on db1.
    # The count changes in db1 and not in db2.
    count1 = input.models.OperationPlanMaterial.objects.all().using(db1).count()
    management.call_command('runplan', plantype=1, constraint=15, env='supply', database=db1)
    count1 = input.models.OperationPlanMaterial.objects.all().using(db1).count()
    self.assertNotEqual(count1, 0)
    # Run a plan on db2.
    # The count changes in db1 and not in db2.
    # The count in both databases is expected to be different since we run a different plan
    count1new = input.models.OperationPlanMaterial.objects.all().using(db1).count()
    management.call_command('runplan', plantype=1, constraint=0, env='supply', database=db2)
    count1new = input.models.OperationPlanMaterial.objects.all().using(db1).count()
    count2 = input.models.OperationPlanMaterial.objects.all().using(db2).count()
    self.assertEqual(count1new, count1)
    self.assertNotEqual(count2, 0)
    self.assertNotEqual(count2, count1new)


class FixtureTest(TransactionTestCase):

  def test_fixture_demo(self):
    self.assertEqual(common.models.Bucket.objects.count(), 0)
    management.call_command('loaddata', "demo.json", verbosity=0)
    self.assertGreater(common.models.Bucket.objects.count(), 0)

  def test_fixture_jobshop(self):
    self.assertEqual(common.models.Bucket.objects.count(), 0)
    management.call_command('loaddata', "jobshop.json", verbosity=0)
    self.assertGreater(common.models.Bucket.objects.count(), 0)

  def test_fixture_unicode_test(self):
    self.assertEqual(common.models.Bucket.objects.count(), 0)
    management.call_command('loaddata', "unicode_test.json", verbosity=0)
    self.assertGreater(common.models.Bucket.objects.count(), 0)

  def test_fixture_parameter_test(self):
    self.assertEqual(common.models.Parameter.objects.count(), 0)
    management.call_command('loaddata', "parameters.json", verbosity=0)
    self.assertGreater(common.models.Parameter.objects.count(), 0)

  def test_fixture_dates_test(self):
    self.assertEqual(common.models.Bucket.objects.count(), 0)
    management.call_command('loaddata', "dates.json", verbosity=0)
    self.assertGreater(common.models.Bucket.objects.count(), 0)

  def test_fixture_flow_line_test(self):
    self.assertEqual(common.models.Bucket.objects.count(), 0)
    management.call_command('loaddata', "flow_line.json", verbosity=0)
    self.assertGreater(common.models.Bucket.objects.count(), 0)


class execute_simulation(TransactionTestCase):

  fixtures = ["demo"]

  def setUp(self):
    # Make sure the test database is used
    os.environ['FREPPLE_TEST'] = "YES"
    param = Parameter.objects.all().get_or_create(pk='plan.webservice')[0]
    param.value = 'true'
    param.save()

  def tearDown(self):
    del os.environ['FREPPLE_TEST']

  def test_run_cmd(self):
    # Run the plan and measure the lateness
    management.call_command('runplan', plantype=1, constraint=15, env='supply')
    initial_planned_late = output.models.Problem.objects.all().filter(name="late").aggregate(
      count=Count('id'),
      lateness=Sum('weight')
      )

    # Run the simulation.
    # The default implementation assumes the actual execution is exactly
    # matching the specified leadtime.
    management.call_command('simulation', step=7, horizon=120, verbosity=0)

    # Verify that the simulated execution is matching the original plan
    self.assertEqual(
      input.models.Demand.objects.all().filter(~Q(status='closed')).count(), 0,
      "Some demands weren't shipped"
      )
    # TODO add comparison with initial_planned_late


class remote_commands(TransactionTestCase):

  fixtures = ["demo"]

  def setUp(self):
    # Make sure the test database is used
    os.environ['FREPPLE_TEST'] = "YES"
    param = Parameter.objects.all().get_or_create(pk='plan.webservice')[0]
    param.value = 'false'
    param.save()
    if not User.objects.filter(username="admin").count():
      User.objects.create_superuser('admin', 'your@company.com', 'admin')

  def tearDown(self):
    del os.environ['FREPPLE_TEST']

  def test_remote_command(self):
    # Create a header for basic authentication
    headers = {
      'HTTP_AUTHORIZATION': 'Basic ' + base64.b64encode('admin:admin'.encode()).decode()
      }

    # Run a plan
    response = self.client.post(
      '/execute/api/runplan/',
      {'constraint': 1, 'plantype': 1},
      **headers
      )

    self.assertEqual(response.status_code, 200)
    taskinfo = json.loads(response.content.decode())
    taskid0 = taskinfo['taskid']
    self.assertGreater(taskid0, 0)

    # Wait 10 seconds for the plan the finish
    cnt = 0
    while cnt <= 10:
      response = self.client.get(
        '/execute/api/status/?id=%s' % taskid0,
        **headers
        )
      self.assertEqual(response.status_code, 200)
      taskinfo = json.loads(response.content.decode())
      if taskinfo[str(taskid0)]['status'] == "Done":
        break
      sleep(1)
      cnt += 1
    self.assertLess(cnt, 10, "Running task taking too long")

    # Copy a plan
    response = self.client.post(
      '/execute/api/empty/',
      {},
      **headers
      )
    self.assertEqual(response.status_code, 200)
    taskinfo = json.loads(response.content.decode())
    taskid1 = taskinfo['taskid']
    self.assertEqual(taskid1, taskid0 + 1)

    # Wait for the flush the finish
    cnt = 0
    while cnt <= 20:
      response = self.client.get(
        '/execute/api/status/?id=%s' % taskid1,
        **headers
        )
      self.assertEqual(response.status_code, 200)
      taskinfo = json.loads(response.content.decode())
      if taskinfo[str(taskid1)]['status'] == "Done":
        break
      sleep(1)
      cnt += 1
    self.assertLess(cnt, 20, "Running task taking too long")
