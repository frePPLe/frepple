#
# Copyright (C) 2022 by frePPLe bv
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

from datetime import datetime, time, timedelta

from django.test import TestCase


from freppledb.input.models import (
    Calendar,
    CalendarBucket,
    DistributionOrder,
    Item,
    ItemDistribution,
    ItemSupplier,
    Location,
    Operation,
    OperationMaterial,
    OperationPlan,
    OperationPlanMaterial,
    OperationPlanResource,
    OperationResource,
    PurchaseOrder,
    Resource,
    Supplier,
)


class OperationplanTest(TestCase):
    def assertOperationplan(self, reference, expected):
        # Compare the operationplan as stored in the database
        obj = OperationPlan.objects.get(pk=reference)
        self.assertDictEqual(
            {
                "quantity": float(obj.quantity),
                "startdate": obj.startdate,
                "enddate": obj.enddate,
                "status": obj.status,
                "materials": [
                    (i.quantity, i.date, i.item.name) for i in obj.materials.all()
                ],
                "resources": [
                    (i.quantity, i.startdate, i.enddate, i.resource.name)
                    for i in obj.resources.all()
                ],
            },
            expected,
        )

    def test_manufacturing_orders(self):

        cal = Calendar(name="working hours", defaultvalue=0)
        cal.save()
        CalendarBucket(
            calendar=cal,
            value=1,
            monday=True,
            tuesday=True,
            wednesday=True,
            friday=True,
            saturday=True,
            sunday=True,
            starttime=time(9, 0, 0),
            endtime=time(17, 0, 0),
        ).save()

        loc = Location(name="factory", available=cal)
        loc.save()
        oper = Operation(
            name="test1",
            type="time_per",
            location=loc,
            duration=timedelta(hours=1),
            duration_per=timedelta(hours=1),
            # sizeminimum=10,
            sizemultiple=20,
            # sizemaximum=14,
        )
        oper.save()

        item1 = Item(name="item1")
        item1.save()
        OperationMaterial(operation=oper, type="end", item=item1, quantity=2).save()

        item2 = Item(name="item2")
        item2.save()
        OperationMaterial(operation=oper, type="start", item=item2, quantity=-1).save()

        res = Resource(name="machine", location=loc, type="default", maximum=1)
        res.save()
        OperationResource(operation=oper, resource=res, quantity=1).save()

        # Test creation of an operationplan
        opplan = OperationPlan(
            reference="MO #1",
            operation=oper,
            startdate=datetime(2023, 1, 1),
            quantity=4,
            status="approved",
        )
        opplan.update(create=True)
        opplan.save()
        self.assertOperationplan(
            opplan.reference,
            {
                "quantity": 20,
                "startdate": datetime(2023, 1, 1),
                "enddate": datetime(2023, 1, 1, 21),
                "status": "approved",
                "materials": [
                    (40, datetime(2023, 1, 1, 21), "item1"),
                    (-20, datetime(2023, 1, 1), "item2"),
                ],
                "resources": [
                    (1, datetime(2023, 1, 1), datetime(2023, 1, 1, 21), "machine")
                ],
            },
        )

        # Test changing the start date
        opplan.startdate = datetime(2023, 2, 1)
        opplan.update(startdate=datetime(2023, 2, 1))
        opplan.save()
        self.assertOperationplan(
            opplan,
            {
                "quantity": 20,
                "startdate": datetime(2023, 2, 1),
                "enddate": datetime(2023, 2, 1, 21),
                "status": "approved",
                "materials": [
                    (40, datetime(2023, 2, 1, 21), "item1"),
                    (-20, datetime(2023, 2, 1), "item2"),
                ],
                "resources": [
                    (1, datetime(2023, 2, 1), datetime(2023, 2, 1, 21), "machine")
                ],
            },
        )

        # Test deletion of the operationplan
        opplan.update(delete=True)
        opplan.delete()
        self.assertEqual(OperationPlan.objects.filter(reference="MO #1").count(), 0)
        self.assertEqual(
            OperationPlanMaterial.objects.filter(
                operationplan__reference="MO #1"
            ).count(),
            0,
        )
        self.assertEqual(
            OperationPlanResource.objects.filter(
                operationplan__reference="MO #1"
            ).count(),
            0,
        )

    def test_purchase_orders(self):

        cal = Calendar(name="working hours", defaultvalue=0)
        cal.save()
        CalendarBucket(
            calendar=cal,
            value=1,
            monday=True,
            tuesday=True,
            wednesday=True,
            friday=True,
            saturday=True,
            sunday=True,
            starttime=time(9, 0, 0),
            endtime=time(17, 0, 0),
        ).save()

        loc = Location(name="factory", available=cal)
        loc.save()
        supplier = Supplier(name="My supplier")
        supplier.save()

        item = Item(name="item1")
        item.save()
        ItemSupplier(item=item, location=loc, sizemultiple=10).save()

        # Test creation of an operationplan
        opplan = PurchaseOrder(
            reference="PO #1",
            item=item,
            location=loc,
            supplier=supplier,
            startdate=datetime(2023, 1, 1),
            quantity=4,
            status="approved",
        )
        opplan.update(create=True)
        opplan.save()
        self.assertOperationplan(
            opplan.reference,
            {
                "quantity": 20,
                "startdate": datetime(2023, 1, 1),
                "enddate": datetime(2023, 1, 1, 21),
                "status": "approved",
                "materials": [
                    (20, datetime(2023, 1, 1, 21), "item"),
                ],
                "resources": [],
            },
        )

        # Test changing the start date
        opplan.startdate = datetime(2023, 2, 1)
        opplan.update(startdate=datetime(2023, 2, 1))
        opplan.save()
        self.assertOperationplan(
            opplan,
            {
                "quantity": 20,
                "startdate": datetime(2023, 2, 1),
                "enddate": datetime(2023, 2, 1, 21),
                "status": "approved",
                "materials": [
                    (20, datetime(2023, 2, 1, 21), "item"),
                ],
                "resources": [],
            },
        )

        # Test deletion of the operationplan
        opplan.update(delete=True)
        opplan.delete()
        self.assertEqual(OperationPlan.objects.filter(reference="PO #1").count(), 0)
        self.assertEqual(
            OperationPlanMaterial.objects.filter(
                operationplan__reference="PO #1"
            ).count(),
            0,
        )
        self.assertEqual(
            OperationPlanResource.objects.filter(
                operationplan__reference="PO #1"
            ).count(),
            0,
        )

    def test_distribution_orders(self):

        cal = Calendar(name="working hours", defaultvalue=0)
        cal.save()
        CalendarBucket(
            calendar=cal,
            value=1,
            monday=True,
            tuesday=True,
            wednesday=True,
            friday=True,
            saturday=True,
            sunday=True,
            starttime=time(9, 0, 0),
            endtime=time(17, 0, 0),
        ).save()

        loc1 = Location(name="factory", available=cal)
        loc1.save()
        loc2 = Location(name="warehouse", available=cal)
        loc2.save()

        item = Item(name="item1")
        item.save()
        ItemDistribution(location=loc2, origin=loc1, item=item).save()

        # Test creation of an operationplan
        opplan = DistributionOrder(
            reference="DO #1",
            location=loc2,
            origin=loc2,
            item=item,
            startdate=datetime(2023, 1, 1),
            quantity=4,
            status="approved",
        )
        opplan.update(create=True)
        opplan.save()
        self.assertOperationplan(
            opplan.reference,
            {
                "quantity": 20,
                "startdate": datetime(2023, 1, 1),
                "enddate": datetime(2023, 1, 1, 21),
                "status": "approved",
                "materials": [
                    (40, datetime(2023, 1, 1, 21), "item1"),
                    (-20, datetime(2023, 1, 1), "item2"),
                ],
                "resources": [],
            },
        )

        # Test changing the start date
        opplan.startdate = datetime(2023, 2, 1)
        opplan.update(startdate=datetime(2023, 2, 1))
        opplan.save()
        self.assertOperationplan(
            opplan,
            {
                "quantity": 20,
                "startdate": datetime(2023, 2, 1),
                "enddate": datetime(2023, 2, 1, 21),
                "status": "approved",
                "materials": [
                    (40, datetime(2023, 2, 1, 21), "item1"),
                    (-20, datetime(2023, 2, 1), "item2"),
                ],
                "resources": [],
            },
        )

        # Test deletion of the operationplan
        opplan.update(delete=True)
        opplan.delete()
        self.assertEqual(OperationPlan.objects.filter(reference="DO #1").count(), 0)
        self.assertEqual(
            OperationPlanMaterial.objects.filter(
                operationplan__reference="DO #1"
            ).count(),
            0,
        )
        self.assertEqual(
            OperationPlanResource.objects.filter(
                operationplan__reference="DO #1"
            ).count(),
            0,
        )
