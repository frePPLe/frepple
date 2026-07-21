#
# Copyright (C) 2023 by frePPLe bv
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
from dateutil.parser import parse


from rest_framework import serializers
from django_bulk_drf import BulkModelSerializer

from freppledb.common.api.filters import FilterSet
from freppledb.common.api.serializers import (
    getAttributeAPIFilterDefinition,
    getAttributeAPIFields,
    getAttributeAPIReadOnlyFields,
)
from freppledb.common.api.views import (
    frePPleBulkModelViewSet,
    frePPleRetrieveUpdateDestroyAPIView,
)
from freppledb.common.models import Parameter
from freppledb.forecast.models import Forecast, Measure, ForecastPlan


class ForecastFilter(FilterSet):
    class Meta:
        model = Forecast
        fields = dict(
            {
                "name": ["exact", "in", "contains"],
                "description": ["exact", "in", "contains"],
                "category": ["exact", "in", "contains"],
                "subcategory": ["exact", "in", "contains"],
                "batch": ["exact", "in", "contains"],
                "item": ["exact", "in"],
                "customer": ["exact", "in"],
                "location": ["exact", "in"],
                "operation": ["exact", "in"],
                "priority": ["exact", "in", "gt", "gte", "lt", "lte"],
                "minshipment": ["exact", "in", "gt", "gte", "lt", "lte"],
                "maxlateness": ["exact", "in", "gt", "gte", "lt", "lte"],
                "discrete": ["exact"],
                "out_smape": ["exact", "in", "gt", "gte", "lt", "lte"],
                "out_method": ["exact", "in"],
                "out_deviation": ["exact", "in", "gt", "gte", "lt", "lte"],
                "source": ["exact", "in"],
                "lastmodified": ["exact", "in", "gt", "gte", "lt", "lte"],
            },
            **getAttributeAPIFilterDefinition(Forecast),
        )


class ForecastSerializer(BulkModelSerializer):
    class Meta:
        model = Forecast
        fields = (
            "name",
            "description",
            "category",
            "subcategory",
            "batch",
            "customer",
            "item",
            "location",
            "operation",
            "method",
            "priority",
            "minshipment",
            "maxlateness",
            "discrete",
            "out_smape",
            "out_method",
            "out_deviation",
            "source",
            "lastmodified",
        ) + getAttributeAPIFields(Forecast)
        read_only_fields = ("lastmodified",) + getAttributeAPIReadOnlyFields(Forecast)


class ForecastAPI(frePPleBulkModelViewSet):
    def get_queryset(self):
        return Forecast.objects.using(self.request.database).all()

    serializer_class = ForecastSerializer
    filterset_class = ForecastFilter

    unique_fields = ["name"]


class ForecastdetailAPI(frePPleRetrieveUpdateDestroyAPIView):
    def get_queryset(self):
        return Forecast.objects.using(self.request.database).all()

    serializer_class = ForecastSerializer


class ForecastPlanSerializer(BulkModelSerializer):
    class Meta:
        model = ForecastPlan
        fields = ("item", "location", "customer", "startdate", "enddate", "value")
        read_only_fields = None


class ForecastPlanFilter(FilterSet):
    pass


class ForecastPlanAPI(frePPleBulkModelViewSet):
    def get_queryset(self):
        try:
            parameter_currentdate = parse(
                Parameter.objects.get(name="currentdate").value
            )
        except Exception:
            parameter_currentdate = datetime.now()
        return ForecastPlan.objects.using(self.request.database).raw("""
            select forecastplan.item_id||' @ '||
            forecastplan.location_id||' @ '||
            forecastplan.customer_id||' @ '||
            forecastplan.startdate as id,
            forecastplan.item_id,
            forecastplan.location_id,
            forecastplan.customer_id,
            forecastplan.startdate,
            forecastplan.enddate,
            jsonb_strip_nulls(
                to_jsonb(forecastplan)
                - array['customer_id', 'item_id', 'location_id', 'startdate', 'enddate']
                ) as value
            FROM forecastplan
            inner join forecast on forecast.item_id = forecastplan.item_id
            and forecast.location_id = forecastplan.location_id
            and forecast.customer_id = forecastplan.customer_id
            and forecast.planned = true
            where
            forecastplan.enddate > to_date('%s','YYYY-MM-DD HH24:MI:SS')
            """ % (parameter_currentdate.strftime("%Y-%m-%d %H:%M:%S"),))

    serializer_class = ForecastPlanSerializer
    filterset_class = None

    unique_fields = ["id"]


class MeasureFilter(FilterSet):
    class Meta:
        model = Measure
        fields = {
            "name": ["exact", "in", "contains"],
            "label": ["exact", "in", "contains"],
            "description": ["exact", "in", "contains"],
            "type": ["exact", "in", "contains"],
            "discrete": ["exact"],
            "defaultvalue": ["exact", "in", "gt", "gte", "lt", "lte"],
            "mode_future": ["exact", "in", "contains"],
            "mode_past": ["exact", "in", "gt", "gte", "lt", "lte"],
            "compute_expression": ["exact", "in", "contains"],
            "update_expression": ["exact", "in", "contains"],
            "source": ["exact", "in"],
            "lastmodified": ["exact", "in", "gt", "gte", "lt", "lte"],
        }


class MeasureSerializer(BulkModelSerializer):
    def validate_name(self, value):
        if value and not value.isalnum():
            raise serializers.ValidationError("Measure name can only be alphanumeric")

    class Meta:
        model = Measure
        fields = (
            "name",
            "label",
            "description",
            "type",
            "discrete",
            "defaultvalue",
            "mode_future",
            "mode_past",
            "compute_expression",
            "update_expression",
            "overrides",
            "source",
            "lastmodified",
        )


class MeasureAPI(frePPleBulkModelViewSet):
    def get_queryset(self):
        return Measure.objects.using(self.request.database).all()

    serializer_class = MeasureSerializer
    filterset_class = MeasureFilter

    unique_fields = ["name"]


class MeasuredetailAPI(frePPleRetrieveUpdateDestroyAPIView):
    def get_queryset(self):
        return Measure.objects.using(self.request.database).all()
