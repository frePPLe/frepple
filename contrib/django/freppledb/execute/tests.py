#
# Copyright (C) 2007-2012 by Johan De Taeye, frePPLe bvba
#
# This library is free software; you can redistribute it and/or modify it
# under the terms of the GNU Lesser General Public License as published
# by the Free Software Foundation; either version 2.1 of the License, or
# (at your option) any later version.
#
# This library is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU Lesser
# General Public License for more details.
#
# You should have received a copy of the GNU Lesser General Public
# License along with this library; if not, write to the Free Software
# Foundation Inc., 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301 USA
#

# file : $URL$
# revision : $LastChangedRevision$  $LastChangedBy$
# date : $LastChangedDate$

import os

from django.core import management
from django.test import TransactionTestCase
from django.conf import settings
from django.db import DEFAULT_DB_ALIAS, connections, transaction

import freppledb.output as output
import freppledb.input as input


class execute_from_user_interface(TransactionTestCase):

  def setUp(self):
    # Login
    self.client.login(username='frepple', password='frepple')

  def test_execute_page(self):
    response = self.client.get('/execute/')
    self.assertEqual(response.status_code, 200)

  def test_run_ui(self):
    # Empty the database tables
    response = self.client.post('/execute/erase/', {'action':'erase'})
    # The answer is a redirect to a new page, which also contains the success message
    self.assertRedirects(response, '/execute/execute.html#database')
    self.assertEqual(input.models.Calendar.objects.count(),0)
    self.assertEqual(input.models.Demand.objects.count(),0)
    self.assertEqual(output.models.Problem.objects.count(),0)
    self.assertEqual(output.models.FlowPlan.objects.count(),0)
    self.assertEqual(output.models.LoadPlan.objects.count(),0)
    self.assertEqual(output.models.OperationPlan.objects.count(),0)

    # Load a dataset
    response = self.client.post('/execute/fixture/', {'action':'load', 'datafile':'small_demo'})
    self.assertRedirects(response, '/execute/execute.html#database')
    self.assertNotEqual(input.models.Calendar.objects.count(),0)
    self.assertNotEqual(input.models.Demand.objects.count(),0)

    # Run frePPLe,  and make sure the test database is used
    os.environ['FREPPLE_TEST'] = "YES"
    response = self.client.post('/execute/runfrepple/', {'action':'run', 'constraint':'15', 'plantype':'1'})
    del os.environ['FREPPLE_TEST']
    self.assertRedirects(response, '/execute/execute.html#plan')

    # Count the output records
    self.assertEqual(output.models.Problem.objects.count(),27)
    self.assertEqual(output.models.FlowPlan.objects.count(),211)
    self.assertEqual(output.models.LoadPlan.objects.count(),51)
    self.assertEqual(output.models.OperationPlan.objects.count(),128)


class execute_with_commands(TransactionTestCase):

  def setUp(self):
    os.environ['FREPPLE_TEST'] = "YES"

  def tearDown(self):
    del os.environ['FREPPLE_TEST']

  def test_run_cmd(self):
    # Empty the database tables
    self.assertNotEqual(input.models.Calendar.objects.count(),0)
    management.call_command('frepple_flush')
    self.assertEqual(input.models.Calendar.objects.count(),0)
    self.assertEqual(input.models.Demand.objects.count(),0)
    self.assertEqual(output.models.Problem.objects.count(),0)
    self.assertEqual(output.models.FlowPlan.objects.count(),0)
    self.assertEqual(output.models.LoadPlan.objects.count(),0)
    self.assertEqual(output.models.OperationPlan.objects.count(),0)

    # Create a new model
    management.call_command('frepple_createmodel', cluster='1', verbosity='0')
    self.assertNotEqual(input.models.Calendar.objects.count(),0)
    self.assertNotEqual(input.models.Demand.objects.count(),0)

    # Run frePPLe, and make sure the test database is used
    management.call_command('frepple_run', plantype=1, constraint=15, nonfatal=True)
    self.assertEqual(output.models.Problem.objects.count(),194)
    self.assertEqual(output.models.FlowPlan.objects.count(),795)
    self.assertEqual(output.models.LoadPlan.objects.count(),84)
    self.assertEqual(output.models.OperationPlan.objects.count(),413)


class execute_multidb(TransactionTestCase):
  multi_db = True

  def setUp(self):
    os.environ['FREPPLE_TEST'] = "YES"

  def tearDown(self):
    del os.environ['FREPPLE_TEST']

  def test_multidb_cmd(self):
    # Find out which databases to use
    db1 = DEFAULT_DB_ALIAS
    db2 = None
    for i in settings.DATABASES.keys():
      if i != DEFAULT_DB_ALIAS:
        db2 = i
        break
    if not db2:
      # Only a single database is configured and we skip this test
      return

    # Check count in both databases
    count1 = output.models.FlowPlan.objects.all().using(db1).count()
    count2 = output.models.FlowPlan.objects.all().using(db2).count()
    self.assertEqual(count1,0)
    self.assertEqual(count2,0)

    # Erase second database
    count1 = input.models.Demand.objects.all().using(db1).count()
    management.call_command('frepple_flush', database=db2)
    count1new = input.models.Demand.objects.all().using(db1).count()
    count2 = input.models.Demand.objects.all().using(db2).count()
    self.assertEqual(count1new,count1)
    self.assertEqual(count2,0)

    # Copy the db1 into db2.
    # We need to close the transactions, since they can block the copy
    transaction.commit(using=db1)
    transaction.commit(using=db2)
    management.call_command('frepple_copy', db1, db2, nonfatal=True)
    count1 = output.models.Demand.objects.all().using(db1).count()
    count2 = output.models.Demand.objects.all().using(db2).count()
    self.assertEqual(count1,count2)

    # Run the plan on db1.
    # The count changes in db1 and not in db2.
    management.call_command('frepple_run', plantype=1, constraint=15, nonfatal=True, database=db1)
    count1 = output.models.FlowPlan.objects.all().using(db1).count()
    count2 = output.models.FlowPlan.objects.all().using(db2).count()
    self.assertNotEqual(count1,0)
    self.assertEqual(count2,0)

    # Run a plan on db2.
    # The count changes in db1 and not in db2.
    # The count in both databases is expected to be different since we run a different plan
    management.call_command('frepple_run', plantype=1, constraint=0, nonfatal=True, database=db2)
    count1new = output.models.FlowPlan.objects.all().using(db1).count()
    count2 = output.models.FlowPlan.objects.all().using(db2).count()
    self.assertEqual(count1new,count1)
    self.assertNotEqual(count2,0)
    self.assertNotEqual(count2,count1new)
