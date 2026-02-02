#
# Copyright (C) 2007-2016 by frePPLe bv
#
# Permission is hereby granted, free of charge, to any person obtaining
# a copy of this software and associated documentation files (the
# "Software"), to deal in the Software without restriction, including
# without limitation the rights to use, copy, modify, merge, publish,
# distribute, sublicense, and/or sell copies of the Software, and to
# permit persons to whom the Software is furnished to do so, subject to
# the following conditions:
#
# The above copyright notice and this permission notice shall be
# included in all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND,
# EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF
# MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND
# NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE
# LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION
# OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION
# WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.
#

import os
from shutil import rmtree
import tempfile

from django.core import management
from django.db import DEFAULT_DB_ALIAS
from django.test import TransactionTestCase

from freppledb.input.models import ManufacturingOrder, PurchaseOrder, DistributionOrder
from freppledb.common.models import Notification, User, Comment
from freppledb.common.utils import get_databases


class execute_with_commands(TransactionTestCase):
    fixtures = ["demo", "initial"]

    def setUp(self):
        # Make sure the test database is used
        os.environ["FREPPLE_TEST"] = "YES"
        # Export and import from a temporary folder to avoid interfering with
        # existing data files
        self.datafolder = tempfile.mkdtemp()
        get_databases()[DEFAULT_DB_ALIAS]["FILEUPLOADFOLDER"] = self.datafolder
        if not User.objects.filter(username="admin").count():
            User.objects.create_superuser("admin", "your@company.com", "admin")
        self.client.login(username="admin", password="admin")
        super().setUp()

    def tearDown(self):
        rmtree(self.datafolder)
        Notification.wait()
        del os.environ["FREPPLE_TEST"]
        super().tearDown()

    def test_exportimportfromfolder(self):

        # Try the execute screen and all task widgets
        response = self.client.get("/execute/")
        self.assertEqual(response.status_code, 200)

        self.assertEqual(ManufacturingOrder.objects.count(), 1)
        self.assertEqual(PurchaseOrder.objects.count(), 4)
        self.assertEqual(DistributionOrder.objects.count(), 0)

        # The exporttofolder filters by status so the count must also filter
        countMO = ManufacturingOrder.objects.filter(status="proposed").count()
        countPO = PurchaseOrder.objects.filter(status="proposed").count()
        countDO = DistributionOrder.objects.filter(status="proposed").count()

        management.call_command("exporttofolder")

        ManufacturingOrder.objects.all().delete()
        DistributionOrder.objects.all().delete()
        PurchaseOrder.objects.all().delete()
        Comment.objects.all().delete()

        self.assertEqual(DistributionOrder.objects.count(), 0)
        self.assertEqual(PurchaseOrder.objects.count(), 0)
        self.assertEqual(ManufacturingOrder.objects.count(), 0)
        self.assertEqual(Comment.objects.count(), 0)

        # Move export files to the import folder
        for file in [
            "purchaseorder.csv.gz",
            "distributionorder.csv.gz",
            "manufacturingorder.csv.gz",
        ]:
            os.rename(
                os.path.join(self.datafolder, "export", file),
                os.path.join(self.datafolder, file),
            )

        management.call_command("importfromfolder")

        self.assertEqual(DistributionOrder.objects.count(), countDO)
        self.assertEqual(PurchaseOrder.objects.count(), countPO)
        self.assertEqual(ManufacturingOrder.objects.count(), countMO)
        self.assertEqual(Comment.objects.count(), 0)
