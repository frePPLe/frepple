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

from django.test import TestCase


class OutputTest(TestCase):

  fixtures = ["demo"]

  def setUp(self):
    # Login
    self.client.login(username='admin', password='admin')

  # Buffer
  def test_output_buffer(self):
    response = self.client.get('/buffer/?format=json')
    self.assertEqual(response.status_code, 200)
    self.assertContains(response, '"records":8,')
    response = self.client.get('/buffer/?format=csvtable')
    self.assertEqual(response.status_code, 200)
    self.assertTrue(response.__getitem__('Content-Type').startswith('text/csv; charset='))
    response = self.client.get('/buffer/?format=csvlist')
    self.assertEqual(response.status_code, 200)
    self.assertTrue(response.__getitem__('Content-Type').startswith('text/csv; charset='))
    response = self.client.get('/buffer/?format=spreadsheettable')
    self.assertEqual(response.status_code, 200)
    self.assertTrue(response.__getitem__('Content-Type').startswith('application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'))


  # Resource
  def test_output_resource(self):
    response = self.client.get('/resource/?format=json')
    self.assertEqual(response.status_code, 200)
    self.assertContains(response, '"records":3,')
    response = self.client.get('/resource/?format=csvtable')
    self.assertEqual(response.status_code, 200)
    self.assertTrue(response.__getitem__('Content-Type').startswith('text/csv; charset='))
    response = self.client.get('/resource/?format=spreadsheetlist')
    self.assertEqual(response.status_code, 200)
    self.assertTrue(response.__getitem__('Content-Type').startswith('application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'))

  # Demand
  def test_output_demand(self):
    response = self.client.get('/demand/')
    self.assertEqual(response.status_code, 200)
    self.assertContains(response, 'Demand report')
    response = self.client.get('/demand/?format=csvlist')
    self.assertEqual(response.status_code, 200)
    self.assertTrue(response.__getitem__('Content-Type').startswith('text/csv; charset='))
    response = self.client.get('/demand/?format=spreadsheettable')
    self.assertEqual(response.status_code, 200)
    self.assertTrue(response.__getitem__('Content-Type').startswith('application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'))

  # Manufacturing orders
  def test_output_manufacturing_orders(self):
    response = self.client.get('/operation/?format=json')
    self.assertEqual(response.status_code, 200)
    self.assertContains(response, '"records":3,')
    response = self.client.get('/operation/?format=csvtable')
    self.assertEqual(response.status_code, 200)
    self.assertTrue(response.__getitem__('Content-Type').startswith('text/csv; charset='))
    response = self.client.get('/operation/?format=spreadsheetlist')
    self.assertEqual(response.status_code, 200)
    self.assertTrue(response.__getitem__('Content-Type').startswith('application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'))

  # Purchase orders
  def test_output_purchase_orders(self):
    response = self.client.get('/purchase/?format=json')
    self.assertEqual(response.status_code, 200)
    self.assertContains(response, '"records":4,')
    response = self.client.get('/purchase/?format=csvtable')
    self.assertEqual(response.status_code, 200)
    self.assertTrue(response.__getitem__('Content-Type').startswith('text/csv; charset='))
    response = self.client.get('/purchase/?format=spreadsheetlist')
    self.assertEqual(response.status_code, 200)
    self.assertTrue(response.__getitem__('Content-Type').startswith('application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'))

  # Distribution orders
  def test_output_distribution_orders(self):
    response = self.client.get('/distribution/?format=json')
    self.assertEqual(response.status_code, 200)
    self.assertContains(response, '"records":1,')
    response = self.client.get('/distribution/?format=csvtable')
    self.assertEqual(response.status_code, 200)
    self.assertTrue(response.__getitem__('Content-Type').startswith('text/csv; charset='))
    response = self.client.get('/distribution/?format=spreadsheetlist')
    self.assertEqual(response.status_code, 200)
    self.assertTrue(response.__getitem__('Content-Type').startswith('application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'))

  # Problem
  def test_output_problem(self):
    response = self.client.get('/problem/?format=json')
    self.assertEqual(response.status_code, 200)
    self.assertContains(response, '"records":25,')  # specific for community
    response = self.client.get('/problem/?format=csvlist')
    self.assertEqual(response.status_code, 200)
    self.assertTrue(response.__getitem__('Content-Type').startswith('text/csv; charset='))
    response = self.client.get('/problem/?format=spreadsheetlist')
    self.assertEqual(response.status_code, 200)
    self.assertTrue(response.__getitem__('Content-Type').startswith('application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'))

  # Pegging
  def test_output_pegging(self):
    response = self.client.get('/demandpegging/Demand%2001/?format=json')
    self.assertContains(response, '"records":1,')
    self.assertEqual(response.status_code, 200)

  # Constraint
  def test_output_constraint(self):
    response = self.client.get('/constraint/?format=json')
    self.assertEqual(response.status_code, 200)
    self.assertContains(response, '"records":0,')
    response = self.client.get('/constraint/?format=csvlist')
    self.assertEqual(response.status_code, 200)
    self.assertTrue(response.__getitem__('Content-Type').startswith('text/csv; charset='))
    response = self.client.get('/constraint/?format=spreadsheetlist')
    self.assertEqual(response.status_code, 200)
    self.assertTrue(response.__getitem__('Content-Type').startswith('application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'))

  # KPI
  def test_output_kpi(self):
    response = self.client.get('/kpi/')
    self.assertEqual(response.status_code, 200)
    self.assertContains(response, 'Performance Indicators')
    response = self.client.get('/kpi/?format=csvlist')
    self.assertEqual(response.status_code, 200)
    self.assertTrue(response.__getitem__('Content-Type').startswith('text/csv; charset='))
    response = self.client.get('/kpi/?format=spreadsheetlist')
    self.assertEqual(response.status_code, 200)
    self.assertTrue(response.__getitem__('Content-Type').startswith('application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'))
