#
# Copyright (C) 2007-2016 by frePPLe bvba
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
import unittest

from django.conf import settings
from django.core import management
from django.db import DEFAULT_DB_ALIAS
from django.test import TransactionTestCase
from django.test.utils import override_settings

import freppledb.input as input


@override_settings(INSTALLED_APPS=settings.INSTALLED_APPS + ('django.contrib.sessions',))
class execute_with_commands(TransactionTestCase):

  fixtures = ["demo"]

  def setUp(self):
    # Make sure the test database is used
    os.environ['FREPPLE_TEST'] = "YES"

  @unittest.skipUnless(
    os.path.isdir(settings.DATABASES[DEFAULT_DB_ALIAS].get('FILEUPLOADFOLDER', '')),
    "Requires FILEUPLOADFOLDER to be configured"
    )

  def test_exportimportfromfolder(self):

    # Run frePPLe on the test database.
    management.call_command('frepple_run', plantype=1, constraint=15, env='supply')

    self.assertTrue(input.models.ManufacturingOrder.objects.count() > 30)
    self.assertTrue(input.models.PurchaseOrder.objects.count() > 20)
    self.assertTrue(input.models.DistributionOrder.objects.count() > 0)

    #the exporttofolder filters by status so the count must also filter
    countMO = input.models.ManufacturingOrder.objects.filter(status = 'proposed').count()
    countPO = input.models.PurchaseOrder.objects.filter(status = 'proposed').count()
    countDO = input.models.DistributionOrder.objects.filter(status = 'proposed').count()

    management.call_command('frepple_exporttofolder', )

    input.models.ManufacturingOrder.objects.all().delete()
    input.models.DistributionOrder.objects.all().delete()
    input.models.PurchaseOrder.objects.all().delete()

    self.assertEqual(input.models.DistributionOrder.objects.count(), 0)
    self.assertEqual(input.models.PurchaseOrder.objects.count(),0)
    self.assertEqual(input.models.ManufacturingOrder.objects.count(), 0)

    management.call_command('frepple_importfromfolder', )
    self.assertEqual(input.models.DistributionOrder.objects.count(), countDO)
    self.assertEqual(input.models.PurchaseOrder.objects.count(), countPO)
    self.assertEqual(input.models.ManufacturingOrder.objects.count(), countMO)

