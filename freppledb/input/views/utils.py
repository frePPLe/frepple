#
# Copyright (C) 2007-2013 by frePPLe bv
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

from django.conf import settings
from django.contrib.admin.views.decorators import staff_member_required
from django.core.exceptions import FieldDoesNotExist
from django.db import connections
from django.db.models import Q, F
from django.db.models.expressions import RawSQL
from django.db.models.fields import CharField
from django.http import HttpResponse, Http404
from django.http.response import StreamingHttpResponse, HttpResponseServerError
from django.utils.decorators import method_decorator
from django.utils.translation import gettext_lazy as _
from django.utils.translation import ngettext
from django.utils.encoding import force_str
from django.utils.text import format_lazy
from django.views.generic import View
from django.views.decorators.csrf import csrf_exempt

from freppledb.common.auth import getWebserviceAuthorization
from freppledb.common.report import (
    GridReport,
    GridFieldText,
    GridFieldNumber,
    GridFieldInteger,
    GridFieldBoolNullable,
    GridFieldDuration,
    getCurrentDate,
    getHorizon,
)
from freppledb.input.models import (
    Resource,
    Operation,
    Location,
    Buffer,
    Demand,
    Item,
    OperationPlan,
    OperationPlanMaterial,
    OperationPlanResource,
)
from freppledb.admin import data_site
from freppledb.webservice.utils import getWebServiceContext

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
    with_forecast = "freppledb.forecast" in settings.INSTALLED_APPS
    if with_forecast:
        from freppledb.forecast.models import Forecast

        query = (
            Forecast.objects.using(request.database)
            .filter(
                Q(item__name__icontains=term) | Q(item__description__icontains=term)
            )
            .order_by("item__name")
            .distinct("item__name")
            .values_list("item__name", "item__description")
        )
        count = len(query)
        if count > 0:
            result.append(
                {
                    "value": None,
                    "label": (
                        ngettext(
                            "%(name)s - %(count)d match",
                            "%(name)s - %(count)d matches",
                            count,
                        )
                        % {"name": force_str(_("Forecast editor")), "count": count}
                    ).capitalize(),
                }
            )
            result.extend(
                [
                    {
                        "url": "/forecast/editor/",
                        "value": i[0],
                        "display": "%s%s" % (i[0], " %s" % (i[1],) if i[1] else ""),
                    }
                    for i in query[:10]
                ]
            )
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
                            ngettext(
                                "%(name)s - %(count)d match",
                                "%(name)s - %(count)d matches",
                                count,
                            )
                            % {
                                "name": force_str(cls._meta.verbose_name),
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
                            "removeTrailingSlash": (
                                True if issubclass(cls, OperationPlan) else False
                            ),
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


class OperationPlanMixin(GridReport):
    # Hack to allow variable height depending on the detail position
    variableheight = True

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
            left outer join forecast on substring(key from 0 for length(key)
                                                                 - position(' - ' in reverse(key))
                                                                 -1) = forecast.name
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

    @classmethod
    def _generate_kanban_data(cls, request, *args, **kwargs):
        # Preparation of the correct filter for a column is currently done on the client side.
        # The kanban query also doesn't know about pages.
        request.GET = request.GET.copy()
        request.GET["page"] = None
        request.limit = request.pagesize
        return cls._generate_json_data(request, *args, **kwargs)

    @classmethod
    def _generate_calendar_data(cls, request, *args, **kwargs):
        request.GET = request.GET.copy()
        request.GET["page"] = None
        request.limit = request.pagesize
        return cls._generate_json_data(request, *args, **kwargs)

    calendarmode = "duration"

    @classmethod
    def extra_context(reportclass, request, *args, **kwargs):
        reportclass.getBuckets(request)
        prefs = getattr(request, "prefs", None)
        if prefs:
            widgets = prefs.get("widgets", None)
        else:
            request.prefs = {}
            widgets = None
        if not widgets:
            # Inject the default layout of the widgets
            request.prefs["widgets"] = [
                {
                    "name": "column1",
                    "cols": [
                        {
                            "width": 6,
                            "widgets": [
                                ["operationplan", {"collapsed": False}],
                                ["inventorygraph", {"collapsed": False}],
                            ],
                        }
                    ],
                },
                {
                    "name": "column2",
                    "cols": [
                        {
                            "width": 6,
                            "widgets": [
                                ["inventorydata", {"collapsed": False}],
                                ["operationproblems", {"collapsed": False}],
                                ["operationresources", {"collapsed": False}],
                                ["operationflowplans", {"collapsed": False}],
                                ["operationdemandpegging", {"collapsed": False}],
                            ],
                        }
                    ],
                },
                {
                    "name": "column3",
                    "cols": [
                        {
                            "width": 12,
                            "widgets": [
                                ["networkstatus", {"collapsed": False}],
                                ["downstreamoperationplans", {"collapsed": False}],
                                ["upstreamoperationplans", {"collapsed": False}],
                            ],
                        }
                    ],
                },
            ]
            return {"preferences": request.prefs} | getWebServiceContext(request)
        else:
            return getWebServiceContext(request)


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
        GridFieldText(
            "uom",
            title=format_lazy("{} - {}", _("item"), _("Unit of Measure")),
            editable=False,
            sortable=False,
            initially_hidden=True,
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
        GridFieldText("blockedby", editable=False, sortable=False, hidden=True),
        GridFieldText("blocking", editable=False, sortable=False, hidden=True),
        # for time_per/fixed_time operations, rownb,y refer to the position (row,col)
        # of the suboperation in a routing when operation dependencies exist in the routing
        # for routing opertions, rownb,colnb refer to the number of rows and columns the routing should
        # have. If no depndencies exist in that routing, rownb and colnb are None
        GridFieldInteger("rownb", editable=False, sortable=False, hidden=True),
        GridFieldInteger("colnb", editable=False, sortable=False, hidden=True),
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
            "title": force_str(reportclass.objecttype._meta.verbose_name)
            + " "
            + (buffer_name if "buffer_name" in vars() else args[0]),
            "post_title": (
                _("where used") if reportclass.downstream else _("supply path")
            ),
            "downstream": reportclass.downstream,
            "active_tab": reportclass.downstream and "whereused" or "supplypath",
            "model": reportclass.objecttype,
        }

    @classmethod
    def getOperationFromItem(
        reportclass, request, cursor, item_name, downstream, depth
    ):
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
      item_description,
      (select jsonb_object_agg(distinct operation_dependency.blockedby_id, operation_dependency.quantity)
      filter (where operation_dependency.blockedby_id is not null)
      from operation_dependency where operation_id = operation),
      (select jsonb_object_agg(distinct operation_dependency.operation_id, operation_dependency.quantity)
      filter (where operation_dependency.operation_id is not null)
      from operation_dependency where blockedby_id = operation),
      item_uom,
      (select jsonb_object_agg(distinct operation_dependency.blockedby_id, operation_dependency.quantity)
      filter (where operation_dependency.blockedby_id is not null)
      from operation_dependency where operation_id = parentoperation),
      (select jsonb_object_agg(distinct operation_dependency.operation_id, operation_dependency.quantity)
      filter (where operation_dependency.operation_id is not null)
      from operation_dependency where blockedby_id = parentoperation)
       from
      (
      select operation.name as operation,
           coalesce(operation.type,'fixed_time') operation_type,
           operation.location_id operation_location,
           coalesce(operation.priority, 1) as operation_priority,
           operation.duration as operation_duration,
           operation.duration_per as operation_duration_per,
           case when operation.item_id is not null then jsonb_build_object(operation.item_id||' @ '||operation.location_id, 1) else '{}'::jsonb end
           ||jsonb_object_agg(operationmaterial.item_id||' @ '||coalesce(operationmaterial.location_id, operation.location_id),
                              coalesce(operationmaterial.quantity, operationmaterial.quantity_fixed,0)) filter (where operationmaterial.id is not null) as operation_om,
           jsonb_object_agg(operationresource.resource_id, operationresource.quantity) filter (where operationresource.id is not null) as operation_or,
             parentoperation.name as parentoperation,
           parentoperation.type as parentoperation_type,
           coalesce(parentoperation.priority, 1) parentoperation_priority,
             sibling.name as sibling,
           sibling.type as sibling_type,
           sibling.location_id as sibling_location,
           coalesce(sibling.priority, 1) as sibling_priority,
           sibling.duration as sibling_duration,
           sibling.duration_per as sibling_duration_per,
           case when grandparentoperation.item_id is not null
           and coalesce(sibling.priority, 1) = (select max(priority) from operation where owner_id = parentoperation.name)
           then jsonb_build_object(grandparentoperation.item_id||' @ '||grandparentoperation.location_id, 1) else '{}'::jsonb end
           ||case when parentoperation.item_id is not null
           and coalesce(sibling.priority, 1) = (select max(priority) from operation where owner_id = parentoperation.name)
           then jsonb_build_object(parentoperation.item_id||' @ '||parentoperation.location_id, 1) else '{}'::jsonb end
           ||case when sibling.item_id is not null then jsonb_build_object(sibling.item_id||' @ '||sibling.location_id, 1) else '{}'::jsonb end
           ||coalesce(jsonb_object_agg(siblingoperationmaterial.item_id||' @ '||coalesce(siblingoperationmaterial.location_id,sibling.location_id),
                                       coalesce(siblingoperationmaterial.quantity, siblingoperationmaterial.quantity_fixed,0)) filter (where siblingoperationmaterial.id is not null), '{}'::jsonb) as sibling_om,
           jsonb_object_agg(siblingoperationresource.resource_id, siblingoperationresource.quantity)filter (where siblingoperationresource.id is not null) as sibling_or,
             grandparentoperation.name as grandparentoperation,
           grandparentoperation.type as grandparentoperation_type,
           coalesce(grandparentoperation.priority, 1) as grandparentoperation_priority,
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
           item.description as item_description,
           item.uom as item_uom,
           null, -- blockedby parent
           null -- blocking parent
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
      where coalesce(operation.priority,1) != 0 and
      not exists (select 1 from operation parent_op where parent_op.name = operation.owner_id and parent_op.priority = 0)
      and coalesce(operation.type,'fixed_time') in ('time_per','fixed_time')
      %s
      group by operation.name, parentoperation.name, sibling.name, grandparentoperation.name,
      grandparentitem.name, parentitem.name, item.name, grandparentitem.description, parentitem.description, item.description
      ) t
      union all
      -- DISTRIBUTION OPERATIONS
      select 'Ship '||item.name||' from '||itemdistribution.origin_id||' to '||itemdistribution.location_id,
      itemdistribution.location_id,
      'distribution' as type,
      itemdistribution.priority,
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
      item.description,
      null, -- blockedby
      null, --blocking
      item.uom as item_uom,
      null, -- blockedby parent
      null -- blocking parent
      from itemdistribution
      inner join item parent on parent.name = itemdistribution.item_id
      inner join item on item.name = %%s and item.lft between parent.lft and parent.rght
      """ % (
            (
                """
                and (operation.item_id = %s or
                (exists (select 1 from operationmaterial op1 where op1.operation_id = operation.name and op1.item_id = %s and op1.quantity > 0))
                or parentoperation.item_id = %s
                or grandparentoperation.item_id = %s)
            """,
            )
            if not downstream
            else (
                """
                and (
                  exists (select 1 from operationmaterial om where om.operation_id = operation.name
                  and om.item_id = %s and om.quantity < 0)
                  or exists(select 1 from operation_dependency
                   where (operation.name = operation_dependency.operation_id
                     or operation.name = operation_dependency.blockedby_id)
                     and operation.item_id = %s)
                )
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
      itemsupplier.priority,
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
      item.description,
      null, -- blockedby
      null, --blocking
      item.uom as item_uom,
      null, -- blockedby parent
      null -- blocking parent
      from itemsupplier
      inner join item i_parent on i_parent.name = itemsupplier.item_id
      inner join item on item.name = %s and item.lft between i_parent.lft and i_parent.rght
      inner join location on location.name = itemsupplier.location_id
      union all
      select 'Purchase '||item.name||' @ '|| location.name||' from '||itemsupplier.supplier_id,
      location.name as location_id,
      'purchase' as type,
      itemsupplier.priority,
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
      item.description,
      null, -- blockedby
      null, --blocking
      item.uom as item_uom,
      null, -- blockedby parent
      null -- blocking parent
      from itemsupplier
      inner join item i_parent on i_parent.name = itemsupplier.item_id
      inner join item on item.name = %s and item.lft between i_parent.lft and i_parent.rght
      inner join location on location.lft = location.rght - 1
      where location_id is null
      """
            )

        query = (
            query
            + " order by grandparentoperation_priority, grandparentoperation, parentoperation_priority, parentoperation, sibling_priority"
        )

        if downstream:
            cursor.execute(query, (item_name,) * 3)
        else:
            cursor.execute(query, (item_name,) * 7)

        for i in cursor.fetchall():
            yield from reportclass.processRecord(
                cursor, i, request, depth, downstream, None, 1
            )

    @classmethod
    def getOperationFromResource(
        reportclass, request, cursor, resource_name, downstream, depth
    ):
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
      item_description,
      (select jsonb_object_agg(distinct operation_dependency.blockedby_id, operation_dependency.quantity)
      filter (where operation_dependency.blockedby_id is not null)
      from operation_dependency where operation_id = operation),
      (select jsonb_object_agg(distinct operation_dependency.operation_id, operation_dependency.quantity)
      filter (where operation_dependency.operation_id is not null)
      from operation_dependency where blockedby_id = operation),
      item_uom,
      (select jsonb_object_agg(distinct operation_dependency.blockedby_id, operation_dependency.quantity)
      filter (where operation_dependency.blockedby_id is not null)
      from operation_dependency where operation_id = parentoperation),
      (select jsonb_object_agg(distinct operation_dependency.operation_id, operation_dependency.quantity)
      filter (where operation_dependency.operation_id is not null)
      from operation_dependency where blockedby_id = parentoperation)
       from
      (
      select operation.name as operation,
           coalesce(operation.type,'fixed_time') operation_type,
           operation.location_id operation_location,
           operation.priority as operation_priority,
           operation.duration as operation_duration,
           operation.duration_per as operation_duration_per,
           case when operation.item_id is not null then jsonb_build_object(operation.item_id||' @ '||operation.location_id, 1) else '{}'::jsonb end
           ||jsonb_object_agg(operationmaterial.item_id||' @ '||coalesce(operationmaterial.location_id, operation.location_id),
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
           item.description as item_description,
           item.uom as item_uom
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
      where
      coalesce(operation.priority,1) != 0 and
      not exists (select 1 from operation parent_op where parent_op.name = operation.owner_id and parent_op.priority = 0)
      and coalesce(operation.type,'fixed_time') in ('time_per','fixed_time')
      and %s
      group by operation.name, parentoperation.name, sibling.name, grandparentoperation.name,
      grandparentitem.name, parentitem.name, item.name, grandparentitem.description, parentitem.description, item.description
      ) t
      union all
      -- DISTRIBUTION OPERATIONS
      select 'Ship '||item.name||' from '||itemdistribution.origin_id||' to '||itemdistribution.location_id,
      itemdistribution.location_id,
      'distribution' as type,
      itemdistribution.priority,
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
      item.description,
      null, -- blockedby
      null, --blocking
      item.uom as item_uom,
      null, -- blockedby parent
      null -- blocking parent
      from itemdistribution
      inner join item parent on parent.name = itemdistribution.item_id
      inner join item on item.lft between parent.lft and parent.rght
      where itemdistribution.resource_id = %%s
      union all
      -- PURCHASING OPERATIONS
      select 'Purchase '||item.name||' @ '|| location.name||' from '||itemsupplier.supplier_id,
      location.name as location_id,
      'purchase' as type,
      itemsupplier.priority,
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
      item.description,
      null, -- blockedby
      null, --blocking
      item.uom as item_uom,
      null, -- blockedby parent
      null -- blocking parent
      from itemsupplier
      inner join item i_parent on i_parent.name = itemsupplier.item_id
      inner join item on item.lft between i_parent.lft and i_parent.rght
      inner join location on location.name = itemsupplier.location_id
      where itemsupplier.resource_id = %%s
      union all
      select 'Purchase '||item.name||' @ '|| location.name||' from '||itemsupplier.supplier_id,
      location.name as location_id,
      'purchase' as type,
      itemsupplier.priority,
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
      item.description,
      null, -- blockedby
      null, --blocking
      item.uom as item_uom,
      null, -- blockedby parent
      null -- blocking parent
      from itemsupplier
      inner join item i_parent on i_parent.name = itemsupplier.item_id
      inner join item on item.lft between i_parent.lft and i_parent.rght
      inner join location on location.lft = location.rght - 1
      where location_id is null and itemsupplier.resource_id = %%s
      order by grandparentoperation_priority, grandparentoperation, parentoperation_priority, parentoperation, sibling_priority
      """ % (
            "operationresource.resource_id = %s"
            if not downstream
            else "exists (select 1 from operationresource where operation_id = operation.name and resource_id = %s)"
        )

        cursor.execute(query, (resource_name,) * 4)

        for i in cursor.fetchall():
            yield from reportclass.processRecord(
                cursor, i, request, depth, downstream, None, 1
            )

    @classmethod
    def getOperationFromName(
        reportclass,
        request,
        cursor,
        operation_name,
        downstream,
        depth,
        previousOperation=None,
        bom_quantity=1,
    ):
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
      item_description,
      (select jsonb_object_agg(distinct operation_dependency.blockedby_id, operation_dependency.quantity)
      filter (where operation_dependency.blockedby_id is not null)
      from operation_dependency where operation_id = operation),
      (select jsonb_object_agg(distinct operation_dependency.operation_id, operation_dependency.quantity)
      filter (where operation_dependency.operation_id is not null)
      from operation_dependency where blockedby_id = operation),
      item_uom,
      (select jsonb_object_agg(distinct operation_dependency.blockedby_id, operation_dependency.quantity)
      filter (where operation_dependency.blockedby_id is not null)
      from operation_dependency where operation_id = parentoperation),
      (select jsonb_object_agg(distinct operation_dependency.operation_id, operation_dependency.quantity)
      filter (where operation_dependency.operation_id is not null)
      from operation_dependency where blockedby_id = parentoperation)
       from
      (
      select operation.name as operation,
           coalesce(operation.type,'fixed_time') operation_type,
           operation.location_id operation_location,
           operation.priority as operation_priority,
           operation.duration as operation_duration,
           operation.duration_per as operation_duration_per,
           case when operation.item_id is not null then jsonb_build_object(operation.item_id||' @ '||operation.location_id, 1) else '{}'::jsonb end
           ||jsonb_object_agg(operationmaterial.item_id||' @ '||coalesce(operationmaterial.location_id,operation.location_id),
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
           item.description as item_description,
           item.uom as item_uom
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
      where coalesce(operation.priority,1) != 0 and
      not exists (select 1 from operation parent_op where parent_op.name = operation.owner_id and parent_op.priority = 0)
      and coalesce(operation.type,'fixed_time') in ('time_per','fixed_time')
      and (operation.name = %s or parentoperation.name = %s or grandparentoperation.name = %s)
      group by operation.name, parentoperation.name, sibling.name, grandparentoperation.name,
      grandparentitem.name, parentitem.name, item.name, grandparentitem.description, parentitem.description, item.description
      ) t
      order by grandparentoperation_priority, grandparentoperation, parentoperation_priority, parentoperation, sibling_priority
      """

        cursor.execute(query, (operation_name,) * 3)

        for i in cursor.fetchall():
            yield from reportclass.processRecord(
                cursor, i, request, depth, downstream, previousOperation, bom_quantity
            )

    @classmethod
    def getOperationFromBuffer(
        reportclass,
        request,
        cursor,
        buffer_name,
        downstream,
        depth,
        previousOperation,
        bom_quantity,
    ):
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
      item_description,
      (select jsonb_object_agg(distinct operation_dependency.blockedby_id, operation_dependency.quantity)
      filter (where operation_dependency.blockedby_id is not null)
      from operation_dependency where operation_id = operation),
      (select jsonb_object_agg(distinct operation_dependency.operation_id, operation_dependency.quantity)
      filter (where operation_dependency.operation_id is not null)
      from operation_dependency where blockedby_id = operation),
      item_uom,
      (select jsonb_object_agg(distinct operation_dependency.blockedby_id, operation_dependency.quantity)
      filter (where operation_dependency.blockedby_id is not null)
      from operation_dependency where operation_id = parentoperation),
      (select jsonb_object_agg(distinct operation_dependency.operation_id, operation_dependency.quantity)
      filter (where operation_dependency.operation_id is not null)
      from operation_dependency where blockedby_id = parentoperation)
      from
      (
      select operation.name as operation,
           coalesce(operation.type,'fixed_time') operation_type,
           operation.location_id operation_location,
           operation.priority as operation_priority,
           operation.duration as operation_duration,
           operation.duration_per as operation_duration_per,
           case when operation.item_id is not null then jsonb_build_object(operation.item_id||' @ '||operation.location_id, 1) else '{}'::jsonb end
           ||jsonb_object_agg(operationmaterial.item_id||' @ '||coalesce(operationmaterial.location_id,operation.location_id),
                              coalesce(operationmaterial.quantity, operationmaterial.quantity_fixed, 0)) filter (where operationmaterial.id is not null and operationmaterial.quantity < 0) as operation_om,
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
           ||coalesce(jsonb_object_agg(siblingoperationmaterial.item_id||' @ '||coalesce(siblingoperationmaterial.location_id,sibling.location_id),
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
           item.description as item_description,
           item.uom as item_uom
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
      where coalesce(operation.priority,1) != 0 and
      not exists (select 1 from operation parent_op where parent_op.name = operation.owner_id and parent_op.priority = 0)
      and coalesce(operation.type,'fixed_time') in ('time_per','fixed_time')
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
      itemdistribution.priority,
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
      item.description,
      null, -- blockedby
      null, --blocking
      item.uom as item_uom,
      null, -- blockedby parent
      null -- blocking parent
      from itemdistribution
      inner join item parent on parent.name = itemdistribution.item_id
      inner join item on item.name = %%s and item.lft between parent.lft and parent.rght
      where itemdistribution.%s = %%s
      """ % (
            (
                """
                and (operation.item_id = %s or
                (exists (select 1 from operationmaterial op1 where op1.operation_id = operation.name and op1.item_id = %s and op1.quantity > 0))
                or parentoperation.item_id = %s
                or grandparentoperation.item_id = %s)
                """,
                "location_id",
            )
            if not downstream
            else (
                """
                and (exists (select 1 from operationmaterial om where om.operation_id = operation.name
                and om.item_id = %s and om.quantity < 0)
                or exists(select 1 from operation_dependency
                   where (operation.name = operation_dependency.operation_id
                     or operation.name = operation_dependency.blockedby_id)
                     and operation.item_id = %s
                     and operation.location_id = %s)
                )
                """,
                "origin_id",
            )
        )

        if not downstream:
            query += """
        union all
      -- PURCHASING OPERATIONS
      select 'Purchase '||item.name||' @ '|| location.name||' from '||itemsupplier.supplier_id,
      location.name as location_id,
      'purchase' as type,
      itemsupplier.priority,
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
      item.description,
      null, -- blockedby
      null, --blocking
      item.uom as item_uom,
      null, -- blockedby parent
      null -- blocking parent
      from itemsupplier
      inner join item i_parent on i_parent.name = itemsupplier.item_id
      inner join item on item.name = %s and item.lft between i_parent.lft and i_parent.rght
      inner join location on location.name = %s and location.name = itemsupplier.location_id
      union all
      select 'Purchase '||item.name||' @ '|| location.name||' from '||itemsupplier.supplier_id,
      location.name as location_id,
      'purchase' as type,
      itemsupplier.priority,
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
      item.description,
      null, -- blockedby
      null, --blocking
      item.uom as item_uom,
      null, -- blockedby parent
      null -- blocking parent
      from itemsupplier
      inner join item i_parent on i_parent.name = itemsupplier.item_id
      inner join item on item.name = %s and item.lft between i_parent.lft and i_parent.rght
      inner join location on location.name = %s and location.lft = location.rght - 1
      where location_id is null
      """

        query += " order by grandparentoperation_priority, grandparentoperation, parentoperation_priority, parentoperation, sibling_priority"

        if downstream:
            cursor.execute(query, (location, item, item, location, item, location))
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
            yield from reportclass.processRecord(
                cursor, i, request, depth, downstream, previousOperation, bom_quantity
            )

    @classmethod
    def processRecord(
        reportclass,
        cursor,
        i,
        request,
        depth,
        downstream,
        previousOperation,
        bom_quantity,
    ):
        # check if routing dependencies has been done
        if not reportclass.routing_dependencies_done:
            reportclass.routing_dependencies_done = True
            reportclass.routing_operation_position = {}
            cursor.execute(
                """
            with q as (
                with recursive cte as
                (
                select 1 as y, operation.owner_id, operation.name, null::text as blockedby_id
                from operation
                where operation.owner_id is not null
                and not exists (select 1 from operation_dependency
                                inner join operation bb on bb.name = operation_dependency.blockedby_id
                                and bb.owner_id = operation.owner_id
                                where operation_dependency.operation_id = operation.name)
                and exists (select 1 from operation_dependency
                           inner join operation op1 on op1.name = operation_dependency.operation_id
                           inner join operation op2 on op2.name = operation_dependency.blockedby_id
                           where op1.owner_id = operation.owner_id
                           and op2.owner_id = operation.owner_id)
                union all
                select cte.y+1, operation.owner_id, operation.name, operation_dependency.blockedby_id
                from operation_dependency
                inner join cte on cte.name = operation_dependency.blockedby_id
                inner join operation on operation.name = operation_dependency.operation_id and operation.owner_id = cte.owner_id
                )
                select distinct cte.owner_id, y, name from cte
                )
            select owner_id, name, row_number() over(partition by owner_id, y order by name) as x, y from q
            order by 1,2,3
            """
            )
            for rec in cursor:
                reportclass.routing_operation_position[rec[1]] = (rec[2], rec[3])
                # for the routing, x,y refers to the number of rows and columns
                if rec[0] not in reportclass.routing_operation_position:
                    reportclass.routing_operation_position[rec[0]] = (rec[2], rec[3])
                else:
                    reportclass.routing_operation_position[rec[0]] = (
                        max(rec[2], reportclass.routing_operation_position[rec[0]][0]),
                        max(rec[3], reportclass.routing_operation_position[rec[0]][1]),
                    )

        # First can we go further ?
        if len(reportclass.node_count) > 400:
            return
        opdetail = json.loads(i[14])

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
                "uom": None,
                "location": i[1],
                "resources": None,
                "parentoper": None,
                "suboperation": 0,
                "duration": None,
                "duration_per": None,
                "quantity": 1,
                "buffers": None,
                "parent": reportclass.operation_dict.get(previousOperation, None),
                "leaf": "false",
                "expanded": "true",
                "numsuboperations": reportclass.suboperations_count_dict[i[11]],
                "realdepth": -depth if reportclass.downstream else depth,
                "sizeminimum": opdetail["grandparentoperation_min"],
                "sizemaximum": opdetail["grandparentoperation_max"],
                "sizemultiple": opdetail["grandparentoperation_multiple"],
                "alternate": "false",
                "blockedby": None,
                "blocking": None,
                "rownb": None,
                "colnb": None,
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
                "uom": None,
                "priority": i[10],
                "location": i[1],
                "resources": None,
                "parentoper": i[11],
                "suboperation": -reportclass.parent_count_dict[i[11]] if i[11] else 0,
                "duration": None,
                "duration_per": None,
                "quantity": 1,
                "buffers": None,
                "parent": reportclass.operation_dict.get(
                    i[11], reportclass.operation_dict.get(previousOperation, None)
                ),
                "leaf": "false",
                "expanded": "true",
                "numsuboperations": reportclass.suboperations_count_dict[i[8]],
                "realdepth": -depth if reportclass.downstream else depth,
                "sizeminimum": opdetail["parentoperation_min"],
                "sizemaximum": opdetail["parentoperation_max"],
                "sizemultiple": opdetail["parentoperation_multiple"],
                "alternate": "false",
                "blockedby": tuple(json.loads(i[24]).items()) if i[24] else None,
                "blocking": tuple(json.loads(i[25]).items()) if i[25] else None,
                "rownb": (
                    reportclass.routing_operation_position[i[8]][0]
                    if i[8] in reportclass.routing_operation_position
                    else None
                ),
                "colnb": (
                    reportclass.routing_operation_position[i[8]][1]
                    if i[8] in reportclass.routing_operation_position
                    else None
                ),
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
                "uom": i[23],
                "location": i[1],
                "resources": tuple(json.loads(i[5]).items()) if i[5] else None,
                "parentoper": i[8],
                "suboperation": (
                    0
                    if not i[8]
                    else (
                        reportclass.parent_count_dict[i[8]]
                        if i[9] == "routing"
                        else -reportclass.parent_count_dict[i[8]]
                    )
                ),
                "duration": i[6],
                "duration_per": i[7],
                "quantity": abs(bom_quantity),
                "buffers": (
                    tuple(json.loads(i[4]).items())
                    if i[4]
                    else tuple([("%s @ %s" % (i[17], i[1]), 1)]) if i[17] else None
                ),
                "parent": reportclass.operation_dict.get(
                    i[8], reportclass.operation_dict.get(previousOperation, None)
                ),
                "leaf": "false",
                "expanded": "true",
                "numsuboperations": 0,
                "realdepth": -depth if reportclass.downstream else depth,
                "sizeminimum": opdetail["operation_min"],
                "sizemaximum": opdetail["operation_max"],
                "sizemultiple": opdetail["operation_multiple"],
                "alternate": "false",
                "alternate_priority": (i[13] or i[10] or i[3] or 999),
                "alternate_operation": (i[11] or i[8] or i[0]),
                "blockedby": tuple(json.loads(i[21]).items()) if i[21] else None,
                "blocking": tuple(json.loads(i[22]).items()) if i[22] else None,
                "rownb": (
                    reportclass.routing_operation_position[i[0]][0]
                    if i[0] in reportclass.routing_operation_position
                    else None
                ),
                "colnb": (
                    reportclass.routing_operation_position[i[0]][1]
                    if i[0] in reportclass.routing_operation_position
                    else None
                ),
            }
            reportclass.node_count.add(i[0])
            yield operation

        if i[5]:
            for resource, quantity in tuple(json.loads(i[5]).items()):
                reportclass.node_count.add(resource)

        if i[4]:
            for buffer, quantity in tuple(json.loads(i[4]).items()):
                # I might already have visisted that buffer
                if buffer in reportclass.node_count:
                    continue
                reportclass.node_count.add(buffer)
                if float(quantity) < 0 and not downstream:
                    yield from reportclass.getOperationFromBuffer(
                        request,
                        cursor,
                        buffer,
                        downstream,
                        depth + 1,
                        i[0],
                        float(quantity),
                    )
                elif float(quantity) > 0 and downstream:
                    yield from reportclass.getOperationFromBuffer(
                        request,
                        cursor,
                        buffer,
                        downstream,
                        depth + 1,
                        i[0],
                        float(quantity),
                    )

        if i[21] and not downstream:
            for blockedby in tuple(json.loads(i[21]).items()):
                if not blockedby[0] in reportclass.operation_dict:
                    yield from reportclass.getOperationFromName(
                        request,
                        cursor,
                        blockedby[0],
                        downstream,
                        depth + 1,
                        i[0],
                        blockedby[1],
                    )

        if i[22] and downstream:
            for blocking in tuple(json.loads(i[22]).items()):
                if not blocking[0] in reportclass.operation_dict:
                    yield from reportclass.getOperationFromName(
                        request,
                        cursor,
                        blocking[0],
                        downstream,
                        depth + 1,
                        i[0],
                        blocking[1],
                    )

        if i[24] and not downstream:
            for blockedby in tuple(json.loads(i[24]).items()):
                if not blockedby[0] in reportclass.operation_dict:
                    yield from reportclass.getOperationFromName(
                        request,
                        cursor,
                        blockedby[0],
                        downstream,
                        depth + 1,
                        i[0],
                        blockedby[1],
                    )

        if i[25] and downstream:
            for blocking in tuple(json.loads(i[25]).items()):
                if not blocking[0] in reportclass.operation_dict:
                    yield from reportclass.getOperationFromName(
                        request,
                        cursor,
                        blocking[0],
                        downstream,
                        depth + 1,
                        i[0],
                        blocking[1],
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

        # A flag to figure out if the routing dependencies have been scanned
        reportclass.routing_dependencies_done = False

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
        with connections[request.database].cursor() as cursor:

            if str(reportclass.objecttype._meta) == "input.buffer":
                buffer_name = basequery.query.get_compiler(basequery.db).as_sql(
                    with_col_aliases=False
                )[1][0]
                if " @ " not in buffer_name:
                    b = Buffer.objects.get(id=buffer_name)
                    buffer_name = "%s @ %s" % (b.item.name, b.location.name)

                for i in reportclass.getOperationFromBuffer(
                    request, cursor, buffer_name, reportclass.downstream, 0, None, 1
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
                        cursor,
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
                        request, cursor, operation_name, reportclass.downstream, depth=0
                    ):
                        results.append(i)
            elif str(reportclass.objecttype._meta) == "input.resource":
                resource_name = basequery.query.get_compiler(basequery.db).as_sql(
                    with_col_aliases=False
                )[1][0]

                for i in reportclass.getOperationFromResource(
                    request, cursor, resource_name, reportclass.downstream, depth=0
                ):
                    results.append(i)
            elif str(reportclass.objecttype._meta) == "input.operation":
                operation_name = basequery.query.get_compiler(basequery.db).as_sql(
                    with_col_aliases=False
                )[1][0]

                for i in reportclass.getOperationFromName(
                    request, cursor, operation_name, reportclass.downstream, depth=0
                ):
                    results.append(i)
            elif str(reportclass.objecttype._meta) == "input.item":
                item_name = basequery.query.get_compiler(basequery.db).as_sql(
                    with_col_aliases=False
                )[1][0]

                for i in reportclass.getOperationFromItem(
                    request, cursor, item_name, reportclass.downstream, depth=0
                ):
                    results.append(i)
            elif (
                str(reportclass.objecttype._meta) == "forecast.forecast"
                and "freppledb.forecast" in settings.INSTALLED_APPS
            ):
                from freppledb.forecast.models import Forecast

                forecast_name = basequery.query.get_compiler(basequery.db).as_sql(
                    with_col_aliases=False
                )[1][0]
                d = Forecast.objects.get(name=forecast_name)
                buffer_name = "%s @ %s" % (d.item.name, d.location.name)

                yield from reportclass.getOperationFromBuffer(
                    request,
                    cursor,
                    buffer_name,
                    reportclass.downstream,
                    depth=0,
                    previousOperation=None,
                    bom_quantity=1,
                )

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

        yield from results


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


class OperationPlanDetail(View):
    def getData(self, request):
        current_date = getCurrentDate(request.database, lastplan=True)
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
                .select_related("operation", "item", "supplier")
            ]
            opplanmats = [
                x
                for x in OperationPlanMaterial.objects.all()
                .using(request.database)
                .filter(Q(operationplan_id__in=ids) | Q(operationplan__owner__in=ids))
                .annotate(
                    consume_or_produce=RawSQL(
                        "sign(operationplanmaterial.quantity)", ()
                    )
                )
                .order_by("consume_or_produce", "item_id")
                .values(
                    "operationplan_id",
                    "item_id",
                    "location_id",
                    "onhand",
                    "flowdate",
                    "quantity",
                    "item__description",
                    "operationplan__owner__reference",
                )
            ]
            opplanrscs = [
                x
                for x in OperationPlanResource.objects.all()
                .using(request.database)
                .filter(Q(operationplan_id__in=ids) | Q(operationplan__owner__in=ids))
                .order_by(F("resource__owner").desc(nulls_last=True), "resource_id")
                .values(
                    "operationplan_id",
                    "quantity",
                    "resource_id",
                    "operationplan__startdate",
                    "operationplan__owner__reference",
                )
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
                    "start": (
                        opplan.startdate.strftime("%Y-%m-%dT%H:%M:%S")
                        if opplan.startdate
                        else None
                    ),
                    "end": (
                        opplan.enddate.strftime("%Y-%m-%dT%H:%M:%S")
                        if opplan.enddate
                        else None
                    ),
                    "setupend": (
                        opplan.plan["setupend"].replace(" ", "T")
                        if opplan.plan and "setupend" in opplan.plan
                        else None
                    ),
                    "quantity": float(opplan.quantity),
                    "quantity_completed": float(opplan.quantity_completed or 0),
                    "criticality": (
                        float(opplan.criticality) if opplan.criticality else ""
                    ),
                    "delay": opplan.delay.total_seconds() if opplan.delay else "",
                    "status": opplan.status,
                    "type": opplan.type,
                    "name": opplan.name,
                    "destination": opplan.destination_id,
                    "location": opplan.location_id,
                    "origin": opplan.origin_id,
                    "supplier": opplan.supplier_id,
                    "supplier__description": (
                        opplan.supplier.description if opplan.supplier else None
                    ),
                    "item": opplan.item_id,
                    "item__description": (
                        opplan.item.description if opplan.item else None
                    ),
                    "color": float(opplan.color) if opplan.color else "",
                    "owner": opplan.owner.reference if opplan.owner else None,
                    "batch": opplan.batch,
                }
                if opplan.plan and "pegging" in opplan.plan:
                    res["pegging_demand"] = []
                    for d, q in opplan.plan["pegging"].items():
                        try:
                            obj = (
                                Demand.objects.all()
                                .using(request.database)
                                .only("name", "item", "item__description", "due")
                                .get(name=d)
                            )
                            res["pegging_demand"].append(
                                {
                                    "demand": {
                                        "name": obj.name,
                                        "item": {
                                            "name": obj.item.name,
                                            "description": obj.item.description,
                                        },
                                        "due": obj.due.strftime(
                                            settings.DATE_INPUT_FORMATS[0]
                                        ),
                                    },
                                    "quantity": q,
                                }
                            )
                        except Demand.DoesNotExist:
                            if "freppledb.forecast" in settings.INSTALLED_APPS:
                                try:
                                    d, due = d.rsplit(" - ", 1)
                                    cursor.execute(
                                        """
                                        select
                                          forecast.item_id, item.description,
                                          case
                                            when lower(d.value) = 'start' then startdate
                                            when lower(d.value) = 'end' then enddate - interval '1 second'
                                            else date_trunc('day', startdate + (enddate - startdate)/2)
                                          end as due
                                        from forecast
                                        inner join item
                                          on item.name = forecast.item_id
                                        left outer join common_parameter d on d.name = 'forecast.DueWithinBucket'
                                        inner join common_parameter b on b.name = 'forecast.calendar'
                                        inner join common_bucketdetail on common_bucketdetail.bucket_id = b.value
                                          and to_date(%s, 'YYYY-MM-DD') >= common_bucketdetail.startdate
                                          and to_date(%s, 'YYYY-MM-DD') < common_bucketdetail.enddate
                                        where forecast.name = %s
                                        """,
                                        (due, due, d),
                                    )
                                    rec = cursor.fetchone()
                                    res["pegging_demand"].append(
                                        {
                                            "demand": {
                                                "name": d,
                                                "item": {
                                                    "name": rec[0],
                                                    "description": rec[1],
                                                },
                                                "due": rec[2].strftime(
                                                    settings.DATE_INPUT_FORMATS[0]
                                                ),
                                                "forecast": True,
                                            },
                                            "quantity": q,
                                        }
                                    )
                                except Exception:
                                    # Looks like this demand was deleted since the plan was generated
                                    continue
                            else:
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
                if hasattr(opplan, "remark"):
                    res["remark"] = getattr(opplan, "remark", None)
                if "info" in getattr(opplan, "plan", {}):
                    res["info"] = opplan.plan["info"]

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
                            inner join operation
                               on a.operation_id = operation.name
                            where (operation.name = %s or operation.owner_id = %s)
                            and a.id != b.id
                            """,
                            (
                                opplan.operation.name,
                                opplan.operation.name,
                            ),
                        )
                        for i in cursor.fetchall():
                            if i[0] not in alts:
                                alts[i[0]] = set()
                            alts[i[0]].add(i[1])
                    firstmat = True
                    for m in opplanmats:
                        if opplan.reference not in (
                            m["operationplan_id"],
                            m["operationplan__owner__reference"],
                        ):
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
                                "description": m["item__description"],
                                "location": m["location_id"],
                            },
                            "reference": m["operationplan_id"],
                        }
                        # List matching alternates
                        if m["item_id"] in alts:
                            flowplan["alternates"] = list(alts[m["item_id"]])
                            flowplan["alternates"].sort()
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
                            inner join operation
                               on operationresource.operation_id = operation.name
                            where (operationresource.skill_id is null or exists (
                               select 1 from resourceskill
                               where resourceskill.resource_id = alt_res_children.name
                               and resourceskill.skill_id = alt_opres.skill_id
                               ))
                            and (operation.owner_id = %s or operation.name = %s)
                            """,
                            (opplan.operation.name, opplan.operation.name),
                        )
                        for i in cursor.fetchall():
                            if i[0] not in alts:
                                alts[i[0]] = set()
                            alts[i[0]].add(i[1])
                    firstres = True
                    for m in opplanrscs:
                        if opplan.reference not in (
                            m["operationplan_id"],
                            m["operationplan__owner__reference"],
                        ):
                            continue
                        if firstres:
                            firstres = False
                            res["loadplans"] = []
                        ldplan = {
                            "date": m["operationplan__startdate"].strftime(
                                "%Y-%m-%dT%H:%M:%S"
                            ),
                            "quantity": float(m["quantity"]),
                            "resource": {"name": m["resource_id"]},
                            "reference": m["operationplan_id"],
                        }
                        # List matching alternates
                        for a in alts.values():
                            if m["resource_id"] in a:
                                t = [i for i in a if i != m["resource_id"]]
                                if t:
                                    t.sort()
                                    ldplan["alternates"] = [{"name": i} for i in t]
                                break
                        res["loadplans"].append(ldplan)

                # Retrieve network status
                if opplan.item_id:
                    cursor.execute(
                        """
                        with items as (
                           select name from item where name = %%s
                           )
                        select
                          items.name,
                          false,
                          location.name,
                          coalesce(onhand.qty,0) + coalesce(completed.quantity,0),
                          orders_plus.PO,
                          coalesce(orders_plus.DO, 0) - coalesce(orders_minus.DO, 0),
                          orders_plus.MO,
                          sales.BO,
                          sales.SO,
                          to_char(%%s,'%s HH24:MI:SS') as current_date
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
                          where status in ('approved', 'confirmed') and operationplan.owner_id is null
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
                          sum(case when due < %%s then quantity end) as BO,
                          sum(case when due >= %%s then quantity end) as SO
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
                          or (items.name = %%s and location.name = %%s)
                        order by items.name, location.name
                        """
                        % (settings.DATE_FORMAT_JS,),
                        (
                            opplan.item_id,
                            current_date,
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
                                a[9],
                            ]
                        )

                # Downstream operationplans
                cursor.execute(
                    """
                    with recursive cte as
                (
                select 1 as level,
                (to_char(operationplan.startdate,'YYYYMMDDHH24MISS')||'/'||coalesce(operationplan.item_id,'')||'/'||operationplan.reference)::varchar as path,
                operationplan.reference::text,
                0::numeric as pegged_x,
                operationplan.quantity::numeric as pegged_y,
                operationplan.owner_id
                from operationplan
                where reference = %%s
                union all
                select case when downstream_opplan.owner_id = cte.owner_id then cte.level else cte.level+1 end,
                cte.path||'/'||to_char(downstream_opplan.startdate,'YYYYMMDDHH24MISS')||'/'||coalesce(downstream_opplan.item_id,'')||'/'||downstream_opplan.reference,
                t1.downstream_reference::text,
                greatest(t1.x, t1.x + (t1.y-t1.x)/(t2.y-t2.x)*(cte.pegged_x-t2.x)) as pegged_x,
                least(t1.y, t1.x + (t1.y-t1.x)/(t2.y-t2.x)*(cte.pegged_x-t2.x) + (cte.pegged_y-cte.pegged_x)*(t1.y-t1.x)/(t2.y-t2.x)) as pegged_y,
                downstream_opplan.owner_id
                from operationplan
                inner join cte on cte.reference = operationplan.reference
                inner join lateral
                (select t->>0 downstream_reference,
                (t->>1)::numeric + (t->>2)::numeric as y,
                (t->>2)::numeric as x from jsonb_array_elements(operationplan.plan->'downstream_opplans') t) t1 on true
                inner join operationplan downstream_opplan on downstream_opplan.reference = t1.downstream_reference
                inner join lateral
                (select t->>0 upstream_reference,
                (t->>1)::numeric+(t->>2)::numeric as y,
                (t->>2)::numeric as x from jsonb_array_elements(downstream_opplan.plan->'upstream_opplans') t) t2
                    on t2.upstream_reference = operationplan.reference and numrange(t2.x,t2.y) && numrange(cte.pegged_x,cte.pegged_y)
                )
                select cte.level,
                cte.reference,
                operationplan.type,
                case when operationplan.type = 'PO' then 'Purchase '||operationplan.item_id||' @ '||operationplan.location_id||' from '||operationplan.supplier_id
                when operationplan.type = 'DO' then 'Ship '||operationplan.item_id||' from '||operationplan.origin_id||' to '||operationplan.destination_id
                %s
                else operationplan.operation_id end as operation_name,
                operationplan.status,
                operationplan.item_id,
                coalesce(operationplan.location_id, operationplan.destination_id),
                operationplan.startdate,
                operationplan.enddate,
                (pegged_y-pegged_x) as quantity,
                operationplan.quantity,
                path,
                operationplan.owner_id
                from cte
                inner join operationplan on operationplan.reference = cte.reference
                where cte.level < 25
                order by cte.path, cte.level desc
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
                                a[3] or "",  # operation
                                a[4],  # status
                                a[5],  # item
                                a[6],  # location
                                (
                                    a[7].strftime(settings.DATETIME_INPUT_FORMATS[0])
                                    if a[7]
                                    else ""
                                ),  # startdate
                                (
                                    a[8].strftime(settings.DATETIME_INPUT_FORMATS[0])
                                    if a[8]
                                    else ""
                                ),  # enddate
                                float(a[9] or 0),  # quantity,
                                float(a[10] or 0),  # opplan quantity,
                                0 if a[0] == 1 else 2,
                                a[12],  # owner_id
                            ]
                        )

                # Upstream operationplans
                cursor.execute(
                    """
                    with recursive cte as
                (
                select 1 as level,
                (to_char(operationplan.startdate,'YYYYMMDDHH24MISS')||'/'||coalesce(operationplan.item_id,'')||'/'||operationplan.reference)::varchar as path,
                operationplan.reference::text,
                0::numeric as pegged_x,
                operationplan.quantity::numeric as pegged_y,
                operationplan.owner_id
                from operationplan
                where reference = %s
                union all
                select case when upstream_opplan.owner_id = cte.owner_id then cte.level else cte.level+1 end,
                cte.path||'/'||to_char(upstream_opplan.startdate,'YYYYMMDDHH24MISS')||'/'||coalesce(upstream_opplan.item_id,'')||'/'||upstream_opplan.reference,
                t1.upstream_reference::text,
                greatest(t1.x, t1.x + (t1.y-t1.x)/(t2.y-t2.x)*(cte.pegged_x-t2.x)) as pegged_x,
                least(t1.y, t1.x + (t1.y-t1.x)/(t2.y-t2.x)*(cte.pegged_x-t2.x) + (cte.pegged_y-cte.pegged_x)*(t1.y-t1.x)/(t2.y-t2.x)) as pegged_y,
                upstream_opplan.owner_id
                from operationplan
                inner join cte on cte.reference = operationplan.reference
                inner join lateral
                (select t->>0 upstream_reference,
                (t->>1)::numeric + (t->>2)::numeric as y,
                (t->>2)::numeric as x from jsonb_array_elements(operationplan.plan->'upstream_opplans') t) t1 on true
                inner join operationplan upstream_opplan on upstream_opplan.reference = t1.upstream_reference
                inner join lateral
                (select t->>0 downstream_reference,
                (t->>1)::numeric+(t->>2)::numeric as y,
                (t->>2)::numeric as x from jsonb_array_elements(upstream_opplan.plan->'downstream_opplans') t) t2
                    on t2.downstream_reference = operationplan.reference and numrange(t2.x,t2.y) && numrange(cte.pegged_x,cte.pegged_y)
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
                operationplan.startdate,
                operationplan.enddate,
                (pegged_y-pegged_x) as quantity,
                operationplan.quantity,
                path,
                operationplan.owner_id
                from cte
                inner join operationplan on operationplan.reference = cte.reference
                where cte.level < 25
                order by cte.path, cte.level desc
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
                                (
                                    a[7].strftime(settings.DATETIME_INPUT_FORMATS[0])
                                    if a[7]
                                    else ""
                                ),  # startdate
                                (
                                    a[8].strftime(settings.DATETIME_INPUT_FORMATS[0])
                                    if a[8]
                                    else ""
                                ),  # enddate
                                float(a[9] or 0),  # quantity,
                                float(a[10] or 0),  # opplan quantity
                                0 if a[0] == 1 else 2,
                                a[12],  # owner_id
                            ]
                        )

                # INVENTORY REPORT
                current, start, end = getHorizon(request)
                cursor.execute(
                    """

                with arguments as (
                select %s::timestamp report_startdate,
                %s::timestamp report_enddate,
                %s::timestamp report_currentdate,
                %s report_bucket,
                %s item_id,
                %s location_id,
                %s batch,
                %s buffer
                )

                select

                d.bucket,
                d.startdate,
                d.enddate,
                d.history,

                case
                when d.history then json_build_object(
                'onhand', min(ax_buffer.onhand)
                )
                else coalesce(
                (
                select json_build_object(
                'onhand', onhand,
                'flowdate', to_char(flowdate,'YYYY-MM-DD HH24:MI:SS'),
                'periodofcover', periodofcover
                )
                from operationplanmaterial
                inner join operationplan
                on operationplanmaterial.operationplan_id = operationplan.reference
                where operationplanmaterial.item_id = arguments.item_id
                and operationplanmaterial.location_id = arguments.location_id
                and (item.type is distinct from 'make to order' or operationplan.batch is not distinct from arguments.batch)
                and flowdate < greatest(d.startdate,arguments.report_startdate)
                order by flowdate desc, id desc limit 1
                ),
                (
                select json_build_object(
                'onhand', 0.0,
                'flowdate', to_char(flowdate,'YYYY-MM-DD HH24:MI:SS'),
                'periodofcover', 1
                )
                from operationplanmaterial
                inner join operationplan
                on operationplanmaterial.operationplan_id = operationplan.reference
                where operationplanmaterial.item_id = arguments.item_id
                and operationplanmaterial.location_id = arguments.location_id
                and (item.type is distinct from 'make to order' or operationplan.batch is not distinct from arguments.batch)
                and flowdate >= greatest(d.startdate,arguments.report_startdate)
                and operationplanmaterial.quantity < 0
                order by flowdate asc, id asc limit 1
                ),
                (
                select json_build_object(
                'onhand', 0.0,
                'flowdate', to_char(flowdate,'YYYY-MM-DD HH24:MI:SS'),
                'periodofcover', 1
                )
                from operationplanmaterial
                inner join operationplan
                on operationplanmaterial.operationplan_id = operationplan.reference
                where operationplanmaterial.item_id = arguments.item_id
                and operationplanmaterial.location_id = arguments.location_id
                and (item.type is distinct from 'make to order' or operationplan.batch is not distinct from arguments.batch)
                and flowdate >= greatest(d.startdate,arguments.report_startdate)
                and operationplanmaterial.quantity >= 0
                order by flowdate asc, id asc limit 1
                )
                )
            end as startoh,

            case when d.history then json_build_object()
            else (
             select json_build_object(
               'consumed_confirmed', coalesce(sum(case when operationplan.status in ('approved','confirmed','completed') and (opm.flowdate >= greatest(d.startdate,arguments.report_startdate) and opm.flowdate < d.enddate) and opm.quantity < 0 then -opm.quantity else 0 end), 0),
               'consumed_proposed', coalesce(sum(case when operationplan.status = 'proposed' and (opm.flowdate >= greatest(d.startdate,arguments.report_startdate) and opm.flowdate < d.enddate) and opm.quantity < 0 then -opm.quantity else 0 end), 0),
               'produced_confirmed', coalesce(sum(case when operationplan.status in ('approved','confirmed','completed') and (opm.flowdate >= greatest(d.startdate,arguments.report_startdate) and opm.flowdate < d.enddate) and opm.quantity > 0 then opm.quantity else 0 end), 0),
               'produced_proposed', coalesce(sum(case when operationplan.status = 'proposed' and (opm.flowdate >= greatest(d.startdate,arguments.report_startdate) and opm.flowdate < d.enddate) and opm.quantity > 0 then opm.quantity else 0 end), 0)
               )
             from operationplanmaterial opm
             inner join operationplan
             on operationplan.reference = opm.operationplan_id
               and ((startdate < d.enddate and enddate >= d.enddate)
               or (opm.flowdate >= greatest(d.startdate,arguments.report_startdate) and opm.flowdate < d.enddate)
               or (operationplan.type = 'DLVR' and due < d.enddate and due >= case when arguments.report_currentdate >= d.startdate and arguments.report_currentdate < d.enddate then '1970-01-01'::timestamp else d.startdate end))
             where opm.item_id = arguments.item_id
               and opm.location_id = arguments.location_id
               and (item.type is distinct from 'make to order' or operationplan.batch is not distinct from arguments.batch)
             )
           end as ongoing,


           case when d.history then min(ax_buffer.safetystock)
           else
           (select safetystock from
            (
            select 1 as priority, coalesce(
              (select value from calendarbucket
               where calendar_id = 'SS for ' || arguments.buffer
               and greatest(d.startdate,arguments.report_startdate) >= coalesce(startdate, '1971-01-01'::timestamp)
               and greatest(d.startdate,arguments.report_startdate) < coalesce(enddate, '2030-12-31'::timestamp)
               order by priority limit 1),
              (select defaultvalue from calendar where name = 'SS for ' || arguments.buffer)
              ) as safetystock
            union all
            select 2 as priority, coalesce(
              (select value
               from calendarbucket
               where calendar_id = (
                 select minimum_calendar_id
                 from buffer
                 where item_id = arguments.item_id
                 and location_id = arguments.location_id
                 and (item.type is distinct from 'make to order' or buffer.batch is not distinct from arguments.batch)
                 )
               and greatest(d.startdate,arguments.report_startdate) >= coalesce(startdate, '1971-01-01'::timestamp)
               and greatest(d.startdate,arguments.report_startdate) < coalesce(enddate, '2030-12-31'::timestamp)
               order by priority limit 1),
              (select defaultvalue
               from calendar
               where name = (
                 select minimum_calendar_id
                 from buffer
                 where item_id = arguments.item_id
                 and location_id = arguments.location_id
                 and (item.type is distinct from 'make to order' or buffer.batch is not distinct from arguments.batch)
                 )
              )
            ) as safetystock
            union all
            select 3 as priority, minimum as safetystock
            from buffer
            where item_id = arguments.item_id
            and location_id = arguments.location_id
            and (item.type is distinct from 'make to order' or buffer.batch is not distinct from arguments.batch)
            ) t
            where t.safetystock is not null
            order by priority
            limit 1)
            end as safetystock

                from (select distinct operationplanmaterial.item_id,
                operationplanmaterial.location_id,
                operationplan.batch
                        from operationplanmaterial
                        cross join arguments
                        inner join operationplan on operationplan.reference = operationplanmaterial.operationplan_id
                        inner join item on item.name = operationplanmaterial.item_id
                      where operationplanmaterial.item_id = arguments.item_id
                      and operationplanmaterial.location_id = arguments.location_id
                      and (item.type is distinct from 'make to order'
                           or coalesce(operationplan.batch,'') is not distinct from arguments.batch)
                    ) operationplanmaterial
                cross join arguments
                inner join item on item.name = operationplanmaterial.item_id

                -- Multiply with buckets
                cross join (
                    select name as bucket, startdate, enddate,
                    min(snapshot_date) as snapshot_date,
                    enddate < arguments.report_currentdate as history
                    from common_bucketdetail
                    cross join arguments
                    left outer join ax_manager
                    on snapshot_date >= common_bucketdetail.startdate
                    and snapshot_date < common_bucketdetail.enddate
                    where common_bucketdetail.bucket_id = arguments.report_bucket
                    and common_bucketdetail.enddate > arguments.report_startdate
                    and common_bucketdetail.startdate < arguments.report_enddate
                    group by common_bucketdetail.name, common_bucketdetail.startdate,
                            common_bucketdetail.enddate, arguments.report_currentdate
                    ) d

                -- join with the archive data
                left outer join ax_buffer
                    on ax_buffer.snapshot_date_id = d.snapshot_date
                    and ax_buffer.item =  operationplanmaterial.item_id
                    and ax_buffer.location =  operationplanmaterial.location_id
                    and (ax_buffer.batch is not distinct from arguments.batch)

                group by d.history,
                arguments.item_id,
                arguments.location_id,
                arguments.buffer,
                arguments.batch,
                arguments.report_startdate,
                arguments.report_currentdate,
                item.type,
                d.startdate,
                d.bucket,
                d.enddate

                order by d.startdate
                """,
                    (
                        start,
                        end,
                        current,
                        request.user.horizonbuckets,
                        opplan.item.name,
                        (
                            opplan.destination.name
                            if opplan.type == "DO"
                            else opplan.location.name
                        ),
                        opplan.batch or "",
                        "%s @ %s"
                        % (
                            opplan.item.name,
                            (
                                opplan.destination.name
                                if opplan.type == "DO"
                                else opplan.location.name
                            ),
                        ),
                    ),
                )

                if cursor.rowcount > 0:
                    res["inventoryreport"] = []
                    for row in cursor.fetchall():

                        # bucket
                        # bucket start
                        # bucket end
                        # history
                        # start oh
                        # safety stock
                        # total consumed
                        # consumed proposed
                        # consumed confirmed
                        # total produced
                        # produced proposed
                        # produced confirmed
                        # endoh

                        res["inventoryreport"].append(
                            [
                                row[0],  # bucket
                                row[1].strftime(
                                    settings.DATETIME_INPUT_FORMATS[0]
                                ),  # d.startdate
                                row[2].strftime(
                                    settings.DATETIME_INPUT_FORMATS[0]
                                ),  # d.enddate,
                                row[3],  # d.history
                                row[4]["onhand"] or 0,  # startoh
                                float(row[6] or 0),  # safety stock
                                (0 if row[3] else row[5]["consumed_proposed"])
                                + (
                                    0 if row[3] else row[5]["consumed_confirmed"]
                                ),  # total consumed
                                0 if row[3] else row[5]["consumed_proposed"],
                                0 if row[3] else row[5]["consumed_confirmed"],
                                (0 if row[3] else row[5]["produced_proposed"])
                                + (
                                    0 if row[3] else row[5]["produced_confirmed"]
                                ),  # total produced
                                0 if row[3] else row[5]["produced_proposed"],
                                0 if row[3] else row[5]["produced_confirmed"],
                                (row[4]["onhand"] or 0)
                                + (0 if row[3] else row[5]["produced_proposed"])
                                + (0 if row[3] else row[5]["produced_confirmed"])
                                - (0 if row[3] else row[5]["consumed_proposed"])
                                - (
                                    0 if row[3] else row[5]["consumed_confirmed"]
                                ),  # endoh
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
        if request.headers.get("x-requested-with") != "XMLHttpRequest":
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
        if request.headers.get("x-requested-with") != "XMLHttpRequest":
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
                if "quantity_completed" in opplan_data:
                    # Update quantity
                    opplan.quantity_completed = opplan_data["quantity_completed"]
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
                            "quantity_completed",
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
