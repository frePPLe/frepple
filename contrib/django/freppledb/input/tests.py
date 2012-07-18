#
# Copyright (C) 2007-2012 by Johan De Taeye, frePPLe bvba
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

# file : $URL$
# revision : $LastChangedRevision$  $LastChangedBy$
# date : $LastChangedDate$

from datetime import datetime
import tempfile

from django.core.exceptions import ObjectDoesNotExist
from django.test import TestCase

from freppledb.input.models import Location, Calendar

class DataLoadTest(TestCase):

  def setUp(self):
    # Login
    self.client.login(username='frepple', password='frepple')

  def test_input_customer(self):
    response = self.client.get('/admin/input/customer/?format=json')
    self.assertContains(response, '"records":2,')

  def test_input_flow(self):
    response = self.client.get('/admin/input/flow/?format=json')
    self.assertContains(response, '"records":19,')

  def test_input_buffer(self):
    response = self.client.get('/admin/input/buffer/?format=json')
    self.assertContains(response, '"records":8,')

  def test_input_calendar(self):
    response = self.client.get('/admin/input/calendar/?format=json')
    self.assertContains(response, '"records":4,')

  def test_input_demand(self):
    response = self.client.get('/admin/input/demand/?format=json')
    self.assertContains(response, '"records":14,')

  def test_input_item(self):
    response = self.client.get('/admin/input/item/?format=json')
    self.assertContains(response, '"records":5,')

  def test_input_load(self):
    response = self.client.get('/admin/input/load/?format=json')
    self.assertContains(response, '"records":3,')

  def test_input_location(self):
    response = self.client.get('/admin/input/location/?format=json')
    self.assertContains(response, '"records":2,')

  def test_input_operation(self):
    response = self.client.get('/admin/input/operation/?format=json')
    self.assertContains(response, '"records":14,')

  def test_input_operationplan(self):
    response = self.client.get('/admin/input/operationplan/?format=json')
    self.assertContains(response, '"records":4,')

  def test_input_parameter(self):
    response = self.client.get('/admin/common/parameter/?format=json')
    self.assertContains(response, '"records":2,')

  def test_input_resource(self):
    response = self.client.get('/admin/input/resource/?format=json')
    self.assertContains(response, '"records":3,')

  def test_input_suboperation(self):
    response = self.client.get('/admin/input/suboperation/?format=json')
    self.assertContains(response, '"records":4,')

  def test_csv_upload(self):
    self.assertEqual(
      [(i.name, i.category) for i in Location.objects.all()],
      [(u'factory 1',u''), (u'factory 2',u'')]
      )
    try:
      data = tempfile.TemporaryFile(mode='w+b')
      print >>data, 'name, category'
      print >>data, 'factory 3, cat1'
      print >>data, 'factory 4,'
      data.seek(0)
      response = self.client.post('/admin/input/location/', {'csv_file': data})
      self.assertRedirects(response, '/admin/input/location/')
    finally:
      data.close()
    self.assertEqual(
      [(i.name, i.category) for i in Location.objects.order_by('name')],
      [(u'factory 1',u''), (u'factory 2',u''), (u'factory 3',u'cat1'), (u'factory 4',u'')]
      )

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
      self.assertNotEqual(i.startdate, None, 'Missing start date')
      self.assertNotEqual(i.enddate, None, 'Missing end date')
      self.assertTrue(i.startdate<i.enddate, 'End date before the start date')
      if prevend:
        self.assertEqual(i.startdate, prevend, 'Non-adjacent calendar buckets')
      prevend = i.enddate
    # Verify original buckets
    self.assertEqual(
      [(str(i.startdate), str(i.enddate), int(i.value)) for i in calendar.buckets.all()],
      [('2012-01-01 00:00:00', '2012-02-01 00:00:00', 1),
       ('2012-02-01 00:00:00', '2030-12-31 00:00:00', 2)
      ])
    # Create a new bucket - start date aligned with existing bucket
    calendar.setvalue(datetime(2012,2,1), datetime(2012,3,3), 12)
    self.assertEqual(
      [(str(i.startdate), str(i.enddate), int(i.value)) for i in calendar.buckets.all()],
      [('2012-01-01 00:00:00', '2012-02-01 00:00:00', 1),
       ('2012-02-01 00:00:00', '2012-03-03 00:00:00', 12),
       ('2012-03-03 00:00:00', '2030-12-31 00:00:00', 2)
      ])
    # Create a new bucket - end date aligned with existing bucket
    calendar.setvalue(datetime(2012,2,10), datetime(2012,3,3), 100)
    self.assertEqual(
      [(str(i.startdate), str(i.enddate), int(i.value)) for i in calendar.buckets.all()],
      [('2012-01-01 00:00:00', '2012-02-01 00:00:00', 1),
       ('2012-02-01 00:00:00', '2012-02-10 00:00:00', 12),
       ('2012-02-10 00:00:00', '2012-03-03 00:00:00', 100),
       ('2012-03-03 00:00:00', '2030-12-31 00:00:00', 2)
      ])
    # 2 buckets partially updates and one deleted
    calendar.setvalue(datetime(2012,1,10), datetime(2012,4,3), 3)
    self.assertEqual(
      [(str(i.startdate), str(i.enddate), int(i.value)) for i in calendar.buckets.all()],
      [('2012-01-01 00:00:00', '2012-01-10 00:00:00', 1),
       ('2012-01-10 00:00:00', '2012-03-03 00:00:00', 3),
       ('2012-03-03 00:00:00', '2012-04-03 00:00:00', 3),
       ('2012-04-03 00:00:00', '2030-12-31 00:00:00', 2)
      ])
    # Create a new bucket - end date aligned with existing bucket
    calendar.setvalue(datetime(2012,2,10), datetime(2012,3,3), 4)
    self.assertEqual(
      [(str(i.startdate), str(i.enddate), int(i.value)) for i in calendar.buckets.all()],
      [('2012-01-01 00:00:00', '2012-01-10 00:00:00', 1),
       ('2012-01-10 00:00:00', '2012-02-10 00:00:00', 3),
       ('2012-02-10 00:00:00', '2012-03-03 00:00:00', 4),
       ('2012-03-03 00:00:00', '2012-04-03 00:00:00', 3),
       ('2012-04-03 00:00:00', '2030-12-31 00:00:00', 2)
      ])
    # Completely override the value of an existing bucket
    calendar.setvalue(datetime(2012,3,3), datetime(2012,4,3), 5)
    self.assertEqual(
      [(str(i.startdate), str(i.enddate), int(i.value)) for i in calendar.buckets.all()],
      [('2012-01-01 00:00:00', '2012-01-10 00:00:00', 1),
       ('2012-01-10 00:00:00', '2012-02-10 00:00:00', 3),
       ('2012-02-10 00:00:00', '2012-03-03 00:00:00', 4),
       ('2012-03-03 00:00:00', '2012-04-03 00:00:00', 5),
       ('2012-04-03 00:00:00', '2030-12-31 00:00:00', 2)
      ])
