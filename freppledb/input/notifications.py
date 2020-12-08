#
# Copyright (C) 2020 by frePPLe bv
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

from freppledb.common.models import NotificationFactory
from .models import (
    CalendarBucket,
    Calendar,
    Location,
    Customer,
    Supplier,
    Item,
    ItemSupplier,
    ItemDistribution,
    Operation,
    SubOperation,
    Buffer,
    SetupRule,
    SetupMatrix,
    Skill,
    ResourceSkill,
    Resource,
    OperationMaterial,
    OperationResource,
    ManufacturingOrder,
    DistributionOrder,
    PurchaseOrder,
    DeliveryOrder,
    Demand,
    OperationPlanResource,
    OperationPlanMaterial,
)


@NotificationFactory.register(CalendarBucket, [CalendarBucket])
def CalendarBucketNotification(flw, msg):
    return flw.content_type == msg.content_type and flw.object_pk == msg.object_pk


@NotificationFactory.register(Calendar, [Calendar, CalendarBucket])
def CalendarNotification(flw, msg):
    if flw.content_type == msg.content_type:
        return flw.object_pk == msg.object_pk
    elif msg.content_type.model_class() == CalendarBucket:
        return flw.object_pk == msg.content_object.calendar.name


@NotificationFactory.register(Location, [Location])
def LocationNotification(flw, msg):
    return flw.content_type == msg.content_type and flw.object_pk == msg.object_pk
    # TODO
    #     return flw.content_type == msg.content_type and (
    #         flw.object_pk == msg.object_pk
    #         or flw.content_object.lft <= msg.content_object.lft <= flw.content_object.rght
    #     )


@NotificationFactory.register(Customer, [Customer])
def CustomerNotification(flw, msg):
    return flw.content_type == msg.content_type and flw.object_pk == msg.object_pk


@NotificationFactory.register(Supplier, [Supplier])
def SupplierNotification(flw, msg):
    return flw.content_type == msg.content_type and flw.object_pk == msg.object_pk


@NotificationFactory.register(Item, [Item])
def ItemNotification(flw, msg):
    return flw.content_type == msg.content_type and flw.object_pk == msg.object_pk


@NotificationFactory.register(ItemSupplier, [ItemSupplier])
def ItemSupplierNotification(flw, msg):
    return flw.content_type == msg.content_type and flw.object_pk == msg.object_pk


@NotificationFactory.register(ItemDistribution, [ItemDistribution])
def ItemDistributionNotification(flw, msg):
    return flw.content_type == msg.content_type and flw.object_pk == msg.object_pk


@NotificationFactory.register(Operation, [Operation])
def OperationNotification(flw, msg):
    return flw.content_type == msg.content_type and flw.object_pk == msg.object_pk


@NotificationFactory.register(SubOperation, [SubOperation])
def SubOperationNotification(flw, msg):
    return flw.content_type == msg.content_type and flw.object_pk == msg.object_pk


@NotificationFactory.register(Buffer, [Buffer])
def BufferNotification(flw, msg):
    return flw.content_type == msg.content_type and flw.object_pk == msg.object_pk


@NotificationFactory.register(SetupRule, [SetupRule])
def SetupRuleNotification(flw, msg):
    return flw.content_type == msg.content_type and flw.object_pk == msg.object_pk


@NotificationFactory.register(SetupMatrix, [SetupMatrix])
def SetupMatrixNotification(flw, msg):
    return flw.content_type == msg.content_type and flw.object_pk == msg.object_pk


@NotificationFactory.register(Skill, [Skill])
def SkillNotification(flw, msg):
    return flw.content_type == msg.content_type and flw.object_pk == msg.object_pk


@NotificationFactory.register(ResourceSkill, [ResourceSkill])
def ResourceSkillNotification(flw, msg):
    return flw.content_type == msg.content_type and flw.object_pk == msg.object_pk


@NotificationFactory.register(Resource, [Resource])
def ResourceNotification(flw, msg):
    return flw.content_type == msg.content_type and flw.object_pk == msg.object_pk


@NotificationFactory.register(OperationMaterial, [OperationMaterial])
def OperationMaterialNotification(flw, msg):
    return flw.content_type == msg.content_type and flw.object_pk == msg.object_pk


@NotificationFactory.register(OperationResource, [OperationResource])
def OperationResourceNotification(flw, msg):
    return flw.content_type == msg.content_type and flw.object_pk == msg.object_pk


@NotificationFactory.register(ManufacturingOrder, [ManufacturingOrder])
def ManufacturingOrderNotification(flw, msg):
    return flw.content_type == msg.content_type and flw.object_pk == msg.object_pk


@NotificationFactory.register(DistributionOrder, [DistributionOrder])
def DistributionOrderNotification(flw, msg):
    return flw.content_type == msg.content_type and flw.object_pk == msg.object_pk


@NotificationFactory.register(PurchaseOrder, [PurchaseOrder])
def PurchaseOrderNotification(flw, msg):
    return flw.content_type == msg.content_type and flw.object_pk == msg.object_pk


@NotificationFactory.register(DeliveryOrder, [DeliveryOrder])
def DeliveryOrderNotification(flw, msg):
    return flw.content_type == msg.content_type and flw.object_pk == msg.object_pk


@NotificationFactory.register(Demand, [Demand])
def DemandNotification(flw, msg):
    return flw.content_type == msg.content_type and flw.object_pk == msg.object_pk


@NotificationFactory.register(OperationPlanResource, [OperationPlanResource])
def OperationPlanResourceNotification(flw, msg):
    return flw.content_type == msg.content_type and flw.object_pk == msg.object_pk


@NotificationFactory.register(OperationPlanMaterial, [OperationPlanMaterial])
def OperationPlanMaterialNotification(flw, msg):
    return flw.content_type == msg.content_type and flw.object_pk == msg.object_pk
