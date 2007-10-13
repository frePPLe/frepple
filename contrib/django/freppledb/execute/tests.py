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
# Foundation Inc., 59 Temple Place, Suite 330, Boston, MA 02111-1307, USA
#

# file : $URL$
# revision : $LastChangedRevision$  $LastChangedBy$
# date : $LastChangedDate$
# email : jdetaeye@users.sourceforge.net

import django.test
from freppledb.input.models import *
import freppledb.output.models
from django.test.client import Client
from django.core.exceptions import ObjectDoesNotExist

class ExecuteTest(django.test.TestCase):

  def setUp(self):
    # Create a client
    self.client = Client()
    self.client.login(username='frepple', password='frepple')

  def test_execute_page(self):
    response = self.client.get('/execute/')
    self.failUnlessEqual(response.status_code, 200)

  def test_run_frepple(self):
    # Verify the output tables are empty
    self.failUnlessEqual(freppledb.output.models.Problem.objects.count(),0)
    self.failUnlessEqual(freppledb.output.models.FlowPlan.objects.count(),0)
    self.failUnlessEqual(freppledb.output.models.LoadPlan.objects.count(),0)
    self.failUnlessEqual(freppledb.output.models.OperationPlan.objects.count(),0)

    # Run frepple
    response = self.client.post('/execute/runfrepple/', {'action':'run', 'type':7})
    # The answer is a redirect to a new page, which also contains the success message
    self.failUnlessEqual(response.status_code, 302)
    response = self.client.get(response._headers['location'])
    self.assertContains(response.content, 'Successfully ran frepple')
    # xxx problem: frepple doesn't export in the test database...

    # Count the output records
    self.failIfEqual(freppledb.output.models.Problem.objects.count(),0)
    self.failIfEqual(freppledb.output.models.Flowplan.objects.count(),0)
    self.failIfEqual(freppledb.output.models.LoadPlan.objects.count(),0)
    self.failIfEqual(freppledb.output.models.OperationPlan.objects.count(),0)
