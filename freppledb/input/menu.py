# Copyright (C) 2013 by frePPLe bv
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

from freppledb.menu import menu
from freppledb.input.utils import hasRoutingOperations

import freppledb.input.views
from freppledb.input.models import (
    Buffer,
    Calendar,
    CalendarBucket,
    Customer,
    DeliveryOrder,
    Demand,
    DistributionOrder,
    Item,
    ItemDistribution,
    ItemSupplier,
    Location,
    ManufacturingOrder,
    WorkOrder,
    Operation,
    OperationDependency,
    OperationMaterial,
    OperationPlanMaterial,
    OperationPlanResource,
    OperationResource,
    PurchaseOrder,
    Resource,
    ResourceSkill,
    SetupMatrix,
    SetupRule,
    Skill,
    SubOperation,
    Supplier,
)


menu.addItem(
    "inventory",
    "inventory detail",
    url="/data/input/operationplanmaterial/",
    report=freppledb.input.views.InventoryDetail,
    index=200,
    model=OperationPlanMaterial,
    dependencies=[Item, Location],
)
menu.addItem(
    "inventory",
    "distribution orders",
    url="/data/input/distributionorder/",
    report=freppledb.input.views.DistributionOrderList,
    index=50,
    model=DistributionOrder,
    dependencies=[ItemDistribution],
)
menu.addItem(
    "inventory",
    "buffer admin",
    url="/data/input/buffer/",
    report=freppledb.input.views.BufferList,
    index=1200,
    model=Buffer,
    dependencies=[Item, Location],
)
menu.addItem(
    "inventory",
    "item distributions",
    url="/data/input/itemdistribution/",
    report=freppledb.input.views.ItemDistributionList,
    index=1300,
    model=ItemDistribution,
    dependencies=[Item, Location],
)
menu.addItem(
    "sales",
    "demand",
    url="/data/input/demand/",
    report=freppledb.input.views.DemandList,
    index=100,
    model=Demand,
    dependencies=[Item, Location, Customer],
)
menu.addItem(
    "sales",
    "delivery order",
    url="/data/input/deliveryorder/",
    report=freppledb.input.views.DeliveryOrderList,
    index=300,
    model=DeliveryOrder,
    dependencies=[Demand],
)
menu.addItem(
    "sales",
    "item",
    url="/data/input/item/",
    report=freppledb.input.views.ItemList,
    index=1100,
    model=Item,
)
menu.addItem(
    "sales",
    "locations",
    url="/data/input/location/",
    report=freppledb.input.views.LocationList,
    index=1150,
    model=Location,
)
menu.addItem(
    "sales",
    "customer",
    url="/data/input/customer/",
    report=freppledb.input.views.CustomerList,
    index=1200,
    model=Customer,
)
menu.addItem(
    "purchasing",
    "purchase orders",
    url="/data/input/purchaseorder/",
    report=freppledb.input.views.PurchaseOrderList,
    index=100,
    model=PurchaseOrder,
    dependencies=[Item, Location, Supplier],
)
menu.addItem(
    "purchasing",
    "suppliers",
    url="/data/input/supplier/",
    report=freppledb.input.views.SupplierList,
    index=1100,
    model=Supplier,
)
menu.addItem(
    "purchasing",
    "item suppliers",
    url="/data/input/itemsupplier/",
    report=freppledb.input.views.ItemSupplierList,
    index=1200,
    model=ItemSupplier,
    dependencies=[Item, Location, Supplier],
)
menu.addItem(
    "capacity",
    "resource detail report",
    url="/data/input/operationplanresource/",
    report=freppledb.input.views.ResourceDetail,
    index=200,
    model=OperationPlanResource,
    dependencies=[Resource],
)
menu.addItem(
    "capacity",
    "resources",
    url="/data/input/resource/",
    report=freppledb.input.views.ResourceList,
    index=1100,
    model=Resource,
)
menu.addItem(
    "capacity",
    "skills",
    url="/data/input/skill/",
    report=freppledb.input.views.SkillList,
    index=1200,
    model=Skill,
    dependencies=[Resource],
)
menu.addItem(
    "capacity",
    "resource skills",
    url="/data/input/resourceskill/",
    report=freppledb.input.views.ResourceSkillList,
    index=1300,
    model=ResourceSkill,
    dependencies=[Resource, Skill],
)
menu.addItem(
    "capacity",
    "setup matrices",
    url="/data/input/setupmatrix/",
    report=freppledb.input.views.SetupMatrixList,
    index=1400,
    model=SetupMatrix,
    dependencies=[Resource],
)
menu.addItem(
    "capacity",
    "setup rules",
    url="/data/input/setuprule/",
    report=freppledb.input.views.SetupRuleList,
    index=1500,
    model=SetupRule,
    dependencies=[SetupMatrix],
)
menu.addItem(
    "manufacturing",
    "manufacturing orders",
    url="/data/input/manufacturingorder/",
    report=freppledb.input.views.ManufacturingOrderList,
    index=100,
    model=ManufacturingOrder,
    dependencies=[Operation],
)
menu.addItem(
    "manufacturing",
    "work orders",
    url="/data/input/workorder/",
    report=freppledb.input.views.WorkOrderList,
    index=150,
    model=WorkOrder,
    dependencies=[
        hasRoutingOperations,
    ],
)
menu.addItem(
    "manufacturing",
    "calendars",
    url="/data/input/calendar/",
    report=freppledb.input.views.CalendarList,
    index=1200,
    model=Calendar,
)
menu.addItem(
    "manufacturing",
    "calendarbucket",
    url="/data/input/calendarbucket/",
    report=freppledb.input.views.CalendarBucketList,
    index=1300,
    model=CalendarBucket,
    dependencies=[Calendar],
)
menu.addItem(
    "manufacturing",
    "operations",
    url="/data/input/operation/",
    report=freppledb.input.views.OperationList,
    index=1400,
    model=Operation,
    dependencies=[Item, Location],
)
menu.addItem(
    "manufacturing",
    "operationmaterials",
    url="/data/input/operationmaterial/",
    report=freppledb.input.views.OperationMaterialList,
    index=1500,
    model=OperationMaterial,
    dependencies=[Operation],
)
menu.addItem(
    "manufacturing",
    "operationresources",
    url="/data/input/operationresource/",
    report=freppledb.input.views.OperationResourceList,
    index=1600,
    model=OperationResource,
    dependencies=[Operation, Resource],
)
menu.addItem(
    "manufacturing",
    "operationdependencies",
    url="/data/input/operationdependency/",
    report=freppledb.input.views.OperationDependencyList,
    index=16500,
    model=OperationDependency,
    dependencies=[Operation],
)
menu.addItem(
    "manufacturing",
    "suboperations",
    url="/data/input/suboperation/",
    report=freppledb.input.views.SubOperationList,
    index=1700,
    model=SubOperation,
    dependencies=[Operation],
)
