#
# Copyright (C) 2007-2011 by Johan De Taeye, frePPLe bvba
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

from django.test import TestCase

class OutputTest(TestCase):

  def setUp(self):
    # Login
    self.client.login(username='frepple', password='frepple')

  # Buffer
  def test_output_buffer(self):
    response = self.client.get('/buffer/')
    self.assertEqual(response.status_code, 200)
    self.assertContains(response, '8 buffers')

  def test_output_buffer_csvtable(self):
    response = self.client.get('/buffer/', {'reporttype':'csv'})
    self.assertEqual(response.status_code, 200)
    self.assertTrue(response.__getitem__('Content-Type').startswith('text/csv; charset='))

  def test_output_buffer_csvlist(self):
    response = self.client.get('/buffer/', {'reporttype':'csvlist'})
    self.assertEqual(response.status_code, 200)
    self.assertTrue(response.__getitem__('Content-Type').startswith('text/csv; charset='))

  # Resource
  def test_output_resource(self):
    response = self.client.get('/resource/')
    self.assertEqual(response.status_code, 200)
    self.assertContains(response, '3 resources')

  def test_output_resource_csvtable(self):
    response = self.client.get('/resource/', {'reporttype':'csv'})
    self.assertEqual(response.status_code, 200)
    self.assertTrue(response.__getitem__('Content-Type').startswith('text/csv; charset='))

  # Demand
  def test_output_demand(self):
    response = self.client.get('/demand/')
    self.assertEqual(response.status_code, 200)
    self.assertContains(response, 'Demand report')

  def test_output_demand_csvlist(self):
    response = self.client.get('/demand/', {'reporttype':'csvlist'})
    self.assertEqual(response.status_code, 200)
    self.assertTrue(response.__getitem__('Content-Type').startswith('text/csv; charset='))

  # Forecast
  def test_output_forecast(self):
    response = self.client.get('/forecast/')
    self.assertEqual(response.status_code, 200)
    self.assertContains(response, '2 forecasts')

  def test_output_forecast_csvlist(self):
    response = self.client.get('/forecast/', {'reporttype':'csvlist'})
    self.assertEqual(response.status_code, 200)
    self.assertTrue(response.__getitem__('Content-Type').startswith('text/csv; charset='))

  # Operation
  def test_output_operation(self):
    response = self.client.get('/operation/')
    self.assertEqual(response.status_code, 200)
    self.assertContains(response, '14 operations')

  def test_output_operation_csvtable(self):
    response = self.client.get('/operation/', {'reporttype':'csv'})
    self.assertEqual(response.status_code, 200)
    self.assertTrue(response.__getitem__('Content-Type').startswith('text/csv; charset='))

  # Problem
  def test_output_problem(self):
    response = self.client.get('/problem/')
    self.assertEqual(response.status_code, 200)
    self.assertContains(response, '0 problems')

  def test_output_problem_csvlist(self):
    response = self.client.get('/problem/', {'reporttype':'csvlist'})
    self.assertEqual(response.status_code, 200)
    self.assertTrue(response.__getitem__('Content-Type').startswith('text/csv; charset='))

  # Constraint
  def test_output_constraint(self):
    response = self.client.get('/constraint/')
    self.assertEqual(response.status_code, 200)
    self.assertContains(response, '0 constraints')

  def test_output_constraint_csvlist(self):
    response = self.client.get('/constraint/', {'reporttype':'csvlist'})
    self.assertEqual(response.status_code, 200)
    self.assertTrue(response.__getitem__('Content-Type').startswith('text/csv; charset='))

  # KPI
  def test_output_kpi(self):
    response = self.client.get('/kpi/')
    self.assertEqual(response.status_code, 200)
    self.assertContains(response, 'Performance Indicators')

  def test_output_kpi_csvlist(self):
    response = self.client.get('/kpi/', {'reporttype':'csvlist'})
    self.assertEqual(response.status_code, 200)
    self.assertTrue(response.__getitem__('Content-Type').startswith('text/csv; charset='))
