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
from django.test.client import Client
from django.core.exceptions import ObjectDoesNotExist


class DataLoadTest(django.test.TestCase):

  def setUp(self):
    # Create a test user
    from django.contrib.auth.models import User
    user = User.objects.create_user('test', 'f@frepple.com', 'test')
    user.is_staff = True
    user.is_superuser = True
    user.save()

    # Create a client
    self.client = Client()
    self.client.login(username='test', password='test')

  def test_input_customer(self):
    response = self.client.get('/admin/input/customer/')
    self.assertContains(response, '2 customers')

  def test_input_flow(self):
    response = self.client.get('/admin/input/flow/')
    self.assertContains(response, '19 flows')

  def test_input_buffer(self):
    response = self.client.get('/admin/input/buffer/')
    self.assertContains(response, '8 buffers')

  def test_input_calendar(self):
    response = self.client.get('/admin/input/calendar/')
    self.assertContains(response, '2 calendars')

  def test_input_demand(self):
    response = self.client.get('/admin/input/demand/')
    self.assertContains(response, '14 demands')

  def test_input_item(self):
    response = self.client.get('/admin/input/item/')
    self.assertContains(response, '5 items')

  def test_input_load(self):
    response = self.client.get('/admin/input/load/')
    self.assertContains(response, '3 loads')

  def test_input_location(self):
    response = self.client.get('/admin/input/location/')
    self.assertContains(response, '2 locations')

  def test_input_operation(self):
    response = self.client.get('/admin/input/operation/')
    self.assertContains(response, '14 operations')

  def test_input_operationplan(self):
    response = self.client.get('/admin/input/operationplan/')
    self.assertContains(response, '4 operation plans')

  def test_input_plan(self):
    response = self.client.get('/admin/input/plan/')
    self.assertContains(response, '1 plan')

  def test_input_resource(self):
    response = self.client.get('/admin/input/resource/')
    self.assertContains(response, '3 resources')

  def test_input_suboperation(self):
    response = self.client.get('/admin/input/suboperation/')
    self.assertContains(response, '4 sub operations')

  def test_buckets(self):
    # Find the calendar
    try:
      calendar = Calendar.objects.get(name='pack capacity factory 1')
    except ObjectDoesNotExist:
      self.fail("Calendar 'pack capacity factory 1' not found")
    buckets = calendar.buckets.all()
    # Assure it has 2 buckets
    self.assertEqual(len(buckets),2)
    # Verify the bucket dates are filled in correctly
    prevend = None
    for i in buckets:
      self.failIfEqual(i.startdate, None, 'Missing start date')
      self.failIfEqual(i.enddate, None, 'Missing end date')
      self.failUnless(i.startdate<i.enddate, 'End date before the start date')
      if prevend:
        self.failUnlessEqual(i.startdate, prevend, 'Non-adjacent calendar buckets')
      prevend = i.enddate
