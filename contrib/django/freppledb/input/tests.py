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

from django.core.exceptions import ObjectDoesNotExist
from django.test import TestCase

from input.models import *

class DataLoadTest(TestCase):

  def setUp(self):
    # Login
    self.client.login(username='frepple', password='frepple')

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
    self.assertContains(response, '3 calendars')

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
    self.assertContains(response, '4 operationplans')

  def test_input_plan(self):
    response = self.client.get('/admin/input/plan/')
    self.assertContains(response, '1 plan')

  def test_input_resource(self):
    response = self.client.get('/admin/input/resource/')
    self.assertContains(response, '3 resources')

  def test_input_suboperation(self):
    response = self.client.get('/admin/input/suboperation/')
    self.assertContains(response, '4 suboperations')

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
    # Verify original buckets
    self.failUnlessEqual(
      [(str(i.startdate), str(i.enddate), int(i.value)) for i in calendar.buckets.all()],
      [('2007-01-01 00:00:00', '2007-02-01 00:00:00', 1),
       ('2007-02-01 00:00:00', '2030-12-31 00:00:00', 0)
      ])
    # Create a new bucket - start date aligned with existing bucket
    calendar.setvalue(datetime(2007,2,1), datetime(2007,3,3), 12)
    self.failUnlessEqual(
      [(str(i.startdate), str(i.enddate), int(i.value)) for i in calendar.buckets.all()],
      [('2007-01-01 00:00:00', '2007-02-01 00:00:00', 1),
       ('2007-02-01 00:00:00', '2007-03-03 00:00:00', 12),
       ('2007-03-03 00:00:00', '2030-12-31 00:00:00', 0)
      ])
    # Create a new bucket - end date aligned with existing bucket
    calendar.setvalue(datetime(2007,2,10), datetime(2007,3,3), 100)
    self.failUnlessEqual(
      [(str(i.startdate), str(i.enddate), int(i.value)) for i in calendar.buckets.all()],
      [('2007-01-01 00:00:00', '2007-02-01 00:00:00', 1),
       ('2007-02-01 00:00:00', '2007-02-10 00:00:00', 12),
       ('2007-02-10 00:00:00', '2007-03-03 00:00:00', 100),
       ('2007-03-03 00:00:00', '2030-12-31 00:00:00', 0)
      ])
    # 2 buckets partially updates and one deleted
    calendar.setvalue(datetime(2007,1,10), datetime(2007,4,3), 3)
    self.failUnlessEqual(
      [(str(i.startdate), str(i.enddate), int(i.value)) for i in calendar.buckets.all()],
      [('2007-01-01 00:00:00', '2007-01-10 00:00:00', 1),
       ('2007-01-10 00:00:00', '2007-03-03 00:00:00', 3),
       ('2007-03-03 00:00:00', '2007-04-03 00:00:00', 3),
       ('2007-04-03 00:00:00', '2030-12-31 00:00:00', 0)
      ])
    # Create a new bucket - end date aligned with existing bucket
    calendar.setvalue(datetime(2007,2,10), datetime(2007,3,3), 4)
    self.failUnlessEqual(
      [(str(i.startdate), str(i.enddate), int(i.value)) for i in calendar.buckets.all()],
      [('2007-01-01 00:00:00', '2007-01-10 00:00:00', 1),
       ('2007-01-10 00:00:00', '2007-02-10 00:00:00', 3),
       ('2007-02-10 00:00:00', '2007-03-03 00:00:00', 4),
       ('2007-03-03 00:00:00', '2007-04-03 00:00:00', 3),
       ('2007-04-03 00:00:00', '2030-12-31 00:00:00', 0)
      ])
    # Completely override the value of an existing bucket
    calendar.setvalue(datetime(2007,3,3), datetime(2007,4,3), 5)
    self.failUnlessEqual(
      [(str(i.startdate), str(i.enddate), int(i.value)) for i in calendar.buckets.all()],
      [('2007-01-01 00:00:00', '2007-01-10 00:00:00', 1),
       ('2007-01-10 00:00:00', '2007-02-10 00:00:00', 3),
       ('2007-02-10 00:00:00', '2007-03-03 00:00:00', 4),
       ('2007-03-03 00:00:00', '2007-04-03 00:00:00', 5),
       ('2007-04-03 00:00:00', '2030-12-31 00:00:00', 0)
      ])
