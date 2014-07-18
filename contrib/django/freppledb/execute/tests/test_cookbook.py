#
# Copyright (C) 2007-2013 by Johan De Taeye, frePPLe bvba
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

import os.path
try:
  from urllib2 import urlopen
except:
  from urllib.request import urlopen

from django.conf import settings
from django.core import management
from django.test import TransactionTestCase

import freppledb.output as output


class cookbooktest(TransactionTestCase):

  def setUp(self):
    # Make sure the test database is used
    if not 'django.contrib.sessions' in settings.INSTALLED_APPS:
      settings.INSTALLED_APPS += ('django.contrib.sessions',)
    os.environ['FREPPLE_TEST'] = "YES"

  def tearDown(self):
    del os.environ['FREPPLE_TEST']

  def loadExcel(self, url):
    # Read the excel file from the website in memory
    data = urlopen(url).read()
    self.assertTrue(len(data)>0, "Can't load excel file")
    # Upload the excel data as a form
    self.client.login(username='admin', password='admin')
    response = self.client.post('/execute/launch/importworkbook/', {'spreadsheet': data})
    self.assertRedirects(response, '/execute/')
    self.client.logout()

  def assertOperationplans(self, resultfile):
    resultfilename = os.path.join(os.path.dirname(os.path.realpath(__file__)), resultfile)
    opplans = [ "%s,%s,%s,%s" % (i.operation, i.startdate, i.enddate, i.quantity) for i in output.models.OperationPlan.objects.order_by('operation','startdate','quantity').only('operation','startdate','enddate','quantity') ]
    row = 0
    print ("zzzz",'\n'.join(opplans))
    with open(resultfilename, 'r') as f:
      for line in f:
        if opplans[row] != line:
          self.fail("Difference in expected results")
        row += 1
    if row != len(opplans):
      self.fail("Difference in expected results1")

  def test_calendar_working_hours(self):
    management.call_command('frepple_flush')
    self.loadExcel("http://frepple.com/wp-content/uploads/calendar_working_hours.xlsx")
    management.call_command('frepple_run', plantype=1, constraint=15)
    self.assertOperationplans("calendar_working_hours.expect")

  def test_resource_types(self):
    management.call_command('frepple_flush')
    self.loadExcel("http://frepple.com/wp-content/uploads/resource_types.xlsx")
    management.call_command('frepple_run', plantype=1, constraint=15)
    self.assertOperationplans("resource_types.expect")

  def test_demand_priorities(self):
    management.call_command('frepple_flush')
    self.loadExcel("http://frepple.com/wp-content/uploads/demand_priorities.xlsx")
    management.call_command('frepple_run', plantype=1, constraint=15)
    self.assertOperationplans("demand_priorities.expect")

  def test_demand_policies(self):
    management.call_command('frepple_flush')
    self.loadExcel("http://frepple.com/wp-content/uploads/demand_policies.xlsx")
    management.call_command('frepple_run', plantype=1, constraint=15)
    self.assertOperationplans("demand_policies.expect")
