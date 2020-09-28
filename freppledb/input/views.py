#
# Copyright (C) 2007-2013 by frePPLe bv
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

from datetime import datetime
from dateutil.parser import parse
import json

from django.conf import settings
from django.contrib.admin.utils import unquote
from django.contrib.admin.views.decorators import staff_member_required
from django.core.exceptions import FieldDoesNotExist
from django.db import connections
from django.db.models.functions import Cast
from django.db.models import Q, F, FloatField, DateTimeField, DurationField
from django.db.models.expressions import RawSQL
from django.db.models.fields import CharField
from django.http import HttpResponse, Http404
from django.http.response import StreamingHttpResponse, HttpResponseServerError
from django.utils.decorators import method_decorator
from django.utils.translation import gettext_lazy as _
from django.utils.translation import ungettext
from django.utils.encoding import force_text
from django.utils.text import format_lazy
from django.views.generic import View
from django.views.decorators.csrf import csrf_exempt

from freppledb.boot import getAttributeFields
from freppledb.common.models import Parameter
from freppledb.input.models import Resource, Operation, Location, SetupMatrix, SetupRule
from freppledb.input.models import Skill, Buffer, Customer, Demand, DeliveryOrder
from freppledb.input.models import Item, OperationResource, OperationMaterial
from freppledb.input.models import (
    Calendar,
    CalendarBucket,
    ManufacturingOrder,
    SubOperation,
)
from freppledb.input.models import ResourceSkill, Supplier, ItemSupplier, searchmode
from freppledb.input.models import ItemDistribution, DistributionOrder, PurchaseOrder
from freppledb.input.models import (
    OperationPlan,
    OperationPlanMaterial,
    OperationPlanResource,
)
from freppledb.common.report import GridReport, GridFieldBool, GridFieldLastModified
from freppledb.common.report import GridFieldDateTime, GridFieldTime, GridFieldText
from freppledb.common.report import GridFieldNumber, GridFieldInteger, GridFieldCurrency
from freppledb.common.report import GridFieldChoice, GridFieldDuration, GridFieldJSON
from freppledb.admin import data_site

import logging

logger = logging.getLogger(__name__)


@staff_member_required
def search(request):
    term = request.GET.get("term").strip()
    result = []

    # Loop over all models in the data_site
    # We are interested in models satisfying these criteria:
    #  - primary key is of type text
    #  - user has change permissions
    for cls, admn in data_site._registry.items():
        if request.user.has_perm(
            "%s.view_%s" % (cls._meta.app_label, cls._meta.object_name.lower())
        ) and isinstance(cls._meta.pk, CharField):
            descriptionExists = True
            try:
                cls._meta.get_field("description")
                query = (
                    cls.objects.using(request.database)
                    .filter(Q(pk__icontains=term) | Q(description__icontains=term))
                    .order_by("pk")
                    .values_list("pk", "description")
                )
            except FieldDoesNotExist:
                descriptionExists = False
                query = (
                    cls.objects.using(request.database)
                    .filter(pk__icontains=term)
                    .order_by("pk")
                    .values_list("pk")
                )
            count = len(query)
            if count > 0:
                result.append(
                    {
                        "value": None,
                        "label": (
                            ungettext(
                                "%(name)s - %(count)d match",
                                "%(name)s - %(count)d matches",
                                count,
                            )
                            % {
                                "name": force_text(cls._meta.verbose_name),
                                "count": count,
                            }
                        ).capitalize(),
                    }
                )
                result.extend(
                    [
                        {
                            "url": (
                                "/data/%s/%s/?noautofilter&parentreference="
                                if issubclass(cls, OperationPlan)
                                else "/detail/%s/%s/"
                            )
                            % (cls._meta.app_label, cls._meta.object_name.lower()),
                            "removeTrailingSlash": True
                            if issubclass(cls, OperationPlan)
                            else False,
                            "value": i[0],
                            "display": "%s%s"
                            % (
                                i[0],
                                " %s" % (i[1],) if descriptionExists and i[1] else "",
                            ),
                        }
                        for i in query[:10]
                    ]
                )
    # Construct reply
    return HttpResponse(
        content_type="application/json; charset=%s" % settings.DEFAULT_CHARSET,
        content=json.dumps(result).encode(settings.DEFAULT_CHARSET),
    )


class PathReport(GridReport):
    """
  A report showing the upstream supply path or following downstream a
  where-used path.
  The supply path report shows all the materials, operations and resources
  used to make a certain item.
  The where-used report shows all the materials and operations that use
  a specific item.
  """

    template = "input/path.html"
    title = _("supply path")
    filterable = False
    frozenColumns = 0
    editable = False
    default_sort = None
    isTreeView = True
    multiselect = False
    help_url = "user-interface/plan-analysis/supply-path-where-used.html"

    rows = (
        GridFieldText("depth", title=_("depth"), editable=False, sortable=False),
        GridFieldText(
            "operation",
            title=_("operation"),
            editable=False,
            sortable=False,
            formatter="detail",
            extra='"role":"input/operation"',
        ),
        GridFieldText(
            "item",
            title=_("item"),
            editable=False,
            sortable=False,
            formatter="detail",
            extra='"role":"input/item"',
        ),
        GridFieldText(
            "description",
            title=format_lazy("{} - {}", _("item"), _("description")),
            editable=False,
            sortable=False,
        ),
        GridFieldNumber(
            "priority", title=_("priority"), editable=False, sortable=False
        ),
        GridFieldNumber(
            "sizeminimum",
            title=_("size minimum"),
            editable=False,
            sortable=False,
            initially_hidden=True,
        ),
        GridFieldNumber(
            "sizemultiple",
            title=_("size multiple"),
            editable=False,
            sortable=False,
            initially_hidden=True,
        ),
        GridFieldNumber(
            "sizemaximum",
            title=_("size maximum"),
            editable=False,
            sortable=False,
            initially_hidden=True,
        ),
        GridFieldNumber(
            "quantity", title=_("quantity"), editable=False, sortable=False
        ),
        GridFieldText(
            "location",
            title=_("location"),
            field_name="location",
            formatter="detail",
            extra='"role":"input/location"',
        ),
        GridFieldText("type", title=_("type"), editable=False, sortable=False),
        GridFieldDuration(
            "duration", title=_("duration"), editable=False, sortable=False
        ),
        GridFieldDuration(
            "duration_per", title=_("duration per unit"), editable=False, sortable=False
        ),
        GridFieldText(
            "resources", editable=False, sortable=False, extra="formatter:reslistfmt"
        ),
        GridFieldText("buffers", editable=False, sortable=False, hidden=True),
        GridFieldText("suboperation", editable=False, sortable=False, hidden=True),
        GridFieldText("numsuboperations", editable=False, sortable=False, hidden=True),
        GridFieldText("parentoper", editable=False, sortable=False, hidden=True),
        GridFieldText("realdepth", editable=False, sortable=False, hidden=True),
        GridFieldText("id", editable=False, sortable=False, hidden=True),
        GridFieldText("parent", editable=False, sortable=False, hidden=True),
        GridFieldText("leaf", editable=False, sortable=False, hidden=True),
        GridFieldText("expanded", editable=False, sortable=False, hidden=True),
        GridFieldText("alternate", editable=False, sortable=False, hidden=True),
    )

    # Attributes to be specified by the subclasses
    objecttype = None
    downstream = None

    @classmethod
    def basequeryset(reportclass, request, *args, **kwargs):
        if str(reportclass.objecttype._meta) != "input.buffer":
            return reportclass.objecttype.objects.filter(name__exact=args[0]).values(
                "name"
            )
        else:
            return (
                reportclass.objecttype.objects.annotate(
                    name=RawSQL("item_id||' @ '||location_id", ())
                )
                .filter(name__exact=args[0])
                .values("name")
            )

    @classmethod
    def extra_context(reportclass, request, *args, **kwargs):
        if reportclass.downstream:
            request.session["lasttab"] = "whereused"
        else:
            request.session["lasttab"] = "supplypath"

        if reportclass.objecttype._meta.model_name == "buffer":
            index = args[0].find(" @ ")
            if index == -1:
                b = Buffer.objects.get(id=args[0])
                buffer_name = b.item.name + " @ " + b.location.name
            else:
                buffer_name = args[0]

        return {
            "title": force_text(reportclass.objecttype._meta.verbose_name)
            + " "
            + (buffer_name if "buffer_name" in vars() else args[0]),
            "post_title": _("where used")
            if reportclass.downstream
            else _("supply path"),
            "downstream": reportclass.downstream,
            "active_tab": reportclass.downstream and "whereused" or "supplypath",
            "model": reportclass.objecttype._meta,
        }

    @classmethod
    def getOperationFromItem(reportclass, request, item_name, downstream, depth):
        cursor = connections[request.database].cursor()
        query = """
      -- MANUFACTURING OPERATIONS
      select distinct 
      case when parentoperation is null then operation else sibling end,
      case when parentoperation is null then operation_location else sibling_location end,
      case when parentoperation is null then operation_type else sibling_type end,
      case when parentoperation is null then operation_priority else sibling_priority end,
      case when parentoperation is null then operation_om else sibling_om end,
      case when parentoperation is null then operation_or else sibling_or end,
      case when parentoperation is null then operation_duration else sibling_duration end,
      case when parentoperation is null then operation_duration_per else sibling_duration_per end,
      parentoperation,
      parentoperation_type,
      parentoperation_priority,
      grandparentoperation,
      grandparentoperation_type,
      grandparentoperation_priority,
      sizes,
      grandparentitem_name,
      parentitem_name,
      item_name,
      grandparentitem_description,
      parentitem_description,
      item_description
       from
      (
      select operation.name as operation, 
           operation.type operation_type,
           operation.location_id operation_location,
           operation.priority as operation_priority, 
           operation.duration as operation_duration, 
           operation.duration_per as operation_duration_per,
           case when operation.item_id is not null then jsonb_build_object(operation.item_id||' @ '||operation.location_id, 1) else '{}'::jsonb end
           ||jsonb_object_agg(operationmaterial.item_id||' @ '||operation.location_id, 
                              coalesce(operationmaterial.quantity, operationmaterial.quantity_fixed,0)) filter (where operationmaterial.id is not null) as operation_om,
           jsonb_object_agg(operationresource.resource_id, operationresource.quantity) filter (where operationresource.id is not null) as operation_or,
             parentoperation.name as parentoperation, 
           parentoperation.type as parentoperation_type,
           parentoperation.priority parentoperation_priority,
             sibling.name as sibling, 
           sibling.type as sibling_type,
           sibling.location_id as sibling_location,
           sibling.priority as sibling_priority, 
           sibling.duration as sibling_duration, 
           sibling.duration_per as sibling_duration_per,
           case when grandparentoperation.item_id is not null 
           and sibling.priority = (select max(priority) from operation where owner_id = parentoperation.name) 
           then jsonb_build_object(grandparentoperation.item_id||' @ '||grandparentoperation.location_id, 1) else '{}'::jsonb end
           ||case when parentoperation.item_id is not null 
           and sibling.priority = (select max(priority) from operation where owner_id = parentoperation.name) 
           then jsonb_build_object(parentoperation.item_id||' @ '||parentoperation.location_id, 1) else '{}'::jsonb end
           ||case when sibling.item_id is not null then jsonb_build_object(sibling.item_id||' @ '||sibling.location_id, 1) else '{}'::jsonb end
           ||coalesce(jsonb_object_agg(siblingoperationmaterial.item_id||' @ '||sibling.location_id, 
                                       coalesce(siblingoperationmaterial.quantity, siblingoperationmaterial.quantity_fixed,0)) filter (where siblingoperationmaterial.id is not null), '{}'::jsonb) as sibling_om,
           jsonb_object_agg(siblingoperationresource.resource_id, siblingoperationresource.quantity)filter (where siblingoperationresource.id is not null) as sibling_or,
             grandparentoperation.name as grandparentoperation, 
           grandparentoperation.type as grandparentoperation_type,
           grandparentoperation.priority as grandparentoperation_priority,
           jsonb_build_object( 'operation_min', operation.sizeminimum,
                               'operation_multiple', operation.sizemultiple,
                               'operation_max', operation.sizemaximum,
                               'parentoperation_min', parentoperation.sizeminimum,
                               'parentoperation_multiple',parentoperation.sizemultiple,
                               'parentoperation_max', parentoperation.sizemaximum,
                               'grandparentoperation_min', grandparentoperation.sizeminimum, 
                               'grandparentoperation_multiple', grandparentoperation.sizemultiple,
                               'grandparentoperation_max', grandparentoperation.sizemaximum) as sizes,
           grandparentitem.name as grandparentitem_name,
           parentitem.name as parentitem_name,
           item.name as item_name,
           grandparentitem.description as grandparentitem_description,
           parentitem.description as parentitem_description,
           item.description as item_description
      from operation
      left outer join operationmaterial on operationmaterial.operation_id = operation.name
      left outer join operationresource on operationresource.operation_id = operation.name
      left outer join operation parentoperation on parentoperation.name = operation.owner_id
      left outer join operation grandparentoperation on grandparentoperation.name = parentoperation.owner_id
      left outer join operation sibling on sibling.owner_id = parentoperation.name
      left outer join operationmaterial siblingoperationmaterial on siblingoperationmaterial.operation_id = sibling.name
      left outer join operationresource siblingoperationresource on siblingoperationresource.operation_id = sibling.name
      left outer join item grandparentitem on grandparentitem.name = grandparentoperation.item_id
      left outer join item parentitem on parentitem.name = parentoperation.item_id
      left outer join item on item.name = coalesce(operation.item_id, 
                                                   (select item_id from operationmaterial where operation_id = operation.name and quantity > 0 limit 1))
      where operation.type in ('time_per','fixed_time')
      %s
      group by operation.name, parentoperation.name, sibling.name, grandparentoperation.name,
      grandparentitem.name, parentitem.name, item.name, grandparentitem.description, parentitem.description, item.description
      ) t
      union all
      -- DISTRIBUTION OPERATIONS
      select 'Ship '||item.name||' from '||itemdistribution.origin_id||' to '||itemdistribution.location_id,    
      itemdistribution.location_id,
      'distribution' as type,
      priority,
      jsonb_build_object(item.name||' @ '||itemdistribution.origin_id, -1,
                         item.name||' @ '||itemdistribution.location_id, 1) as operation_om,                      
      case when itemdistribution.resource_id is not null 
      then jsonb_build_object(itemdistribution.resource_id, itemdistribution.resource_qty) 
      else '{}'::jsonb end operation_or,
      leadtime as duration,
      null as duration_per,
      null,
      null,
      null,
      null,
      null,
      null,
      jsonb_build_object( 'operation_min', itemdistribution.sizeminimum,
                               'operation_multiple', itemdistribution.sizemultiple,
                               'operation_max', itemdistribution.sizemaximum) as sizes,
      null,
      null,
      item.name,
      null,
      null,
      item.description
      from itemdistribution
      inner join item parent on parent.name = itemdistribution.item_id
      inner join item on item.name = %%s and item.lft between parent.lft and parent.rght 
      """ % (
            (
                """
                and (operation.item_id = %s or 
                (operationmaterial.item_id = %s and operationmaterial.quantity > 0)
                or parentoperation.item_id = %s
                or grandparentoperation.item_id = %s)
            """,
            )
            if not downstream
            else (
                """
                and exists (select 1 from operationmaterial om where om.operation_id = operation.name
                and om.item_id = %s and om.quantity < 0)
            """,
            )
        )

        if not downstream:
            query = (
                query
                + """
        union all
      -- PURCHASING OPERATIONS
      select 'Purchase '||item.name||' @ '|| location.name||' from '||itemsupplier.supplier_id,
      location.name as location_id,
      'purchase' as type,
      priority,
      jsonb_build_object(item.name||' @ '|| location.name,1),
      case when itemsupplier.resource_id is not null then jsonb_build_object(itemsupplier.resource_id, itemsupplier.resource_qty) else '{}'::jsonb end resources,
      itemsupplier.leadtime as duration,
      null as duration_per,
      null,
      null,
      null,
      null,
      null,
      null,
      jsonb_build_object( 'operation_min', itemsupplier.sizeminimum,
                               'operation_multiple', itemsupplier.sizemultiple,
                               'operation_max', itemsupplier.sizemaximum) as sizes,
      null,
      null,
      item.name,
      null,
      null,
      item.description
      from itemsupplier
      inner join item i_parent on i_parent.name = itemsupplier.item_id
      inner join item on item.name = %s and item.lft between i_parent.lft and i_parent.rght
      inner join location l_parent on l_parent.name = itemsupplier.location_id
      inner join location on location.lft between l_parent.lft and l_parent.rght
      union all
      select 'Purchase '||item.name||' @ '|| location.name||' from '||itemsupplier.supplier_id,
      location.name as location_id,
      'purchase' as type,
      priority,
      jsonb_build_object(item.name||' @ '|| location.name,1),
      case when itemsupplier.resource_id is not null then jsonb_build_object(itemsupplier.resource_id, itemsupplier.resource_qty) else '{}'::jsonb end resources,
      itemsupplier.leadtime as duration,
      null as duration_per,
      null,
      null,
      null,
      null,
      null,
      null,
      jsonb_build_object( 'operation_min', itemsupplier.sizeminimum,
                               'operation_multiple', itemsupplier.sizemultiple,
                               'operation_max', itemsupplier.sizemaximum) as sizes,
      null,
      null,
      item.name,
      null,
      null,
      item.description
      from itemsupplier
      inner join item i_parent on i_parent.name = itemsupplier.item_id
      inner join item on item.name = %s and item.lft between i_parent.lft and i_parent.rght
      inner join location on location.lft = location.rght - 1
      where location_id is null
      """
            )

        query = (
            query + " order by grandparentoperation, parentoperation, sibling_priority"
        )

        if downstream:
            cursor.execute(query, (item_name,) * 2)
        else:
            cursor.execute(query, (item_name,) * 7)

        for i in cursor.fetchall():
            for j in reportclass.processRecord(i, request, depth, downstream, None, 1):
                yield j

    @classmethod
    def getOperationFromResource(
        reportclass, request, resource_name, downstream, depth
    ):
        cursor = connections[request.database].cursor()
        query = """      
      -- MANUFACTURING OPERATIONS
      select distinct 
      case when parentoperation is null then operation else sibling end,
      case when parentoperation is null then operation_location else sibling_location end,
      case when parentoperation is null then operation_type else sibling_type end,
      case when parentoperation is null then operation_priority else sibling_priority end,
      case when parentoperation is null then operation_om else sibling_om end,
      case when parentoperation is null then operation_or else sibling_or end,
      case when parentoperation is null then operation_duration else sibling_duration end,
      case when parentoperation is null then operation_duration_per else sibling_duration_per end,
      parentoperation,
      parentoperation_type,
      parentoperation_priority,
      grandparentoperation,
      grandparentoperation_type,
      grandparentoperation_priority,
      sizes,
      grandparentitem_name,
      parentitem_name,
      item_name,
      grandparentitem_description,
      parentitem_description,
      item_description
       from
      (
      select operation.name as operation, 
           operation.type operation_type,
           operation.location_id operation_location,
           operation.priority as operation_priority, 
           operation.duration as operation_duration, 
           operation.duration_per as operation_duration_per,
           case when operation.item_id is not null then jsonb_build_object(operation.item_id||' @ '||operation.location_id, 1) else '{}'::jsonb end
           ||jsonb_object_agg(operationmaterial.item_id||' @ '||operation.location_id, 
                              coalesce(operationmaterial.quantity, operationmaterial.quantity_fixed, 0)) filter (where operationmaterial.id is not null) as operation_om,
           jsonb_object_agg(operationresource.resource_id, operationresource.quantity) filter (where operationresource.id is not null) as operation_or,
             parentoperation.name as parentoperation, 
           parentoperation.type as parentoperation_type,
           parentoperation.priority parentoperation_priority,
             sibling.name as sibling, 
           sibling.type as sibling_type,
           sibling.location_id as sibling_location,
           sibling.priority as sibling_priority, 
           sibling.duration as sibling_duration, 
           sibling.duration_per as sibling_duration_per,
           case when grandparentoperation.item_id is not null 
           and sibling.priority = (select max(priority) from operation where owner_id = parentoperation.name) 
           then jsonb_build_object(grandparentoperation.item_id||' @ '||grandparentoperation.location_id, 1) else '{}'::jsonb end
           ||case when parentoperation.item_id is not null 
           and sibling.priority = (select max(priority) from operation where owner_id = parentoperation.name) 
           then jsonb_build_object(parentoperation.item_id||' @ '||parentoperation.location_id, 1) else '{}'::jsonb end
           ||case when sibling.item_id is not null then jsonb_build_object(sibling.item_id||' @ '||sibling.location_id, 1) else '{}'::jsonb end
           || coalesce(jsonb_object_agg(siblingoperationmaterial.item_id||' @ '||sibling.location_id, 
                                        coalesce(siblingoperationmaterial.quantity, siblingoperationmaterial.quantity_fixed, 0)) filter (where siblingoperationmaterial.id is not null), '{}'::jsonb) as sibling_om,
           jsonb_object_agg(siblingoperationresource.resource_id, siblingoperationresource.quantity)filter (where siblingoperationresource.id is not null) as sibling_or,
             grandparentoperation.name as grandparentoperation, 
           grandparentoperation.type as grandparentoperation_type,
           grandparentoperation.priority as grandparentoperation_priority,
           jsonb_build_object( 'operation_min', operation.sizeminimum,
                               'operation_multiple', operation.sizemultiple,
                               'operation_max', operation.sizemaximum,
                               'parentoperation_min', parentoperation.sizeminimum,
                               'parentoperation_multiple',parentoperation.sizemultiple,
                               'parentoperation_max', parentoperation.sizemaximum,
                               'grandparentoperation_min', grandparentoperation.sizeminimum, 
                               'grandparentoperation_multiple', grandparentoperation.sizemultiple,
                               'grandparentoperation_max', grandparentoperation.sizemaximum) as sizes,
           grandparentitem.name as grandparentitem_name,
           parentitem.name as parentitem_name,
           item.name as item_name,
           grandparentitem.description as grandparentitem_description,
           parentitem.description as parentitem_description,
           item.description as item_description
      from operation
      left outer join operationmaterial on operationmaterial.operation_id = operation.name
      left outer join operationresource on operationresource.operation_id = operation.name
      left outer join operation parentoperation on parentoperation.name = operation.owner_id
      left outer join operation grandparentoperation on grandparentoperation.name = parentoperation.owner_id
      left outer join operation sibling on sibling.owner_id = parentoperation.name      
      left outer join operationmaterial siblingoperationmaterial on siblingoperationmaterial.operation_id = sibling.name
      left outer join operationresource siblingoperationresource on siblingoperationresource.operation_id = sibling.name
      left outer join item grandparentitem on grandparentitem.name = grandparentoperation.item_id
      left outer join item parentitem on parentitem.name = parentoperation.item_id
      left outer join item on item.name = coalesce(operation.item_id, 
                                                   (select item_id from operationmaterial where operation_id = operation.name and quantity > 0 limit 1))
      where operation.type in ('time_per','fixed_time')
      and %s
      group by operation.name, parentoperation.name, sibling.name, grandparentoperation.name,
      grandparentitem.name, parentitem.name, item.name, grandparentitem.description, parentitem.description, item.description
      ) t
      union all
      -- DISTRIBUTION OPERATIONS
      select 'Ship '||item.name||' from '||itemdistribution.origin_id||' to '||itemdistribution.location_id,    
      itemdistribution.location_id,
      'distribution' as type,
      priority,
      jsonb_build_object(item.name||' @ '||itemdistribution.origin_id, -1,
                         item.name||' @ '||itemdistribution.location_id, 1) as operation_om,                      
      case when itemdistribution.resource_id is not null 
      then jsonb_build_object(itemdistribution.resource_id, itemdistribution.resource_qty) 
      else '{}'::jsonb end operation_or,
      leadtime as duration,
      null as duration_per,
      null,
      null,
      null,
      null,
      null,
      null,
      jsonb_build_object( 'operation_min', itemdistribution.sizeminimum,
                               'operation_multiple', itemdistribution.sizemultiple,
                               'operation_max', itemdistribution.sizemaximum) as sizes,
      null,
      null,
      item.name,
      null,
      null,
      item.description
      from itemdistribution
      inner join item parent on parent.name = itemdistribution.item_id
      inner join item on item.lft between parent.lft and parent.rght 
      where itemdistribution.resource_id = %%s
      union all
      -- PURCHASING OPERATIONS
      select 'Purchase '||item.name||' @ '|| location.name||' from '||itemsupplier.supplier_id,
      location.name as location_id,
      'purchase' as type,
      priority,
      jsonb_build_object(item.name||' @ '|| location.name,1),
      case when itemsupplier.resource_id is not null then jsonb_build_object(itemsupplier.resource_id, itemsupplier.resource_qty) else '{}'::jsonb end resources,
      itemsupplier.leadtime as duration,
      null as duration_per,
      null,
      null,
      null,
      null,
      null,
      null,
      jsonb_build_object( 'operation_min', itemsupplier.sizeminimum,
                               'operation_multiple', itemsupplier.sizemultiple,
                               'operation_max', itemsupplier.sizemaximum) as sizes,
      null,
      null,
      item.name,
      null,
      null,
      item.description
      from itemsupplier
      inner join item i_parent on i_parent.name = itemsupplier.item_id
      inner join item on item.lft between i_parent.lft and i_parent.rght
      inner join location l_parent on l_parent.name = itemsupplier.location_id
      inner join location on location.lft between l_parent.lft and l_parent.rght
      where itemsupplier.resource_id = %%s
      union all
      select 'Purchase '||item.name||' @ '|| location.name||' from '||itemsupplier.supplier_id,
      location.name as location_id,
      'purchase' as type,
      priority,
      jsonb_build_object(item.name||' @ '|| location.name,1),
      case when itemsupplier.resource_id is not null then jsonb_build_object(itemsupplier.resource_id, itemsupplier.resource_qty) else '{}'::jsonb end resources,
      itemsupplier.leadtime as duration,
      null as duration_per,
      null,
      null,
      null,
      null,
      null,
      null,
      jsonb_build_object( 'operation_min', itemsupplier.sizeminimum,
                               'operation_multiple', itemsupplier.sizemultiple,
                               'operation_max', itemsupplier.sizemaximum) as sizes,
      null,
      null,
      item.name,
      null,
      null,
      item.description
      from itemsupplier
      inner join item i_parent on i_parent.name = itemsupplier.item_id
      inner join item on item.lft between i_parent.lft and i_parent.rght
      inner join location on location.lft = location.rght - 1
      where location_id is null and itemsupplier.resource_id = %%s
      order by grandparentoperation, parentoperation, sibling_priority
      """ % (
            "operationresource.resource_id = %s"
            if downstream == False
            else """
             exists (select 1 from operationresource where operation_id = operation.name and resource_id = %s)      
            """
        )

        cursor.execute(query, (resource_name,) * 4)

        for i in cursor.fetchall():
            for j in reportclass.processRecord(i, request, depth, downstream, None, 1):
                yield j

    @classmethod
    def getOperationFromName(reportclass, request, operation_name, downstream, depth):
        cursor = connections[request.database].cursor()
        query = """      
      -- MANUFACTURING OPERATIONS
      select distinct 
      case when parentoperation is null then operation else sibling end,
      case when parentoperation is null then operation_location else sibling_location end,
      case when parentoperation is null then operation_type else sibling_type end,
      case when parentoperation is null then operation_priority else sibling_priority end,
      case when parentoperation is null then operation_om else sibling_om end,
      case when parentoperation is null then operation_or else sibling_or end,
      case when parentoperation is null then operation_duration else sibling_duration end,
      case when parentoperation is null then operation_duration_per else sibling_duration_per end,
      parentoperation,
      parentoperation_type,
      parentoperation_priority,
      grandparentoperation,
      grandparentoperation_type,
      grandparentoperation_priority,
      sizes,
      grandparentitem_name,
      parentitem_name,
      item_name,
      grandparentitem_description,
      parentitem_description,
      item_description
       from
      (
      select operation.name as operation, 
           operation.type operation_type,
           operation.location_id operation_location,
           operation.priority as operation_priority, 
           operation.duration as operation_duration, 
           operation.duration_per as operation_duration_per,
           case when operation.item_id is not null then jsonb_build_object(operation.item_id||' @ '||operation.location_id, 1) else '{}'::jsonb end
           ||jsonb_object_agg(operationmaterial.item_id||' @ '||operation.location_id, 
                              coalesce(operationmaterial.quantity, operationmaterial.quantity_fixed, 0)) filter (where operationmaterial.id is not null) as operation_om,
           jsonb_object_agg(operationresource.resource_id, operationresource.quantity) filter (where operationresource.id is not null) as operation_or,
             parentoperation.name as parentoperation, 
           parentoperation.type as parentoperation_type,
           parentoperation.priority parentoperation_priority,
             sibling.name as sibling, 
           sibling.type as sibling_type,
           sibling.location_id as sibling_location,
           sibling.priority as sibling_priority, 
           sibling.duration as sibling_duration, 
           sibling.duration_per as sibling_duration_per,
           case when grandparentoperation.item_id is not null 
           and sibling.priority = (select max(priority) from operation where owner_id = parentoperation.name) 
           then jsonb_build_object(grandparentoperation.item_id||' @ '||grandparentoperation.location_id, 1) else '{}'::jsonb end
           ||case when parentoperation.item_id is not null 
           and sibling.priority = (select max(priority) from operation where owner_id = parentoperation.name) 
           then jsonb_build_object(parentoperation.item_id||' @ '||parentoperation.location_id, 1) else '{}'::jsonb end
           ||case when sibling.item_id is not null then jsonb_build_object(sibling.item_id||' @ '||sibling.location_id, 1) else '{}'::jsonb end
           ||coalesce(jsonb_object_agg(siblingoperationmaterial.item_id||' @ '||sibling.location_id, 
                                       coalesce(siblingoperationmaterial.quantity, siblingoperationmaterial.quantity_fixed, 0)) filter (where siblingoperationmaterial.id is not null), '{}'::jsonb) as sibling_om,
           jsonb_object_agg(siblingoperationresource.resource_id, siblingoperationresource.quantity)filter (where siblingoperationresource.id is not null) as sibling_or,
             grandparentoperation.name as grandparentoperation, 
           grandparentoperation.type as grandparentoperation_type,
           grandparentoperation.priority as grandparentoperation_priority,
           jsonb_build_object( 'operation_min', operation.sizeminimum,
                               'operation_multiple', operation.sizemultiple,
                               'operation_max', operation.sizemaximum,
                               'parentoperation_min', parentoperation.sizeminimum,
                               'parentoperation_multiple',parentoperation.sizemultiple,
                               'parentoperation_max', parentoperation.sizemaximum,
                               'grandparentoperation_min', grandparentoperation.sizeminimum, 
                               'grandparentoperation_multiple', grandparentoperation.sizemultiple,
                               'grandparentoperation_max', grandparentoperation.sizemaximum) as sizes,
           grandparentitem.name as grandparentitem_name,
           parentitem.name as parentitem_name,
           item.name as item_name,
           grandparentitem.description as grandparentitem_description,
           parentitem.description as parentitem_description,
           item.description as item_description
      from operation
      left outer join operationmaterial on operationmaterial.operation_id = operation.name
      left outer join operationresource on operationresource.operation_id = operation.name
      left outer join operation parentoperation on parentoperation.name = operation.owner_id
      left outer join operation grandparentoperation on grandparentoperation.name = parentoperation.owner_id
      left outer join operation sibling on sibling.owner_id = parentoperation.name
      left outer join operationmaterial siblingoperationmaterial on siblingoperationmaterial.operation_id = sibling.name
      left outer join operationresource siblingoperationresource on siblingoperationresource.operation_id = sibling.name
      left outer join item grandparentitem on grandparentitem.name = grandparentoperation.item_id
      left outer join item parentitem on parentitem.name = parentoperation.item_id
      left outer join item on item.name = coalesce(operation.item_id, 
                                                   (select item_id from operationmaterial where operation_id = operation.name and quantity > 0 limit 1))
      where operation.type in ('time_per','fixed_time')
      and (operation.name = %s or parentoperation.name = %s or grandparentoperation.name = %s)
      group by operation.name, parentoperation.name, sibling.name, grandparentoperation.name,
      grandparentitem.name, parentitem.name, item.name, grandparentitem.description, parentitem.description, item.description
      ) t
      order by grandparentoperation, parentoperation, sibling_priority
      """

        cursor.execute(query, (operation_name,) * 3)

        for i in cursor.fetchall():
            for j in reportclass.processRecord(i, request, depth, downstream, None, 1):
                yield j

    @classmethod
    def getOperationFromBuffer(
        reportclass,
        request,
        buffer_name,
        downstream,
        depth,
        previousOperation,
        bom_quantity,
    ):
        cursor = connections[request.database].cursor()
        item = buffer_name[0 : buffer_name.find(" @ ")]
        location = buffer_name[buffer_name.find(" @ ") + 3 :]
        query = """      
      -- MANUFACTURING OPERATIONS
      select distinct 
      case when parentoperation is null then operation else sibling end,
      case when parentoperation is null then operation_location else sibling_location end,
      case when parentoperation is null then operation_type else sibling_type end,
      case when parentoperation is null then operation_priority else sibling_priority end,
      case when parentoperation is null then operation_om else sibling_om end,
      case when parentoperation is null then operation_or else sibling_or end,
      case when parentoperation is null then operation_duration else sibling_duration end,
      case when parentoperation is null then operation_duration_per else sibling_duration_per end,
      parentoperation,
      parentoperation_type,
      parentoperation_priority,
      grandparentoperation,
      grandparentoperation_type,
      grandparentoperation_priority,
      sizes,
      grandparentitem_name,
      parentitem_name,
      item_name,
      grandparentitem_description,
      parentitem_description,
      item_description
       from
      (
      select operation.name as operation, 
           operation.type operation_type,
           operation.location_id operation_location,
           operation.priority as operation_priority, 
           operation.duration as operation_duration, 
           operation.duration_per as operation_duration_per,
           case when operation.item_id is not null then jsonb_build_object(operation.item_id||' @ '||operation.location_id, 1) else '{}'::jsonb end
           ||jsonb_object_agg(operationmaterial.item_id||' @ '||operation.location_id, 
                              coalesce(operationmaterial.quantity, operationmaterial.quantity_fixed, 0)) filter (where operationmaterial.id is not null) as operation_om,
           jsonb_object_agg(operationresource.resource_id, operationresource.quantity) filter (where operationresource.id is not null) as operation_or,
             parentoperation.name as parentoperation, 
           parentoperation.type as parentoperation_type,
           parentoperation.priority parentoperation_priority,
             sibling.name as sibling, 
           sibling.type as sibling_type,
           sibling.location_id as sibling_location,
           sibling.priority as sibling_priority, 
           sibling.duration as sibling_duration, 
           sibling.duration_per as sibling_duration_per,
           case when grandparentoperation.item_id is not null 
           and sibling.priority = (select max(priority) from operation where owner_id = parentoperation.name) 
           then jsonb_build_object(grandparentoperation.item_id||' @ '||grandparentoperation.location_id, 1) else '{}'::jsonb end
           ||case when parentoperation.item_id is not null 
           and sibling.priority = (select max(priority) from operation where owner_id = parentoperation.name) 
           then jsonb_build_object(parentoperation.item_id||' @ '||parentoperation.location_id, 1) else '{}'::jsonb end
           ||case when sibling.item_id is not null then jsonb_build_object(sibling.item_id||' @ '||sibling.location_id, 1) else '{}'::jsonb end
           ||coalesce(jsonb_object_agg(siblingoperationmaterial.item_id||' @ '||sibling.location_id, 
                                       coalesce(siblingoperationmaterial.quantity, siblingoperationmaterial.quantity_fixed, 0)) filter (where siblingoperationmaterial.id is not null), '{}'::jsonb) as sibling_om,
           jsonb_object_agg(siblingoperationresource.resource_id, siblingoperationresource.quantity)filter (where siblingoperationresource.id is not null) as sibling_or,
             grandparentoperation.name as grandparentoperation, 
           grandparentoperation.type as grandparentoperation_type,
           grandparentoperation.priority as grandparentoperation_priority,
           jsonb_build_object( 'operation_min', operation.sizeminimum,
                               'operation_multiple', operation.sizemultiple,
                               'operation_max', operation.sizemaximum,
                               'parentoperation_min', parentoperation.sizeminimum,
                               'parentoperation_multiple',parentoperation.sizemultiple,
                               'parentoperation_max', parentoperation.sizemaximum,
                               'grandparentoperation_min', grandparentoperation.sizeminimum, 
                               'grandparentoperation_multiple', grandparentoperation.sizemultiple,
                               'grandparentoperation_max', grandparentoperation.sizemaximum) as sizes,
           grandparentitem.name as grandparentitem_name,
           parentitem.name as parentitem_name,
           item.name as item_name,
           grandparentitem.description as grandparentitem_description,
           parentitem.description as parentitem_description,
           item.description as item_description
      from operation
      left outer join operationmaterial on operationmaterial.operation_id = operation.name
      left outer join operationresource on operationresource.operation_id = operation.name
      left outer join operation parentoperation on parentoperation.name = operation.owner_id
      left outer join operation grandparentoperation on grandparentoperation.name = parentoperation.owner_id
      left outer join operation sibling on sibling.owner_id = parentoperation.name
      left outer join operationmaterial siblingoperationmaterial on siblingoperationmaterial.operation_id = sibling.name
      left outer join operationresource siblingoperationresource on siblingoperationresource.operation_id = sibling.name
      left outer join item grandparentitem on grandparentitem.name = grandparentoperation.item_id
      left outer join item parentitem on parentitem.name = parentoperation.item_id
      left outer join item on item.name = coalesce(operation.item_id, 
                                                   (select item_id from operationmaterial where operation_id = operation.name and quantity > 0 limit 1))
      where operation.type in ('time_per','fixed_time')
      and operation.location_id = %%s
      %s
      group by operation.name, parentoperation.name, sibling.name, grandparentoperation.name,
      grandparentitem.name, parentitem.name, item.name, grandparentitem.description, parentitem.description, item.description
      ) t
      union all
      -- DISTRIBUTION OPERATIONS
      select 'Ship '||item.name||' from '||itemdistribution.origin_id||' to '||itemdistribution.location_id,    
      itemdistribution.location_id,
      'distribution' as type,
      priority,
      jsonb_build_object(item.name||' @ '||itemdistribution.origin_id, -1,
                         item.name||' @ '||itemdistribution.location_id, 1) as operation_om,                      
      case when itemdistribution.resource_id is not null 
      then jsonb_build_object(itemdistribution.resource_id, itemdistribution.resource_qty) 
      else '{}'::jsonb end operation_or,
      leadtime as duration,
      null as duration_per,
      null,
      null,
      null,
      null,
      null,
      null,
      jsonb_build_object( 'operation_min', itemdistribution.sizeminimum,
                               'operation_multiple', itemdistribution.sizemultiple,
                               'operation_max', itemdistribution.sizemaximum) as sizes,
      null,
      null,
      item.name,
      null,
      null,
      item.description
      from itemdistribution
      inner join item parent on parent.name = itemdistribution.item_id
      inner join item on item.name = %%s and item.lft between parent.lft and parent.rght 
      where itemdistribution.%s = %%s
      """ % (
            (
                """
                and (operation.item_id = %s or 
                (operationmaterial.item_id = %s and operationmaterial.quantity > 0)
                or parentoperation.item_id = %s
                or grandparentoperation.item_id = %s)
            """,
                "location_id",
            )
            if not downstream
            else (
                """
                and exists (select 1 from operationmaterial om where om.operation_id = operation.name
                and om.item_id = %s and om.quantity < 0)
            """,
                "origin_id",
            )
        )

        if not downstream:
            query = (
                query
                + """
        union all
      -- PURCHASING OPERATIONS
      select 'Purchase '||item.name||' @ '|| location.name||' from '||itemsupplier.supplier_id,
      location.name as location_id,
      'purchase' as type,
      priority,
      jsonb_build_object(item.name||' @ '|| location.name,1),
      case when itemsupplier.resource_id is not null then jsonb_build_object(itemsupplier.resource_id, itemsupplier.resource_qty) else '{}'::jsonb end resources,
      itemsupplier.leadtime as duration,
      null as duration_per,
      null,
      null,
      null,
      null,
      null,
      null,
      jsonb_build_object( 'operation_min', itemsupplier.sizeminimum,
                               'operation_multiple', itemsupplier.sizemultiple,
                               'operation_max', itemsupplier.sizemaximum) as sizes,
      null,
      null,
      item.name,
      null,
      null,
      item.description
      from itemsupplier
      inner join item i_parent on i_parent.name = itemsupplier.item_id
      inner join item on item.name = %s and item.lft between i_parent.lft and i_parent.rght
      inner join location l_parent on l_parent.name = itemsupplier.location_id
      inner join location on location.name = %s and location.lft between l_parent.lft and l_parent.rght
      union all
      select 'Purchase '||item.name||' @ '|| location.name||' from '||itemsupplier.supplier_id,
      location.name as location_id,
      'purchase' as type,
      priority,
      jsonb_build_object(item.name||' @ '|| location.name,1),
      case when itemsupplier.resource_id is not null then jsonb_build_object(itemsupplier.resource_id, itemsupplier.resource_qty) else '{}'::jsonb end resources,
      itemsupplier.leadtime as duration,
      null as duration_per,
      null,
      null,
      null,
      null,
      null,
      null,
      jsonb_build_object( 'operation_min', itemsupplier.sizeminimum,
                               'operation_multiple', itemsupplier.sizemultiple,
                               'operation_max', itemsupplier.sizemaximum) as sizes,
      null,
      null,
      item.name,
      null,
      null,
      item.description
      from itemsupplier
      inner join item i_parent on i_parent.name = itemsupplier.item_id
      inner join item on item.name = %s and item.lft between i_parent.lft and i_parent.rght
      inner join location on location.name = %s and location.lft = location.rght - 1
      where location_id is null
      """
            )

        query = (
            query + " order by grandparentoperation, parentoperation, sibling_priority"
        )

        if downstream:
            cursor.execute(query, (location, item, item, location))
        else:
            cursor.execute(
                query,
                (
                    location,
                    item,
                    item,
                    item,
                    item,
                    item,
                    location,
                    item,
                    location,
                    item,
                    location,
                ),
            )

        for i in cursor.fetchall():
            for j in reportclass.processRecord(
                i, request, depth, downstream, previousOperation, bom_quantity
            ):
                yield j

    @classmethod
    def processRecord(
        reportclass, i, request, depth, downstream, previousOperation, bom_quantity
    ):

        # First can we go further ?
        if len(reportclass.node_count) > 400:
            return

        # do we have a grandparentoperation
        if i[11] and not i[11] in reportclass.operation_dict:
            reportclass.operation_id = reportclass.operation_id + 1
            reportclass.operation_dict[i[11]] = reportclass.operation_id
            if i[11] not in reportclass.suboperations_count_dict:
                reportclass.suboperations_count_dict[i[11]] = Operation.objects.filter(
                    owner_id=i[11]
                ).count()
            grandparentoperation = {
                "depth": depth * 2,
                "id": reportclass.operation_id,
                "operation": i[11],
                "priority": i[13],
                "type": i[12],
                "item": i[15],
                "description": i[18],
                "location": i[1],
                "resources": None,
                "parentoper": None,
                "suboperation": 0,
                "duration": None,
                "duration_per": None,
                "quantity": 1,
                "buffers": None,
                "parent": (
                    reportclass.operation_dict[previousOperation]
                    if previousOperation
                    else None
                ),
                "leaf": "false",
                "expanded": "true",
                "numsuboperations": reportclass.suboperations_count_dict[i[11]],
                "realdepth": -depth if reportclass.downstream else depth,
                "sizeminimum": i[14]["grandparentoperation_min"],
                "sizemaximum": i[14]["grandparentoperation_max"],
                "sizemultiple": i[14]["grandparentoperation_multiple"],
                "alternate": "false",
            }
            reportclass.node_count.add(i[11])
            yield grandparentoperation

        # do we have a parent operation
        if i[8] and not i[8] in reportclass.operation_dict:
            reportclass.operation_id = reportclass.operation_id + 1
            reportclass.operation_dict[i[8]] = reportclass.operation_id
            if i[8] not in reportclass.suboperations_count_dict:
                reportclass.suboperations_count_dict[i[8]] = Operation.objects.filter(
                    owner_id=i[8]
                ).count()
            if i[11]:
                if i[11] in reportclass.parent_count_dict:
                    reportclass.parent_count_dict[i[11]] = (
                        reportclass.parent_count_dict[i[11]] + 1
                    )
                else:
                    reportclass.parent_count_dict[i[11]] = 1
            parentoperation = {
                "depth": depth * 2,
                "id": reportclass.operation_id,
                "operation": i[8],
                "type": i[9],
                "item": i[16],
                "description": i[19],
                "priority": i[10],
                "location": i[1],
                "resources": None,
                "parentoper": i[11],
                "suboperation": -reportclass.parent_count_dict[i[11]] if i[11] else 0,
                "duration": None,
                "duration_per": None,
                "quantity": 1,
                "buffers": None,
                "parent": reportclass.operation_dict[i[11]]
                if i[11]
                else (
                    reportclass.operation_dict[previousOperation]
                    if previousOperation
                    else None
                ),
                "leaf": "false",
                "expanded": "true",
                "numsuboperations": reportclass.suboperations_count_dict[i[8]],
                "realdepth": -depth if reportclass.downstream else depth,
                "sizeminimum": i[14]["parentoperation_min"],
                "sizemaximum": i[14]["parentoperation_max"],
                "sizemultiple": i[14]["parentoperation_multiple"],
                "alternate": "false",
            }
            reportclass.node_count.add(i[8])
            yield parentoperation

        # go through the regular time_per/fixed_time operation
        if i[0] not in reportclass.operation_dict:
            reportclass.operation_id = reportclass.operation_id + 1
            reportclass.operation_dict[i[0]] = reportclass.operation_id
            if i[8]:
                if i[8] in reportclass.parent_count_dict:
                    reportclass.parent_count_dict[i[8]] = (
                        reportclass.parent_count_dict[i[8]] + 1
                    )
                else:
                    reportclass.parent_count_dict[i[8]] = 1
            operation = {
                "depth": depth * 2 if not i[8] else depth * 2 + 1,
                "id": reportclass.operation_id,
                "operation": i[0],
                "priority": i[3],
                "type": i[2],
                "item": i[17],
                "description": i[20],
                "location": i[1],
                "resources": tuple(i[5].items()) if i[5] else None,
                "parentoper": i[8],
                "suboperation": 0
                if not i[8]
                else (
                    reportclass.parent_count_dict[i[8]]
                    if i[9] == "routing"
                    else -reportclass.parent_count_dict[i[8]]
                ),
                "duration": i[6],
                "duration_per": i[7],
                "quantity": bom_quantity,
                "buffers": tuple(i[4].items()) if i[4] else None,
                "parent": reportclass.operation_dict[i[8]]
                if i[8]
                else (
                    reportclass.operation_dict[previousOperation]
                    if previousOperation
                    else None
                ),
                "leaf": "false",
                "expanded": "true",
                "numsuboperations": 0,
                "realdepth": -depth if reportclass.downstream else depth,
                "sizeminimum": i[14]["operation_min"],
                "sizemaximum": i[14]["operation_max"],
                "sizemultiple": i[14]["operation_multiple"],
                "alternate": "false",
                "alternate_priority": (i[13] or i[10] or i[3] or 999),
                "alternate_operation": (i[11] or i[8] or i[0]),
            }
            reportclass.node_count.add(i[0])
            yield operation

        if i[5]:
            for resource, quantity in tuple(i[5].items()):
                reportclass.node_count.add(resource)

        if i[4]:
            for buffer, quantity in tuple(i[4].items()):

                # I might already have visisted that buffer
                if buffer in reportclass.node_count:
                    continue
                reportclass.node_count.add(buffer)
                if float(quantity) < 0 and not downstream:
                    yield from reportclass.getOperationFromBuffer(
                        request, buffer, downstream, depth + 1, i[0], float(quantity)
                    )
                elif float(quantity) > 0 and downstream:
                    yield from reportclass.getOperationFromBuffer(
                        request, buffer, downstream, depth + 1, i[0], float(quantity)
                    )

    @classmethod
    def query(reportclass, request, basequery):
        """
        A function that recurses upstream or downstream in the supply chain.
        """
        # Update item and location hierarchies
        Item.rebuildHierarchy(database=request.database)
        Location.rebuildHierarchy(database=request.database)

        # dictionary to retrieve the operation id from its name
        reportclass.operation_dict = {}

        # counter used to give a unique id to the operation
        reportclass.operation_id = 0

        # dictionary to count the number of suboperations
        # prevents to hit database more than once for a given routing/alternate
        reportclass.suboperations_count_dict = {}

        # dictionary to reassign a priority to the alternate/routing suboperations
        # required otherwise suboperations with same priority overlap.
        reportclass.parent_count_dict = {}

        # set used to count the number of nodes in the graph.
        # we stop at 400 otherwise we could draw the full supply chain
        # in the case of downstream raw material.
        reportclass.node_count = set()

        results = []

        if str(reportclass.objecttype._meta) == "input.buffer":
            buffer_name = basequery.query.get_compiler(basequery.db).as_sql(
                with_col_aliases=False
            )[1][0]
            if " @ " not in buffer_name:
                b = Buffer.objects.get(id=buffer_name)
                buffer_name = "%s @ %s" % (b.item.name, b.location.name)

            for i in reportclass.getOperationFromBuffer(
                request, buffer_name, reportclass.downstream, 0, None, 1
            ):
                results.append(i)
        elif str(reportclass.objecttype._meta) == "input.demand":
            demand_name = basequery.query.get_compiler(basequery.db).as_sql(
                with_col_aliases=False
            )[1][0]
            d = Demand.objects.get(name=demand_name)
            if d.operation is None:
                buffer_name = "%s @ %s" % (d.item.name, d.location.name)

                for i in reportclass.getOperationFromBuffer(
                    request,
                    buffer_name,
                    reportclass.downstream,
                    depth=0,
                    previousOperation=None,
                    bom_quantity=1,
                ):
                    results.append(i)
            else:
                operation_name = d.operation.name

                for i in reportclass.getOperationFromName(
                    request, operation_name, reportclass.downstream, depth=0
                ):
                    results.append(i)
        elif str(reportclass.objecttype._meta) == "input.resource":
            resource_name = basequery.query.get_compiler(basequery.db).as_sql(
                with_col_aliases=False
            )[1][0]

            for i in reportclass.getOperationFromResource(
                request, resource_name, reportclass.downstream, depth=0
            ):
                results.append(i)
        elif str(reportclass.objecttype._meta) == "input.operation":
            operation_name = basequery.query.get_compiler(basequery.db).as_sql(
                with_col_aliases=False
            )[1][0]

            for i in reportclass.getOperationFromName(
                request, operation_name, reportclass.downstream, depth=0
            ):
                results.append(i)
        elif str(reportclass.objecttype._meta) == "input.item":
            item_name = basequery.query.get_compiler(basequery.db).as_sql(
                with_col_aliases=False
            )[1][0]

            for i in reportclass.getOperationFromItem(
                request, item_name, reportclass.downstream, depth=0
            ):
                results.append(i)
        else:
            raise Exception("Supply path for an unknown entity")

        # post-process results to calculate leaf field
        parents = [i["parent"] for i in results if i["parent"]]
        for i in results:
            if i["type"] in ["time_per", "fixed_time", "purchase", "distribution"]:
                i["leaf"] = "true" if i["id"] not in parents else "false"
            else:
                i["leaf"] = "false"

        # post-process results for alternate operations
        # a first loop to find the min priority
        d = {}
        for i in results:
            if i["buffers"]:
                for j in i["buffers"]:
                    if j[1] > 0:
                        d[j[0]] = (
                            i["alternate_priority"]
                            if j[0] not in d
                            else min(i["alternate_priority"], d[j[0]])
                        )
        # a second loop to find alternate operations
        alternate_ops = []
        for i in results:
            if i["buffers"]:
                for j in i["buffers"]:
                    if j[1] > 0 and i["alternate_priority"] > d[j[0]]:
                        alternate_ops.append(i["alternate_operation"])

        # a third loop to set the alternate flag
        for i in results:
            if i["type"] not in ("purchase", "distribution", "time_per", "fixed_time"):
                continue
            if (i["operation"] in alternate_ops and not i["parentoper"]) or (
                i["parentoper"] and i["parentoper"] in alternate_ops
            ):
                i["alternate"] = "true"

        for i in results:
            yield i


class UpstreamDemandPath(PathReport):
    downstream = False
    objecttype = Demand


class UpstreamItemPath(PathReport):
    downstream = False
    objecttype = Item


class UpstreamBufferPath(PathReport):
    downstream = False
    objecttype = Buffer

    @classmethod
    def getRoot(reportclass, request, entity):
        from django.core.exceptions import ObjectDoesNotExist

        try:
            buf = (
                Buffer.objects.using(request.database)
                .annotate(name=RawSQL("item_id||' @ '||location_id", ()))
                .get(name=entity)
            )
            if reportclass.downstream:
                return reportclass.findUsage(buf, request.database, 0, 1, 0, True)
            else:
                return reportclass.findReplenishment(
                    buf, request.database, 0, 1, 0, True
                )
        except ObjectDoesNotExist:
            raise Http404("buffer %s doesn't exist" % entity)


class UpstreamResourcePath(PathReport):
    downstream = False
    objecttype = Resource

    @classmethod
    def getRoot(reportclass, request, entity):
        from django.core.exceptions import ObjectDoesNotExist

        try:
            root = Resource.objects.using(request.database).get(name=entity)
        except ObjectDoesNotExist:
            raise Http404("resource %s doesn't exist" % entity)
        return [
            (
                0,
                None,
                i.operation,
                1,
                0,
                None,
                0,
                True,
                i.operation.location.name if i.operation.location else None,
            )
            for i in root.operationresources.using(request.database).all()
        ]


class UpstreamOperationPath(PathReport):
    downstream = False
    objecttype = Operation


class DownstreamItemPath(UpstreamItemPath):
    downstream = True
    objecttype = Item
    title = _("where used")


class DownstreamDemandPath(UpstreamDemandPath):
    downstream = True
    objecttype = Demand
    title = _("where used")


class DownstreamBufferPath(UpstreamBufferPath):
    downstream = True
    objecttype = Buffer
    title = _("where used")


class DownstreamResourcePath(UpstreamResourcePath):
    downstream = True
    objecttype = Resource
    title = _("where used")


class DownstreamOperationPath(UpstreamOperationPath):
    downstream = True
    objecttype = Operation
    title = _("where used")


class BufferList(GridReport):
    title = _("buffers")
    basequeryset = Buffer.objects.all()
    model = Buffer
    frozenColumns = 1
    help_url = "modeling-wizard/master-data/buffers.html"

    rows = (
        GridFieldInteger(
            "id",
            title=_("identifier"),
            key=True,
            formatter="detail",
            extra='"role":"input/buffer"',
            initially_hidden=True,
        ),
        GridFieldText("description", title=_("description")),
        GridFieldText("category", title=_("category"), initially_hidden=True),
        GridFieldText("subcategory", title=_("subcategory"), initially_hidden=True),
        GridFieldText(
            "location",
            title=_("location"),
            field_name="location__name",
            formatter="detail",
            extra='"role":"input/location"',
        ),
        GridFieldText(
            "item",
            title=_("item"),
            field_name="item__name",
            formatter="detail",
            extra='"role":"input/item"',
        ),
        GridFieldText("batch", title=_("batch"), field_name="batch"),
        GridFieldNumber("onhand", title=_("onhand")),
        GridFieldChoice("type", title=_("type"), choices=Buffer.types),
        GridFieldNumber("minimum", title=_("minimum")),
        GridFieldText(
            "minimum_calendar",
            title=_("minimum calendar"),
            field_name="minimum_calendar__name",
            formatter="detail",
            extra='"role":"input/calendar"',
            initially_hidden=True,
        ),
        GridFieldText("source", title=_("source")),
        GridFieldLastModified("lastmodified"),
        # Optional fields referencing the item
        GridFieldText(
            "item__type",
            title=format_lazy("{} - {}", _("item"), _("type")),
            initially_hidden=True,
            editable=False,
        ),
        GridFieldText(
            "item__description",
            title=format_lazy("{} - {}", _("item"), _("description")),
            initially_hidden=True,
            editable=False,
        ),
        GridFieldText(
            "item__category",
            title=format_lazy("{} - {}", _("item"), _("category")),
            initially_hidden=True,
            editable=False,
        ),
        GridFieldText(
            "item__subcategory",
            title=format_lazy("{} - {}", _("item"), _("subcategory")),
            initially_hidden=True,
            editable=False,
        ),
        GridFieldText(
            "item__owner",
            title=format_lazy("{} - {}", _("item"), _("owner")),
            field_name="item__owner__name",
            initially_hidden=True,
            editable=False,
        ),
        GridFieldText(
            "item__source",
            title=format_lazy("{} - {}", _("item"), _("source")),
            initially_hidden=True,
            editable=False,
        ),
        GridFieldLastModified(
            "item__lastmodified",
            title=format_lazy("{} - {}", _("item"), _("last modified")),
            initially_hidden=True,
            editable=False,
        ),
        # Optional fields referencing the location
        GridFieldText(
            "location__description",
            title=format_lazy("{} - {}", _("location"), _("description")),
            initially_hidden=True,
            editable=False,
        ),
        GridFieldText(
            "location__category",
            title=format_lazy("{} - {}", _("location"), _("category")),
            initially_hidden=True,
            editable=False,
        ),
        GridFieldText(
            "location__subcategory",
            title=format_lazy("{} - {}", _("location"), _("subcategory")),
            initially_hidden=True,
            editable=False,
        ),
        GridFieldText(
            "location__available",
            title=format_lazy("{} - {}", _("location"), _("available")),
            initially_hidden=True,
            field_name="location__available__name",
            formatter="detail",
            extra='"role":"input/calendar"',
            editable=False,
        ),
        GridFieldText(
            "location__owner",
            title=format_lazy("{} - {}", _("location"), _("owner")),
            initially_hidden=True,
            field_name="location__owner__name",
            formatter="detail",
            extra='"role":"input/location"',
            editable=False,
        ),
        GridFieldText(
            "location__source",
            title=format_lazy("{} - {}", _("location"), _("source")),
            initially_hidden=True,
            editable=False,
        ),
        GridFieldLastModified(
            "location__lastmodified",
            title=format_lazy("{} - {}", _("location"), _("last modified")),
            initially_hidden=True,
            editable=False,
        ),
    )


class SetupMatrixList(GridReport):
    title = _("setup matrices")
    basequeryset = SetupMatrix.objects.all()
    model = SetupMatrix
    frozenColumns = 1
    help_url = "model-reference/setup-matrices.html"

    rows = (
        GridFieldText(
            "name",
            title=_("name"),
            key=True,
            formatter="detail",
            extra='"role":"input/setupmatrix"',
        ),
        GridFieldText("source", title=_("source")),
        GridFieldLastModified("lastmodified"),
    )


class SetupRuleList(GridReport):
    title = _("setup rules")
    basequeryset = SetupRule.objects.all()
    model = SetupRule
    frozenColumns = 1
    help_url = "model-reference/setup-matrices.html"

    rows = (
        GridFieldInteger(
            "id",
            title=_("identifier"),
            key=True,
            formatter="detail",
            extra='"role":"input/setuprule"',
            initially_hidden=True,
        ),
        GridFieldText(
            "setupmatrix",
            title=_("setup matrix"),
            field_name="setupmatrix__name",
            formatter="detail",
            extra='"role":"input/setupmatrix"',
        ),
        GridFieldInteger("priority", title=_("priority")),
        GridFieldText("fromsetup", title=_("from setup")),
        GridFieldText("tosetup", title=_("to setup")),
        GridFieldDuration("duration", title=_("duration")),
        GridFieldCurrency("cost", title=_("cost"), initially_hidden=True),
        GridFieldText(
            "resource",
            title=_("resource"),
            formatter="detail",
            extra='"role":"input/resource"',
        ),
        GridFieldLastModified("lastmodified"),
    )


class ResourceList(GridReport):
    title = _("resources")
    basequeryset = Resource.objects.all()
    model = Resource
    frozenColumns = 1
    help_url = "modeling-wizard/manufacturing-capacity/resources.html"

    rows = (
        GridFieldText(
            "name",
            title=_("name"),
            key=True,
            formatter="detail",
            extra='"role":"input/resource"',
        ),
        GridFieldText("description", title=_("description")),
        GridFieldText("category", title=_("category"), initially_hidden=True),
        GridFieldText("subcategory", title=_("subcategory"), initially_hidden=True),
        GridFieldText(
            "location",
            title=_("location"),
            field_name="location__name",
            formatter="detail",
            extra='"role":"input/location"',
        ),
        GridFieldText(
            "owner",
            title=_("owner"),
            field_name="owner__name",
            formatter="detail",
            extra='"role":"input/resource"',
            initially_hidden=True,
        ),
        GridFieldChoice("type", title=_("type"), choices=Resource.types),
        GridFieldBool("constrained", title=_("constrained")),
        GridFieldNumber("maximum", title=_("maximum")),
        GridFieldText(
            "maximum_calendar",
            title=_("maximum calendar"),
            field_name="maximum_calendar__name",
            formatter="detail",
            extra='"role":"input/calendar"',
        ),
        GridFieldText(
            "available",
            title=_("available"),
            field_name="available__name",
            formatter="detail",
            extra='"role":"input/calendar"',
        ),
        GridFieldCurrency("cost", title=_("cost"), initially_hidden=True),
        GridFieldDuration("maxearly", title=_("maxearly"), initially_hidden=True),
        GridFieldText(
            "setupmatrix",
            title=_("setup matrix"),
            field_name="setupmatrix__name",
            formatter="detail",
            extra='"role":"input/setupmatrix"',
            initially_hidden=True,
        ),
        GridFieldText("setup", title=_("setup"), initially_hidden=True),
        GridFieldText("source", title=_("source")),
        GridFieldLastModified("lastmodified"),
        GridFieldNumber(
            "efficiency",
            title=_("efficiency %"),
            initially_hidden=True,
            formatter="percentage",
        ),
        GridFieldText(
            "efficiency_calendar",
            title=_("efficiency %% calendar"),
            initially_hidden=True,
            field_name="efficiency_calendar__name",
            formatter="detail",
            extra='"role":"input/calendar"',
        ),
        # Optional fields referencing the location
        GridFieldText(
            "location__description",
            title=format_lazy("{} - {}", _("location"), _("description")),
            initially_hidden=True,
            editable=False,
        ),
        GridFieldText(
            "location__category",
            title=format_lazy("{} - {}", _("location"), _("category")),
            initially_hidden=True,
            editable=False,
        ),
        GridFieldText(
            "location__subcategory",
            title=format_lazy("{} - {}", _("location"), _("subcategory")),
            initially_hidden=True,
            editable=False,
        ),
        GridFieldText(
            "location__available",
            title=format_lazy("{} - {}", _("location"), _("available")),
            initially_hidden=True,
            field_name="location__available__name",
            formatter="detail",
            extra='"role":"input/calendar"',
            editable=False,
        ),
        GridFieldText(
            "location__owner",
            title=format_lazy("{} - {}", _("location"), _("owner")),
            initially_hidden=True,
            field_name="location__owner__name",
            formatter="detail",
            extra='"role":"input/location"',
            editable=False,
        ),
        GridFieldText(
            "location__source",
            title=format_lazy("{} - {}", _("location"), _("source")),
            initially_hidden=True,
            editable=False,
        ),
        GridFieldLastModified(
            "location__lastmodified",
            title=format_lazy("{} - {}", _("location"), _("last modified")),
            initially_hidden=True,
            editable=False,
        ),
    )


class LocationList(GridReport):
    title = _("locations")
    basequeryset = Location.objects.all()
    model = Location
    frozenColumns = 1
    help_url = "modeling-wizard/master-data/locations.html"

    rows = (
        GridFieldText(
            "name",
            title=_("name"),
            key=True,
            formatter="detail",
            extra='"role":"input/location"',
        ),
        GridFieldText("description", title=_("description")),
        GridFieldText("category", title=_("category"), initially_hidden=True),
        GridFieldText("subcategory", title=_("subcategory"), initially_hidden=True),
        GridFieldText(
            "available",
            title=_("available"),
            field_name="available__name",
            formatter="detail",
            extra='"role":"input/calendar"',
        ),
        GridFieldText(
            "owner",
            title=_("owner"),
            field_name="owner__name",
            formatter="detail",
            extra='"role":"input/location"',
        ),
        GridFieldText("source", title=_("source")),
        GridFieldLastModified("lastmodified"),
    )


class CustomerList(GridReport):
    title = _("customers")
    basequeryset = Customer.objects.all()
    model = Customer
    frozenColumns = 1
    help_url = "modeling-wizard/master-data/customers.html"

    rows = (
        GridFieldText(
            "name",
            title=_("name"),
            key=True,
            formatter="detail",
            extra='"role":"input/customer"',
        ),
        GridFieldText("description", title=_("description")),
        GridFieldText("category", title=_("category"), initially_hidden=True),
        GridFieldText("subcategory", title=_("subcategory"), initially_hidden=True),
        GridFieldText(
            "owner",
            title=_("owner"),
            field_name="owner__name",
            formatter="detail",
            extra='"role":"input/customer"',
        ),
        GridFieldText("source", title=_("source")),
        GridFieldLastModified("lastmodified"),
    )


class SupplierList(GridReport):
    title = _("suppliers")
    basequeryset = Supplier.objects.all()
    model = Supplier
    frozenColumns = 1
    help_url = "modeling-wizard/purchasing/suppliers.html"

    rows = (
        GridFieldText(
            "name",
            title=_("name"),
            key=True,
            formatter="detail",
            extra='"role":"input/supplier"',
        ),
        GridFieldText("description", title=_("description")),
        GridFieldText("category", title=_("category"), initially_hidden=True),
        GridFieldText("subcategory", title=_("subcategory"), initially_hidden=True),
        GridFieldText(
            "owner",
            title=_("owner"),
            field_name="owner__name",
            formatter="detail",
            extra='"role":"input/supplier"',
            initially_hidden=True,
        ),
        GridFieldText("source", title=_("source")),
        GridFieldLastModified("lastmodified"),
        GridFieldText(
            "available",
            title=_("available"),
            field_name="available__name",
            formatter="detail",
            extra='"role":"input/calendar"',
            initially_hidden=True,
        ),
    )


class ItemSupplierList(GridReport):
    title = _("item suppliers")
    basequeryset = ItemSupplier.objects.all()
    model = ItemSupplier
    frozenColumns = 1
    help_url = "modeling-wizard/purchasing/item-suppliers.html"

    rows = (
        GridFieldInteger(
            "id",
            title=_("identifier"),
            key=True,
            formatter="detail",
            extra='"role":"input/itemsupplier"',
            initially_hidden=True,
        ),
        GridFieldText(
            "item",
            title=_("item"),
            field_name="item__name",
            formatter="detail",
            extra='"role":"input/item"',
        ),
        GridFieldText(
            "location",
            title=_("location"),
            field_name="location__name",
            formatter="detail",
            extra='"role":"input/location"',
        ),
        GridFieldText(
            "supplier",
            title=_("supplier"),
            field_name="supplier__name",
            formatter="detail",
            extra='"role":"input/supplier"',
        ),
        GridFieldDuration("leadtime", title=_("lead time")),
        GridFieldNumber("sizeminimum", title=_("size minimum")),
        GridFieldNumber("sizemultiple", title=_("size multiple")),
        GridFieldNumber("sizemaximum", title=_("size maximum")),
        GridFieldCurrency("cost", title=_("cost")),
        GridFieldInteger("priority", title=_("priority")),
        GridFieldDuration("fence", title=_("fence"), initially_hidden=True),
        GridFieldDateTime(
            "effective_start", title=_("effective start"), initially_hidden=True
        ),
        GridFieldDateTime(
            "effective_end", title=_("effective end"), initially_hidden=True
        ),
        GridFieldText(
            "resource",
            title=_("resource"),
            field_name="resource__name",
            formatter="detail",
            extra='"role":"input/resource"',
            initially_hidden=True,
        ),
        GridFieldNumber(
            "resource_qty", title=_("resource quantity"), initially_hidden=True
        ),
        GridFieldText("source", title=_("source")),
        GridFieldLastModified("lastmodified"),
        # Optional fields referencing the item
        GridFieldText(
            "item__type",
            title=format_lazy("{} - {}", _("item"), _("type")),
            initially_hidden=True,
            editable=False,
        ),
        GridFieldText(
            "item__description",
            title=format_lazy("{} - {}", _("item"), _("description")),
            initially_hidden=True,
            editable=False,
        ),
        GridFieldText(
            "item__category",
            title=format_lazy("{} - {}", _("item"), _("category")),
            initially_hidden=True,
            editable=False,
        ),
        GridFieldText(
            "item__subcategory",
            title=format_lazy("{} - {}", _("item"), _("subcategory")),
            initially_hidden=True,
            editable=False,
        ),
        GridFieldText(
            "item__owner",
            title=format_lazy("{} - {}", _("item"), _("owner")),
            field_name="item__owner__name",
            initially_hidden=True,
            editable=False,
        ),
        GridFieldText(
            "item__source",
            title=format_lazy("{} - {}", _("item"), _("source")),
            initially_hidden=True,
            editable=False,
        ),
        GridFieldLastModified(
            "item__lastmodified",
            title=format_lazy("{} - {}", _("item"), _("last modified")),
            initially_hidden=True,
            editable=False,
        ),
        # Optional fields referencing the location
        GridFieldText(
            "location__description",
            title=format_lazy("{} - {}", _("location"), _("description")),
            initially_hidden=True,
            editable=False,
        ),
        GridFieldText(
            "location__category",
            title=format_lazy("{} - {}", _("location"), _("category")),
            initially_hidden=True,
            editable=False,
        ),
        GridFieldText(
            "location__subcategory",
            title=format_lazy("{} - {}", _("location"), _("subcategory")),
            initially_hidden=True,
            editable=False,
        ),
        GridFieldText(
            "location__available",
            title=format_lazy("{} - {}", _("location"), _("available")),
            initially_hidden=True,
            field_name="location__available__name",
            formatter="detail",
            extra='"role":"input/calendar"',
            editable=False,
        ),
        GridFieldText(
            "location__owner",
            title=format_lazy("{} - {}", _("location"), _("owner")),
            initially_hidden=True,
            field_name="location__owner__name",
            formatter="detail",
            extra='"role":"input/location"',
            editable=False,
        ),
        GridFieldText(
            "location__source",
            title=format_lazy("{} - {}", _("location"), _("source")),
            initially_hidden=True,
            editable=False,
        ),
        GridFieldLastModified(
            "location__lastmodified",
            title=format_lazy("{} - {}", _("location"), _("last modified")),
            initially_hidden=True,
            editable=False,
        ),
        # Optional fields referencing the supplier
        GridFieldText(
            "supplier__description",
            title=format_lazy("{} - {}", _("supplier"), _("description")),
            initially_hidden=True,
            editable=False,
        ),
        GridFieldText(
            "supplier__category",
            title=format_lazy("{} - {}", _("supplier"), _("category")),
            initially_hidden=True,
            editable=False,
        ),
        GridFieldText(
            "supplier__subcategory",
            title=format_lazy("{} - {}", _("supplier"), _("subcategory")),
            initially_hidden=True,
            editable=False,
        ),
        GridFieldText(
            "supplier__available",
            title=format_lazy("{} - {}", _("supplier"), _("available")),
            field_name="supplier__available__name",
            formatter="detail",
            extra='"role":"input/calendar"',
            initially_hidden=True,
            editable=False,
        ),
        GridFieldText(
            "supplier__source",
            title=format_lazy("{} - {}", _("supplier"), _("source")),
            initially_hidden=True,
            editable=False,
        ),
        GridFieldLastModified(
            "supplier__lastmodified",
            title=format_lazy("{} - {}", _("supplier"), _("last modified")),
            initially_hidden=True,
            editable=False,
        ),
    )


class ItemDistributionList(GridReport):
    title = _("item distributions")
    basequeryset = ItemDistribution.objects.all()
    model = ItemDistribution
    frozenColumns = 1
    help_url = "modeling-wizard/distribution/item-distributions.html"

    rows = (
        GridFieldInteger(
            "id",
            title=_("identifier"),
            key=True,
            formatter="detail",
            extra='"role":"input/itemdistribution"',
            initially_hidden=True,
        ),
        GridFieldText(
            "item",
            title=_("item"),
            field_name="item__name",
            formatter="detail",
            extra='"role":"input/item"',
        ),
        GridFieldText(
            "location",
            title=_("location"),
            field_name="location__name",
            formatter="detail",
            extra='"role":"input/location"',
        ),
        GridFieldText(
            "origin",
            title=_("origin"),
            field_name="origin__name",
            formatter="detail",
            extra='"role":"input/location"',
        ),
        GridFieldDuration("leadtime", title=_("lead time")),
        GridFieldNumber("sizeminimum", title=_("size minimum")),
        GridFieldNumber("sizemultiple", title=_("size multiple")),
        GridFieldNumber("sizemaximum", title=_("size maximum")),
        GridFieldCurrency("cost", title=_("cost"), initially_hidden=True),
        GridFieldInteger("priority", title=_("priority"), initially_hidden=True),
        GridFieldDuration("fence", title=_("fence"), initially_hidden=True),
        GridFieldDateTime(
            "effective_start", title=_("effective start"), initially_hidden=True
        ),
        GridFieldDateTime(
            "effective_end", title=_("effective end"), initially_hidden=True
        ),
        GridFieldText(
            "resource",
            title=_("resource"),
            field_name="resource__name",
            formatter="detail",
            extra='"role":"input/resource"',
            initially_hidden=True,
        ),
        GridFieldNumber(
            "resource_qty", title=_("resource quantity"), initially_hidden=True
        ),
        GridFieldText("source", title=_("source")),
        GridFieldLastModified("lastmodified"),
        # Optional fields referencing the item
        GridFieldText(
            "item__type",
            title=format_lazy("{} - {}", _("item"), _("type")),
            initially_hidden=True,
            editable=False,
        ),
        GridFieldText(
            "item__description",
            title=format_lazy("{} - {}", _("item"), _("description")),
            initially_hidden=True,
            editable=False,
        ),
        GridFieldText(
            "item__category",
            title=format_lazy("{} - {}", _("item"), _("category")),
            initially_hidden=True,
            editable=False,
        ),
        GridFieldText(
            "item__subcategory",
            title=format_lazy("{} - {}", _("item"), _("subcategory")),
            initially_hidden=True,
            editable=False,
        ),
        GridFieldText(
            "item__owner",
            title=format_lazy("{} - {}", _("item"), _("owner")),
            field_name="item__owner__name",
            initially_hidden=True,
            editable=False,
        ),
        GridFieldText(
            "item__source",
            title=format_lazy("{} - {}", _("item"), _("source")),
            initially_hidden=True,
            editable=False,
        ),
        GridFieldLastModified(
            "item__lastmodified",
            title=format_lazy("{} - {}", _("item"), _("last modified")),
            initially_hidden=True,
            editable=False,
        ),
        # Optional fields referencing the location
        GridFieldText(
            "location__description",
            title=format_lazy("{} - {}", _("location"), _("description")),
            initially_hidden=True,
            editable=False,
        ),
        GridFieldText(
            "location__category",
            title=format_lazy("{} - {}", _("location"), _("category")),
            initially_hidden=True,
            editable=False,
        ),
        GridFieldText(
            "location__subcategory",
            title=format_lazy("{} - {}", _("location"), _("subcategory")),
            initially_hidden=True,
            editable=False,
        ),
        GridFieldText(
            "location__available",
            title=format_lazy("{} - {}", _("location"), _("available")),
            initially_hidden=True,
            field_name="location__available__name",
            formatter="detail",
            extra='"role":"input/calendar"',
            editable=False,
        ),
        GridFieldText(
            "location__owner",
            title=format_lazy("{} - {}", _("location"), _("owner")),
            initially_hidden=True,
            field_name="location__owner__name",
            formatter="detail",
            extra='"role":"input/location"',
            editable=False,
        ),
        GridFieldText(
            "location__source",
            title=format_lazy("{} - {}", _("location"), _("source")),
            initially_hidden=True,
            editable=False,
        ),
        GridFieldLastModified(
            "location__lastmodified",
            title=format_lazy("{} - {}", _("location"), _("last modified")),
            initially_hidden=True,
            editable=False,
        ),
        # Optional fields referencing the origin location
        GridFieldText(
            "origin__description",
            title=format_lazy("{} - {}", _("origin"), _("description")),
            initially_hidden=True,
            editable=False,
        ),
        GridFieldText(
            "origin__category",
            title=format_lazy("{} - {}", _("origin"), _("category")),
            initially_hidden=True,
            editable=False,
        ),
        GridFieldText(
            "origin__subcategory",
            title=format_lazy("{} - {}", _("origin"), _("subcategory")),
            initially_hidden=True,
            editable=False,
        ),
        GridFieldText(
            "origin__available",
            title=format_lazy("{} - {}", _("origin"), _("available")),
            initially_hidden=True,
            field_name="origin__available__name",
            formatter="detail",
            extra='"role":"input/calendar"',
            editable=False,
        ),
        GridFieldText(
            "origin__owner",
            title=format_lazy("{} - {}", _("origin"), _("owner")),
            initially_hidden=True,
            field_name="origin__owner__name",
            formatter="detail",
            extra='"role":"input/location"',
            editable=False,
        ),
        GridFieldText(
            "origin__source",
            title=format_lazy("{} - {}", _("origin"), _("source")),
            initially_hidden=True,
            editable=False,
        ),
        GridFieldLastModified(
            "origin__lastmodified",
            title=format_lazy("{} - {}", _("origin"), _("last modified")),
            initially_hidden=True,
            editable=False,
        ),
    )


class ItemList(GridReport):
    title = _("items")
    basequeryset = Item.objects.all()
    model = Item
    frozenColumns = 1
    editable = True
    help_url = "modeling-wizard/master-data/items.html"

    rows = (
        GridFieldText(
            "name",
            title=_("name"),
            key=True,
            formatter="detail",
            extra='"role":"input/item"',
        ),
        GridFieldText("description", title=_("description")),
        GridFieldText("category", title=_("category"), initially_hidden=True),
        GridFieldText("subcategory", title=_("subcategory"), initially_hidden=True),
        GridFieldText(
            "owner",
            title=_("owner"),
            field_name="owner__name",
            formatter="detail",
            extra='"role":"input/item"',
        ),
        GridFieldCurrency("cost", title=_("cost")),
        GridFieldChoice("type", title=_("type"), choices=Item.types),
        GridFieldText("source", title=_("source")),
        GridFieldLastModified("lastmodified"),
    )


class SkillList(GridReport):
    title = _("skills")
    basequeryset = Skill.objects.all()
    model = Skill
    frozenColumns = 1
    help_url = "model-reference/skills.html"

    rows = (
        GridFieldText(
            "name",
            title=_("name"),
            key=True,
            formatter="detail",
            extra='"role":"input/skill"',
        ),
        GridFieldText("source", title=_("source")),
        GridFieldLastModified("lastmodified"),
    )


class ResourceSkillList(GridReport):
    title = _("resource skills")
    basequeryset = ResourceSkill.objects.all()
    model = ResourceSkill
    frozenColumns = 1
    help_url = "model-reference/resource-skills.html"

    rows = (
        GridFieldInteger(
            "id",
            title=_("identifier"),
            key=True,
            formatter="detail",
            extra='"role":"input/resourceskill"',
        ),
        GridFieldText(
            "resource",
            title=_("resource"),
            field_name="resource__name",
            formatter="detail",
            extra='"role":"input/resource"',
        ),
        GridFieldText(
            "skill",
            title=_("skill"),
            field_name="skill__name",
            formatter="detail",
            extra='"role":"input/skill"',
        ),
        GridFieldDateTime(
            "effective_start", title=_("effective start"), initially_hidden=True
        ),
        GridFieldDateTime(
            "effective_end", title=_("effective end"), initially_hidden=True
        ),
        GridFieldInteger("priority", title=_("priority"), initially_hidden=True),
        GridFieldText("source", title=_("source")),
        GridFieldLastModified("lastmodified"),
    )


class OperationResourceList(GridReport):
    title = _("operation resources")
    basequeryset = OperationResource.objects.all()
    model = OperationResource
    frozenColumns = 1
    help_url = "modeling-wizard/manufacturing-capacity/operation-resources.html"

    rows = (
        GridFieldInteger(
            "id",
            title=_("identifier"),
            key=True,
            formatter="detail",
            extra='"role":"input/operationresource"',
            initially_hidden=True,
        ),
        GridFieldText(
            "operation",
            title=_("operation"),
            field_name="operation__name",
            formatter="detail",
            extra='"role":"input/operation"',
        ),
        GridFieldText(
            "resource",
            title=_("resource"),
            field_name="resource__name",
            formatter="detail",
            extra='"role":"input/resource"',
        ),
        GridFieldText(
            "skill",
            title=_("skill"),
            field_name="skill__name",
            formatter="detail",
            extra='"role":"input/skill"',
            initially_hidden=True,
        ),
        GridFieldNumber("quantity", title=_("quantity")),
        GridFieldNumber(
            "quantity_fixed", title=_("quantity fixed"), initially_hidden=True
        ),
        GridFieldDateTime(
            "effective_start", title=_("effective start"), initially_hidden=True
        ),
        GridFieldDateTime(
            "effective_end", title=_("effective end"), initially_hidden=True
        ),
        GridFieldText("name", title=_("name"), initially_hidden=True),
        GridFieldInteger("priority", title=_("priority"), initially_hidden=True),
        GridFieldText("setup", title=_("setup"), initially_hidden=True),
        GridFieldChoice(
            "search", title=_("search mode"), choices=searchmode, initially_hidden=True
        ),
        GridFieldText("source", title=_("source")),
        GridFieldLastModified("lastmodified"),
        # Operation fields
        GridFieldText(
            "operation__description",
            title=format_lazy("{} - {}", _("operation"), _("description")),
            initially_hidden=True,
            editable=False,
        ),
        GridFieldText(
            "operation__category",
            title=format_lazy("{} - {}", _("operation"), _("category")),
            initially_hidden=True,
            editable=False,
        ),
        GridFieldText(
            "operation__subcategory",
            title=format_lazy("{} - {}", _("operation"), _("subcategory")),
            initially_hidden=True,
            editable=False,
        ),
        GridFieldChoice(
            "operation__type",
            title=format_lazy("{} - {}", _("operation"), _("type")),
            choices=Operation.types,
            initially_hidden=True,
            editable=False,
        ),
        GridFieldDuration(
            "operation__duration",
            title=format_lazy("{} - {}", _("operation"), _("duration")),
            initially_hidden=True,
            editable=False,
        ),
        GridFieldDuration(
            "operation__duration_per",
            title=format_lazy("{} - {}", _("operation"), _("duration per unit")),
            initially_hidden=True,
            editable=False,
        ),
        GridFieldDuration(
            "operation__fence",
            title=format_lazy("{} - {}", _("operation"), _("release fence")),
            initially_hidden=True,
            editable=False,
        ),
        GridFieldDuration(
            "operation__posttime",
            title=format_lazy("{} - {}", _("operation"), _("post-op time")),
            initially_hidden=True,
            editable=False,
        ),
        GridFieldNumber(
            "operation__sizeminimum",
            title=format_lazy("{} - {}", _("operation"), _("size minimum")),
            initially_hidden=True,
            editable=False,
        ),
        GridFieldNumber(
            "operation__sizemultiple",
            title=format_lazy("{} - {}", _("operation"), _("size multiple")),
            initially_hidden=True,
            editable=False,
        ),
        GridFieldNumber(
            "operation__sizemaximum",
            title=format_lazy("{} - {}", _("operation"), _("size maximum")),
            initially_hidden=True,
            editable=False,
        ),
        GridFieldInteger(
            "operation__priority",
            title=format_lazy("{} - {}", _("operation"), _("priority")),
            initially_hidden=True,
            editable=False,
        ),
        GridFieldDateTime(
            "operation__effective_start",
            title=format_lazy("{} - {}", _("operation"), _("effective start")),
            initially_hidden=True,
            editable=False,
        ),
        GridFieldDateTime(
            "operation__effective_end",
            title=format_lazy("{} - {}", _("operation"), _("effective end")),
            initially_hidden=True,
            editable=False,
        ),
        GridFieldCurrency(
            "operation__cost",
            title=format_lazy("{} - {}", _("operation"), _("cost")),
            initially_hidden=True,
            editable=False,
        ),
        GridFieldChoice(
            "operation__search",
            title=format_lazy("{} - {}", _("operation"), _("search mode")),
            choices=searchmode,
            initially_hidden=True,
            editable=False,
        ),
        GridFieldText(
            "operation__source",
            title=format_lazy("{} - {}", _("operation"), _("source")),
            initially_hidden=True,
            editable=False,
        ),
        GridFieldLastModified(
            "operation__lastmodified",
            title=format_lazy("{} - {}", _("operation"), _("last modified")),
            initially_hidden=True,
            editable=False,
        ),
        # Optional fields referencing the resource
        GridFieldText(
            "resource__description",
            editable=False,
            initially_hidden=True,
            title=format_lazy("{} - {}", _("resource"), _("description")),
        ),
        GridFieldText(
            "resource__category",
            editable=False,
            initially_hidden=True,
            title=format_lazy("{} - {}", _("resource"), _("category")),
        ),
        GridFieldText(
            "resource__subcategory",
            editable=False,
            initially_hidden=True,
            title=format_lazy("{} - {}", _("resource"), _("subcategory")),
        ),
        GridFieldText(
            "resource__type",
            editable=False,
            initially_hidden=True,
            title=format_lazy("{} - {}", _("resource"), _("type")),
        ),
        GridFieldNumber(
            "resource__maximum",
            editable=False,
            initially_hidden=True,
            title=format_lazy("{} - {}", _("resource"), _("maximum")),
        ),
        GridFieldText(
            "resource__maximum_calendar",
            editable=False,
            initially_hidden=True,
            title=format_lazy("{} - {}", _("resource"), _("maximum calendar")),
            field_name="resource__maximum_calendar__name",
            formatter="detail",
            extra='"role":"input/calendar"',
        ),
        GridFieldCurrency(
            "resource__cost",
            editable=False,
            initially_hidden=True,
            title=format_lazy("{} - {}", _("resource"), _("cost")),
        ),
        GridFieldDuration(
            "resource__maxearly",
            editable=False,
            initially_hidden=True,
            title=format_lazy("{} - {}", _("resource"), _("maxearly")),
        ),
        GridFieldText(
            "resource__setupmatrix",
            editable=False,
            initially_hidden=True,
            title=format_lazy("{} - {}", _("resource"), _("setupmatrix")),
            field_name="resource__setupmatrix__name",
            formatter="detail",
            extra='"role":"input/setupmatrix"',
        ),
        GridFieldText(
            "resource__setup",
            editable=False,
            initially_hidden=True,
            title=format_lazy("{} - {}", _("resource"), _("setup")),
        ),
        GridFieldText(
            "resource__location",
            editable=False,
            initially_hidden=True,
            title=format_lazy("{} - {}", _("resource"), _("location")),
            field_name="resource__location__name",
            formatter="detail",
            extra='"role":"input/location"',
        ),
    )


class OperationMaterialList(GridReport):
    title = _("operation materials")
    basequeryset = OperationMaterial.objects.all()
    model = OperationMaterial
    frozenColumns = 1
    help_url = "modeling-wizard/manufacturing-bom/operation-materials.html"

    rows = (
        GridFieldInteger(
            "id",
            title=_("identifier"),
            key=True,
            formatter="detail",
            extra='"role":"input/operationmaterial"',
            initially_hidden=True,
        ),
        GridFieldText(
            "operation",
            title=_("operation"),
            field_name="operation__name",
            formatter="detail",
            extra='"role":"input/operation"',
        ),
        GridFieldText(
            "item",
            title=_("item"),
            field_name="item__name",
            formatter="detail",
            extra='"role":"input/item"',
        ),
        GridFieldChoice("type", title=_("type"), choices=OperationMaterial.types),
        GridFieldNumber("quantity", title=_("quantity")),
        GridFieldDateTime(
            "effective_start", title=_("effective start"), initially_hidden=True
        ),
        GridFieldDateTime(
            "effective_end", title=_("effective end"), initially_hidden=True
        ),
        GridFieldText("name", title=_("name"), initially_hidden=True),
        GridFieldInteger("priority", title=_("priority"), initially_hidden=True),
        GridFieldChoice(
            "search", title=_("search mode"), choices=searchmode, initially_hidden=True
        ),
        GridFieldText("source", title=_("source")),
        GridFieldLastModified("lastmodified"),
        GridFieldNumber(
            "transferbatch", title=_("transfer batch quantity"), initially_hidden=True
        ),
        GridFieldDuration("offset", title=_("offset"), initially_hidden=True),
        GridFieldNumber("quantity_fixed", title=_("fixed quantity")),
        # Operation fields
        GridFieldText(
            "operation__description",
            title=format_lazy("{} - {}", _("operation"), _("description")),
            initially_hidden=True,
            editable=False,
        ),
        GridFieldText(
            "operation__category",
            title=format_lazy("{} - {}", _("operation"), _("category")),
            initially_hidden=True,
            editable=False,
        ),
        GridFieldText(
            "operation__subcategory",
            title=format_lazy("{} - {}", _("operation"), _("subcategory")),
            initially_hidden=True,
            editable=False,
        ),
        GridFieldChoice(
            "operation__type",
            title=format_lazy("{} - {}", _("operation"), _("type")),
            choices=Operation.types,
            initially_hidden=True,
            editable=False,
        ),
        GridFieldDuration(
            "operation__duration",
            title=format_lazy("{} - {}", _("operation"), _("duration")),
            initially_hidden=True,
            editable=False,
        ),
        GridFieldDuration(
            "operation__duration_per",
            title=format_lazy("{} - {}", _("operation"), _("duration per unit")),
            initially_hidden=True,
            editable=False,
        ),
        GridFieldDuration(
            "operation__fence",
            title=format_lazy("{} - {}", _("operation"), _("release fence")),
            initially_hidden=True,
            editable=False,
        ),
        GridFieldDuration(
            "operation__posttime",
            title=format_lazy("{} - {}", _("operation"), _("post-op time")),
            initially_hidden=True,
            editable=False,
        ),
        GridFieldNumber(
            "operation__sizeminimum",
            title=format_lazy("{} - {}", _("operation"), _("size minimum")),
            initially_hidden=True,
            editable=False,
        ),
        GridFieldNumber(
            "operation__sizemultiple",
            title=format_lazy("{} - {}", _("operation"), _("size multiple")),
            initially_hidden=True,
            editable=False,
        ),
        GridFieldNumber(
            "operation__sizemaximum",
            title=format_lazy("{} - {}", _("operation"), _("size maximum")),
            initially_hidden=True,
            editable=False,
        ),
        GridFieldInteger(
            "operation__priority",
            title=format_lazy("{} - {}", _("operation"), _("priority")),
            initially_hidden=True,
            editable=False,
        ),
        GridFieldDateTime(
            "operation__effective_start",
            title=format_lazy("{} - {}", _("operation"), _("effective start")),
            initially_hidden=True,
            editable=False,
        ),
        GridFieldDateTime(
            "operation__effective_end",
            title=format_lazy("{} - {}", _("operation"), _("effective end")),
            initially_hidden=True,
            editable=False,
        ),
        GridFieldCurrency(
            "operation__cost",
            title=format_lazy("{} - {}", _("operation"), _("cost")),
            initially_hidden=True,
            editable=False,
        ),
        GridFieldChoice(
            "operation__search",
            title=format_lazy("{} - {}", _("operation"), _("search mode")),
            choices=searchmode,
            initially_hidden=True,
            editable=False,
        ),
        GridFieldText(
            "operation__source",
            title=format_lazy("{} - {}", _("operation"), _("source")),
            initially_hidden=True,
            editable=False,
        ),
        GridFieldLastModified(
            "operation__lastmodified",
            title=format_lazy("{} - {}", _("operation"), _("last modified")),
            initially_hidden=True,
            editable=False,
        ),
        # Optional fields referencing the item
        GridFieldText(
            "item__type",
            title=format_lazy("{} - {}", _("item"), _("type")),
            initially_hidden=True,
            editable=False,
        ),
        GridFieldText(
            "item__description",
            title=format_lazy("{} - {}", _("item"), _("description")),
            initially_hidden=True,
            editable=False,
        ),
        GridFieldText(
            "item__category",
            title=format_lazy("{} - {}", _("item"), _("category")),
            initially_hidden=True,
            editable=False,
        ),
        GridFieldText(
            "item__subcategory",
            title=format_lazy("{} - {}", _("item"), _("subcategory")),
            initially_hidden=True,
            editable=False,
        ),
        GridFieldText(
            "item__owner",
            title=format_lazy("{} - {}", _("item"), _("owner")),
            field_name="item__owner__name",
            initially_hidden=True,
            editable=False,
        ),
        GridFieldCurrency(
            "item__cost",
            title=format_lazy("{} - {}", _("item"), _("cost")),
            initially_hidden=True,
            editable=False,
        ),
        GridFieldText(
            "item__source",
            title=format_lazy("{} - {}", _("item"), _("source")),
            initially_hidden=True,
            editable=False,
        ),
        GridFieldLastModified(
            "item__lastmodified",
            title=format_lazy("{} - {}", _("item"), _("last modified")),
            initially_hidden=True,
            editable=False,
        ),
    )


class DemandList(GridReport):
    template = "input/demand.html"
    title = _("sales orders")
    model = Demand
    frozenColumns = 1
    help_url = "modeling-wizard/master-data/sales-orders.html"

    @classmethod
    def initialize(reportclass, request):
        if reportclass._attributes_added != 2:
            reportclass._attributes_added = 2
            reportclass.attr_sql = ""
            # Adding custom item attributes
            for f in getAttributeFields(
                Item, related_name_prefix="item", initially_hidden=True
            ):
                reportclass.rows += (f,)
                reportclass.attr_sql += "item.%s, " % f.name.split("__")[-1]
            # Adding custom location attributes
            for f in getAttributeFields(
                Location, related_name_prefix="location", initially_hidden=True
            ):
                reportclass.rows += (f,)
                reportclass.attr_sql += "location.%s, " % f.name.split("__")[-1]

    @classmethod
    def basequeryset(reportclass, request, *args, **kwargs):

        q = Demand.objects.all()

        if "item" in request.GET:
            item = Item.objects.using(request.database).get(
                name__exact=unquote(request.GET["item"])
            )
            q = q.filter(item__lft__gte=item.lft, item__lft__lt=item.rght)
        if "location" in request.GET:
            location = Location.objects.using(request.database).get(
                name__exact=unquote(request.GET["location"])
            )
            q = q.filter(
                location__lft__gte=location.lft, location__lft__lt=location.rght
            )
        if "customer" in request.GET:
            customer = Customer.objects.using(request.database).get(
                name__exact=unquote(request.GET["customer"])
            )
            q = q.filter(customer_lft__gte=customer.lft, customer_lft__lt=customer.rght)
        if "status_in" in request.GET:
            status = unquote(request.GET["status_in"])

            q = q.filter(status__in=status.split(","))

        return q

    rows = (
        GridFieldText(
            "name",
            title=_("name"),
            key=True,
            formatter="detail",
            extra='"role":"input/demand"',
        ),
        GridFieldText(
            "item",
            title=_("item"),
            field_name="item__name",
            formatter="detail",
            extra='"role":"input/item"',
        ),
        GridFieldText("batch", title=_("batch"), initially_hidden=True),
        GridFieldText(
            "location",
            title=_("location"),
            field_name="location__name",
            formatter="detail",
            extra='"role":"input/location"',
        ),
        GridFieldText(
            "customer",
            title=_("customer"),
            field_name="customer__name",
            formatter="detail",
            extra='"role":"input/customer"',
        ),
        GridFieldChoice("status", title=_("status"), choices=Demand.demandstatus),
        GridFieldNumber("quantity", title=_("quantity")),
        GridFieldDateTime("due", title=_("due")),
        GridFieldDuration(
            "delay", title=_("delay"), editable=False, extra='"formatter":delayfmt'
        ),
        GridFieldNumber(
            "plannedquantity",
            title=_("planned quantity"),
            editable=False,
            extra='"formatoptions":{"defaultValue":""}, "cellattr":plannedquantitycellattr',
        ),
        GridFieldDateTime("deliverydate", title=_("delivery date"), editable=False),
        GridFieldText("description", title=_("description"), initially_hidden=True),
        GridFieldText("category", title=_("category"), initially_hidden=True),
        GridFieldText("subcategory", title=_("subcategory"), initially_hidden=True),
        GridFieldText(
            "operation",
            title=_("delivery operation"),
            field_name="operation__name",
            formatter="detail",
            extra='"role":"input/operation"',
            initially_hidden=True,
        ),
        GridFieldInteger("priority", title=_("priority")),
        GridFieldText(
            "owner",
            title=_("owner"),
            field_name="owner__name",
            formatter="detail",
            extra='"role":"input/demand"',
            initially_hidden=True,
        ),
        GridFieldDuration(
            "maxlateness", title=_("maximum lateness"), initially_hidden=True
        ),
        GridFieldNumber(
            "minshipment", title=_("minimum shipment"), initially_hidden=True
        ),
        GridFieldText("batch", title=_("batch"), field_name="batch"),
        GridFieldText("source", title=_("source")),
        GridFieldLastModified("lastmodified"),
        # Optional fields referencing the item
        GridFieldText(
            "item__type",
            title=format_lazy("{} - {}", _("item"), _("type")),
            initially_hidden=True,
            editable=False,
        ),
        GridFieldText(
            "item__description",
            title=format_lazy("{} - {}", _("item"), _("description")),
            initially_hidden=True,
            editable=False,
        ),
        GridFieldText(
            "item__category",
            title=format_lazy("{} - {}", _("item"), _("category")),
            initially_hidden=True,
            editable=False,
        ),
        GridFieldText(
            "item__subcategory",
            title=format_lazy("{} - {}", _("item"), _("subcategory")),
            initially_hidden=True,
            editable=False,
        ),
        GridFieldText(
            "item__owner",
            title=format_lazy("{} - {}", _("item"), _("owner")),
            field_name="item__owner__name",
            initially_hidden=True,
            editable=False,
            formatter="detail",
            extra='"role":"input/item"',
        ),
        GridFieldCurrency(
            "item__cost",
            title=format_lazy("{} - {}", _("item"), _("cost")),
            initially_hidden=True,
            editable=False,
        ),
        GridFieldText(
            "item__source",
            title=format_lazy("{} - {}", _("item"), _("source")),
            initially_hidden=True,
            editable=False,
        ),
        GridFieldLastModified(
            "item__lastmodified",
            title=format_lazy("{} - {}", _("item"), _("last modified")),
            initially_hidden=True,
            editable=False,
        ),
        # Optional fields referencing the location
        GridFieldText(
            "location__description",
            title=format_lazy("{} - {}", _("location"), _("description")),
            initially_hidden=True,
            editable=False,
        ),
        GridFieldText(
            "location__category",
            title=format_lazy("{} - {}", _("location"), _("category")),
            initially_hidden=True,
            editable=False,
        ),
        GridFieldText(
            "location__subcategory",
            title=format_lazy("{} - {}", _("location"), _("subcategory")),
            initially_hidden=True,
            editable=False,
        ),
        GridFieldText(
            "location__available",
            title=format_lazy("{} - {}", _("location"), _("available")),
            initially_hidden=True,
            field_name="location__available__name",
            formatter="detail",
            extra='"role":"input/calendar"',
            editable=False,
        ),
        GridFieldText(
            "location__owner",
            title=format_lazy("{} - {}", _("location"), _("owner")),
            initially_hidden=True,
            field_name="location__owner__name",
            formatter="detail",
            extra='"role":"input/location"',
            editable=False,
        ),
        GridFieldText(
            "location__source",
            title=format_lazy("{} - {}", _("location"), _("source")),
            initially_hidden=True,
            editable=False,
        ),
        GridFieldLastModified(
            "location__lastmodified",
            title=format_lazy("{} - {}", _("location"), _("last modified")),
            initially_hidden=True,
            editable=False,
        ),
        # Optional fields referencing the customer
        GridFieldText(
            "customer__description",
            title=format_lazy("{} - {}", _("customer"), _("description")),
            initially_hidden=True,
            editable=False,
        ),
        GridFieldText(
            "customer__category",
            title=format_lazy("{} - {}", _("customer"), _("category")),
            initially_hidden=True,
            editable=False,
        ),
        GridFieldText(
            "customer__subcategory",
            title=format_lazy("{} - {}", _("customer"), _("subcategory")),
            initially_hidden=True,
            editable=False,
        ),
        GridFieldText(
            "customer__owner",
            title=format_lazy("{} - {}", _("customer"), _("owner")),
            initially_hidden=True,
            field_name="customer__owner__name",
            formatter="detail",
            extra='"role":"input/customer"',
            editable=False,
        ),
        GridFieldText(
            "customer__source",
            title=format_lazy("{} - {}", _("customer"), _("source")),
            initially_hidden=True,
            editable=False,
        ),
        GridFieldLastModified(
            "customer__lastmodified",
            title=format_lazy("{} - {}", _("customer"), _("last modified")),
            initially_hidden=True,
            editable=False,
        ),
    )

    if settings.ERP_CONNECTOR:
        actions = [
            {
                "name": "erp_incr_export",
                "label": format_lazy("export to {erp}", erp=settings.ERP_CONNECTOR),
                "function": "ERPconnection.SODepExport(jQuery('#grid'),'SO')",
            }
        ]
    else:
        actions = [
            {
                "name": "inquiry",
                "label": format_lazy(
                    _("change status to {status}"), status=_("inquiry")
                ),
                "function": "grid.setStatus('inquiry')",
            },
            {
                "name": "quote",
                "label": format_lazy(_("change status to {status}"), status=_("quote")),
                "function": "grid.setStatus('quote')",
            },
            {
                "name": "open",
                "label": format_lazy(_("change status to {status}"), status=_("open")),
                "function": "grid.setStatus('open')",
            },
            {
                "name": "closed",
                "label": format_lazy(
                    _("change status to {status}"), status=_("closed")
                ),
                "function": "grid.setStatus('closed')",
            },
            {
                "name": "canceled",
                "label": format_lazy(
                    _("change status to {status}"), status=_("canceled")
                ),
                "function": "grid.setStatus('canceled')",
            },
        ]


class CalendarList(GridReport):
    title = _("calendars")
    basequeryset = Calendar.objects.all()
    model = Calendar
    frozenColumns = 1
    help_url = "model-reference/calendars.html"

    rows = (
        GridFieldText(
            "name",
            title=_("name"),
            key=True,
            formatter="detail",
            extra='"role":"input/calendar"',
        ),
        GridFieldText("description", title=_("description")),
        GridFieldText("category", title=_("category"), initially_hidden=True),
        GridFieldText("subcategory", title=_("subcategory"), initially_hidden=True),
        GridFieldNumber("defaultvalue", title=_("default value")),
        GridFieldText("source", title=_("source")),
        GridFieldLastModified("lastmodified"),
    )


class CalendarBucketList(GridReport):
    title = _("calendar buckets")
    basequeryset = CalendarBucket.objects.all()
    model = CalendarBucket
    frozenColumns = 1
    help_url = "model-reference/calendar-buckets.html"

    rows = (
        GridFieldInteger(
            "id",
            title=_("identifier"),
            formatter="detail",
            extra='"role":"input/calendarbucket"',
            initially_hidden=True,
        ),
        GridFieldText(
            "calendar",
            title=_("calendar"),
            field_name="calendar__name",
            formatter="detail",
            extra='"role":"input/calendar"',
        ),
        GridFieldDateTime("startdate", title=_("start date")),
        GridFieldDateTime("enddate", title=_("end date")),
        GridFieldNumber("value", title=_("value")),
        GridFieldInteger("priority", title=_("priority")),
        GridFieldBool("monday", title=_("Monday")),
        GridFieldBool("tuesday", title=_("Tuesday")),
        GridFieldBool("wednesday", title=_("Wednesday")),
        GridFieldBool("thursday", title=_("Thursday")),
        GridFieldBool("friday", title=_("Friday")),
        GridFieldBool("saturday", title=_("Saturday")),
        GridFieldBool("sunday", title=_("Sunday")),
        GridFieldTime("starttime", title=_("start time")),
        GridFieldTime("endtime", title=_("end time")),
        GridFieldText(
            "source", title=_("source")
        ),  # Not really right, since the engine doesn't read or store it
        GridFieldLastModified("lastmodified"),
    )


class OperationList(GridReport):
    title = _("operations")
    basequeryset = Operation.objects.all()
    model = Operation
    frozenColumns = 1
    help_url = "modeling-wizard/manufacturing-bom/operations.html"

    rows = (
        GridFieldText(
            "name",
            title=_("name"),
            key=True,
            formatter="detail",
            extra='"role":"input/operation"',
        ),
        GridFieldText("description", title=_("description")),
        GridFieldText("category", title=_("category"), initially_hidden=True),
        GridFieldText("subcategory", title=_("subcategory"), initially_hidden=True),
        GridFieldChoice("type", title=_("type"), choices=Operation.types),
        GridFieldText(
            "item",
            title=_("item"),
            field_name="item__name",
            formatter="detail",
            extra='"role":"input/item"',
        ),
        GridFieldText(
            "location",
            title=_("location"),
            field_name="location__name",
            formatter="detail",
            extra='"role":"input/location"',
        ),
        GridFieldDuration("duration", title=_("duration")),
        GridFieldDuration("duration_per", title=_("duration per unit")),
        GridFieldDuration("fence", title=_("release fence"), initially_hidden=True),
        GridFieldDuration("posttime", title=_("post-op time"), initially_hidden=True),
        GridFieldNumber("sizeminimum", title=_("size minimum"), initially_hidden=True),
        GridFieldNumber(
            "sizemultiple", title=_("size multiple"), initially_hidden=True
        ),
        GridFieldNumber("sizemaximum", title=_("size maximum"), initially_hidden=True),
        GridFieldText(
            "available",
            title=_("available"),
            field_name="available__name",
            formatter="detail",
            extra='"role":"input/calendar"',
        ),
        GridFieldText(
            "owner",
            title=_("owner"),
            field_name="owner__name",
            formatter="detail",
            extra='"role":"input/operation"',
        ),
        GridFieldInteger("priority", title=_("priority"), initially_hidden=True),
        GridFieldDateTime(
            "effective_start", title=_("effective start"), initially_hidden=True
        ),
        GridFieldDateTime(
            "effective_end", title=_("effective end"), initially_hidden=True
        ),
        GridFieldCurrency("cost", title=_("cost"), initially_hidden=True),
        GridFieldChoice(
            "search", title=_("search mode"), choices=searchmode, initially_hidden=True
        ),
        GridFieldText("source", title=_("source")),
        GridFieldLastModified("lastmodified"),
    )


class SubOperationList(GridReport):
    title = _("suboperations")
    basequeryset = SubOperation.objects.all()
    model = SubOperation
    frozenColumns = 1
    help_url = "model-reference/suboperations.html"

    rows = (
        GridFieldInteger("id", title=_("identifier"), key=True, initially_hidden=True),
        GridFieldText(
            "operation",
            title=_("operation"),
            field_name="operation__name",
            formatter="detail",
            extra='"role":"input/operation"',
        ),
        GridFieldText(
            "suboperation",
            title=_("suboperation"),
            field_name="suboperation__name",
            formatter="detail",
            extra='"role":"input/operation"',
        ),
        GridFieldInteger("priority", title=_("priority")),
        GridFieldDateTime(
            "effective_start", title=_("effective start"), initially_hidden=True
        ),
        GridFieldDateTime(
            "effective_end", title=_("effective end"), initially_hidden=True
        ),
        GridFieldText("source", title=_("source")),
        GridFieldLastModified("lastmodified"),
        # Operation fields
        GridFieldText(
            "operation__description",
            title=format_lazy("{} - {}", _("operation"), _("description")),
            initially_hidden=True,
            editable=False,
        ),
        GridFieldText(
            "operation__category",
            title=format_lazy("{} - {}", _("operation"), _("category")),
            initially_hidden=True,
            editable=False,
        ),
        GridFieldText(
            "operation__subcategory",
            title=format_lazy("{} - {}", _("operation"), _("subcategory")),
            initially_hidden=True,
            editable=False,
        ),
        GridFieldChoice(
            "operation__type",
            title=format_lazy("{} - {}", _("operation"), _("type")),
            choices=Operation.types,
            initially_hidden=True,
            editable=False,
        ),
        GridFieldDuration(
            "operation__duration",
            title=format_lazy("{} - {}", _("operation"), _("duration")),
            initially_hidden=True,
            editable=False,
        ),
        GridFieldDuration(
            "operation__duration_per",
            title=format_lazy("{} - {}", _("operation"), _("duration per unit")),
            initially_hidden=True,
            editable=False,
        ),
        GridFieldDuration(
            "operation__fence",
            title=format_lazy("{} - {}", _("operation"), _("release fence")),
            initially_hidden=True,
            editable=False,
        ),
        GridFieldDuration(
            "operation__posttime",
            title=format_lazy("{} - {}", _("operation"), _("post-op time")),
            initially_hidden=True,
            editable=False,
        ),
        GridFieldNumber(
            "operation__sizeminimum",
            title=format_lazy("{} - {}", _("operation"), _("size minimum")),
            initially_hidden=True,
            editable=False,
        ),
        GridFieldNumber(
            "operation__sizemultiple",
            title=format_lazy("{} - {}", _("operation"), _("size multiple")),
            initially_hidden=True,
            editable=False,
        ),
        GridFieldNumber(
            "operation__sizemaximum",
            title=format_lazy("{} - {}", _("operation"), _("size maximum")),
            initially_hidden=True,
            editable=False,
        ),
        GridFieldInteger(
            "operation__priority",
            title=format_lazy("{} - {}", _("operation"), _("priority")),
            initially_hidden=True,
            editable=False,
        ),
        GridFieldDateTime(
            "operation__effective_start",
            title=format_lazy("{} - {}", _("operation"), _("effective start")),
            initially_hidden=True,
            editable=False,
        ),
        GridFieldDateTime(
            "operation__effective_end",
            title=format_lazy("{} - {}", _("operation"), _("effective end")),
            initially_hidden=True,
            editable=False,
        ),
        GridFieldCurrency(
            "operation__cost",
            title=format_lazy("{} - {}", _("operation"), _("cost")),
            initially_hidden=True,
            editable=False,
        ),
        GridFieldChoice(
            "operation__search",
            title=format_lazy("{} - {}", _("operation"), _("search mode")),
            choices=searchmode,
            initially_hidden=True,
            editable=False,
        ),
        GridFieldText(
            "operation__source",
            title=format_lazy("{} - {}", _("operation"), _("source")),
            initially_hidden=True,
            editable=False,
        ),
        GridFieldLastModified(
            "operation__lastmodified",
            title=format_lazy("{} - {}", _("operation"), _("last modified")),
            initially_hidden=True,
            editable=False,
        ),
        # Suboperation fields
        GridFieldText(
            "suboperation__description",
            title=format_lazy("{} - {}", _("suboperation"), _("description")),
            initially_hidden=True,
            editable=False,
        ),
        GridFieldText(
            "suboperation__category",
            title=format_lazy("{} - {}", _("suboperation"), _("category")),
            initially_hidden=True,
            editable=False,
        ),
        GridFieldText(
            "suboperation__subcategory",
            title=format_lazy("{} - {}", _("suboperation"), _("subcategory")),
            initially_hidden=True,
            editable=False,
        ),
        GridFieldChoice(
            "suboperation__type",
            title=format_lazy("{} - {}", _("suboperation"), _("type")),
            choices=Operation.types,
            initially_hidden=True,
            editable=False,
        ),
        GridFieldDuration(
            "suboperation__duration",
            title=format_lazy("{} - {}", _("suboperation"), _("duration")),
            initially_hidden=True,
            editable=False,
        ),
        GridFieldDuration(
            "suboperation__duration_per",
            title=format_lazy("{} - {}", _("suboperation"), _("duration per unit")),
            initially_hidden=True,
            editable=False,
        ),
        GridFieldDuration(
            "suboperation__fence",
            title=format_lazy("{} - {}", _("suboperation"), _("release fence")),
            initially_hidden=True,
            editable=False,
        ),
        GridFieldDuration(
            "suboperation__posttime",
            title=format_lazy("{} - {}", _("suboperation"), _("post-op time")),
            initially_hidden=True,
            editable=False,
        ),
        GridFieldNumber(
            "suboperation__sizeminimum",
            title=format_lazy("{} - {}", _("suboperation"), _("size minimum")),
            initially_hidden=True,
            editable=False,
        ),
        GridFieldNumber(
            "suboperation__sizemultiple",
            title=format_lazy("{} - {}", _("suboperation"), _("size multiple")),
            initially_hidden=True,
            editable=False,
        ),
        GridFieldNumber(
            "suboperation__sizemaximum",
            title=format_lazy("{} - {}", _("suboperation"), _("size maximum")),
            initially_hidden=True,
            editable=False,
        ),
        GridFieldInteger(
            "suboperation__priority",
            title=format_lazy("{} - {}", _("suboperation"), _("priority")),
            initially_hidden=True,
            editable=False,
        ),
        GridFieldDateTime(
            "suboperation__effective_start",
            title=format_lazy("{} - {}", _("suboperation"), _("effective start")),
            initially_hidden=True,
            editable=False,
        ),
        GridFieldDateTime(
            "suboperation__effective_end",
            title=format_lazy("{} - {}", _("suboperation"), _("effective end")),
            initially_hidden=True,
            editable=False,
        ),
        GridFieldCurrency(
            "suboperation__cost",
            title=format_lazy("{} - {}", _("suboperation"), _("cost")),
            initially_hidden=True,
            editable=False,
        ),
        GridFieldChoice(
            "suboperation__search",
            title=format_lazy("{} - {}", _("suboperation"), _("search mode")),
            choices=searchmode,
            initially_hidden=True,
            editable=False,
        ),
        GridFieldText(
            "suboperation__source",
            title=format_lazy("{} - {}", _("suboperation"), _("source")),
            initially_hidden=True,
            editable=False,
        ),
        GridFieldLastModified(
            "suboperation__lastmodified",
            title=format_lazy("{} - {}", _("suboperation"), _("last modified")),
            initially_hidden=True,
            editable=False,
        ),
    )


class OperationPlanMixin:

    if "freppledb.inventoryplanning" in settings.INSTALLED_APPS:
        segmentlist = Segment.segmentList

    @classmethod
    def operationplanExtraBasequery(cls, query, request):

        # special keyword superop used for search field of operationplan
        if "parentreference" in request.GET:
            parentreference = request.GET["parentreference"]
            query = query.filter(
                Q(reference=parentreference) | Q(owner__reference=parentreference)
            )

        if "freppledb.forecast" in settings.INSTALLED_APPS:
            return query.annotate(
                demands=RawSQL(
                    """
          select json_agg(json_build_array(value, key, tp))
          from (
            select
              key, value,
              case when demand.name is not null then 'D' when forecast.name is not null then 'F' end as tp
            from jsonb_each_text(operationplan.plan->'pegging')
            left outer join demand on key = demand.name
            left outer join forecast on substring(key from 0 for position(' - ' in key)) = forecast.name
            where demand.name is not null or forecast.name is not null
            order by value desc, key desc
            limit 10
          ) peg""",
                    [],
                ),
                end_items=RawSQL(
                    """
          select json_agg(json_build_array(key, val))
          from (
            select coalesce(demand.item_id, forecast.item_id) as key, sum(value::numeric) as val
            from jsonb_each_text(operationplan.plan->'pegging')
            left outer join demand on key = demand.name
            left outer join forecast on substring(key from 0 for position(' - ' in key)) = forecast.name
            group by coalesce(demand.item_id, forecast.item_id)
            order by 2 desc
            limit 10
            ) peg_items""",
                    [],
                ),
            )
        else:
            return query.annotate(
                demands=RawSQL(
                    """
          select json_agg(json_build_array(value, key))
          from (
            select key, value
            from jsonb_each_text(operationplan.plan->'pegging')
            order by value desc, key desc
            limit 10
            ) peg""",
                    [],
                ),
                end_items=RawSQL(
                    """
          select json_agg(json_build_array(key, val))
          from (
            select demand.item_id as key, sum(value::numeric) as val
            from jsonb_each_text(operationplan.plan->'pegging')
            inner join demand on key = demand.name
            group by demand.item_id
            order by 2 desc
            limit 10
            ) peg_items""",
                    [],
                ),
            )


class ManufacturingOrderList(OperationPlanMixin, GridReport):
    template = "input/operationplanreport.html"
    title = _("manufacturing orders")
    default_sort = (1, "desc")
    model = ManufacturingOrder
    frozenColumns = 1
    multiselect = True
    editable = True
    height = 250
    help_url = "modeling-wizard/manufacturing-bom/manufacturing-orders.html"

    @classmethod
    def extra_context(reportclass, request, *args, **kwargs):
        if args and args[0]:
            request.session["lasttab"] = "plandetail"
            paths = request.path.split("/")
            path = paths[4]
            if path == "location" or request.path.startswith("/detail/input/location/"):
                return {
                    "active_tab": "plandetail",
                    "model": Location,
                    "title": force_text(Location._meta.verbose_name) + " " + args[0],
                    "post_title": _("manufacturing orders"),
                }
            elif path == "operation" or request.path.startswith(
                "/detail/input/operation/"
            ):
                return {
                    "active_tab": "plandetail",
                    "model": Operation,
                    "title": force_text(Operation._meta.verbose_name) + " " + args[0],
                    "post_title": _("manufacturing orders"),
                }
            elif path == "item" or request.path.startswith("/detail/input/item/"):
                return {
                    "active_tab": "plandetail",
                    "model": Item,
                    "title": force_text(Item._meta.verbose_name) + " " + args[0],
                    "post_title": _("manufacturing orders"),
                }
            elif path == "operationplanmaterial":
                return {
                    "active_tab": "plandetail",
                    "model": Item,
                    "title": force_text(Item._meta.verbose_name) + " " + args[0],
                    "post_title": force_text(
                        _("work in progress in %(loc)s at %(date)s")
                        % {"loc": args[1], "date": args[2]}
                    ),
                }
            elif path == "produced":
                return {
                    "active_tab": "plandetail",
                    "model": Item,
                    "title": force_text(Item._meta.verbose_name) + " " + args[0],
                    "post_title": force_text(
                        _("produced in %(loc)s between %(date1)s and %(date2)s")
                        % {"loc": args[1], "date1": args[2], "date2": args[3]}
                    ),
                }
            elif path == "consumed":
                return {
                    "active_tab": "plandetail",
                    "model": Item,
                    "title": force_text(Item._meta.verbose_name) + " " + args[0],
                    "post_title": force_text(
                        _("consumed in %(loc)s between %(date1)s and %(date2)s")
                        % {"loc": args[1], "date1": args[2], "date2": args[3]}
                    ),
                }
            else:
                return {"active_tab": "edit", "model": Item}
        elif "parentreference" in request.GET:
            return {
                "active_tab": "plandetail",
                "title": force_text(ManufacturingOrder._meta.verbose_name)
                + " "
                + request.GET["parentreference"],
            }
        else:
            return {"active_tab": "plandetail"}

    @classmethod
    def basequeryset(reportclass, request, *args, **kwargs):
        q = ManufacturingOrder.objects.all()
        if args and args[0]:
            path = request.path.split("/")[4]
            if path == "location" or request.path.startswith("/detail/input/location/"):
                q = q.filter(location=args[0])
            elif path == "operation" or request.path.startswith(
                "/detail/input/operation/"
            ):
                q = q.filter(operation=args[0])
            elif path == "item" or request.path.startswith("/detail/input/item/"):
                q = q.filter(
                    reference__in=RawSQL(
                        """
          select operationplan_id from operationplan
          inner join operationplanmaterial on operationplanmaterial.operationplan_id = operationplan.reference
          and operationplanmaterial.item_id = %s
          and operationplanmaterial.quantity > 0
          where operationplan.type = 'MO'
          """,
                        (args[0],),
                    )
                )
            elif path == "operationplanmaterial":
                q = q.filter(
                    reference__in=RawSQL(
                        """
          select operationplan_id from operationplan
          inner join operationplanmaterial on operationplanmaterial.operationplan_id = operationplan.reference
          and operationplanmaterial.item_id = %s and operationplanmaterial.location_id = %s
          and operationplan.startdate < %s and operationplan.enddate >= %s
          where operationplan.type = 'MO'
          """,
                        (args[0], args[1], args[2], args[2]),
                    )
                )
            elif path == "produced":
                q = q.filter(
                    reference__in=RawSQL(
                        """
          select operationplan_id from operationplan
          inner join operationplanmaterial on operationplanmaterial.operationplan_id = operationplan.reference
          and operationplanmaterial.item_id = %s and operationplanmaterial.location_id = %s
          and operationplanmaterial.flowdate >= %s and operationplanmaterial.flowdate < %s
          and operationplanmaterial.quantity > 0
          where operationplan.type = 'MO'
          """,
                        (args[0], args[1], args[2], args[3]),
                    )
                )
            elif path == "consumed":
                q = q.filter(
                    reference__in=RawSQL(
                        """
          select operationplan_id from operationplan
          inner join operationplanmaterial on operationplanmaterial.operationplan_id = operationplan.reference
          and operationplanmaterial.item_id = %s and operationplanmaterial.location_id = %s
          and operationplanmaterial.flowdate >= %s and operationplanmaterial.flowdate < %s
          and operationplanmaterial.quantity < 0
          where operationplan.type = 'MO'
          """,
                        (args[0], args[1], args[2], args[3]),
                    )
                )

        q = reportclass.operationplanExtraBasequery(q, request)
        return q.annotate(
            material=RawSQL(
                "(select json_agg(json_build_array(item_id, quantity)) from (select item_id, round(quantity,2) quantity from operationplanmaterial where operationplan.reference = operationplanmaterial.operationplan_id  order by quantity limit 10) mat)",
                [],
            ),
            resource=RawSQL(
                "(select json_agg(json_build_array(resource_id, quantity)) from (select resource_id, round(quantity,2) quantity from operationplanresource where operationplan.reference = operationplanresource.operationplan_id  order by quantity desc limit 10) res)",
                [],
            ),
            setup=RawSQL(
                "(select json_agg(json_build_array(resource_id, setup)) from (select resource_id, setup from operationplanresource where setup is not null and operationplan.reference = operationplanresource.operationplan_id order by resource_id limit 10) res)",
                [],
            ),
            setup_duration=Cast(
                RawSQL(
                    "(operationplan.plan->>'setup')::numeric * '1 second'::interval", []
                ),
                DurationField(),
            ),
            setup_end=Cast(
                RawSQL("(operationplan.plan->>'setupend')", []), DateTimeField()
            ),
            feasible=RawSQL(
                "coalesce((operationplan.plan->>'feasible')::boolean, true)", []
            ),
            opplan_duration=RawSQL(
                "(operationplan.enddate - operationplan.startdate)", []
            ),
            opplan_net_duration=RawSQL(
                "(operationplan.enddate - operationplan.startdate - coalesce((operationplan.plan->>'unavailable')::int * interval '1 second', interval '0 second'))",
                [],
            ),
            inventory_item=RawSQL("operationplan.plan->'item'", []),
            inventory_location=RawSQL("operationplan.plan->'location'", []),
            computed_color=RawSQL(
                """
                case when operationplan.color >= 999999 and operationplan.plan ? 'item' then
                999999 
                - extract(epoch from operationplan.delay)/86400.0
                + 1000000
                when operationplan.color >= 999999 and not(operationplan.plan ? 'item') then
                999999 
                - extract(epoch from operationplan.delay)/86400.0
                else operationplan.color
                end
                """,
                [],
            ),
        )

    rows = (
        GridFieldText(
            "reference",
            title=_("reference"),
            key=True,
            formatter="detail",
            extra="role:'input/manufacturingorder'",
            editable=not settings.ERP_CONNECTOR,
        ),
        GridFieldText(
            "batch", title=_("batch"), editable="true", initially_hidden=True
        ),
        GridFieldNumber(
            "computed_color",
            title=_("inventory status"),
            formatter="color",
            width="125",
            editable=False,
            extra='"formatoptions":{"defaultValue":""}, "summaryType":"min"',
        ),
        GridFieldNumber("color", hidden=True),
        GridFieldText(
            "item__name",
            title=_("item"),
            formatter="detail",
            extra='"role":"input/item"',
            editable=False,
        ),
        GridFieldText(
            "operation__location__name",
            title=_("location"),
            formatter="detail",
            extra='"role":"input/location"',
            editable=False,
        ),
        GridFieldText(
            "operation",
            title=_("operation"),
            field_name="operation__name",
            formatter="detail",
            extra='"role":"input/operation"',
        ),
        GridFieldDateTime(
            "startdate",
            title=_("start date"),
            extra='"formatoptions":{"srcformat":"Y-m-d H:i:s","newformat":"Y-m-d H:i:s", "defaultValue":""}, "summaryType":"min"',
        ),
        GridFieldDateTime(
            "enddate",
            title=_("end date"),
            extra='"formatoptions":{"srcformat":"Y-m-d H:i:s","newformat":"Y-m-d H:i:s", "defaultValue":""}, "summaryType":"max"',
        ),
        GridFieldDuration(
            "opplan_duration",
            title=_("duration"),
            formatter="duration",
            editable=False,
            extra='"formatoptions":{"defaultValue":""}, "summaryType":"sum"',
        ),
        GridFieldDuration(
            "opplan_net_duration",
            title=_("net duration"),
            formatter="duration",
            editable=False,
            extra='"formatoptions":{"defaultValue":""}, "summaryType":"sum"',
        ),
        GridFieldNumber(
            "quantity",
            title=_("quantity"),
            extra='"formatoptions":{"defaultValue":""}, "summaryType":"sum"',
        ),
        GridFieldChoice(
            "status",
            title=_("status"),
            choices=OperationPlan.orderstatus,
            editable=not settings.ERP_CONNECTOR,
        ),
        GridFieldNumber(
            "criticality",
            title=_("criticality"),
            editable=False,
            initially_hidden=True,
            extra='"formatoptions":{"defaultValue":""}, "summaryType":"min"',
        ),
        GridFieldDuration(
            "delay",
            title=_("delay"),
            editable=False,
            initially_hidden=True,
            extra='"formatoptions":{"defaultValue":""}, "summaryType":"max"',
        ),
        GridFieldJSON(
            "demands",
            title=_("demands"),
            editable=False,
            search=True,
            sortable=False,
            formatter="demanddetail",
            extra='"role":"input/demand"',
        ),
        GridFieldJSON(
            "material",
            title=_("materials"),
            editable=False,
            search=True,
            sortable=False,
            initially_hidden=True,
            formatter="listdetail",
            extra='"role":"input/item"',
        ),
        GridFieldJSON(
            "resource",
            title=_("resources"),
            editable=False,
            search=True,
            sortable=False,
            initially_hidden=True,
            formatter="listdetail",
            extra='"role":"input/resource"',
        ),
        GridFieldText(
            "setup",
            title=_("setups"),
            editable=False,
            search=True,
            sortable=False,
            initially_hidden=True,
            formatter="listdetail",
            extra='"role":"input/resource"',
        ),
        GridFieldText(
            "owner",
            title=_("owner"),
            field_name="owner__reference",
            formatter="detail",
            extra="role:'input/manufacturingorder'",
            initially_hidden=True,
        ),
        GridFieldText("source", title=_("source")),
        GridFieldLastModified("lastmodified"),
        GridFieldText(
            "operation__description",
            title=format_lazy("{} - {}", _("operation"), _("description")),
            initially_hidden=True,
        ),
        GridFieldText(
            "operation__category",
            title=format_lazy("{} - {}", _("operation"), _("category")),
            initially_hidden=True,
        ),
        GridFieldText(
            "operation__subcategory",
            title=format_lazy("{} - {}", _("operation"), _("subcategory")),
            initially_hidden=True,
        ),
        GridFieldChoice(
            "operation__type",
            title=format_lazy("{} - {}", _("operation"), _("type")),
            choices=Operation.types,
            initially_hidden=True,
        ),
        GridFieldDuration(
            "operation__duration",
            title=format_lazy("{} - {}", _("operation"), _("duration")),
            initially_hidden=True,
        ),
        GridFieldDuration(
            "operation__duration_per",
            title=format_lazy("{} - {}", _("operation"), _("duration per unit")),
            initially_hidden=True,
        ),
        GridFieldDuration(
            "operation__fence",
            title=format_lazy("{} - {}", _("operation"), _("release fence")),
            initially_hidden=True,
        ),
        GridFieldDuration(
            "operation__posttime",
            title=format_lazy("{} - {}", _("operation"), _("post-op time")),
            initially_hidden=True,
        ),
        GridFieldNumber(
            "operation__sizeminimum",
            title=format_lazy("{} - {}", _("operation"), _("size minimum")),
            initially_hidden=True,
        ),
        GridFieldNumber(
            "operation__sizemultiple",
            title=format_lazy("{} - {}", _("operation"), _("size multiple")),
            initially_hidden=True,
        ),
        GridFieldNumber(
            "operation__sizemaximum",
            title=format_lazy("{} - {}", _("operation"), _("size maximum")),
            initially_hidden=True,
        ),
        GridFieldInteger(
            "operation__priority",
            title=format_lazy("{} - {}", _("operation"), _("priority")),
            initially_hidden=True,
        ),
        GridFieldDateTime(
            "operation__effective_start",
            title=format_lazy("{} - {}", _("operation"), _("effective start")),
            initially_hidden=True,
        ),
        GridFieldDateTime(
            "operation__effective_end",
            title=format_lazy("{} - {}", _("operation"), _("effective end")),
            initially_hidden=True,
        ),
        GridFieldCurrency(
            "operation__cost",
            title=format_lazy("{} - {}", _("operation"), _("cost")),
            initially_hidden=True,
        ),
        GridFieldChoice(
            "operation__search",
            title=format_lazy("{} - {}", _("operation"), _("search mode")),
            choices=searchmode,
            initially_hidden=True,
        ),
        GridFieldText(
            "operation__source",
            title=format_lazy("{} - {}", _("operation"), _("source")),
            initially_hidden=True,
        ),
        GridFieldLastModified(
            "operation__lastmodified",
            title=format_lazy("{} - {}", _("operation"), _("last modified")),
            initially_hidden=True,
        ),
        GridFieldDuration(
            "setup_duration",
            title=_("setup time"),
            initially_hidden=True,
            search=False,
            editable=False,
        ),
        GridFieldDateTime(
            "setup_end",
            title=_("setup end date"),
            initially_hidden=True,
            search=True,
            editable=False,
        ),
        GridFieldBool(
            "feasible",
            title=_("feasible"),
            editable=False,
            initially_hidden=True,
            search=True,
        ),
        # Optional fields referencing the item
        GridFieldText(
            "operation__item__type",
            title=format_lazy("{} - {}", _("item"), _("type")),
            initially_hidden=True,
            editable=False,
        ),
        GridFieldText(
            "operation__item__description",
            title=format_lazy("{} - {}", _("item"), _("description")),
            initially_hidden=True,
            editable=False,
        ),
        GridFieldText(
            "operation__item__category",
            title=format_lazy("{} - {}", _("item"), _("category")),
            initially_hidden=True,
            editable=False,
        ),
        GridFieldText(
            "operation__item__subcategory",
            title=format_lazy("{} - {}", _("item"), _("subcategory")),
            initially_hidden=True,
            editable=False,
        ),
        GridFieldText(
            "operation__item__owner",
            title=format_lazy("{} - {}", _("item"), _("owner")),
            field_name="operation__item__owner__name",
            initially_hidden=True,
            editable=False,
        ),
        GridFieldText(
            "operation__item__source",
            title=format_lazy("{} - {}", _("item"), _("source")),
            initially_hidden=True,
            editable=False,
        ),
        GridFieldLastModified(
            "operation__item__lastmodified",
            title=format_lazy("{} - {}", _("item"), _("last modified")),
            initially_hidden=True,
            editable=False,
        ),
        # Optional fields referencing the location
        GridFieldText(
            "operation__location__description",
            title=format_lazy("{} - {}", _("location"), _("description")),
            initially_hidden=True,
            editable=False,
        ),
        GridFieldText(
            "operation__location__category",
            title=format_lazy("{} - {}", _("location"), _("category")),
            initially_hidden=True,
            editable=False,
        ),
        GridFieldText(
            "operation__location__subcategory",
            title=format_lazy("{} - {}", _("location"), _("subcategory")),
            initially_hidden=True,
            editable=False,
        ),
        GridFieldText(
            "operation__location__available",
            title=format_lazy("{} - {}", _("location"), _("available")),
            initially_hidden=True,
            field_name="operation__location__available__name",
            formatter="detail",
            extra='"role":"input/calendar"',
            editable=False,
        ),
        GridFieldText(
            "operation__location__owner",
            title=format_lazy("{} - {}", _("location"), _("owner")),
            initially_hidden=True,
            field_name="operation__location__owner__name",
            formatter="detail",
            extra='"role":"input/location"',
            editable=False,
        ),
        GridFieldText(
            "operation__location__source",
            title=format_lazy("{} - {}", _("location"), _("source")),
            initially_hidden=True,
            editable=False,
        ),
        GridFieldLastModified(
            "operation__location__lastmodified",
            title=format_lazy("{} - {}", _("location"), _("last modified")),
            initially_hidden=True,
            editable=False,
        ),
        GridFieldText(
            "end_items",
            title=_("end items"),
            editable=False,
            search=True,
            sortable=False,
            initially_hidden=True,
            formatter="listdetail",
            extra='"role":"input/item"',
        ),
    )

    if settings.ERP_CONNECTOR:
        actions = [
            {
                "name": "erp_incr_export",
                "label": format_lazy("export to {erp}", erp=settings.ERP_CONNECTOR),
                "function": "ERPconnection.IncrementalExport(jQuery('#grid'),'MO')",
            }
        ]
    else:
        actions = [
            {
                "name": "proposed",
                "label": format_lazy(
                    _("change status to {status}"), status=_("proposed")
                ),
                "function": "grid.setStatus('proposed')",
            },
            {
                "name": "approved",
                "label": format_lazy(
                    _("change status to {status}"), status=_("approved")
                ),
                "function": "grid.setStatus('approved')",
            },
            {
                "name": "confirmed",
                "label": format_lazy(
                    _("change status to {status}"), status=_("confirmed")
                ),
                "function": "grid.setStatus('confirmed')",
            },
            {
                "name": "completed",
                "label": format_lazy(
                    _("change status to {status}"), status=_("completed")
                ),
                "function": "grid.setStatus('completed')",
            },
            {
                "name": "closed",
                "label": format_lazy(
                    _("change status to {status}"), status=_("closed")
                ),
                "function": "grid.setStatus('closed')",
            },
        ]

    @classmethod
    def initialize(reportclass, request):
        if reportclass._attributes_added != 2:
            reportclass._attributes_added = 2
            for f in getAttributeFields(ManufacturingOrder):
                reportclass.rows += (f,)
            for f in getAttributeFields(Operation, related_name_prefix="operation"):
                f.editable = False
                reportclass.rows += (f,)
            for f in getAttributeFields(Location, related_name_prefix="location"):
                f.editable = False
                reportclass.rows += (f,)


class DistributionOrderList(OperationPlanMixin, GridReport):
    template = "input/operationplanreport.html"
    title = _("distribution orders")
    default_sort = (1, "desc")
    model = DistributionOrder
    frozenColumns = 1
    multiselect = True
    editable = True
    height = 250
    help_url = "modeling-wizard/distribution/distribution-orders.html"

    @classmethod
    def extra_context(reportclass, request, *args, **kwargs):
        if args and args[0]:
            paths = request.path.split("/")
            if paths[4] == "operationplanmaterial":
                return {
                    "active_tab": "distributionorders",
                    "model": Item,
                    "title": force_text(Item._meta.verbose_name) + " " + args[0],
                    "post_title": force_text(
                        _("in transit in %(loc)s at %(date)s")
                        % {"loc": args[1], "date": args[2]}
                    ),
                }
            elif paths[4] == "produced":
                return {
                    "active_tab": "distributionorders",
                    "model": Item,
                    "title": force_text(Item._meta.verbose_name) + " " + args[0],
                    "post_title": force_text(
                        _("received in %(loc)s between %(date1)s and %(date2)s")
                        % {"loc": args[1], "date1": args[2], "date2": args[3]}
                    ),
                }
            elif paths[4] == "consumed":
                return {
                    "active_tab": "distributionorders",
                    "model": Item,
                    "title": force_text(Item._meta.verbose_name) + " " + args[0],
                    "post_title": force_text(
                        _("shipped to %(loc)s between %(date1)s and %(date2)s")
                        % {"loc": args[1], "date1": args[2], "date2": args[3]}
                    ),
                }
            elif paths[4] == "item":
                return {
                    "active_tab": "distributionorders",
                    "model": Item,
                    "title": force_text(Item._meta.verbose_name) + " " + args[0],
                    "post_title": _("distribution orders"),
                }
            elif paths[4] == "location":
                path = paths[-2]
                if path == "in":
                    return {
                        "active_tab": "inboundorders",
                        "model": Location,
                        "title": force_text(Location._meta.verbose_name)
                        + " "
                        + args[0],
                        "post_title": _("inbound distribution"),
                    }
                elif path == "out":
                    return {
                        "active_tab": "outboundorders",
                        "model": Location,
                        "title": force_text(Location._meta.verbose_name)
                        + " "
                        + args[0],
                        "post_title": _("outbound distribution"),
                    }
            else:
                return {"active_tab": "edit", "model": Item}
        else:
            return {"active_tab": "edit"}

    @classmethod
    def basequeryset(reportclass, request, *args, **kwargs):
        q = DistributionOrder.objects.all()
        if args and args[0]:
            paths = request.path.split("/")
            if paths[4] == "operationplanmaterial":
                q = q.filter(Q(origin=args[1]) | Q(destination=args[1])).filter(
                    item__name=args[0], startdate__lt=args[2], enddate__gte=args[2]
                )
            elif paths[4] == "item":
                q = q.filter(item__name=args[0])
            elif paths[4] == "produced":
                q = q.filter(
                    destination__name=args[1],
                    item__name=args[0],
                    enddate__gte=args[2],
                    enddate__lt=args[3],
                )
            elif paths[4] == "consumed":
                q = q.filter(
                    origin__name=args[1],
                    item__name=args[0],
                    startdate__gte=args[2],
                    startdate__lt=args[3],
                )
            elif paths[4] == "location":
                path = paths[-2]
                if path == "out":
                    q = q.filter(origin_id=args[0])
                elif path == "in":
                    q = q.filter(destination_id=args[0])
        q = reportclass.operationplanExtraBasequery(q, request)
        return q.annotate(
            total_cost=RawSQL(
                "select item.cost*operationplan.quantity from item where name = operationplan.item_id",
                [],
            ),
            feasible=RawSQL(
                "coalesce((operationplan.plan->>'feasible')::boolean, true)", []
            ),
            computed_color=RawSQL(
                """
                case when operationplan.color >= 999999 and operationplan.plan ? 'item' then
                999999 
                - extract(epoch from operationplan.delay)/86400.0
                + 1000000
                when operationplan.color >= 999999 and not(operationplan.plan ? 'item') then
                999999 
                - extract(epoch from operationplan.delay)/86400.0
                else operationplan.color
                end
                """,
                [],
            ),
        )

    rows = (
        GridFieldText(
            "reference",
            title=_("reference"),
            key=True,
            formatter="detail",
            extra='role:"input/distributionorder"',
            editable=not settings.ERP_CONNECTOR,
        ),
        GridFieldNumber(
            "computed_color",
            title=_("inventory status"),
            formatter="color",
            width="125",
            editable=False,
            extra='"formatoptions":{"defaultValue":""}, "summaryType":"min"',
        ),
        GridFieldNumber("color", hidden=True),
        GridFieldText(
            "item",
            title=_("item"),
            field_name="item__name",
            formatter="detail",
            extra='"role":"input/item"',
        ),
        GridFieldText(
            "origin",
            title=_("origin"),
            field_name="origin__name",
            formatter="detail",
            extra='"role":"input/location"',
        ),
        GridFieldText(
            "destination",
            title=_("destination"),
            field_name="destination__name",
            formatter="detail",
            extra='"role":"input/location"',
        ),
        GridFieldDateTime(
            "startdate",
            title=_("shipping date"),
            extra='"formatoptions":{"srcformat":"Y-m-d H:i:s","newformat":"Y-m-d H:i:s", "defaultValue":""}, "summaryType":"min"',
        ),
        GridFieldDateTime(
            "enddate",
            title=_("receipt date"),
            extra='"formatoptions":{"srcformat":"Y-m-d H:i:s","newformat":"Y-m-d H:i:s", "defaultValue":""}, "summaryType":"max"',
        ),
        GridFieldNumber(
            "quantity",
            title=_("quantity"),
            extra='"formatoptions":{"defaultValue":""}, "summaryType":"sum"',
        ),
        GridFieldChoice(
            "status",
            title=_("status"),
            choices=DistributionOrder.orderstatus,
            editable=not settings.ERP_CONNECTOR,
        ),
        GridFieldCurrency(
            "item__cost",
            title=format_lazy("{} - {}", _("item"), _("cost")),
            editable=False,
            extra='"formatoptions":{"defaultValue":""}, "summaryType":"max"',
        ),
        GridFieldCurrency(
            "total_cost",
            title=_("total cost"),
            editable=False,
            search=False,
            extra='"formatoptions":{"defaultValue":""}, "summaryType":"sum"',
        ),
        GridFieldText(
            "batch", title=_("batch"), editable="true", initially_hidden=True
        ),
        GridFieldNumber(
            "criticality",
            title=_("criticality"),
            editable=False,
            initially_hidden=True,
            extra='"formatoptions":{"defaultValue":""}, "summaryType":"min"',
        ),
        GridFieldDuration(
            "delay",
            title=_("delay"),
            editable=False,
            initially_hidden=True,
            extra='"formatoptions":{"defaultValue":""}, "summaryType":"max"',
        ),
        GridFieldJSON(
            "demands",
            title=_("demands"),
            editable=False,
            search=True,
            sortable=False,
            formatter="demanddetail",
            extra='"role":"input/demand"',
        ),
        GridFieldText("source", title=_("source")),
        GridFieldLastModified("lastmodified"),
        GridFieldBool(
            "feasible",
            title=_("feasible"),
            editable=False,
            initially_hidden=True,
            search=False,
        ),
        # Optional fields referencing the item
        GridFieldText(
            "item__type",
            title=format_lazy("{} - {}", _("item"), _("type")),
            initially_hidden=True,
            editable=False,
        ),
        GridFieldText(
            "item__description",
            title=format_lazy("{} - {}", _("item"), _("description")),
            initially_hidden=True,
            editable=False,
        ),
        GridFieldText(
            "item__category",
            title=format_lazy("{} - {}", _("item"), _("category")),
            initially_hidden=True,
            editable=False,
        ),
        GridFieldText(
            "item__subcategory",
            title=format_lazy("{} - {}", _("item"), _("subcategory")),
            initially_hidden=True,
            editable=False,
        ),
        GridFieldText(
            "item__owner",
            title=format_lazy("{} - {}", _("item"), _("owner")),
            field_name="item__owner__name",
            initially_hidden=True,
            editable=False,
        ),
        GridFieldText(
            "item__source",
            title=format_lazy("{} - {}", _("item"), _("source")),
            initially_hidden=True,
            editable=False,
        ),
        GridFieldLastModified(
            "item__lastmodified",
            title=format_lazy("{} - {}", _("item"), _("last modified")),
            initially_hidden=True,
            editable=False,
        ),
        # Optional fields referencing the origin location
        GridFieldText(
            "origin__description",
            title=format_lazy("{} - {}", _("origin"), _("description")),
            initially_hidden=True,
            editable=False,
        ),
        GridFieldText(
            "origin__category",
            title=format_lazy("{} - {}", _("origin"), _("category")),
            initially_hidden=True,
            editable=False,
        ),
        GridFieldText(
            "origin__subcategory",
            title=format_lazy("{} - {}", _("origin"), _("subcategory")),
            initially_hidden=True,
            editable=False,
        ),
        GridFieldText(
            "origin__available",
            title=format_lazy("{} - {}", _("origin"), _("available")),
            initially_hidden=True,
            field_name="origin__available__name",
            formatter="detail",
            extra='"role":"input/calendar"',
            editable=False,
        ),
        GridFieldText(
            "origin__owner",
            title=format_lazy("{} - {}", _("origin"), _("owner")),
            initially_hidden=True,
            field_name="origin__owner__name",
            formatter="detail",
            extra='"role":"input/location"',
            editable=False,
        ),
        GridFieldText(
            "origin__source",
            title=format_lazy("{} - {}", _("origin"), _("source")),
            initially_hidden=True,
            editable=False,
        ),
        GridFieldLastModified(
            "origin__lastmodified",
            title=format_lazy("{} - {}", _("origin"), _("last modified")),
            initially_hidden=True,
            editable=False,
        ),
        # Optional fields referencing the destination location
        GridFieldText(
            "destination__description",
            title=format_lazy("{} - {}", _("destination"), _("description")),
            initially_hidden=True,
            editable=False,
        ),
        GridFieldText(
            "destination__category",
            title=format_lazy("{} - {}", _("destination"), _("category")),
            initially_hidden=True,
            editable=False,
        ),
        GridFieldText(
            "destination__subcategory",
            title=format_lazy("{} - {}", _("destination"), _("subcategory")),
            initially_hidden=True,
            editable=False,
        ),
        GridFieldText(
            "destination__available",
            title=format_lazy("{} - {}", _("destination"), _("available")),
            initially_hidden=True,
            field_name="origin__available__name",
            formatter="detail",
            extra='"role":"input/calendar"',
            editable=False,
        ),
        GridFieldText(
            "destination__owner",
            title=format_lazy("{} - {}", _("destination"), _("owner")),
            initially_hidden=True,
            field_name="origin__owner__name",
            formatter="detail",
            extra='"role":"input/location"',
            editable=False,
        ),
        GridFieldText(
            "destination__source",
            title=format_lazy("{} - {}", _("destination"), _("source")),
            initially_hidden=True,
            editable=False,
        ),
        GridFieldLastModified(
            "destination__lastmodified",
            title=format_lazy("{} - {}", _("destination"), _("last modified")),
            initially_hidden=True,
            editable=False,
        ),
        GridFieldText(
            "end_items",
            title=_("end items"),
            editable=False,
            search=False,
            sortable=False,
            initially_hidden=True,
            formatter="listdetail",
            extra='"role":"input/item"',
        ),
    )

    if settings.ERP_CONNECTOR:
        actions = [
            {
                "name": "erp_incr_export",
                "label": format_lazy("export to {erp}", erp=settings.ERP_CONNECTOR),
                "function": "ERPconnection.IncrementalExport(jQuery('#grid'),'DO')",
            }
        ]

    else:
        actions = [
            {
                "name": "proposed",
                "label": format_lazy(
                    _("change status to {status}"), status=_("proposed")
                ),
                "function": "grid.setStatus('proposed')",
            },
            {
                "name": "approved",
                "label": format_lazy(
                    _("change status to {status}"), status=_("approved")
                ),
                "function": "grid.setStatus('approved')",
            },
            {
                "name": "confirmed",
                "label": format_lazy(
                    _("change status to {status}"), status=_("confirmed")
                ),
                "function": "grid.setStatus('confirmed')",
            },
            {
                "name": "completed",
                "label": format_lazy(
                    _("change status to {status}"), status=_("completed")
                ),
                "function": "grid.setStatus('completed')",
            },
            {
                "name": "closed",
                "label": format_lazy(
                    _("change status to {status}"), status=_("closed")
                ),
                "function": "grid.setStatus('closed')",
            },
        ]

    @classmethod
    def initialize(reportclass, request):
        if reportclass._attributes_added != 2:
            reportclass._attributes_added = 2
            for f in getAttributeFields(DistributionOrder):
                reportclass.rows += (f,)
            for f in getAttributeFields(Item, related_name_prefix="item"):
                f.editable = False
                reportclass.rows += (f,)
            for f in getAttributeFields(Location, related_name_prefix="origin"):
                f.editable = False
                reportclass.rows += (f,)
            for f in getAttributeFields(Location, related_name_prefix="destination"):
                f.editable = False
                reportclass.rows += (f,)


class PurchaseOrderList(OperationPlanMixin, GridReport):
    template = "input/operationplanreport.html"
    title = _("purchase orders")
    model = PurchaseOrder
    default_sort = (1, "desc")
    frozenColumns = 1
    multiselect = True
    editable = True
    height = 250
    help_url = "modeling-wizard/purchasing/purchase-orders.html"

    @classmethod
    def extra_context(reportclass, request, *args, **kwargs):
        if args and args[0]:
            request.session["lasttab"] = "purchaseorders"
            paths = request.path.split("/")
            path = paths[4]
            if path == "supplier" or request.path.startswith("/detail/input/supplier/"):
                return {
                    "active_tab": "purchaseorders",
                    "model": Supplier,
                    "title": force_text(Supplier._meta.verbose_name) + " " + args[0],
                    "post_title": _("purchase orders"),
                }
            elif path == "location" or request.path.startswith(
                "/detail/input/location/"
            ):
                return {
                    "active_tab": "purchaseorders",
                    "model": Location,
                    "title": force_text(Location._meta.verbose_name) + " " + args[0],
                    "post_title": _("purchase orders"),
                }
            elif path == "item" or request.path.startswith("/detail/input/item/"):
                return {
                    "active_tab": "purchaseorders",
                    "model": Item,
                    "title": force_text(Item._meta.verbose_name) + " " + args[0],
                    "post_title": _("purchase orders"),
                }
            elif path == "operationplanmaterial":
                return {
                    "active_tab": "purchaseorders",
                    "model": Item,
                    "title": force_text(Item._meta.verbose_name) + " " + args[0],
                    "post_title": force_text(
                        _("on order in %(loc)s at %(date)s")
                        % {"loc": args[1], "date": args[2]}
                    ),
                }
            elif path == "produced":
                return {
                    "active_tab": "purchaseorders",
                    "model": Item,
                    "title": force_text(Item._meta.verbose_name) + " " + args[0],
                    "post_title": force_text(
                        _("on order in %(loc)s between %(date1)s and %(date2)s")
                        % {"loc": args[1], "date1": args[2], "date2": args[3]}
                    ),
                }
            else:
                return {"active_tab": "edit", "model": Item}
        else:
            return {"active_tab": "purchaseorders"}

    @classmethod
    def basequeryset(reportclass, request, *args, **kwargs):
        q = PurchaseOrder.objects.all()
        if args and args[0]:
            paths = request.path.split("/")
            path = paths[4]
            if paths[4] == "operationplanmaterial":
                q = q.filter(
                    location__name=args[1],
                    item__name=args[0],
                    startdate__lt=args[2],
                    enddate__gte=args[2],
                )
            elif path == "produced":
                q = q.filter(
                    location__name=args[1],
                    item__name=args[0],
                    enddate__gte=args[2],
                    enddate__lt=args[3],
                )
            elif path == "supplier" or request.path.startswith(
                "/detail/input/supplier/"
            ):
                try:
                    Supplier.rebuildHierarchy(database=request.database)
                    sup = (
                        Supplier.objects.all().using(request.database).get(name=args[0])
                    )
                    lft = sup.lft
                    rght = sup.rght
                except Supplier.DoesNotExist:
                    lft = 1
                    rght = 1
                q = q.filter(supplier__lft__gte=lft, supplier__rght__lte=rght)
            elif path == "location" or request.path.startswith(
                "/detail/input/location/"
            ):
                try:
                    Location.rebuildHierarchy(database=request.database)
                    loc = (
                        Location.objects.all().using(request.database).get(name=args[0])
                    )
                    lft = loc.lft
                    rght = loc.rght
                except Location.DoesNotExist:
                    lft = 1
                    rght = 1
                q = q.filter(location__lft__gte=lft, location__rght__lte=rght)
            elif path == "item" or request.path.startswith("/detail/input/item/"):
                try:
                    Item.rebuildHierarchy(database=request.database)
                    itm = Item.objects.all().using(request.database).get(name=args[0])
                    lft = itm.lft
                    rght = itm.rght
                except Item.DoesNotExist:
                    lft = 1
                    rght = 1
                q = q.filter(item__lft__gte=lft, item__rght__lte=rght)

        q = reportclass.operationplanExtraBasequery(q.select_related("item"), request)
        return q.annotate(
            unit_cost=Cast(
                RawSQL(
                    """
            coalesce((select max(cost) from itemsupplier 
                      where itemsupplier.item_id = operationplan.item_id
                      and cost > 0
                      and (itemsupplier.location_id is null or itemsupplier.location_id = operationplan.location_id) 
                      and itemsupplier.supplier_id = operationplan.supplier_id), 
                     (select cost from item where item.name = operationplan.item_id), 0)
                    """,
                    [],
                ),
                output_field=FloatField(),
            ),
            total_cost=Cast(F("unit_cost") * F("quantity"), output_field=FloatField()),
            feasible=RawSQL(
                "coalesce((operationplan.plan->>'feasible')::boolean, true)", []
            ),
            computed_color=RawSQL(
                """
                case when operationplan.color >= 999999 and operationplan.plan ? 'item' then
                999999 
                - extract(epoch from operationplan.delay)/86400.0
                + 1000000
                when operationplan.color >= 999999 and not(operationplan.plan ? 'item') then
                999999 
                - extract(epoch from operationplan.delay)/86400.0
                else operationplan.color
                end
                """,
                [],
            ),
        )

    rows = (
        GridFieldText(
            "reference",
            title=_("reference"),
            key=True,
            formatter="detail",
            extra='role:"input/purchaseorder"',
            editable=not settings.ERP_CONNECTOR,
        ),
        GridFieldNumber(
            "computed_color",
            title=_("inventory status"),
            formatter="color",
            width="125",
            editable=False,
            extra='"formatoptions":{"defaultValue":""}, "summaryType":"min"',
        ),
        GridFieldNumber("color", hidden=True),
        GridFieldText(
            "item",
            title=_("item"),
            field_name="item__name",
            formatter="detail",
            extra='"role":"input/item"',
        ),
        GridFieldText(
            "location",
            title=_("location"),
            field_name="location__name",
            formatter="detail",
            extra='"role":"input/location"',
        ),
        GridFieldText(
            "supplier",
            title=_("supplier"),
            field_name="supplier__name",
            formatter="detail",
            extra='"role":"input/supplier"',
        ),
        GridFieldDateTime(
            "startdate",
            title=_("ordering date"),
            extra='"formatoptions":{"srcformat":"Y-m-d H:i:s","newformat":"Y-m-d H:i:s", "defaultValue":""}, "summaryType":"min"',
        ),
        GridFieldDateTime(
            "enddate",
            title=_("receipt date"),
            extra='"formatoptions":{"srcformat":"Y-m-d H:i:s","newformat":"Y-m-d H:i:s", "defaultValue":""}, "summaryType":"max"',
        ),
        GridFieldNumber(
            "quantity",
            title=_("quantity"),
            extra='"formatoptions":{"defaultValue":""}, "summaryType":"sum"',
        ),
        GridFieldChoice(
            "status",
            title=_("status"),
            choices=PurchaseOrder.orderstatus,
            editable=not settings.ERP_CONNECTOR,
        ),
        GridFieldCurrency(
            "unit_cost",
            title=format_lazy("{} - {}", _("item"), _("cost")),
            editable=False,
            search=True,
            extra='"formatoptions":{"defaultValue":""}, "summaryType":"max"',
        ),
        GridFieldCurrency(
            "total_cost",
            title=_("total cost"),
            editable=False,
            search=True,
            extra='"formatoptions":{"defaultValue":""}, "summaryType":"sum"',
        ),
        GridFieldText(
            "batch", title=_("batch"), editable="true", initially_hidden=True
        ),
        GridFieldNumber(
            "criticality",
            title=_("criticality"),
            editable=False,
            initially_hidden=True,
            extra='"formatoptions":{"defaultValue":""}, "summaryType":"min"',
        ),
        GridFieldDuration(
            "delay",
            title=_("delay"),
            editable=False,
            initially_hidden=True,
            extra='"formatoptions":{"defaultValue":""}, "summaryType":"max"',
        ),
        GridFieldJSON(
            "demands",
            title=_("demands"),
            editable=False,
            search=True,
            sortable=False,
            formatter="demanddetail",
            extra='"role":"input/demand"',
        ),
        GridFieldText("source", title=_("source")),
        GridFieldBool(
            "feasible",
            title=_("feasible"),
            editable=False,
            initially_hidden=True,
            search=True,
        ),
        GridFieldLastModified("lastmodified"),
        # Optional fields referencing the item
        GridFieldText(
            "item__type",
            title=format_lazy("{} - {}", _("item"), _("type")),
            initially_hidden=True,
            editable=False,
        ),
        GridFieldText(
            "item__description",
            title=format_lazy("{} - {}", _("item"), _("description")),
            initially_hidden=True,
            editable=False,
        ),
        GridFieldText(
            "item__category",
            title=format_lazy("{} - {}", _("item"), _("category")),
            initially_hidden=True,
            editable=False,
        ),
        GridFieldText(
            "item__subcategory",
            title=format_lazy("{} - {}", _("item"), _("subcategory")),
            initially_hidden=True,
            editable=False,
        ),
        GridFieldText(
            "item__owner",
            title=format_lazy("{} - {}", _("item"), _("owner")),
            field_name="item__owner__name",
            initially_hidden=True,
            editable=False,
        ),
        GridFieldText(
            "item__source",
            title=format_lazy("{} - {}", _("item"), _("source")),
            initially_hidden=True,
            editable=False,
        ),
        GridFieldLastModified(
            "item__lastmodified",
            title=format_lazy("{} - {}", _("item"), _("last modified")),
            initially_hidden=True,
            editable=False,
        ),
        # Optional fields referencing the location
        GridFieldText(
            "location__description",
            title=format_lazy("{} - {}", _("location"), _("description")),
            initially_hidden=True,
            editable=False,
        ),
        GridFieldText(
            "location__category",
            title=format_lazy("{} - {}", _("location"), _("category")),
            initially_hidden=True,
            editable=False,
        ),
        GridFieldText(
            "location__subcategory",
            title=format_lazy("{} - {}", _("location"), _("subcategory")),
            initially_hidden=True,
            editable=False,
        ),
        GridFieldText(
            "location__available",
            title=format_lazy("{} - {}", _("location"), _("available")),
            initially_hidden=True,
            field_name="location__available__name",
            formatter="detail",
            extra='"role":"input/calendar"',
            editable=False,
        ),
        GridFieldText(
            "location__owner",
            title=format_lazy("{} - {}", _("location"), _("owner")),
            initially_hidden=True,
            field_name="location__owner__name",
            formatter="detail",
            extra='"role":"input/location"',
            editable=False,
        ),
        GridFieldText(
            "location__source",
            title=format_lazy("{} - {}", _("location"), _("source")),
            initially_hidden=True,
            editable=False,
        ),
        GridFieldLastModified(
            "location__lastmodified",
            title=format_lazy("{} - {}", _("location"), _("last modified")),
            initially_hidden=True,
            editable=False,
        ),
        # Optional fields referencing the supplier
        GridFieldText(
            "supplier__description",
            title=format_lazy("{} - {}", _("supplier"), _("description")),
            initially_hidden=True,
            editable=False,
        ),
        GridFieldText(
            "supplier__category",
            title=format_lazy("{} - {}", _("supplier"), _("category")),
            initially_hidden=True,
            editable=False,
        ),
        GridFieldText(
            "supplier__subcategory",
            title=format_lazy("{} - {}", _("supplier"), _("subcategory")),
            initially_hidden=True,
            editable=False,
        ),
        GridFieldText(
            "supplier__owner",
            title=format_lazy("{} - {}", _("supplier"), _("owner")),
            initially_hidden=True,
            field_name="supplier__owner__name",
            formatter="detail",
            extra='"role":"input/supplier"',
            editable=False,
        ),
        GridFieldText(
            "supplier__source",
            title=format_lazy("{} - {}", _("supplier"), _("source")),
            initially_hidden=True,
            editable=False,
        ),
        GridFieldLastModified(
            "supplier__lastmodified",
            title=format_lazy("{} - {}", _("supplier"), _("last modified")),
            initially_hidden=True,
            editable=False,
        ),
        GridFieldText(
            "end_items",
            title=_("end items"),
            editable=False,
            search=False,
            sortable=False,
            initially_hidden=True,
            formatter="listdetail",
            extra='"role":"input/item"',
        ),
    )

    if settings.ERP_CONNECTOR:
        actions = [
            {
                "name": "erp_incr_export",
                "label": format_lazy("export to {erp}", erp=settings.ERP_CONNECTOR),
                "function": "ERPconnection.IncrementalExport(jQuery('#grid'),'PO')",
            }
        ]
    else:
        actions = [
            {
                "name": "proposed",
                "label": format_lazy(
                    _("change status to {status}"), status=_("proposed")
                ),
                "function": "grid.setStatus('proposed')",
            },
            {
                "name": "approved",
                "label": format_lazy(
                    _("change status to {status}"), status=_("approved")
                ),
                "function": "grid.setStatus('approved')",
            },
            {
                "name": "confirmed",
                "label": format_lazy(
                    _("change status to {status}"), status=_("confirmed")
                ),
                "function": "grid.setStatus('confirmed')",
            },
            {
                "name": "completed",
                "label": format_lazy(
                    _("change status to {status}"), status=_("completed")
                ),
                "function": "grid.setStatus('completed')",
            },
            {
                "name": "closed",
                "label": format_lazy(
                    _("change status to {status}"), status=_("closed")
                ),
                "function": "grid.setStatus('closed')",
            },
        ]

    @classmethod
    def initialize(reportclass, request):
        if reportclass._attributes_added != 2:
            reportclass._attributes_added = 2
            for f in getAttributeFields(PurchaseOrder):
                reportclass.rows += (f,)
            for f in getAttributeFields(Item, related_name_prefix="item"):
                f.editable = False
                reportclass.rows += (f,)
            for f in getAttributeFields(Location, related_name_prefix="location"):
                f.editable = False
                reportclass.rows += (f,)
            for f in getAttributeFields(Supplier, related_name_prefix="supplier"):
                f.editable = False
                reportclass.rows += (f,)


class DeliveryOrderList(GridReport):
    template = "input/deliveryorder.html"
    title = _("delivery orders")
    model = DeliveryOrder
    frozenColumns = 0
    editable = True
    multiselect = True
    help_url = "model-reference/delivery-orders.html"
    rows = (
        GridFieldText(
            "reference",
            title=_("reference"),
            key=True,
            formatter="detail",
            extra='role:"input/deliveryorder"',
            editable=not settings.ERP_CONNECTOR,
        ),
        GridFieldText(
            "batch", title=_("batch"), editable="true", initially_hidden=True
        ),
        GridFieldText(
            "demand",
            title=_("demand"),
            field_name="demand__name",
            formatter="detail",
            extra='"role":"input/demand"',
        ),
        GridFieldText(
            "item",
            title=_("item"),
            field_name="item__name",
            formatter="detail",
            extra='"role":"input/item"',
        ),
        GridFieldText(
            "customer",
            title=_("customer"),
            field_name="demand__customer__name",
            formatter="detail",
            extra='"role":"input/customer"',
        ),
        GridFieldText(
            "location",
            title=_("location"),
            field_name="location__name",
            formatter="detail",
            extra='"role":"input/location"',
        ),
        GridFieldNumber("quantity", title=_("quantity")),
        GridFieldNumber("demand__quantity", title=_("demand quantity"), editable=False),
        GridFieldDateTime("startdate", title=_("start date")),
        GridFieldDateTime(
            "enddate",
            title=_("end date"),
            extra=GridFieldDateTime.extra + ',"cellattr":enddatecellattr',
        ),
        GridFieldDateTime(
            "due", field_name="demand__due", title=_("due date"), editable=False
        ),
        GridFieldChoice(
            "status",
            title=_("status"),
            choices=OperationPlan.orderstatus,
            editable=not settings.ERP_CONNECTOR,
        ),
        GridFieldText("batch", title=_("batch"), field_name="batch"),
        GridFieldDuration(
            "delay",
            title=_("delay"),
            editable=False,
            initially_hidden=True,
            extra='"formatoptions":{"defaultValue":""}, "summaryType":"max"',
        ),
        # Optional fields referencing the item
        GridFieldText(
            "item__type",
            title=format_lazy("{} - {}", _("item"), _("type")),
            initially_hidden=True,
            editable=False,
        ),
        GridFieldText(
            "item__description",
            title=format_lazy("{} - {}", _("item"), _("description")),
            initially_hidden=True,
            editable=False,
        ),
        GridFieldText(
            "item__category",
            title=format_lazy("{} - {}", _("item"), _("category")),
            initially_hidden=True,
            editable=False,
        ),
        GridFieldText(
            "item__subcategory",
            title=format_lazy("{} - {}", _("item"), _("subcategory")),
            initially_hidden=True,
            editable=False,
        ),
        GridFieldText(
            "item__owner",
            title=format_lazy("{} - {}", _("item"), _("owner")),
            field_name="item__owner__name",
            initially_hidden=True,
            editable=False,
        ),
        GridFieldText(
            "item__source",
            title=format_lazy("{} - {}", _("item"), _("source")),
            initially_hidden=True,
            editable=False,
        ),
        GridFieldLastModified(
            "item__lastmodified",
            title=format_lazy("{} - {}", _("item"), _("last modified")),
            initially_hidden=True,
            editable=False,
        ),
        # Optional fields referencing the location
        GridFieldText(
            "location__description",
            title=format_lazy("{} - {}", _("location"), _("description")),
            initially_hidden=True,
            editable=False,
        ),
        GridFieldText(
            "location__category",
            title=format_lazy("{} - {}", _("location"), _("category")),
            initially_hidden=True,
            editable=False,
        ),
        GridFieldText(
            "location__subcategory",
            title=format_lazy("{} - {}", _("location"), _("subcategory")),
            initially_hidden=True,
            editable=False,
        ),
        GridFieldText(
            "location__available",
            title=format_lazy("{} - {}", _("location"), _("available")),
            initially_hidden=True,
            field_name="location__available__name",
            formatter="detail",
            extra='"role":"input/calendar"',
            editable=False,
        ),
        GridFieldText(
            "location__owner",
            title=format_lazy("{} - {}", _("location"), _("owner")),
            initially_hidden=True,
            field_name="location__owner__name",
            formatter="detail",
            extra='"role":"input/location"',
            editable=False,
        ),
        GridFieldText(
            "location__source",
            title=format_lazy("{} - {}", _("location"), _("source")),
            initially_hidden=True,
            editable=False,
        ),
        GridFieldLastModified(
            "location__lastmodified",
            title=format_lazy("{} - {}", _("location"), _("last modified")),
            initially_hidden=True,
            editable=False,
        ),
        # Optional fields referencing the customer
        GridFieldText(
            "demand__customer__description",
            title=format_lazy("{} - {}", _("customer"), _("description")),
            initially_hidden=True,
            editable=False,
        ),
        GridFieldText(
            "demand__customer__category",
            title=format_lazy("{} - {}", _("customer"), _("category")),
            initially_hidden=True,
            editable=False,
        ),
        GridFieldText(
            "demand__customer__subcategory",
            title=format_lazy("{} - {}", _("customer"), _("subcategory")),
            initially_hidden=True,
            editable=False,
        ),
        GridFieldText(
            "demand__customer__owner",
            title=format_lazy("{} - {}", _("customer"), _("owner")),
            initially_hidden=True,
            field_name="supplier__owner__name",
            formatter="detail",
            extra='"role":"input/supplier"',
            editable=False,
        ),
        GridFieldText(
            "demand__customer__source",
            title=format_lazy("{} - {}", _("customer"), _("source")),
            initially_hidden=True,
            editable=False,
        ),
        GridFieldLastModified(
            "demand__customer__lastmodified",
            title=format_lazy("{} - {}", _("customer"), _("last modified")),
            initially_hidden=True,
            editable=False,
        ),
    )

    @classmethod
    def basequeryset(reportclass, request, *args, **kwargs):

        q = DeliveryOrder.objects.all()

        # special keyword superop used for search field of operationplan
        if "parentreference" in request.GET:
            parentreference = request.GET["parentreference"]
            q = q.filter(reference=parentreference)

        if args and args[0]:
            path = request.path.split("/")[4]
            if path == "consumed":
                return q.filter(
                    item__name=args[0],
                    location__name=args[1],
                    enddate__gte=args[2],
                    enddate__lt=args[3],
                )
            else:
                try:
                    itm = Item.objects.all().using(request.database).get(name=args[0])
                    lft = itm.lft
                    rght = itm.rght
                except Item.DoesNotExist:
                    lft = 1
                    rght = 1
                q = q.filter(item__lft__gte=lft, item__rght__lte=rght)

        return q

    @classmethod
    def extra_context(reportclass, request, *args, **kwargs):
        if args and args[0]:
            request.session["lasttab"] = "deliveryorders"
            path = request.path.split("/")[4]
            if path == "consumed":
                return {
                    "active_tab": "deliveryorders",
                    "model": Item,
                    "title": force_text(Item._meta.verbose_name) + " " + args[0],
                    "post_title": force_text(
                        _("delivered from %(loc)s between %(date1)s and %(date2)s")
                        % {"loc": args[1], "date1": args[2], "date2": args[3]}
                    ),
                }
            else:
                return {
                    "active_tab": "deliveryorders",
                    "title": force_text(Item._meta.verbose_name) + " " + args[0],
                    "post_title": _("delivery orders"),
                }
        else:
            return {"active_tab": "deliveryorders"}

    @classmethod
    def initialize(reportclass, request):
        if reportclass._attributes_added != 2:
            reportclass._attributes_added = 2
            for f in getAttributeFields(DeliveryOrder):
                reportclass.rows += (f,)
            for f in getAttributeFields(Item, related_name_prefix="item"):
                f.editable = False
                f.initially_hidden = True
                reportclass.rows += (f,)
            for f in getAttributeFields(Location, related_name_prefix="location"):
                f.editable = False
                f.initially_hidden = True
                reportclass.rows += (f,)
            for f in getAttributeFields(
                Customer, related_name_prefix="demand__customer"
            ):
                f.editable = False
                f.initially_hidden = True
                reportclass.rows += (f,)


class InventoryDetail(OperationPlanMixin, GridReport):
    """
    A list report to show OperationPlanMaterial.
    """

    template = "input/operationplanreport.html"
    title = _("Inventory detail")
    model = OperationPlanMaterial
    permissions = (("view_inventory_report", "Can view inventory report"),)
    frozenColumns = 0
    editable = True
    multiselect = True
    height = 250
    help_url = "user-interface/plan-analysis/inventory-detail-report.html"

    @classmethod
    def basequeryset(reportclass, request, *args, **kwargs):
        if len(args) and args[0]:
            if request.path_info.startswith(
                "/data/input/operationplanmaterial/item/"
            ) or request.path_info.startswith("/detail/input/item/"):
                base = OperationPlanMaterial.objects.filter(item=args[0])

            elif request.path_info.startswith(
                "/data/input/operationplanmaterial/buffer/"
            ):
                i_b_l = args[0].split(" @ ")
                if len(i_b_l) == 1:
                    buffer = Buffer.objects.get(id=args[0])
                    base = OperationPlanMaterial.objects.filter(
                        item=buffer.item.name, location=buffer.location.name
                    )
                elif len(i_b_l) == 2:
                    base = OperationPlanMaterial.objects.filter(
                        item=i_b_l[0], location=i_b_l[1]
                    )
                else:
                    base = OperationPlanMaterial.objects.filter(
                        item=i_b_l[0], location=i_b_l[2], operationplan__batch=i_b_l[1]
                    )
        else:
            base = OperationPlanMaterial.objects
        base = reportclass.operationplanExtraBasequery(base, request)
        return base.select_related().annotate(
            feasible=RawSQL(
                "coalesce((operationplan.plan->>'feasible')::boolean, true)", []
            )
        )

    @classmethod
    def extra_context(reportclass, request, *args, **kwargs):
        if args and args[0]:
            if request.path_info.startswith(
                "/data/input/operationplanmaterial/item/"
            ) or request.path_info.startswith("/detail/input/item/"):
                request.session["lasttab"] = "inventorydetail"
                return {
                    "active_tab": "inventorydetail",
                    "model": Item,
                    "title": force_text(Item._meta.verbose_name) + " " + args[0],
                    "post_title": _("inventory detail"),
                }
            elif request.path_info.startswith(
                "/data/input/operationplanmaterial/buffer/"
            ):
                request.session["lasttab"] = "plandetail"
                dlmtr = args[0].find(" @ ")
                if dlmtr != -1:
                    item = args[0][:dlmtr]
                    location = args[0][dlmtr + 3 :]
                else:
                    buffer = Buffer.objects.get(id=args[0])
                    item = buffer.item.name
                    location = buffer.location.name
                return {
                    "active_tab": "plandetail",
                    "model": Buffer,
                    "title": force_text(Buffer._meta.verbose_name)
                    + " "
                    + item
                    + " @ "
                    + location,
                    "post_title": _("plan detail"),
                }
        else:
            return {"active_tab": "plandetail", "model": OperationPlanMaterial}

    rows = (
        GridFieldInteger(
            "id",
            title=_("identifier"),
            key=True,
            editable=False,
            formatter="detail",
            extra='"role":"input/operationplanmaterial"',
            initially_hidden=True,
        ),
        GridFieldText(
            "item",
            title=_("item"),
            field_name="item__name",
            editable=False,
            formatter="detail",
            extra='"role":"input/item"',
        ),
        GridFieldText(
            "location",
            title=_("location"),
            field_name="location__name",
            editable=False,
            formatter="detail",
            extra='"role":"input/location"',
        ),
        GridFieldText("operationplan__reference", title=_("reference"), editable=False),
        GridFieldText(
            "owner",
            title=_("owner"),
            field_name="operationplan__owner__reference",
            formatter="detail",
            extra="role:'input/manufacturingorder'",
            initially_hidden=True,
        ),
        GridFieldText(
            "operationplan__batch",
            title=_("batch"),
            editable=False,
            initially_hidden=True,
        ),
        GridFieldText(
            "color",
            title=_("inventory status"),
            formatter="color",
            field_name="operationplan__color",
            width="125",
            editable=False,
            extra='"formatoptions":{"defaultValue":""}, "summaryType":"min"',
        ),
        GridFieldText(
            "operationplan__type",
            title=_("type"),
            field_name="operationplan__type",
            editable=False,
        ),
        GridFieldText(
            "operationplan__name",
            title=_("operation"),
            editable=False,
            field_name="operationplan__name",
            formatter="detail",
            extra='"role":"input/operation"',
        ),
        GridFieldText(
            "operationplan__operation__description",
            title=format_lazy("{} - {}", _("operation"), _("description")),
            editable=False,
            initially_hidden=True,
        ),
        GridFieldText(
            "operationplan__operation__category",
            title=format_lazy("{} - {}", _("operation"), _("category")),
            editable=False,
            initially_hidden=True,
        ),
        GridFieldText(
            "operationplan__operation__subcategory",
            title=format_lazy("{} - {}", _("operation"), _("subcategory")),
            editable=False,
            initially_hidden=True,
        ),
        GridFieldText(
            "operationplan__operation__type",
            title=format_lazy("{} - {}", _("operation"), _("type")),
            initially_hidden=True,
        ),
        GridFieldDuration(
            "operationplan__operation__duration",
            title=format_lazy("{} - {}", _("operation"), _("duration")),
            initially_hidden=True,
        ),
        GridFieldDuration(
            "operationplan__operation__duration_per",
            title=format_lazy("{} - {}", _("operation"), _("duration per unit")),
            initially_hidden=True,
        ),
        GridFieldDuration(
            "operationplan__operation__fence",
            title=format_lazy("{} - {}", _("operation"), _("release fence")),
            initially_hidden=True,
        ),
        GridFieldDuration(
            "operationplan__operation__posttime",
            title=format_lazy("{} - {}", _("operation"), _("post-op time")),
            initially_hidden=True,
        ),
        GridFieldNumber(
            "operationplan__operation__sizeminimum",
            title=format_lazy("{} - {}", _("operation"), _("size minimum")),
            initially_hidden=True,
        ),
        GridFieldNumber(
            "operationplan__operation__sizemultiple",
            title=format_lazy("{} - {}", _("operation"), _("size multiple")),
            initially_hidden=True,
        ),
        GridFieldNumber(
            "operationplan__operation__sizemaximum",
            title=format_lazy("{} - {}", _("operation"), _("size maximum")),
            initially_hidden=True,
        ),
        GridFieldInteger(
            "operationplan__operation__priority",
            title=format_lazy("{} - {}", _("operation"), _("priority")),
            initially_hidden=True,
        ),
        GridFieldDateTime(
            "operationplan__operation__effective_start",
            title=format_lazy("{} - {}", _("operation"), _("effective start")),
            initially_hidden=True,
        ),
        GridFieldDateTime(
            "operationplan__operation__effective_end",
            title=format_lazy("{} - {}", _("operation"), _("effective end")),
            initially_hidden=True,
        ),
        GridFieldCurrency(
            "operationplan__operation__cost",
            title=format_lazy("{} - {}", _("operation"), _("cost")),
            initially_hidden=True,
        ),
        GridFieldText(
            "operationplan__operation__search",
            title=format_lazy("{} - {}", _("operation"), _("search mode")),
            initially_hidden=True,
        ),
        GridFieldText(
            "operationplan__operation__source",
            title=format_lazy("{} - {}", _("operation"), _("source")),
            initially_hidden=True,
        ),
        GridFieldLastModified(
            "operationplan__operation__lastmodified",
            title=format_lazy("{} - {}", _("operation"), _("last modified")),
            initially_hidden=True,
        ),
        GridFieldDateTime(
            "flowdate",
            title=_("date"),
            editable=False,
            extra='"formatoptions":{"srcformat":"Y-m-d H:i:s","newformat":"Y-m-d H:i:s", "defaultValue":""}, "summaryType":"min"',
        ),
        GridFieldNumber(
            "quantity",
            title=_("quantity"),
            editable=False,
            extra='"formatoptions":{"defaultValue":""}, "summaryType":"sum"',
        ),
        GridFieldNumber(
            "onhand",
            title=_("expected onhand"),
            editable=False,
            extra='"formatoptions":{"defaultValue":""}, "summaryType":"sum"',
        ),
        GridFieldDuration(
            "periodofcover",
            title=_("period of cover"),
            editable=False,
            extra='"formatoptions":{"defaultValue":""}, "summaryType":"sum"',
        ),
        GridFieldDateTime(
            "operationplan__startdate",
            title=_("start date"),
            editable=False,
            extra='"formatoptions":{"srcformat":"Y-m-d H:i:s","newformat":"Y-m-d H:i:s", "defaultValue":""}, "summaryType":"min"',
        ),
        GridFieldDateTime(
            "operationplan__enddate",
            title=_("end date"),
            editable=False,
            extra='"formatoptions":{"srcformat":"Y-m-d H:i:s","newformat":"Y-m-d H:i:s", "defaultValue":""}, "summaryType":"max"',
        ),
        GridFieldText(
            "operationplan__status",
            title=_("status"),
            editable=False,
            field_name="operationplan__status",
        ),
        GridFieldText(
            "operationplan__batch",
            title=_("batch"),
            editable=False,
            field_name="operationplan__batch",
        ),
        GridFieldNumber(
            "operationplan__criticality",
            title=_("criticality"),
            field_name="operationplan__criticality",
            editable=False,
            extra='"formatoptions":{"defaultValue":""}, "summaryType":"min"',
        ),
        GridFieldDuration(
            "delay",
            title=_("delay"),
            field_name="operationplan__delay",
            editable=False,
            extra='"formatoptions":{"defaultValue":""}, "summaryType":"max"',
        ),
        GridFieldNumber(
            "operationplan__quantity",
            title=_("operationplan quantity"),
            editable=False,
            extra='"formatoptions":{"defaultValue":""}, "summaryType":"sum"',
        ),
        GridFieldText(
            "demands",
            title=_("demands"),
            formatter="demanddetail",
            extra='"role":"input/demand"',
            width=300,
            editable=False,
            sortable=False,
        ),
        GridFieldBool(
            "feasible",
            title=_("feasible"),
            editable=False,
            initially_hidden=True,
            search=False,
        ),
        # Optional fields referencing the item
        GridFieldText(
            "item__type",
            title=format_lazy("{} - {}", _("item"), _("type")),
            initially_hidden=True,
            editable=False,
        ),
        GridFieldText(
            "item__description",
            title=format_lazy("{} - {}", _("item"), _("description")),
            initially_hidden=True,
            editable=False,
        ),
        GridFieldText(
            "item__category",
            title=format_lazy("{} - {}", _("item"), _("category")),
            initially_hidden=True,
            editable=False,
        ),
        GridFieldText(
            "item__subcategory",
            title=format_lazy("{} - {}", _("item"), _("subcategory")),
            initially_hidden=True,
            editable=False,
        ),
        GridFieldNumber(
            "item__cost",
            title=format_lazy("{} - {}", _("item"), _("cost")),
            initially_hidden=True,
            editable=False,
        ),
        GridFieldText(
            "item__owner",
            title=format_lazy("{} - {}", _("item"), _("owner")),
            field_name="item__owner__name",
            initially_hidden=True,
            editable=False,
        ),
        GridFieldText(
            "item__source",
            title=format_lazy("{} - {}", _("item"), _("source")),
            initially_hidden=True,
            editable=False,
        ),
        GridFieldLastModified(
            "item__lastmodified",
            title=format_lazy("{} - {}", _("item"), _("last modified")),
            initially_hidden=True,
            editable=False,
        ),
        # Optional fields referencing the location
        GridFieldText(
            "location__description",
            title=format_lazy("{} - {}", _("location"), _("description")),
            initially_hidden=True,
            editable=False,
        ),
        GridFieldText(
            "location__category",
            title=format_lazy("{} - {}", _("location"), _("category")),
            initially_hidden=True,
            editable=False,
        ),
        GridFieldText(
            "location__subcategory",
            title=format_lazy("{} - {}", _("location"), _("subcategory")),
            initially_hidden=True,
            editable=False,
        ),
        GridFieldText(
            "location__available",
            title=format_lazy("{} - {}", _("location"), _("available")),
            initially_hidden=True,
            field_name="location__available__name",
            formatter="detail",
            extra='"role":"input/calendar"',
            editable=False,
        ),
        GridFieldText(
            "location__owner",
            title=format_lazy("{} - {}", _("location"), _("owner")),
            initially_hidden=True,
            field_name="location__owner__name",
            formatter="detail",
            extra='"role":"input/location"',
            editable=False,
        ),
        GridFieldText(
            "location__source",
            title=format_lazy("{} - {}", _("location"), _("source")),
            initially_hidden=True,
            editable=False,
        ),
        GridFieldLastModified(
            "location__lastmodified",
            title=format_lazy("{} - {}", _("location"), _("last modified")),
            initially_hidden=True,
            editable=False,
        ),
        GridFieldChoice(
            "status",
            title=_("material status"),
            choices=OperationPlanMaterial.OPMstatus,
        ),
        GridFieldLastModified("lastmodified", initially_hidden=True),
    )


class ResourceDetail(OperationPlanMixin, GridReport):
    template = "input/operationplanreport.html"
    title = _("resource detail")
    model = OperationPlanResource
    permissions = (("view_resource_report", "Can view resource report"),)
    frozenColumns = 3
    editable = True
    multiselect = True
    height = 250
    help_url = "user-interface/plan-analysis/resource-detail-report.html"

    @classmethod
    def basequeryset(reportclass, request, *args, **kwargs):
        if args and args[0]:
            try:
                res = Resource.objects.using(request.database).get(name__exact=args[0])
                base = OperationPlanResource.objects.filter(
                    resource__lft__gte=res.lft, resource__rght__lte=res.rght
                )
            except OperationPlanResource.DoesNotExist:
                base = OperationPlanResource.objects.filter(resource__exact=args[0])
        else:
            base = OperationPlanResource.objects
        base = reportclass.operationplanExtraBasequery(base, request)
        return base.select_related().annotate(
            opplan_duration=RawSQL(
                "(operationplan.enddate - operationplan.startdate)", []
            ),
            opplan_net_duration=RawSQL(
                "(operationplan.enddate - operationplan.startdate - coalesce((operationplan.plan->>'unavailable')::int * interval '1 second', interval '0 second'))",
                [],
            ),
            setup_end=RawSQL("(operationplan.plan->>'setupend')", []),
            setup_duration=RawSQL("(operationplan.plan->>'setup')", []),
            feasible=RawSQL(
                "coalesce((operationplan.plan->>'feasible')::boolean, true)", []
            ),
        )

    @classmethod
    def initialize(reportclass, request):
        if reportclass._attributes_added != 2:
            reportclass._attributes_added = 2
            # Adding custom operation attributes
            for f in getAttributeFields(
                Operation, related_name_prefix="operationplan__operation"
            ):
                f.editable = False
                reportclass.rows += (f,)
            # Adding custom resource attributes
            for f in getAttributeFields(Resource, related_name_prefix="resource"):
                f.editable = False
                reportclass.rows += (f,)

    @classmethod
    def extra_context(reportclass, request, *args, **kwargs):
        if args and args[0]:
            request.session["lasttab"] = "plandetail"
            return {
                "active_tab": "plandetail",
                "model": Resource,
                "title": force_text(Resource._meta.verbose_name) + " " + args[0],
                "post_title": _("plan detail"),
            }
        else:
            return {"active_tab": "plandetail", "model": OperationPlanResource}

    rows = (
        GridFieldInteger(
            "id",
            title="identifier",
            key=True,
            editable=False,
            formatter="detail",
            extra='"role":"input/operationplanresource"',
            initially_hidden=True,
        ),
        GridFieldText(
            "resource",
            title=_("resource"),
            field_name="resource__name",
            formatter="detail",
            extra='"role":"input/resource"',
        ),
        GridFieldText("operationplan__reference", title=_("reference"), editable=False),
        GridFieldText(
            "owner",
            title=_("owner"),
            field_name="operationplan__owner__reference",
            formatter="detail",
            extra="role:'input/manufacturingorder'",
            initially_hidden=True,
        ),
        GridFieldText(
            "color",
            title=_("inventory status"),
            formatter="color",
            field_name="operationplan__color",
            width="125",
            editable=False,
            extra='"formatoptions":{"defaultValue":""}, "summaryType":"min"',
        ),
        GridFieldText(
            "operationplan__item",
            title=_("item"),
            editable=False,
            formatter="detail",
            extra='"role":"input/item"',
        ),
        GridFieldText(
            "operationplan__location",
            title=_("location"),
            editable=False,
            formatter="detail",
            extra='"role":"input/location"',
        ),
        GridFieldText(
            "operationplan__operation__name",
            title=_("operation"),
            editable=False,
            formatter="detail",
            extra='"role":"input/operation"',
        ),
        GridFieldText(
            "operationplan__operation__description",
            title=format_lazy("{} - {}", _("operation"), _("description")),
            editable=False,
            initially_hidden=True,
        ),
        GridFieldText(
            "operationplan__operation__category",
            title=format_lazy("{} - {}", _("operation"), _("category")),
            editable=False,
            initially_hidden=True,
        ),
        GridFieldText(
            "operationplan__operation__subcategory",
            title=format_lazy("{} - {}", _("operation"), _("subcategory")),
            editable=False,
            initially_hidden=True,
        ),
        GridFieldText(
            "operationplan__operation__type",
            title=format_lazy("{} - {}", _("operation"), _("type")),
            initially_hidden=True,
        ),
        GridFieldDuration(
            "operationplan__operation__duration",
            title=format_lazy("{} - {}", _("operation"), _("duration")),
            initially_hidden=True,
        ),
        GridFieldDuration(
            "operationplan__operation__duration_per",
            title=format_lazy("{} - {}", _("operation"), _("duration per unit")),
            initially_hidden=True,
        ),
        GridFieldDuration(
            "operationplan__operation__fence",
            title=format_lazy("{} - {}", _("operation"), _("release fence")),
            initially_hidden=True,
        ),
        GridFieldDuration(
            "operationplan__operation__posttime",
            title=format_lazy("{} - {}", _("operation"), _("post-op time")),
            initially_hidden=True,
        ),
        GridFieldNumber(
            "operationplan__operation__sizeminimum",
            title=format_lazy("{} - {}", _("operation"), _("size minimum")),
            initially_hidden=True,
        ),
        GridFieldNumber(
            "operationplan__operation__sizemultiple",
            title=format_lazy("{} - {}", _("operation"), _("size multiple")),
            initially_hidden=True,
        ),
        GridFieldNumber(
            "operationplan__operation__sizemaximum",
            title=format_lazy("{} - {}", _("operation"), _("size maximum")),
            initially_hidden=True,
        ),
        GridFieldInteger(
            "operationplan__operation__priority",
            title=format_lazy("{} - {}", _("operation"), _("priority")),
            initially_hidden=True,
        ),
        GridFieldDateTime(
            "operationplan__operation__effective_start",
            title=format_lazy("{} - {}", _("operation"), _("effective start")),
            initially_hidden=True,
        ),
        GridFieldDateTime(
            "operationplan__operation__effective_end",
            title=format_lazy("{} - {}", _("operation"), _("effective end")),
            initially_hidden=True,
        ),
        GridFieldCurrency(
            "operationplan__operation__cost",
            title=format_lazy("{} - {}", _("operation"), _("cost")),
            initially_hidden=True,
        ),
        GridFieldText(
            "operationplan__operation__search",
            title=format_lazy("{} - {}", _("operation"), _("search mode")),
            initially_hidden=True,
        ),
        GridFieldText(
            "operationplan__operation__source",
            title=format_lazy("{} - {}", _("operation"), _("source")),
            initially_hidden=True,
        ),
        GridFieldLastModified(
            "operationplan__operation__lastmodified",
            title=format_lazy("{} - {}", _("operation"), _("last modified")),
            initially_hidden=True,
        ),
        GridFieldDateTime(
            "operationplan__startdate",
            title=_("start date"),
            editable=False,
            extra='"formatoptions":{"srcformat":"Y-m-d H:i:s","newformat":"Y-m-d H:i:s", "defaultValue":""}, "summaryType":"min"',
        ),
        GridFieldDateTime(
            "operationplan__enddate",
            title=_("end date"),
            editable=False,
            extra='"formatoptions":{"srcformat":"Y-m-d H:i:s","newformat":"Y-m-d H:i:s", "defaultValue":""}, "summaryType":"max"',
        ),
        GridFieldDuration(
            "opplan_duration",
            title=_("duration"),
            editable=False,
            extra='"formatoptions":{"defaultValue":""}, "summaryType":"sum"',
        ),
        GridFieldDuration(
            "opplan_net_duration",
            title=_("net duration"),
            editable=False,
            extra='"formatoptions":{"defaultValue":""}, "summaryType":"sum"',
        ),
        GridFieldNumber(
            "operationplan__quantity",
            title=_("quantity"),
            editable=False,
            extra='"formatoptions":{"defaultValue":""}, "summaryType":"sum"',
        ),
        GridFieldText("operationplan__status", title=_("status"), editable=False),
        GridFieldText(
            "operationplan__batch",
            title=_("batch"),
            editable=False,
            field_name="operationplan__batch",
        ),
        GridFieldNumber(
            "operationplan__criticality",
            title=_("criticality"),
            editable=False,
            extra='"formatoptions":{"defaultValue":""}, "summaryType":"min"',
        ),
        GridFieldDuration(
            "delay",
            title=_("delay"),
            field_name="operationplan__delay",
            editable=False,
            extra='"formatoptions":{"defaultValue":""}, "summaryType":"max"',
        ),
        GridFieldText(
            "demands",
            title=_("demands"),
            formatter="demanddetail",
            extra='"role":"input/demand"',
            width=300,
            editable=False,
            sortable=False,
        ),
        GridFieldText(
            "operationplan__type",
            title=_("type"),
            field_name="operationplan__type",
            editable=False,
        ),
        GridFieldNumber(
            "quantity",
            title=_("load quantity"),
            extra='"formatoptions":{"defaultValue":""}, "summaryType":"sum"',
        ),
        GridFieldText("setup", title=_("setup"), editable=False, initially_hidden=True),
        GridFieldDateTime(
            "setup_end",
            title=_("setup end date"),
            editable=False,
            initially_hidden=True,
        ),
        GridFieldDuration(
            "setup_duration",
            title=_("setup duration"),
            editable=False,
            initially_hidden=True,
            search=False,
        ),
        GridFieldBool(
            "feasible",
            title=_("feasible"),
            editable=False,
            initially_hidden=True,
            search=False,
        ),
        # Optional fields referencing the item
        GridFieldText(
            "operationplan__operation__item__type",
            title=format_lazy("{} - {}", _("item"), _("type")),
            initially_hidden=True,
            editable=False,
        ),
        GridFieldText(
            "operationplan__operation__item__description",
            initially_hidden=True,
            editable=False,
            title=format_lazy("{} - {}", _("item"), _("description")),
        ),
        GridFieldText(
            "operationplan__operation__item__category",
            initially_hidden=True,
            editable=False,
            title=format_lazy("{} - {}", _("item"), _("category")),
        ),
        GridFieldText(
            "operationplan__operation__item__subcategory",
            initially_hidden=True,
            editable=False,
            title=format_lazy("{} - {}", _("item"), _("subcategory")),
        ),
        GridFieldText(
            "operationplan__operation__item__owner",
            initially_hidden=True,
            editable=False,
            title=format_lazy("{} - {}", _("item"), _("owner")),
            field_name="operationplan__operation__item__owner__name",
        ),
        GridFieldText(
            "operationplan__operation__item__source",
            initially_hidden=True,
            editable=False,
            title=format_lazy("{} - {}", _("item"), _("source")),
        ),
        GridFieldLastModified(
            "operationplan__operation__item__lastmodified",
            initially_hidden=True,
            editable=False,
            title=format_lazy("{} - {}", _("item"), _("last modified")),
        ),
        # Optional fields referencing the operation location
        GridFieldText(
            "operationplan__operation__location__description",
            initially_hidden=True,
            editable=False,
            title=format_lazy("{} - {}", _("location"), _("description")),
        ),
        GridFieldText(
            "operationplan__operation__location__category",
            title=format_lazy("{} - {}", _("location"), _("category")),
            initially_hidden=True,
            editable=False,
        ),
        GridFieldText(
            "operationplan__operation__location__subcategory",
            title=format_lazy("{} - {}", _("location"), _("subcategory")),
            initially_hidden=True,
            editable=False,
        ),
        GridFieldText(
            "operationplan__operation__location__available",
            editable=False,
            title=format_lazy("{} - {}", _("location"), _("available")),
            initially_hidden=True,
            field_name="operationplan__operation__location__available__name",
            formatter="detail",
            extra='"role":"input/calendar"',
        ),
        GridFieldText(
            "operationplan__operation__location__owner",
            initially_hidden=True,
            title=format_lazy("{} - {}", _("location"), _("owner")),
            field_name="operationplan__operation__location__owner__name",
            formatter="detail",
            extra='"role":"input/location"',
            editable=False,
        ),
        GridFieldText(
            "operationplan__operation__location__source",
            initially_hidden=True,
            editable=False,
            title=format_lazy("{} - {}", _("location"), _("source")),
        ),
        GridFieldLastModified(
            "operationplan__operation__location__lastmodified",
            initially_hidden=True,
            editable=False,
            title=format_lazy("{} - {}", _("location"), _("last modified")),
        ),
        # Optional fields referencing the resource
        GridFieldText(
            "resource__description",
            editable=False,
            initially_hidden=True,
            title=format_lazy("{} - {}", _("resource"), _("description")),
        ),
        GridFieldText(
            "resource__category",
            editable=False,
            initially_hidden=True,
            title=format_lazy("{} - {}", _("resource"), _("category")),
        ),
        GridFieldText(
            "resource__subcategory",
            editable=False,
            initially_hidden=True,
            title=format_lazy("{} - {}", _("resource"), _("subcategory")),
        ),
        GridFieldText(
            "resource__type",
            editable=False,
            initially_hidden=True,
            title=format_lazy("{} - {}", _("resource"), _("type")),
        ),
        GridFieldBool(
            "resource__constrained",
            editable=False,
            initially_hidden=True,
            title=format_lazy("{} - {}", _("resource"), _("constrained")),
        ),
        GridFieldNumber(
            "resource__maximum",
            editable=False,
            initially_hidden=True,
            title=format_lazy("{} - {}", _("resource"), _("maximum")),
        ),
        GridFieldText(
            "resource__maximum_calendar",
            editable=False,
            initially_hidden=True,
            title=format_lazy("{} - {}", _("resource"), _("maximum calendar")),
            field_name="resource__maximum_calendar__name",
            formatter="detail",
            extra='"role":"input/calendar"',
        ),
        GridFieldCurrency(
            "resource__cost",
            editable=False,
            initially_hidden=True,
            title=format_lazy("{} - {}", _("resource"), _("cost")),
        ),
        GridFieldDuration(
            "resource__maxearly",
            editable=False,
            initially_hidden=True,
            title=format_lazy("{} - {}", _("resource"), _("maxearly")),
        ),
        GridFieldText(
            "resource__setupmatrix",
            editable=False,
            initially_hidden=True,
            title=format_lazy("{} - {}", _("resource"), _("setupmatrix")),
            field_name="resource__setupmatrix__name",
            formatter="detail",
            extra='"role":"input/setupmatrix"',
        ),
        GridFieldText(
            "resource__setup",
            editable=False,
            initially_hidden=True,
            title=format_lazy("{} - {}", _("resource"), _("setup")),
        ),
        GridFieldText(
            "resource_location",
            editable=False,
            initially_hidden=True,
            title=format_lazy("{} - {}", _("resource"), _("location")),
            field_name="resource__location__name",
            formatter="detail",
            extra='"role":"input/location"',
        ),
        # Optional fields referencing the resource location
        GridFieldText(
            "resource__location__description",
            initially_hidden=True,
            editable=False,
            title=format_lazy(
                "{} - {} - {}", _("resource"), _("location"), _("description")
            ),
        ),
        GridFieldText(
            "resource__location__category",
            initially_hidden=True,
            editable=False,
            title=format_lazy(
                "{} - {} - {}", _("resource"), _("location"), _("category")
            ),
        ),
        GridFieldText(
            "resource__location__subcategory",
            initially_hidden=True,
            editable=False,
            title=format_lazy(
                "{} - {} - {}", _("resource"), _("location"), _("subcategory")
            ),
        ),
        GridFieldText(
            "resource__location__available",
            initially_hidden=True,
            editable=False,
            title=format_lazy(
                "{} - {} - {}", _("resource"), _("location"), _("available")
            ),
            field_name="resource__location__available__name",
            formatter="detail",
            extra='"role":"input/calendar"',
        ),
        GridFieldText(
            "resource__location__owner",
            extra='"role":"input/location"',
            editable=False,
            title=format_lazy("{} - {} - {}", _("resource"), _("location"), _("owner")),
            initially_hidden=True,
            field_name="resource__location__owner__name",
            formatter="detail",
        ),
        GridFieldText(
            "resource__location__source",
            initially_hidden=True,
            editable=False,
            title=format_lazy(
                "{} - {} - {}", _("resource"), _("location"), _("source")
            ),
        ),
        # Status field currently not used
        # GridFieldChoice('status', title=_('load status'), choices=OperationPlanResource.OPRstatus),
        GridFieldLastModified("lastmodified", initially_hidden=True),
    )


class OperationPlanDetail(View):
    def getData(self, request):
        # Current date
        try:
            current_date = parse(
                Parameter.objects.using(request.database).get(name="currentdate").value
            )
        except Exception:
            current_date = datetime.now()
        cursor = connections[request.database].cursor()

        # Read the results from the database
        ids = request.GET.getlist("reference")
        first = True
        if not ids:
            yield "[]"
            raise StopIteration
        try:
            opplans = [
                x
                for x in OperationPlan.objects.all()
                .using(request.database)
                .filter(reference__in=ids)
                .select_related("operation")
            ]
            opplanmats = [
                x
                for x in OperationPlanMaterial.objects.all()
                .using(request.database)
                .filter(operationplan__reference__in=ids)
                .values()
            ]
            opplanrscs = [
                x
                for x in OperationPlanResource.objects.all()
                .using(request.database)
                .filter(operationplan__reference__in=ids)
                .values()
            ]
        except Exception as e:
            logger.error("Error retrieving operationplan data: %s" % e)
            yield "[]"
            raise StopIteration

        # Store my permissions
        view_PO = request.user.has_perm("input.view_purchaseorder")
        view_MO = request.user.has_perm("input.view_manufacturingorder")
        view_DO = request.user.has_perm("input.view_distributionorder")
        view_OpplanMaterial = request.user.has_perm("input.view_operationplanmaterial")
        view_OpplanResource = request.user.has_perm("input.view_operationplanresource")

        # Loop over all operationplans
        for opplan in opplans:

            # Check permissions
            if opplan.type == "DO" and not view_DO:
                continue
            if opplan.type == "PO" and not view_PO:
                continue
            if opplan.type == "MO" and not view_MO:
                continue
            try:
                # Base information
                res = {
                    "reference": opplan.reference,
                    "start": opplan.startdate.strftime("%Y-%m-%dT%H:%M:%S")
                    if opplan.startdate
                    else None,
                    "end": opplan.enddate.strftime("%Y-%m-%dT%H:%M:%S")
                    if opplan.enddate
                    else None,
                    "setupend": opplan.plan["setupend"].replace(" ", "T")
                    if "setupend" in opplan.plan
                    else None,
                    "quantity": float(opplan.quantity),
                    "criticality": float(opplan.criticality)
                    if opplan.criticality
                    else "",
                    "delay": opplan.delay.total_seconds() if opplan.delay else "",
                    "status": opplan.status,
                    "type": opplan.type,
                    "name": opplan.name,
                    "destination": opplan.destination_id,
                    "location": opplan.location_id,
                    "origin": opplan.origin_id,
                    "supplier": opplan.supplier_id,
                    "item": opplan.item_id,
                    "color": float(opplan.color) if opplan.color else "",
                    "owner": opplan.owner.reference if opplan.owner else None,
                }
                if opplan.plan and "pegging" in opplan.plan:
                    res["pegging_demand"] = []
                    for d, q in opplan.plan["pegging"].items():
                        try:
                            obj = (
                                Demand.objects.all()
                                .using(request.database)
                                .only("name", "item", "due")
                                .get(name=d)
                            )
                            res["pegging_demand"].append(
                                {
                                    "demand": {
                                        "name": obj.name,
                                        "item": {"name": obj.item.name},
                                        "due": obj.due.strftime("%Y-%m-%dT%H:%M:%S"),
                                    },
                                    "quantity": q,
                                }
                            )
                        except Demand.DoesNotExist:
                            # Looks like this demand was deleted since the plan was generated
                            continue
                    res["pegging_demand"].sort(
                        key=lambda f: (f["demand"]["name"], f["demand"]["due"])
                    )
                if opplan.operation:
                    res["operation"] = {
                        "name": opplan.operation.name,
                        "type": "operation_%s" % opplan.operation.type,
                    }

                # Information on materials
                if view_OpplanMaterial:
                    # Retrieve information about eventual alternates
                    alts = {}
                    if opplan.operation:
                        cursor.execute(
                            """
                            select a.item_id, b.item_id
                            from operationmaterial a 
                            inner join operationmaterial b on a.operation_id = b.operation_id and a.name = b.name
                            where a.operation_id = %s
                            and a.id != b.id
                            """,
                            (opplan.operation.name,),
                        )
                        for i in cursor.fetchall():
                            if i[0] not in alts:
                                alts[i[0]] = set()
                            alts[i[0]].add(i[1])
                    firstmat = True
                    for m in opplanmats:
                        if m["operationplan_id"] != opplan.reference:
                            continue
                        if firstmat:
                            firstmat = False
                            res["flowplans"] = []
                        flowplan = {
                            "date": m["flowdate"].strftime("%Y-%m-%dT%H:%M:%S"),
                            "quantity": float(m["quantity"]),
                            "onhand": float(m["onhand"] or 0),
                            "buffer": {
                                "item": m["item_id"],
                                "location": m["location_id"],
                            },
                        }
                        # List matching alternates
                        if m["item_id"] in alts:
                            flowplan["alternates"] = list(alts[m["item_id"]])
                        res["flowplans"].append(flowplan)

                # Information on resources
                if view_OpplanResource:
                    # Retrieve information about eventual alternates
                    alts = {}
                    if opplan.operation:
                        cursor.execute(
                            """
                            select res_children.name, alt_res_children.name
                            from operationresource
                            inner join resource
                              on  resource.name = operationresource.resource_id
                            inner join resource res_children
                              on  res_children.lft between resource.lft and resource.rght
                              and res_children.rght = res_children.lft + 1
                            inner join operationresource alt_opres
                              on ((operationresource.name is not null and operationresource.name = alt_opres.name)
                              or (operationresource.name is null and operationresource.id = alt_opres.id))
                              and operationresource.operation_id = alt_opres.operation_id
                            inner join resource alt_res
                              on alt_opres.resource_id = alt_res.name
                            inner join resource alt_res_children
                               on alt_res_children.lft between alt_res.lft and alt_res.rght
                               and alt_res_children.rght = alt_res_children.lft + 1
                            where (operationresource.skill_id is null or exists (
                               select 1 from resourceskill
                               where resourceskill.resource_id = alt_res_children.name
                               and resourceskill.skill_id = alt_opres.skill_id
                               ))
                            and operationresource.operation_id = %s
                            """,
                            (opplan.operation.name,),
                        )
                        for i in cursor.fetchall():
                            if i[0] not in alts:
                                alts[i[0]] = set()
                            alts[i[0]].add(i[1])
                    firstres = True
                    for m in opplanrscs:
                        if m["operationplan_id"] != opplan.reference:
                            continue
                        if firstres:
                            firstres = False
                            res["loadplans"] = []
                        ldplan = {
                            "date": m["startdate"].strftime("%Y-%m-%dT%H:%M:%S"),
                            "quantity": float(m["quantity"]),
                            "resource": {"name": m["resource_id"]},
                        }
                        # List matching alternates
                        for a in alts.values():
                            if m["resource_id"] in a:
                                t = [{"name": i} for i in a if i != m["resource_id"]]
                                if t:
                                    ldplan["alternates"] = t
                                break
                        res["loadplans"].append(ldplan)

                # Retrieve network status
                if opplan.item_id:
                    cursor.execute(
                        """
                        with items as (
                           select name from item where name = %s
                           )
                        select
                          items.name,
                          false,
                          location.name,
                          coalesce(onhand.qty,0) + coalesce(completed.quantity,0),
                          orders_plus.PO,
                          coalesce(orders_plus.DO, 0) - coalesce(orders_minus.DO, 0),
                          orders_plus.MO, sales.BO, sales.SO
                        from items
                        cross join location
                        left outer join (
                          select item_id, location_id, onhand as qty
                          from buffer
                          inner join items on items.name = buffer.item_id
                          ) onhand
                        on onhand.item_id = items.name and onhand.location_id = location.name
                        left outer join (
                           select opm.item_id, opm.location_id, sum(opm.quantity) as quantity
                           from operationplanmaterial opm
                           inner join operationplan op on opm.operationplan_id = op.reference
                           where op.status = 'completed'
                           group by opm.item_id, opm.location_id
                        ) completed
                        on completed.item_id = items.name and completed.location_id = location.name
                        left outer join (
                          select item_id, coalesce(location_id, destination_id) as location_id,
                          sum(case when type = 'MO' then quantity end) as MO,
                          sum(case when type = 'PO' then quantity end) as PO,
                          sum(case when type = 'DO' then quantity end) as DO
                          from operationplan
                          inner join items on items.name = operationplan.item_id
                          and status in ('approved', 'confirmed')
                          group by item_id, coalesce(location_id, destination_id)
                          ) orders_plus
                        on orders_plus.item_id = items.name and orders_plus.location_id = location.name
                        left outer join (
                          select item_id, origin_id as location_id,
                          sum(quantity) as DO
                          from operationplan
                          inner join items on items.name = operationplan.item_id
                          and status in ('approved', 'confirmed')
                          and type = 'DO'
                          group by item_id, origin_id
                          ) orders_minus
                        on orders_minus.item_id = items.name and orders_minus.location_id = location.name
                        left outer join (
                          select item_id, location_id,
                          sum(case when due < %s then quantity end) as BO,
                          sum(case when due >= %s then quantity end) as SO
                          from demand
                          inner join items on items.name = demand.item_id
                          where status in ('open', 'quote')
                          group by item_id, location_id
                          ) sales
                        on sales.item_id = items.name and sales.location_id = location.name
                        where
                          (coalesce(onhand.qty,0) + coalesce(completed.quantity,0)) > 0
                          or orders_plus.MO is not null
                          or orders_plus.PO is not null
                          or orders_plus.DO is not null
                          or orders_minus.DO is not null
                          or sales.BO is not null
                          or sales.SO is not null
                          or (items.name = %s and location.name = %s)
                        order by items.name, location.name
                        """,
                        (
                            opplan.item_id,
                            current_date,
                            current_date,
                            opplan.item_id,
                            opplan.location_id,
                        ),
                    )
                    res["network"] = []
                    for a in cursor.fetchall():
                        res["network"].append(
                            [
                                a[0],
                                a[1],
                                a[2],
                                float(a[3] or 0),
                                float(a[4] or 0),
                                float(a[5] or 0),
                                float(a[6] or 0),
                                float(a[7] or 0),
                                float(a[8] or 0),
                            ]
                        )

                # Downstream operationplans

                cursor.execute(
                    """
                with cte as
                (
                select (value->>0)::int as level,
                value->>1 as reference,
                (value->>2)::numeric as quantity,
                row_number() over() as rownum
                from jsonb_array_elements((select plan->'downstream_opplans' from operationplan where reference = %%s))
                )
                select cte.level,
                cte.reference,
                operationplan.type,
                case when operationplan.type = 'PO' then 'Purchase '||operationplan.item_id||' @ '||operationplan.location_id||' from '||operationplan.supplier_id
                     when operationplan.type = 'DO' then 'Ship '||operationplan.item_id||' from '||operationplan.origin_id||' to '||operationplan.destination_id
                     %s
                else operationplan.operation_id end,
                operationplan.status,
                operationplan.item_id,
                coalesce(operationplan.location_id, operationplan.destination_id),
                to_char(operationplan.startdate,'YYYY-MM-DD hh24:mi:ss'),
                to_char(operationplan.enddate,'YYYY-MM-DD hh24:mi:ss'),
                trim(trailing '.' from (trim(trailing '0' from round(cte.quantity,8)::text)))||'/'||
                trim(trailing '.' from (trim(trailing '0' from round(operationplan.quantity,8)::text)))
                from cte
                inner join operationplan on operationplan.reference = cte.reference
                order by cte.rownum
                """
                    % (
                        "when operationplan.demand_id is not null then 'Deliver '||operationplan.demand_id"
                        if "freppledb.forecast" not in settings.INSTALLED_APPS
                        else """
                        when coalesce(operationplan.demand_id, operationplan.forecast) is not null then 'Deliver '||coalesce(operationplan.demand_id, operationplan.forecast)
                        """
                    ),
                    (opplan.reference,),
                )

                if cursor.rowcount > 0:
                    res["downstreamoperationplans"] = []
                    for a in cursor.fetchall():
                        res["downstreamoperationplans"].append(
                            [
                                a[0],  # level
                                a[1],  # reference
                                a[2],  # type
                                a[3],  # operation
                                a[4],  # status
                                a[5],  # item
                                a[6],  # location
                                a[7],  # startdate
                                a[8],  # enddate
                                a[9],  # quantity,
                                0 if a[0] == 1 else 2,
                            ]
                        )

                # Upstream operationplans

                cursor.execute(
                    """
                with cte as
                (
                select (value->>0)::int as level,
                value->>1 as reference,
                (value->>2)::numeric as quantity,
                row_number() over() as rownum
                from jsonb_array_elements((select plan->'upstream_opplans' from operationplan where reference = %s))
                )
                select cte.level,
                cte.reference,
                operationplan.type,
                case when operationplan.type = 'PO' then 'Purchase '||operationplan.item_id||' @ '||operationplan.location_id||' from '||operationplan.supplier_id
                     when operationplan.type = 'DO' then 'Ship '||operationplan.item_id||' from '||operationplan.origin_id||' to '||operationplan.destination_id
                else operationplan.operation_id end,
                operationplan.status,
                operationplan.item_id,
                coalesce(operationplan.location_id, operationplan.destination_id),
                case when operationplan.type = 'STCK' then '' else to_char(operationplan.startdate,'YYYY-MM-DD hh24:mi:ss') end,
                case when operationplan.type = 'STCK' then '' else to_char(operationplan.enddate,'YYYY-MM-DD hh24:mi:ss') end,
                trim(trailing '.' from (trim(trailing '0' from round(cte.quantity,8)::text)))||'/'||
                trim(trailing '.' from (trim(trailing '0' from round(operationplan.quantity,8)::text)))
                from cte
                inner join operationplan on operationplan.reference = cte.reference
                order by cte.rownum
                """,
                    (opplan.reference,),
                )

                if cursor.rowcount > 0:
                    res["upstreamoperationplans"] = []
                    for a in cursor.fetchall():
                        res["upstreamoperationplans"].append(
                            [
                                a[0],  # level
                                a[1],  # reference
                                a[2],  # type
                                a[3] or "",  # operation (null if optype is STCK)
                                a[4],  # status
                                a[5],  # item
                                a[6],  # location
                                a[7],  # startdate
                                a[8],  # enddate
                                a[9],  # quantity,
                                0 if a[0] == 1 else 2,
                            ]
                        )

                # Final result
                if first:
                    yield "[%s" % json.dumps(res)
                    first = False
                else:
                    yield ",%s" % json.dumps(res)
                yield "]"
            except Exception as e:
                # Ignore exceptions and move on
                logger.error("Error retrieving operationplan: %s" % e)

    @method_decorator(csrf_exempt)
    def dispatch(self, request, *args, **kwargs):
        return super().dispatch(request, *args, **kwargs)

    @method_decorator(staff_member_required)
    def get(self, request):
        # Only accept ajax requests on this URL
        if not request.is_ajax():
            raise Http404("Only ajax requests allowed")

        # Stream back the response
        response = StreamingHttpResponse(
            content_type="application/json; charset=%s" % settings.DEFAULT_CHARSET,
            streaming_content=self.getData(request),
        )
        response["Cache-Control"] = "no-cache, no-store"
        return response

    @method_decorator(staff_member_required)
    def post(self, request):
        # Only accept ajax requests on this URL
        if not request.is_ajax():
            raise Http404("Only ajax requests allowed")

        # Parse the posted data
        try:
            data = json.JSONDecoder().decode(
                request.read().decode(request.encoding or settings.DEFAULT_CHARSET)
            )
        except Exception as e:
            logger.error("Error updating operationplan data: %s" % e)
            return HttpResponseServerError(
                "Error updating operationplan data", content_type="text/html"
            )

        update_PO = request.user.has_perm("input.change_purchaseorder")
        update_MO = request.user.has_perm("input.change_manufacturingorder")
        update_DO = request.user.has_perm("input.change_distributionorder")

        for opplan_data in data:
            try:
                # Read the object from the database
                opplan = (
                    OperationPlan.objects.all()
                    .using(request.database)
                    .get(reference=opplan_data.get("id", None))
                )

                # Check permissions
                if opplan.type == "DO" and not update_DO:
                    continue
                if opplan.type == "PO" and not update_PO:
                    continue
                if opplan.type == "MO" and not update_MO:
                    continue

                # Update fields
                save = False
                if "start" in opplan_data:
                    # Update start date
                    opplan.startdate = datetime.strptime(
                        opplan_data["start"], "%Y-%m-%dT%H:%M:%S"
                    )
                    save = True
                if "end" in opplan_data:
                    # Update end date
                    opplan.enddate = datetime.strptime(
                        opplan_data["end"], "%Y-%m-%dT%H:%M:%S"
                    )
                    save = True
                if "quantity" in opplan_data:
                    # Update quantity
                    opplan.quantity = opplan_data["quantity"]
                    save = True
                if "status" in opplan_data:
                    # Status quantity
                    opplan.status = opplan_data["status"]
                    save = True

                if "reference" in opplan_data:
                    # Update reference
                    opplan.reference = opplan_data["reference"]
                    save = True

                # Save if changed
                if save:
                    opplan.save(
                        using=request.database,
                        update_fields=[
                            "startdate",
                            "enddate",
                            "quantity",
                            "reference",
                            "lastmodified",
                        ],
                    )
            except OperationPlan.DoesNotExist:
                # Silently ignore
                pass
            except Exception as e:
                # Swallow the exception and move on
                logger.error("Error updating operationplan: %s" % e)
        return HttpResponse(content="OK")
