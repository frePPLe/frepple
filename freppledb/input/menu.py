# Copyright (C) 2013 by frePPLe bvba
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

from freppledb.menu import menu

import freppledb.input.views
from freppledb.input.models import Buffer, Item, Customer, Location, Demand
from freppledb.input.models import DistributionOrder, ManufacturingOrder, CalendarBucket
from freppledb.input.models import PurchaseOrder, Supplier, ItemSupplier, OperationMaterial
from freppledb.input.models import ItemDistribution, Skill, Resource, OperationResource
from freppledb.input.models import ResourceSkill, SetupMatrix, SetupRule, SubOperation
from freppledb.input.models import Calendar, Operation, DeliveryOrder


menu.addItem(
  "inventory", "distribution orders", url="/data/input/distributionorder/",
  report=freppledb.input.views.DistributionOrderList, index=50, model=DistributionOrder,
  dependencies=[ItemDistribution]
  )
menu.addItem(
  "inventory", "buffer admin", url="/data/input/buffer/",
  report=freppledb.input.views.BufferList, index=1200, model=Buffer,
  dependencies=[Item, Location]
  )
menu.addItem(
  "inventory", "item distributions", url="/data/input/itemdistribution/",
  report=freppledb.input.views.ItemDistributionList, index=1300, model=ItemDistribution,
  dependencies=[Item, Location]
  )
menu.addItem(
  "sales", "demand", url="/data/input/demand/",
  report=freppledb.input.views.DemandList, index=100, model=Demand,
  dependencies=[Item, Location, Customer]
  )
menu.addItem(
  "sales", "delivery order", url="/data/input/deliveryorder/",
  report=freppledb.input.views.DeliveryOrderList, index=300,
  model=DeliveryOrder, dependencies=[Demand]
  )
menu.addItem(
  "sales", "item", url="/data/input/item/",
  report=freppledb.input.views.ItemList, index=1100, model=Item
  )
menu.addItem(
  "sales", "locations", url="/data/input/location/",
  report=freppledb.input.views.LocationList, index=1150, model=Location
  )
menu.addItem(
  "sales", "customer", url="/data/input/customer/",
  report=freppledb.input.views.CustomerList, index=1200, model=Customer
  )
menu.addItem(
  "purchasing", "purchase orders", url="/data/input/purchaseorder/",
  report=freppledb.input.views.PurchaseOrderList, index=100, model=PurchaseOrder,
  dependencies=[ItemSupplier]
  )
menu.addItem(
  "purchasing", "suppliers", url="/data/input/supplier/",
  report=freppledb.input.views.SupplierList, index=1100, model=Supplier
  )
menu.addItem(
  "purchasing", "item suppliers", url="/data/input/itemsupplier/",
  report=freppledb.input.views.ItemSupplierList, index=1200, model=ItemSupplier,
  dependencies=[Item, Location, Supplier]
  )
menu.addItem(
  "capacity", "resources", url="/data/input/resource/",
  report=freppledb.input.views.ResourceList, index=1100, model=Resource
  )
menu.addItem(
  "capacity", "skills", url="/data/input/skill/",
  report=freppledb.input.views.SkillList, index=1200, model=Skill,
  dependencies=[Resource]
  )
menu.addItem(
  "capacity", "resource skills", url="/data/input/resourceskill/",
  report=freppledb.input.views.ResourceSkillList, index=1300, model=ResourceSkill,
  dependencies=[Resource, Skill]
  )
menu.addItem(
  "capacity", "setup matrices", url="/data/input/setupmatrix/",
  report=freppledb.input.views.SetupMatrixList, index=1400, model=SetupMatrix,
  dependencies=[Resource]
  )
menu.addItem(
  "capacity", "setup rules", url="/data/input/setuprule/",
  report=freppledb.input.views.SetupRuleList, index=1500, model=SetupRule,
  dependencies=[SetupMatrix]
  )
menu.addItem(
  "manufacturing", "manufacturing orders", url="/data/input/manufacturingorder/",
  report=freppledb.input.views.ManufacturingOrderList, index=100, model=ManufacturingOrder,
  dependencies=[Operation]
  )
menu.addItem(
  "manufacturing", "calendars", url="/data/input/calendar/",
  report=freppledb.input.views.CalendarList, index=1200, model=Calendar
  )
menu.addItem(
  "manufacturing", "calendarbucket", url="/data/input/calendarbucket/",
  report=freppledb.input.views.CalendarBucketList, index=1300, model=CalendarBucket,
  dependencies=[Calendar]
  )
menu.addItem(
  "manufacturing", "operations", url="/data/input/operation/",
  report=freppledb.input.views.OperationList, index=1400, model=Operation,
  dependencies=[Item, Location]
  )
menu.addItem(
  "manufacturing", "operationmaterials", url="/data/input/operationmaterial/",
  report=freppledb.input.views.OperationMaterialList, index=1500, model=OperationMaterial,
  dependencies=[Operation]
  )
menu.addItem(
  "manufacturing", "operationresources", url="/data/input/operationresource/",
  report=freppledb.input.views.OperationResourceList, index=1600, model=OperationResource,
  dependencies=[Operation, Resource]
  )
menu.addItem(
  "manufacturing", "suboperations", url="/data/input/suboperation/",
  report=freppledb.input.views.SubOperationList, index=1700, model=SubOperation,
  dependencies=[Operation]
  )
