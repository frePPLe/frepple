#
# Copyright (C) 2007 by Johan De Taeye
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
from django.test.testcases import restore_transaction_methods, disable_transaction_methods
from django.conf import settings

import output.models
import input.models

class execute_from_user_interface(TransactionTestCase):

  def setUp(self):
    # Login
    self.client.login(username='frepple', password='frepple')

  def test_execute_page(self):
    response = self.client.get('/execute/')
    self.failUnlessEqual(response.status_code, 200)

  def test_run_ui(self):
    # Empty the database tables
    response = self.client.post('/execute/erase/', {'action':'erase'})
    # The answer is a redirect to a new page, which also contains the success message
    self.assertRedirects(response, '/execute/execute.html')
    self.failUnlessEqual(input.models.Calendar.objects.count(),0)
    self.failUnlessEqual(input.models.Demand.objects.count(),0)
    self.failUnlessEqual(output.models.Problem.objects.count(),0)
    self.failUnlessEqual(output.models.FlowPlan.objects.count(),0)
    self.failUnlessEqual(output.models.LoadPlan.objects.count(),0)
    self.failUnlessEqual(output.models.OperationPlan.objects.count(),0)

    # Load a dataset
    response = self.client.post('/execute/fixture/', {'action':'load', 'datafile':'small_demo'})
    self.assertRedirects(response, '/execute/execute.html')
    self.failIfEqual(input.models.Calendar.objects.count(),0)
    self.failIfEqual(input.models.Demand.objects.count(),0)

    # Run frePPLe,  and make sure the test database is used
    try: os.environ['FREPPLE_DATABASE_NAME'] = settings.TEST_DATABASE_NAME
    except: pass
    try: os.environ['FREPPLE_DATABASE_USER'] = settings.TEST_DATABASE_USER
    except: pass
    response = self.client.post('/execute/runfrepple/', {'action':'run', 'constraint':'15', 'plantype':'1'})
    self.assertRedirects(response, '/execute/execute.html')

    # Count the output records
    self.failUnlessEqual(output.models.Problem.objects.count(),9)
    self.failUnlessEqual(output.models.FlowPlan.objects.count(),291)
    self.failUnlessEqual(output.models.LoadPlan.objects.count(),83)
    self.failUnlessEqual(output.models.OperationPlan.objects.count(),135)


class execute_with_commands(TransactionTestCase):

  def test_run_cmd(self):
    # Empty the database tables
    self.failIfEqual(input.models.Calendar.objects.count(),0)
    management.call_command('frepple_flush')
    self.failUnlessEqual(input.models.Calendar.objects.count(),0)
    self.failUnlessEqual(input.models.Demand.objects.count(),0)
    self.failUnlessEqual(output.models.Problem.objects.count(),0)
    self.failUnlessEqual(output.models.FlowPlan.objects.count(),0)
    self.failUnlessEqual(output.models.LoadPlan.objects.count(),0)
    self.failUnlessEqual(output.models.OperationPlan.objects.count(),0)

    # Create a new model
    management.call_command('frepple_createmodel', cluster='1', verbosity='0')
    self.failIfEqual(input.models.Calendar.objects.count(),0)
    self.failIfEqual(input.models.Demand.objects.count(),0)

    # Run frePPLe, and make sure the test database is used
    try: os.environ['FREPPLE_DATABASE_NAME'] = settings.TEST_DATABASE_NAME
    except: pass
    try: os.environ['FREPPLE_DATABASE_USER'] = settings.TEST_DATABASE_USER
    except: pass
    management.call_command('frepple_run', plantype='1', nonfatal=True)
    self.failIfEqual(output.models.Problem.objects.count(),0)
    self.failIfEqual(output.models.FlowPlan.objects.count(),0)
    self.failIfEqual(output.models.LoadPlan.objects.count(),0)
    self.failIfEqual(output.models.OperationPlan.objects.count(),0)
