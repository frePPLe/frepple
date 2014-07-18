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

from django.test import TestCase
from django.conf import settings


class OutputTest(TestCase):

  def setUp(self):
    # Login
    if not 'django.contrib.sessions' in settings.INSTALLED_APPS:
      settings.INSTALLED_APPS += ('django.contrib.sessions',)
    self.client.login(username='admin', password='admin')

  # Buffer
  def test_output_buffer(self):
    response = self.client.get('/buffer/?format=json')
    self.assertEqual(response.status_code, 200)
    self.assertContains(response, '"records":8,')

  def test_output_buffer_csvtable(self):
    response = self.client.get('/buffer/?format=csvtable')
    self.assertEqual(response.status_code, 200)
    self.assertTrue(response.__getitem__('Content-Type').startswith('text/csv; charset='))

  def test_output_buffer_csvlist(self):
    response = self.client.get('/buffer/?format=csvlist')
    self.assertEqual(response.status_code, 200)
    self.assertTrue(response.__getitem__('Content-Type').startswith('text/csv; charset='))

  # Resource
  def test_output_resource(self):
    response = self.client.get('/resource/?format=json')
    self.assertEqual(response.status_code, 200)
    self.assertContains(response, '"records":3,')

  def test_output_resource_csvtable(self):
    response = self.client.get('/resource/?format=csvtable')
    self.assertEqual(response.status_code, 200)
    self.assertTrue(response.__getitem__('Content-Type').startswith('text/csv; charset='))

  # Demand
  def test_output_demand(self):
    response = self.client.get('/demand/')
    self.assertEqual(response.status_code, 200)
    self.assertContains(response, 'Demand report')

  def test_output_demand_csvlist(self):
    response = self.client.get('/demand/?format=csvlist')
    self.assertEqual(response.status_code, 200)
    self.assertTrue(response.__getitem__('Content-Type').startswith('text/csv; charset='))

  # Operation
  def test_output_operation(self):
    response = self.client.get('/operation/?format=json')
    self.assertEqual(response.status_code, 200)
    self.assertContains(response, '"records":14,')

  def test_output_operation_csvtable(self):
    response = self.client.get('/operation/?format=csvtable')
    self.assertEqual(response.status_code, 200)
    self.assertTrue(response.__getitem__('Content-Type').startswith('text/csv; charset='))

  # Problem
  def test_output_problem(self):
    response = self.client.get('/problem/?format=json')
    self.assertEqual(response.status_code, 200)
    self.assertContains(response, '"records":0,')

  def test_output_problem_csvlist(self):
    response = self.client.get('/problem/?format=csvlist')
    self.assertEqual(response.status_code, 200)
    self.assertTrue(response.__getitem__('Content-Type').startswith('text/csv; charset='))

  # Constraint
  def test_output_constraint(self):
    response = self.client.get('/constraint/?format=json')
    self.assertEqual(response.status_code, 200)
    self.assertContains(response, '"records":0,')

  def test_output_constraint_csvlist(self):
    response = self.client.get('/constraint/?format=csvlist')
    self.assertEqual(response.status_code, 200)
    self.assertTrue(response.__getitem__('Content-Type').startswith('text/csv; charset='))

  # KPI
  def test_output_kpi(self):
    response = self.client.get('/kpi/')
    self.assertEqual(response.status_code, 200)
    self.assertContains(response, 'Performance Indicators')

  def test_output_kpi_csvlist(self):
    response = self.client.get('/kpi/?format=csvlist')
    self.assertEqual(response.status_code, 200)
    self.assertTrue(response.__getitem__('Content-Type').startswith('text/csv; charset='))
