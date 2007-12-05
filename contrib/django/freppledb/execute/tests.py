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
from input.models import *
import output.models
from django.test.client import Client
from django.core.exceptions import ObjectDoesNotExist

class ExecuteTest(django.test.TestCase):

  def setUp(self):
    # Login
    self.client.login(username='frepple', password='frepple')

  def test_execute_page(self):
    response = self.client.get('/execute/')
    self.failUnlessEqual(response.status_code, 200)

  def test_run_frepple(self):
    # Verify the output tables are empty
    self.failUnlessEqual(output.models.Problem.objects.count(),0)
    self.failUnlessEqual(output.models.FlowPlan.objects.count(),0)
    self.failUnlessEqual(output.models.LoadPlan.objects.count(),0)
    self.failUnlessEqual(output.models.OperationPlan.objects.count(),0)

    # Run frepple
    response = self.client.post('/execute/runfrepple/', {'action':'run', 'type':7})
    # The answer is a redirect to a new page, which also contains the success message
    self.assertRedirects(response, '/execute/execute.html')

    # Count the output records
    self.failUnlessEqual(output.models.Problem.objects.count(),11)
    self.failUnlessEqual(output.models.FlowPlan.objects.count(),158)
    self.failUnlessEqual(output.models.LoadPlan.objects.count(),36)
    self.failUnlessEqual(output.models.OperationPlan.objects.count(),105)
