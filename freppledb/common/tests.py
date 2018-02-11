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

import os
import os.path

from django.core import management
from django.http.response import StreamingHttpResponse
from django.test import TestCase, TransactionTestCase

from freppledb.common.models import User
import freppledb.common as common
import freppledb.input as input

from rest_framework.test import APIClient, APITestCase, APIRequestFactory


class DataLoadTest(TestCase):

  def setUp(self):
    # Login
    self.client.login(username='admin', password='admin')

  def test_common_parameter(self):
    response = self.client.get('/data/common/parameter/?format=json')
    if not isinstance(response, StreamingHttpResponse):
      raise Exception("expected a streaming response")
    for i in response.streaming_content:
      if b'"records":' in i:
        return
    self.fail("Didn't find expected number of parameters")


class UserPreferenceTest(TestCase):

  def test_get_set_preferences(self):
    user = User.objects.all().get(username='admin')
    before = user.getPreference('test')
    self.assertIsNone(before)
    user.setPreference('test', {'a': 1, 'b': 'c'})
    after = user.getPreference('test')
    self.assertEqual(after, {'a': 1, 'b': 'c'})


class ExcelTest(TransactionTestCase):

  fixtures = ['demo']

  def setUp(self):
    # Login
    if not User.objects.filter(username="admin").count():
      User.objects.create_superuser('admin', 'your@company.com', 'admin')
    self.client.login(username='admin', password='admin')

  def tearDown(self):
    if os.path.exists("workbook.xlsx"):
      os.remove("workbook.xlsx")

  def run_workbook(self, language):
    # Change the language preference
    self.client.post('/preferences/', {'pagesize': 100, 'language': language, 'theme': 'orange'})

    # Initial size
    countBuffer = input.models.Buffer.objects.count()
    countCalendarBucket = input.models.CalendarBucket.objects.count()
    countCalendar = input.models.Calendar.objects.count()
    countCustomer = input.models.Customer.objects.count()
    countDemand = input.models.Demand.objects.count()
    countOperationMaterial = input.models.OperationMaterial.objects.count()
    countItem = input.models.Item.objects.count()
    countItemSupplier = input.models.ItemSupplier.objects.count()
    countItemDistribution = input.models.ItemDistribution.objects.count()
    countOperationResource = input.models.OperationResource.objects.count()
    countLocation = input.models.Location.objects.count()
    countPurchaseOrder = input.models.PurchaseOrder.objects.count()
    countDistributionOrder = input.models.DistributionOrder.objects.count()
    countManufacturingOrder = input.models.ManufacturingOrder.objects.count()
    countOperation = input.models.Operation.objects.count()
    countResourceSkill = input.models.ResourceSkill.objects.count()
    countResource = input.models.Resource.objects.count()
    countSetupMatrix = input.models.SetupMatrix.objects.count()
    countSkill = input.models.Skill.objects.count()
    countSubOperation = input.models.SubOperation.objects.count()
    countSupplier = input.models.Supplier.objects.count()
    countBucket = common.models.Bucket.objects.count()
    countBucketDetail = common.models.BucketDetail.objects.count()
    countParameter = common.models.Parameter.objects.count()
    self.assertTrue(countDemand > 0)

    # Export workbook
    response = self.client.post('/execute/launch/exportworkbook/', {
       'entities': [
          'input.demand', 'input.item', 'input.customer', 'input.location', 'input.buffer',
          'input.resource', 'input.skill', 'input.resourceskill', 'input.setupmatrix',
          'input.purchaseorder', 'input.supplier', 'input.itemsupplier',
          'input.distributionorder', 'input.itemdistribution', 'input.operationmaterial',
          'input.manufacturingorder', 'input.calendar', 'input.calendarbucket',
          'input.operation', 'input.operationplanmaterial', 'input.operationresource',
          'input.suboperation', 'common.parameter', 'common.bucket', 'common.bucketdetail',
          ]
       })
    with open("workbook.xlsx", 'wb') as f:
      f.write(response.content)

    # Erase the database
    management.call_command('empty')
    self.assertEqual(input.models.Buffer.objects.count(), 0)
    self.assertEqual(input.models.CalendarBucket.objects.count(), 0)
    self.assertEqual(input.models.Calendar.objects.count(), 0)
    self.assertEqual(input.models.Customer.objects.count(), 0)
    self.assertEqual(input.models.Demand.objects.count(), 0)
    self.assertEqual(input.models.OperationMaterial.objects.count(), 0)
    self.assertEqual(input.models.Item.objects.count(), 0)
    self.assertEqual(input.models.ItemDistribution.objects.count(), 0)
    self.assertEqual(input.models.ItemSupplier.objects.count(), 0)
    self.assertEqual(input.models.OperationResource.objects.count(), 0)
    self.assertEqual(input.models.Location.objects.count(), 0)
    self.assertEqual(input.models.PurchaseOrder.objects.count(), 0)
    self.assertEqual(input.models.DistributionOrder.objects.count(), 0)
    self.assertEqual(input.models.ManufacturingOrder.objects.count(), 0)
    self.assertEqual(input.models.OperationPlanResource.objects.count(), 0)
    self.assertEqual(input.models.OperationPlanMaterial.objects.count(), 0)
    self.assertEqual(input.models.Operation.objects.count(), 0)
    self.assertEqual(input.models.ResourceSkill.objects.count(), 0)
    self.assertEqual(input.models.Resource.objects.count(), 0)
    self.assertEqual(input.models.SetupMatrix.objects.count(), 0)
    self.assertEqual(input.models.Skill.objects.count(), 0)
    self.assertEqual(input.models.SubOperation.objects.count(), 0)
    self.assertEqual(input.models.Supplier.objects.count(), 0)
    self.assertEqual(common.models.Bucket.objects.count(), 0)
    self.assertEqual(common.models.BucketDetail.objects.count(), 0)
    self.assertEqual(common.models.Parameter.objects.count(), 0)

    # Import the same workbook again
    with open("workbook.xlsx", 'rb') as f:
      response = self.client.post('/execute/launch/importworkbook/', {'spreadsheet': f})
      if not isinstance(response, StreamingHttpResponse):
        raise Exception("expected a streaming response")
      for rec in response.streaming_content:
        rec
      self.assertEqual(response.status_code, 200)

    # Verify the new content is identical
    self.assertEqual(input.models.Buffer.objects.count(), countBuffer)
    self.assertEqual(input.models.CalendarBucket.objects.count(), countCalendarBucket)
    self.assertEqual(input.models.Calendar.objects.count(), countCalendar)
    self.assertEqual(input.models.Customer.objects.count(), countCustomer)
    self.assertEqual(input.models.Demand.objects.count(), countDemand)
    self.assertEqual(input.models.OperationMaterial.objects.count(), countOperationMaterial)
    self.assertEqual(input.models.Item.objects.count(), countItem)
    self.assertEqual(input.models.ItemDistribution.objects.count(), countItemDistribution)
    self.assertEqual(input.models.ItemSupplier.objects.count(), countItemSupplier)
    self.assertEqual(input.models.OperationResource.objects.count(), countOperationResource)
    self.assertEqual(input.models.Location.objects.count(), countLocation)
    self.assertEqual(input.models.PurchaseOrder.objects.count(), countPurchaseOrder)
    self.assertEqual(input.models.DistributionOrder.objects.count(), countDistributionOrder)
    self.assertEqual(input.models.ManufacturingOrder.objects.count(), countManufacturingOrder)
    self.assertEqual(input.models.Operation.objects.count(), countOperation)
    self.assertEqual(input.models.ResourceSkill.objects.count(), countResourceSkill)
    self.assertEqual(input.models.Resource.objects.count(), countResource)
    self.assertEqual(input.models.SetupMatrix.objects.count(), countSetupMatrix)
    self.assertEqual(input.models.Skill.objects.count(), countSkill)
    self.assertEqual(input.models.SubOperation.objects.count(), countSubOperation)
    self.assertEqual(input.models.Supplier.objects.count(), countSupplier)
    self.assertEqual(common.models.Bucket.objects.count(), countBucket)
    self.assertEqual(common.models.BucketDetail.objects.count(), countBucketDetail)
    self.assertEqual(common.models.Parameter.objects.count(), countParameter)

  def test_workbook_english(self):
    self.run_workbook("en")

  def test_workbook_chinese(self):
    self.run_workbook("zh-cn")

  def test_workbook_dutch(self):
    self.run_workbook("nl")

  def test_workbook_french(self):
    self.run_workbook("fr")

  def test_workbook_japanese(self):
    self.run_workbook("ja")

  def test_workbook_portuguese(self):
    self.run_workbook("pt")

  def test_workbook_brazilian_portuguese(self):
    self.run_workbook("pt-br")


class freppleREST(APITestCase):


  fixtures = ["demo"]

  #Default request format is multipart
  factory = APIRequestFactory(enforce_csrf_checks=True)

  def setUp(self):
    # Login
    self.client = APIClient()
    self.client.login(username='admin', password='admin')

  # REST API framework
  def test_api_listpages_getapi(self):
    response = self.client.get('/api/')
    self.assertEqual(response.status_code, 200)

    response = self.client.get('/api/input/demand/')
    self.assertEqual(response.status_code, 200)

    response = self.client.get('/api/input/item/')
    self.assertEqual(response.status_code, 200)

    response = self.client.get('/api/input/customer/')
    self.assertEqual(response.status_code, 200)

    response = self.client.get('/api/input/location/')
    self.assertEqual(response.status_code, 200)

    response = self.client.get('/api/input/buffer/')
    self.assertEqual(response.status_code, 200)

    response = self.client.get('/api/input/resource/')
    self.assertEqual(response.status_code, 200)

    response = self.client.get('/api/input/skill/')
    self.assertEqual(response.status_code, 200)

    response = self.client.get('/api/input/resourceskill/')
    self.assertEqual(response.status_code, 200)

    response = self.client.get('/api/input/setupmatrix/')
    self.assertEqual(response.status_code, 200)

    response = self.client.get('/api/input/purchaseorder/')
    self.assertEqual(response.status_code, 200)

    response = self.client.get('/api/input/supplier/')
    self.assertEqual(response.status_code, 200)

    response = self.client.get('/api/input/itemsupplier/')
    self.assertEqual(response.status_code, 200)

    response = self.client.get('/api/input/distributionorder/')
    self.assertEqual(response.status_code, 200)

    response = self.client.get('/api/input/itemdistribution/')
    self.assertEqual(response.status_code, 200)

    response = self.client.get('/api/input/manufacturingorder/')
    self.assertEqual(response.status_code, 200)

    response = self.client.get('/api/input/calendar/')
    self.assertEqual(response.status_code, 200)

    response = self.client.get('/api/input/calendarbucket/')
    self.assertEqual(response.status_code, 200)

    response = self.client.get('/api/input/operation/')
    self.assertEqual(response.status_code, 200)

    response = self.client.get('/api/input/operationmaterial/')
    self.assertEqual(response.status_code, 200)

    response = self.client.get('/api/input/operationresource/')
    self.assertEqual(response.status_code, 200)

    response = self.client.get('/api/input/suboperation/')
    self.assertEqual(response.status_code, 200)

    response = self.client.get('/api/common/parameter/')
    self.assertEqual(response.status_code, 200)

    response = self.client.get('/api/common/bucket/')
    self.assertEqual(response.status_code, 200)

    response = self.client.get('/api/common/bucketdetail/')
    self.assertEqual(response.status_code, 200)


    #Demand tests
  def test_api_demand(self):
    response = self.client.get('/api/input/demand/')
    self.assertEqual(response.status_code, 200)
    response = self.client.options('/api/input/demand/')
    self.assertEqual(response.status_code, 200)
    recordsnumber = input.models.Demand.objects.count()
    data = {
        "name": "Order UFO 25",
        "description": None,
        "category": None,
        "subcategory": None,
        "item": "product",
        "customer": "Customer near factory 1",
        "location": "factory 1",
        "due": "2013-12-01T00:00:00",
        "status": "closed",
        "operation": None,
        "quantity": "110.0000",
        "priority": 1,
        "minshipment": None,
        "maxlateness": None
    }
    response = self.client.post('/api/input/demand/', data, format='json')
    self.assertEqual(response.status_code, 201)
    self.assertEqual(input.models.Demand.objects.count(), recordsnumber + 1)
    self.assertEqual(input.models.Demand.objects.filter(name='Order UFO 25').count(), 1)
    data = {
        "name": "Order UFO 26",
        "description": None,
        "category": None,
        "subcategory": None,
        "item": "product",
        "customer": "Customer near factory 1",
        "location": "factory 1",
        "due": "2013-12-01T00:00:00",
        "status": "closed",
        "operation": None,
        "quantity": "220.0000",
        "priority": 1,
        "minshipment": None,
        "maxlateness": None
    }
    response = self.client.post('/api/input/demand/', data, format='json')
    self.assertEqual(response.status_code, 201)
    self.assertEqual(input.models.Demand.objects.count(), recordsnumber + 2)
    self.assertEqual(input.models.Demand.objects.filter(name='Order UFO 26').count(), 1)

    data = [{
        "name": "Order UFO 27",
        "description": None,
        "category": "TEST DELETE",
        "subcategory": None,
        "item": "product",
        "location": "factory 1",
        "customer": "Customer near factory 1",
        "due": "2013-12-01T00:00:00",
        "status": "closed",
        "operation": None,
        "quantity": "220.0000",
        "priority": 1,
        "minshipment": None,
        "maxlateness": None
    }, {
        "name": "Order UFO 28",
        "description": None,
        "category": "TEST DELETE",
        "subcategory": None,
        "item": "product",
        "customer": "Customer near factory 1",
        "location": "factory 1",
        "due": "2013-12-01T00:00:00",
        "status": "closed",
        "operation": None,
        "quantity": "220.0000",
        "priority": 1,
        "minshipment": None,
        "maxlateness": None
    }]
    response = self.client.post('/api/input/demand/', data, format='json')
    self.assertEqual(response.status_code, 201)
    self.assertEqual(input.models.Demand.objects.count(), recordsnumber + 4)
    self.assertEqual(input.models.Demand.objects.filter(category='TEST DELETE').count(), 2)

    # Demand GET MULTIPART
    response = self.client.get('/api/input/demand/Order UFO 25/')
    self.assertEqual(response.status_code, 200)
    self.assertEqual(input.models.Demand.objects.filter(name='Order UFO 25').count(), 1)
    # Demand OPTIONS
    response = self.client.options('/api/input/demand/Order UFO 25/')
    self.assertEqual(response.status_code, 200)
    # Demand GET JSON tests
    response = self.client.get('/api/input/demand/Order UFO 26/', format='json')
    self.assertEqual(response.status_code, 200)
    self.assertEqual(input.models.Demand.objects.filter(name='Order UFO 26').count(), 1)
    # Demand PUT MULTIPART tests
    data = {
        "name": "Order UFO 25",
        "description": "Put multipart",
        "category": None,
        "subcategory": None,
        "item": "product",
        "customer": "Customer near factory 1",
        "location": "factory 1",
        "due": "2013-12-01T00:00:00",
        "status": "closed",
        "operation": None,
        "quantity": "110.0000",
        "priority": 1,
        "minshipment": None,
        "maxlateness": None
    }
    response = self.client.put('/api/input/demand/Order UFO 25/', data, format='json')
    self.assertEqual(response.status_code, 200)
    self.assertEqual(input.models.Demand.objects.count(), 18)
    self.assertEqual(input.models.Demand.objects.filter(description='Put multipart').count(), 1)
    # Demand PUT JSON tests
    data = {
        "name": "Order UFO 26",
        "description": "Put json",
        "category": None,
        "subcategory": None,
        "item": "product",
        "customer": "Customer near factory 1",
        "location": "factory 1",
        "due": "2013-12-01T00:00:00",
        "status": "closed",
        "operation": None,
        "quantity": "110.0000",
        "priority": 1,
        "minshipment": None,
        "maxlateness": None
    }
    response = self.client.put('/api/input/demand/Order UFO 26/', data, format='json')
    self.assertEqual(response.status_code, 200)
    self.assertEqual(input.models.Demand.objects.count(), recordsnumber + 4)
    self.assertEqual(input.models.Demand.objects.filter(description='Put json').count(), 1)
    # Demand PUT FORM tests
    data = {
        "name": "Order UFO 26",
        "description": "Put form",
        "category": None,
        "subcategory": None,
        "item": "product",
        "customer": "Customer near factory 1",
        "location": "factory 1",
        "due": "2013-12-01T00:00:00",
        "status": "closed",
        "operation": None,
        "quantity": "110.0000",
        "priority": 1,
        "minshipment": None,
        "maxlateness": None
    }
    response = self.client.put('/api/input/demand/Order UFO 26/', data, format='json')
    self.assertEqual(response.status_code, 200)
    self.assertEqual(input.models.Demand.objects.count(), recordsnumber + 4)
    self.assertEqual(input.models.Demand.objects.filter(description='Put form').count(), 1)

    # Demand DELETE tests
    response = self.client.delete('/api/input/demand/Order UFO 26/', format='form')
    self.assertEqual(response.status_code, 204)
    response = self.client.delete('/api/input/demand/Order UFO 25/', format='json')
    self.assertEqual(response.status_code, 204)
    response = self.client.delete('/api/input/demand/Demand 01/', format='api')
    self.assertEqual(response.status_code, 204)
    response = self.client.delete('/api/input/demand/?category=TEST DELETE', format='api')
    self.assertEqual(response.status_code, 204)
    self.assertEqual(input.models.Customer.objects.filter(category='TEST DELETE').count(), 0)

  def test_api_customer(self):
    response = self.client.get('/api/input/customer/')
    self.assertEqual(response.status_code, 200)
    recordsnumber = input.models.Customer.objects.count()
    self.assertEqual(input.models.Customer.objects.count(), 3) # Different between Enterprise Edition and Community Edition
    response = self.client.options('/api/input/customer/')
    self.assertEqual(response.status_code, 200)
    data = {
        "name": "Customer near Area 51"
    }
    response = self.client.post('/api/input/customer/', data)
    self.assertEqual(response.status_code, 201)
    self.assertEqual(input.models.Customer.objects.count(), recordsnumber + 1)
    self.assertEqual(input.models.Customer.objects.filter(name='Customer near Area 51').count(), 1)
    data = {
        "name": "Customer near Area 52"
    }
    response = self.client.post('/api/input/customer/', data, format='json')
    self.assertEqual(response.status_code, 201)
    self.assertEqual(input.models.Customer.objects.count(), recordsnumber + 2)
    self.assertEqual(input.models.Customer.objects.filter(name='Customer near Area 52').count(), 1)
    data = [{
      "name": "Customer near Area 99",
      "source": "TEST DELETE"
      }, {
      "name": "Customer near Area 100",
      "source": "TEST DELETE"
    }]
    response = self.client.post('/api/input/customer/', data, format='json')
    self.assertEqual(response.status_code, 201)
    self.assertEqual(input.models.Customer.objects.count(), recordsnumber + 4)
    self.assertEqual(input.models.Customer.objects.filter(source='TEST DELETE').count(), 2)

    # Customer GET MULTIPART
    response = self.client.get('/api/input/customer/Customer near Area 51/')
    self.assertEqual(response.status_code, 200)
    self.assertEqual(input.models.Customer.objects.filter(name='Customer near Area 51').count(), 1)
    # Customer OPTIONS
    response = self.client.options('/api/input/customer/Customer near Area 51/')
    self.assertEqual(response.status_code, 200)
    # Customer GET JSON tests
    response = self.client.get('/api/input/customer/Customer near Area 52/', format='json')
    self.assertEqual(response.status_code, 200)
    self.assertEqual(input.models.Customer.objects.filter(name='Customer near Area 52').count(), 1)
    # Customer PUT MULTIPART tests
    data = {
      "name": "Customer near Area 51",
      "description": "Patch multipart"
    }
    response = self.client.patch('/api/input/customer/Customer near Area 51/', data)
    self.assertEqual(response.status_code, 200)
    self.assertEqual(input.models.Customer.objects.count(), recordsnumber + 4)
    self.assertEqual(input.models.Customer.objects.filter(description='Patch multipart').count(), 1)
    # Customer PUT JSON tests
    data = {
      "name": "Customer near Area 52",
      "description": "Patch json"
    }
    response = self.client.patch('/api/input/customer/Customer near Area 52/', data, format='json')
    self.assertEqual(response.status_code, 200)
    self.assertEqual(input.models.Customer.objects.count(), recordsnumber + 4)
    self.assertEqual(input.models.Customer.objects.filter(description='Patch json').count(), 1)

    # Customer PUT FORM tests
    data = {
        "name": "Customer near Area 52",
        "description": "Patch json",
        "category": None,
        "subcategory": None,
        "source": "Put json",
        "lastmodified": "2015-12-04T10:18:40.048861"
    }

    response = self.client.patch('/api/input/customer/Customer near Area 52/', data, format='json')
    self.assertEqual(response.status_code, 200)
    self.assertEqual(input.models.Customer.objects.count(), recordsnumber + 4)
    self.assertEqual(input.models.Customer.objects.filter(source='Put json').count(), 1)

    # Customer bulk filtered GET test
    response = self.client.get('/api/input/customer/?name__contains=Area', data, format='json')
    self.assertEqual(response.status_code, 200)
    self.assertEqual(input.models.Customer.objects.filter(name__contains='Area').count(), 4)

    # Customer DELETE tests
    # Bulk "contains" filtered DELETE
    response = self.client.delete('/api/input/customer/?name__contains=Area 5', format='form')
    self.assertEqual(response.status_code, 204)
    self.assertEqual(input.models.Customer.objects.filter(name__contains='Area').count(), 2)
    # Single DELETE
    response = self.client.delete('/api/input/customer/Customer near factory 1/', format='api')
    self.assertEqual(response.status_code, 204)
    # Bulk filtered DELETE
    response = self.client.delete('/api/input/customer/?source=TEST DELETE', format='json')
    self.assertEqual(response.status_code, 204)
    self.assertEqual(input.models.Customer.objects.filter(source='TEST DELETE').count(), 0)
