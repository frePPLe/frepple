#
# Copyright (C) 2022 by frePPLe bv
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

from datetime import datetime
import json
import os
from unittest import skipUnless
import xmlrpc.client

from django.conf import settings
from django.core import management
from django.db.models import F
from django.test import TransactionTestCase
from django.contrib.auth.models import Group

from freppledb.common.models import User
from freppledb.input.models import (
    Item,
    PurchaseOrder,
    ManufacturingOrder,
    Demand,
    WorkOrder,
)
from .utils import getOdooVersion


@skipUnless("freppledb.odoo" in settings.INSTALLED_APPS, "App not activated")
class OdooTest(TransactionTestCase):
    def setUp(self):
        os.environ["FREPPLE_TEST"] = "YES"
        if not User.objects.filter(username="admin").count():
            User.objects.create_superuser("admin", "your@company.com", "admin")
        management.call_command(
            "odoo_container", "--full", "--nolog", "--verbosity", "0"
        )
        # Use the next line to avoid full rebuild
        # management.call_command("odoo_container",  "--verbosity", "0")
        self.client.login(username="admin", password="admin")
        super().setUp()

    def tearDown(self):
        # Comment out the next line to avoid deleting the container at the end of the test
        # management.call_command("odoo_container", "--destroy", "--verbosity", "0")
        del os.environ["FREPPLE_TEST"]
        super().tearDown()

    def odooRPCinit(self, db=None, username=None, password=None, url=None):
        """
        Initialize an XMLRPC connection to the odoo instance
        """
        self.odooversion = getOdooVersion()
        self.db = db or "odoo_frepple_%s" % self.odooversion
        self.url = url or "http://localhost:8069"
        self.username = username or "admin"
        self.password = password or "admin"
        common = xmlrpc.client.ServerProxy("{}/xmlrpc/2/common".format(self.url))
        self.uid = common.authenticate(self.db, self.username, self.password, {})
        self.models = xmlrpc.client.ServerProxy("{}/xmlrpc/2/object".format(self.url))

    def odooRPC(self, odoo_model, odoo_filter=None, odoo_options=None, odoo_fields=None):
        if odoo_filter is None:
            odoo_filter = []
        if odoo_options is None:
            odoo_options = {}
        ids = self.models.execute_kw(
            self.db,
            self.uid,
            self.password,
            odoo_model,
            "search",
            [odoo_filter],
            odoo_options,
        )
        return self.models.execute_kw(
            self.db,
            self.uid,
            self.password,
            odoo_model,
            "read",
            [ids],
            {"fields": odoo_fields} if odoo_fields else {},
        )

    def odooRPCAction(
        self,
        odoo_model,
        action,
        record_ids,  # a list of record ids on which the action should be execued
    ):
        return self.models.execute_kw(
            self.db,
            self.uid,
            self.password,
            odoo_model,
            action,
            [record_ids],
        )

    def updateUserTimeZone(self):
        admin = self.odooRPC(
            "res.users",
            [("login", "=", "admin")],
            {},
            [
                "id",
            ],
        )[0]
        self.models.execute_kw(
            self.db,
            self.uid,
            self.password,
            "res.users",
            "write",
            [
                [
                    admin["id"],
                ],
                {"tz": "UTC"},
            ],
        )

    def test_odoo_e2e(self):
        # Import odoo data
        self.assertEqual(Item.objects.all().count(), 0)
        management.call_command(
            "runplan",
            plantype=1,
            constraint="capa,mfg_lt,po_lt",
            env="odoo_read_1,fcst,invplan,supply,odoo_write_1",
        )
        self.assertGreater(Item.objects.all().count(), 0)

        # Check user sync
        self.assertEqual(Group.objects.filter(name__icontains="odoo").count(), 1)
        self.assertEqual(User.objects.get(username="admin").groups.all().count(), 1)

        # A list with the items we use in our demo
        odoo_version = int(getOdooVersion())
        frepple_items = [
            "chair",
            "chair leg",
            "cushion",
            "varnish",
            "varnished chair",
            "wooden beam - 木头",
        ]
        if odoo_version >= 18:
            # Kitting BOM is present in v18 onwards
            frepple_items.append("DIY varnished chair")

        # Check input data
        self.assertEqual(
            Item.objects.filter(name__in=frepple_items).count(),
            len(frepple_items),
        )
        po_list = PurchaseOrder.objects.filter(
            item__name__in=frepple_items,
            status="confirmed",
        )
        self.assertEqual(po_list.count(), 2)
        po = po_list[0]
        self.assertEqual(po.quantity, 15)
        # TODO receipt date changes between runs, making it difficult to compare here
        # self.assertEqual(po.receipt_date, datetime.today() + timedelta)
        self.assertEqual(
            ManufacturingOrder.objects.filter(
                item__name__in=frepple_items,
                status="confirmed",
            ).count(),
            0,  # TODO add draft and confirmed PO in demo dataset
        )
        self.assertEqual(
            ManufacturingOrder.objects.all()
            .filter(status="proposed")
            .filter(source="odoo_1")
            .count(),
            0,
        )
        self.assertEqual(
            PurchaseOrder.objects.all()
            .filter(status="proposed")
            .filter(source="odoo_1")
            .count(),
            0,
        )
        self.assertEqual(
            Demand.objects.all()
            .filter(item__name__in=frepple_items, status="open")
            .count(),
            {16: 1, 17: 10, 18: 10, 19: 10}[odoo_version],
        )

        if odoo_version >= 15 and odoo_version < 19:
            # Work order level integration is only available from odoo 15 onwards
            self.assertEqual(
                ManufacturingOrder.objects.all()
                .filter(status="approved", quantity=8)
                .count(),
                1,
            )
            self.assertEqual(
                WorkOrder.objects.all().filter(status="approved", quantity=8).count(),
                2,
            )
        elif odoo_version >= 19:
            # One MO is a subcontracted MO
            self.assertEqual(
                ManufacturingOrder.objects.all().filter(status="approved").count(),
                5,
            )
            self.assertEqual(
                WorkOrder.objects.all().filter(status="approved").count(),
                6,
            )

        # Check plan results
        proposed_mo = (
            ManufacturingOrder.objects.filter(
                item__name__in=frepple_items, status="proposed", owner__isnull=True
            )
            .order_by("startdate", "operation")
            .first()
        )
        proposed_po = (
            PurchaseOrder.objects.filter(
                item__name__in=frepple_items, status="proposed"
            )
            .order_by("startdate", "supplier", "item")
            .first()
        )
        self.assertIsNotNone(proposed_mo)
        self.assertIsNotNone(proposed_po)

        # Update user time zone to UTC Approve proposed transactions
        self.odooRPCinit()
        self.updateUserTimeZone()
        response = self.client.post(
            "/erp/upload/",
            json.dumps(
                [
                    {
                        "reference": proposed_mo.reference,
                        "type": "MO",
                        "quantity": float(proposed_mo.quantity),
                        "enddate": datetime.strftime(
                            proposed_mo.enddate, "%Y-%m-%dT%H:%M:%S"
                        ),
                    }
                ]
            ),
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 200)
        response = self.client.post(
            "/erp/upload/",
            json.dumps(
                [
                    {
                        "reference": proposed_po.reference,
                        "type": "PO",
                        "quantity": float(proposed_po.quantity),
                        "enddate": datetime.strftime(
                            proposed_po.enddate, "%Y-%m-%dT%H:%M:%S"
                        ),
                    }
                ]
            ),
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 200)

        # Check new status
        approved_mo = ManufacturingOrder.objects.get(pk=proposed_mo.reference)
        self.assertEqual(approved_mo.status, "approved")
        approved_po = PurchaseOrder.objects.get(pk=proposed_po.reference)
        self.assertEqual(approved_po.status, "approved")

        # Check results in odoo
        cnt = 0
        for odoo_mo in self.odooRPC(
            "mrp.production", [("origin", "=", "frePPLe"), ("state", "=", "draft")]
        ):
            self.assertEqual(approved_mo.quantity, odoo_mo["product_qty"])
            self.assertEqual(
                approved_mo.startdate.strftime("%Y-%m-%d %H:%M:%S"),
                odoo_mo.get(
                    "date_planned_start", odoo_mo.get("date_start")
                ),  # Field name changed in v17
            )
            self.assertTrue(odoo_mo["bom_id"][1] in approved_mo.operation.name)
            cnt += 1
        self.assertEqual(cnt, 1)
        cnt = 0
        for odoo_poline in self.odooRPC(
            "purchase.order.line",
            [("order_id.origin", "=", "frePPLe"), ("order_id.state", "=", "draft")],
        ):
            self.assertEqual(approved_po.quantity, odoo_poline["product_qty"])
            self.assertEqual(approved_po.item.name, odoo_poline["product_id"][1])
            self.assertEqual(
                approved_po.enddate.strftime("%Y-%m-%d %H:%M:%S"),
                odoo_poline["date_planned"],
            )
            cnt += 1
        self.assertEqual(cnt, 1)

        # Recommendations
        count_purchase = 0
        count_reschedule = 0
        count_produce = 0
        count_late_delivery = 0

        # store the recommendaion to approve them
        purchase_rec = 0
        reschedule_rec = 0
        produce_rec = 0

        if odoo_version >= 19:
            for odoo_rec in self.odooRPC(
                "frepple.recommendation",
                [],
                {},
                ["id", "type", "quantity", "product_id"],
            ):
                if odoo_rec["type"] == "purchase":
                    count_purchase += 1
                    if not purchase_rec:
                        purchase_rec = odoo_rec
                elif odoo_rec["type"] == "reschedule":
                    count_reschedule += 1
                    if not reschedule_rec:
                        reschedule_rec = odoo_rec
                elif odoo_rec["type"] == "produce":
                    count_produce += 1
                    if not produce_rec:
                        produce_rec = odoo_rec
                elif odoo_rec["type"] == "latedelivery":
                    count_late_delivery += 1
            self.assertGreaterEqual(count_purchase, 6)
            self.assertGreaterEqual(count_reschedule, 1)
            self.assertGreaterEqual(count_produce, 0)
            self.assertGreaterEqual(count_late_delivery, 9)

            # approve a purchase, a reschedule and a produce
            self.odooRPCAction(
                "frepple.recommendation",
                "action_approve",
                [purchase_rec["id"], reschedule_rec["id"], produce_rec["id"]],
            )

            # Make sure they have been correctly created/update
            cnt = 0
            for odoo_poline in self.odooRPC(
                "purchase.order.line",
                [("order_id.origin", "=", "frePPLe"), ("order_id.state", "=", "draft")],
                {"limit": 1, "order": "create_date desc"},
            ):
                self.assertEqual(odoo_poline["product_qty"], purchase_rec["quantity"])
                self.assertEqual(
                    odoo_poline["product_id"][0], purchase_rec["product_id"][0]
                )
                cnt += 1
            self.assertEqual(cnt, 1)
            cnt = 0
            for odoo_moline in self.odooRPC(
                "mrp.production",
                [("origin", "=", "frePPLe"), ("state", "=", "draft")],
                {"limit": 1, "order": "create_date desc"},
            ):
                self.assertEqual(odoo_moline["product_qty"], produce_rec["quantity"])
                self.assertEqual(
                    odoo_moline["product_id"][0], produce_rec["product_id"][0]
                )
                cnt += 1
            self.assertEqual(cnt, 1)
            # Make sure the records have been deleted from the recommendation
            self.assertEqual(
                count_produce
                + count_reschedule
                + count_purchase
                + count_late_delivery
                - 3,
                len(
                    self.odooRPC(
                        "frepple.recommendation",
                        [],
                        {},
                        [
                            "id",
                        ],
                    )
                ),
            )
