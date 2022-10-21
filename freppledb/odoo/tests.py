#
# Copyright (C) 2022 by frePPLe bv
#
# This library is free software; you can redistribute it and/or modify it
# under the terms of the GNU Affero General Public License as published
# by the Free Software Foundation; either version 3 of the License, or
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
from unittest import skipUnless

from django.conf import settings
from django.core import management
from django.test import TransactionTestCase
from django.contrib.auth.models import Group

from freppledb.common.models import User
from freppledb.input.models import Item, PurchaseOrder, ManufacturingOrder


@skipUnless("freppledb.odoo" in settings.INSTALLED_APPS, "App not activated")
class OdooTest(TransactionTestCase):
    def setUp(self):
        os.environ["FREPPLE_TEST"] = "YES"
        if not User.objects.filter(username="admin").count():
            User.objects.create_superuser("admin", "your@company.com", "admin")
        management.call_command("odoo_container", "--full", "--verbosity", "0")
        # Use the next line to avoid full rebuild
        # management.call_command("odoo_container",  "--verbosity", "0")
        super().setUp()

    def tearDown(self):
        # Comment out the next line to avoid deleting the container at the end of the test
        # management.call_command("odoo_container", "--destroy", "--verbosity", "0")
        del os.environ["FREPPLE_TEST"]
        super().tearDown()

    def test_odoo_e2e(self):
        # Import odoo data
        self.assertEqual(Item.objects.all().count(), 0)
        management.call_command("odoo_import")
        self.assertGreater(Item.objects.all().count(), 0)

        # Check user sync
        self.assertEqual(Group.objects.filter(name__icontains="odoo").count(), 1)
        self.assertEqual(User.objects.get(username="admin").groups.all().count(), 1)

        # Check input data
        self.assertEqual(Item.objects.all().exclude(name__contains="[").count(), 7)
        self.assertEqual(
            PurchaseOrder.objects.all()
            .exclude(item__name__contains="[")
            .filter(status="confirmed")
            .count(),
            0,  # TODO add draft and confirmed MO (with reservations & consumptions in demo dataset)
        )
        self.assertEqual(
            ManufacturingOrder.objects.all()
            .exclude(item__name__contains="[")
            .filter(status="confirmed")
            .count(),
            0,  # TODO add draft and confirmed PO in demo dataset
        )
        self.assertEqual(
            ManufacturingOrder.objects.all().filter(status="proposed").count(),
            0,
        )
        self.assertEqual(
            PurchaseOrder.objects.all().filter(status="proposed").count(),
            0,
        )

        # Generate plan
        management.call_command(
            "runplan", plantype=1, constraint=15, env="supply,fcst,invplan"
        )

        # Check plan results
        self.assertGreater(
            ManufacturingOrder.objects.all()
            .exclude(item__name__contains="[")
            .filter(status="proposed")
            .count(),
            1,
        )
        self.assertGreater(
            PurchaseOrder.objects.all()
            .exclude(item__name__contains="[")
            .filter(status="proposed")
            .count(),
            1,
        )
