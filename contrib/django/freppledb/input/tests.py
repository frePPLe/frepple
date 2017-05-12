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
import tempfile

from django.test import TestCase

from freppledb.input.models import Location


class DataLoadTest(TestCase):

  fixtures = ["demo"]

  def setUp(self):
    # Login
    self.client.login(username='admin', password='admin')

  def test_demo_data(self):
    response = self.client.get('/data/input/customer/?format=json')
    self.assertContains(response, '"records":3,')
    response = self.client.get('/data/input/operationmaterial/?format=json')
    self.assertContains(response, '"records":13,')
    response = self.client.get('/data/input/buffer/?format=json')
    self.assertContains(response, '"records":8,')
    response = self.client.get('/data/input/calendar/?format=json')
    self.assertContains(response, '"records":4,')
    response = self.client.get('/data/input/calendarbucket/?format=json')
    self.assertContains(response, '"records":5,')
    response = self.client.get('/data/input/demand/?format=json')
    self.assertContains(response, '"records":14,')
    response = self.client.get('/data/input/item/?format=json')
    self.assertContains(response, '"records":7,')
    response = self.client.get('/data/input/operationresource/?format=json')
    self.assertContains(response, '"records":3,')
    response = self.client.get('/data/input/location/?format=json')
    self.assertContains(response, '"records":3,')
    response = self.client.get('/data/input/operation/?format=json')
    self.assertContains(response, '"records":9,')
    response = self.client.get('/data/input/manufacturingorder/?format=json')
    self.assertContains(response, '"records":35,')
    response = self.client.get('/data/input/resource/?format=json')
    self.assertContains(response, '"records":3,')
    response = self.client.get('/data/input/suboperation/?format=json')
    self.assertContains(response, '"records":4,')

  def test_csv_upload(self):
    self.assertEqual(
      [(i.name, i.category or u'') for i in Location.objects.all()],
      [(u'All locations', u''), (u'factory 1', u''), (u'factory 2', u'')]  # Test result is different in Enterprise Edition
      )
    try:
      data = tempfile.NamedTemporaryFile(mode='w+b')
      data.write(b'name,category\n')
      data.write(b'factory 3,cat1\n')
      data.write(b'factory 4,\n')
      data.seek(0)
      response = self.client.post('/data/input/location/', {'csv_file': data})
      for rec in response.streaming_content:
        rec
      self.assertEqual(response.status_code, 200)
    finally:
      data.close()
    self.assertEqual(
      [(i.name, i.category or u'') for i in Location.objects.order_by('name')],
      [(u'All locations', u''), (u'factory 1', u''), (u'factory 2', u''), (u'factory 3', u'cat1'), (u'factory 4', u'')]  # Test result is different in Enterprise Edition
      )
