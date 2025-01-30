#
# Copyright (C) 2020 by frePPLe bv
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
    elif not msg.content_object or flw.object_pk != msg.content_object.calendar_id:
        return False
    else:
        args = flw.args.get("sub", None) if flw.args else None
        return msg.model_name() in args if args else True


@NotificationFactory.register(
    Location, [Location, Demand, PurchaseOrder, ManufacturingOrder, DistributionOrder]
)
def LocationNotification(flw, msg):
    if flw.content_type == msg.content_type:
        return flw.object_pk == msg.object_pk
    elif msg.content_type.model_class() == DistributionOrder:
        if not msg.content_object or (
            flw.object_pk != msg.content_object.origin_id
            and flw.object_pk != msg.content_object.destination_id
        ):
            return False
        else:
            args = flw.args.get("sub", None) if flw.args else None
            return msg.model_name() in args if args else True
    elif msg.content_type.model_class() in (
        Demand,
        PurchaseOrder,
        ManufacturingOrder,
        DistributionOrder,
    ):
        if msg.content_object and flw.object_pk != msg.content_object.location_id:
            return False
        else:
            args = flw.args.get("sub", None) if flw.args else None
            return msg.model_name() in args if args else True


@NotificationFactory.register(Customer, [Customer, Demand])
def CustomerNotification(flw, msg):
    if flw.content_type == msg.content_type:
        return flw.object_pk == msg.object_pk
    elif not msg.content_object or flw.object_pk != msg.content_object.customer_id:
        return False
    else:
        args = flw.args.get("sub", None) if flw.args else None
        return msg.model_name() in args if args else True


@NotificationFactory.register(Supplier, [Supplier, PurchaseOrder])
def SupplierNotification(flw, msg):
    if flw.content_type == msg.content_type:
        return flw.object_pk == msg.object_pk
    elif not msg.content_object or flw.object_pk != msg.content_object.supplier_id:
        return False
    else:
        args = flw.args.get("sub", None) if flw.args else None
        return msg.model_name() in args if args else True


@NotificationFactory.register(
    Item,
    [
        Item,
        Demand,
        PurchaseOrder,
        ManufacturingOrder,
        DistributionOrder,
        ItemSupplier,
        ItemDistribution,
        Operation,
    ],
)
def ItemNotification(flw, msg):
    if flw.content_type == msg.content_type:
        return flw.object_pk == msg.object_pk
    elif msg.content_type.model_class() == Item:
        return False
    elif not msg.content_object or flw.object_pk != msg.content_object.item_id:
        return False
    else:
        args = flw.args.get("sub", None) if flw.args else None
        return msg.model_name() in args if args else True


@NotificationFactory.register(ItemSupplier, [ItemSupplier])
def ItemSupplierNotification(flw, msg):
    return flw.content_type == msg.content_type and flw.object_pk == msg.object_pk


@NotificationFactory.register(ItemDistribution, [ItemDistribution])
def ItemDistributionNotification(flw, msg):
    return flw.content_type == msg.content_type and flw.object_pk == msg.object_pk


@NotificationFactory.register(Operation, [Operation, ManufacturingOrder])
def OperationNotification(flw, msg):
    if flw.content_type == msg.content_type:
        return flw.object_pk == msg.object_pk or (
            msg.content_object and flw.object_pk == msg.content_object.owner.name
        )
    elif not msg.content_object or flw.object_pk != msg.content_object.operation_id:
        return False
    else:
        args = flw.args.get("sub", None) if flw.args else None
        return msg.model_name() in args if args else True


@NotificationFactory.register(SubOperation, [SubOperation])
def SubOperationNotification(flw, msg):
    return flw.content_type == msg.content_type and flw.object_pk == msg.object_pk


@NotificationFactory.register(Buffer, [Buffer])
def BufferNotification(flw, msg):
    return flw.content_type == msg.content_type and flw.object_pk == msg.object_pk


@NotificationFactory.register(SetupRule, [SetupRule])
def SetupRuleNotification(flw, msg):
    return flw.content_type == msg.content_type and flw.object_pk == msg.object_pk


@NotificationFactory.register(SetupMatrix, [SetupMatrix, SetupRule])
def SetupMatrixNotification(flw, msg):
    if flw.content_type == msg.content_type:
        return flw.object_pk == msg.object_pk
    elif not msg.content_object or flw.object_pk != msg.content_object.setupmatrix_id:
        return False
    else:
        args = flw.args.get("sub", None) if flw.args else None
        return msg.model_name() in args if args else True


@NotificationFactory.register(Skill, [Skill, ResourceSkill, OperationResource])
def SkillNotification(flw, msg):
    if flw.content_type == msg.content_type:
        return flw.object_pk == msg.object_pk
    elif not msg.content_object or flw.object_pk != msg.content_object.skill_id:
        return False
    else:
        args = flw.args.get("sub", None) if flw.args else None
        return msg.model_name() in args if args else True


@NotificationFactory.register(ResourceSkill, [ResourceSkill])
def ResourceSkillNotification(flw, msg):
    return flw.content_type == msg.content_type and flw.object_pk == msg.object_pk


@NotificationFactory.register(
    Resource, [Resource, ResourceSkill, OperationResource, ManufacturingOrder]
)
def ResourceNotification(flw, msg):
    if flw.content_type == msg.content_type:
        return flw.object_pk == msg.object_pk
    elif msg.content_type.model_class() in (ResourceSkill, OperationResource):
        if not msg.content_object or flw.object_pk != msg.content_object.resource_id:
            return False
        else:
            args = flw.args.get("sub", None) if flw.args else None
            return msg.model_name() in args if args else True
    elif msg.content_type.model_class() == ManufacturingOrder and msg.content_object:
        args = flw.args.get("sub", None) if flw.args else None
        if not args or msg.model_name() not in args:
            return False
        for x in msg.content_object.resources.all():
            if flw.object_pk == x.resource_id:
                return True
        return False
    else:
        return False


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
