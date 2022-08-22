#
# Copyright (C) 2015 by frePPLe bv
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

from django_filters import rest_framework as filters
from rest_framework_bulk.drf3.serializers import BulkListSerializer, BulkSerializerMixin

from freppledb.common.api.views import (
    frePPleListCreateAPIView,
    frePPleRetrieveUpdateDestroyAPIView,
)
from . import models
from freppledb.common.api.serializers import (
    ModelSerializer,
    getAttributeAPIFilterDefinition,
    getAttributeAPIFields,
    getAttributeAPIReadOnlyFields,
)

import logging

logger = logging.getLogger(__name__)


class CalendarFilter(filters.FilterSet):
    class Meta:
        model = models.Calendar
        fields = dict(
            {
                "name": ["exact", "in", "contains"],
                "description": ["exact", "in", "contains"],
                "category": ["exact", "in", "contains"],
                "subcategory": ["exact", "in", "contains"],
                "defaultvalue": ["exact", "in", "gt", "gte", "lt", "lte"],
                "source": ["exact", "in"],
                "lastmodified": ["exact", "in", "gt", "gte", "lt", "lte"],
            },
            **getAttributeAPIFilterDefinition(models.Calendar)
        )
        filter_fields = fields.keys()


class CalendarSerializer(BulkSerializerMixin, ModelSerializer):
    class Meta:
        model = models.Calendar
        fields = (
            "name",
            "description",
            "category",
            "subcategory",
            "defaultvalue",
            "source",
            "lastmodified",
        ) + getAttributeAPIFields(models.Calendar)
        read_only_fields = ("lastmodified",) + getAttributeAPIReadOnlyFields(
            models.Calendar
        )
        list_serializer_class = BulkListSerializer
        update_lookup_field = "name"
        partial = True


class CalendarAPI(frePPleListCreateAPIView):
    queryset = models.Calendar.objects.all()
    serializer_class = CalendarSerializer
    filter_class = CalendarFilter


class CalendardetailAPI(frePPleRetrieveUpdateDestroyAPIView):
    queryset = models.Calendar.objects.all()
    serializer_class = CalendarSerializer


class CalendarBucketFilter(filters.FilterSet):
    class Meta:
        model = models.CalendarBucket
        fields = dict(
            {
                "id": ["exact", "in", "gt", "gte", "lt", "lte"],
                "calendar": ["exact", "in"],
                "value": ["exact", "in", "gt", "gte", "lt", "lte"],
                "priority": ["exact", "in", "gt", "gte", "lt", "lte"],
                "startdate": ["exact", "in", "gt", "gte", "lt", "lte"],
                "enddate": ["exact", "in", "gt", "gte", "lt", "lte"],
                "monday": ["exact"],
                "tuesday": ["exact"],
                "wednesday": ["exact"],
                "thursday": ["exact"],
                "friday": ["exact"],
                "saturday": ["exact"],
                "sunday": ["exact"],
                "starttime": ["exact", "in", "gt", "gte", "lt", "lte"],
                "endtime": ["exact", "in", "gt", "gte", "lt", "lte"],
                "source": ["exact", "in"],
                "lastmodified": ["exact", "in", "gt", "gte", "lt", "lte"],
            },
            **getAttributeAPIFilterDefinition(models.CalendarBucket)
        )
        filter_fields = fields.keys()


class CalendarBucketSerializer(BulkSerializerMixin, ModelSerializer):
    class Meta:
        model = models.CalendarBucket
        fields = (
            "id",
            "calendar",
            "startdate",
            "enddate",
            "value",
            "priority",
            "monday",
            "tuesday",
            "wednesday",
            "thursday",
            "friday",
            "saturday",
            "sunday",
            "starttime",
            "endtime",
            "source",
            "lastmodified",
        ) + getAttributeAPIFields(models.CalendarBucket)
        read_only_fields = ("lastmodified",) + getAttributeAPIReadOnlyFields(
            models.CalendarBucket
        )
        list_serializer_class = BulkListSerializer
        update_lookup_field = "id"
        partial = True


class CalendarBucketAPI(frePPleListCreateAPIView):
    queryset = models.CalendarBucket.objects.all()
    fields = (
        "id",
        "calendar",
        "startdate",
        "enddate",
        "value",
        "priority",
        "monday",
        "tuesday",
        "wednesday",
        "thursday",
        "friday",
        "saturday",
        "sunday",
        "starttime",
        "endtime",
        "source",
        "lastmodified",
    )
    serializer_class = CalendarBucketSerializer
    filter_class = CalendarBucketFilter


class CalendarBucketdetailAPI(frePPleRetrieveUpdateDestroyAPIView):
    queryset = models.CalendarBucket.objects.all()
    serializer_class = CalendarBucketSerializer


class LocationFilter(filters.FilterSet):
    class Meta:
        model = models.Location
        fields = dict(
            {
                "name": ["exact", "in", "contains"],
                "owner": ["exact", "in"],
                "description": ["exact", "in", "contains"],
                "category": ["exact", "in", "contains"],
                "subcategory": ["exact", "in", "contains"],
                "available": ["exact", "in", "gt", "gte", "lt", "lte"],
                "source": ["exact", "in"],
                "lastmodified": ["exact", "in", "gt", "gte", "lt", "lte"],
            },
            **getAttributeAPIFilterDefinition(models.Location)
        )
        filter_fields = fields.keys()


class LocationSerializer(BulkSerializerMixin, ModelSerializer):
    class Meta:
        model = models.Location
        fields = (
            "name",
            "owner",
            "description",
            "category",
            "subcategory",
            "available",
            "source",
            "lastmodified",
        ) + getAttributeAPIFields(models.Location)
        read_only_fields = ("lastmodified",) + getAttributeAPIReadOnlyFields(
            models.Location
        )
        list_serializer_class = BulkListSerializer
        update_lookup_field = "name"
        partial = True


class LocationAPI(frePPleListCreateAPIView):
    queryset = models.Location.objects.all()
    serializer_class = LocationSerializer
    filter_class = LocationFilter


class LocationdetailAPI(frePPleRetrieveUpdateDestroyAPIView):
    queryset = models.Location.objects.all()
    serializer_class = LocationSerializer


class CustomerFilter(filters.FilterSet):
    class Meta:
        model = models.Customer
        fields = dict(
            {
                "name": ["exact", "in", "contains"],
                "owner": ["exact", "in"],
                "description": ["exact", "in", "contains"],
                "category": ["exact", "in", "contains"],
                "subcategory": ["exact", "in", "contains"],
                "source": ["exact", "in"],
                "lastmodified": ["exact", "in", "gt", "gte", "lt", "lte"],
            },
            **getAttributeAPIFilterDefinition(models.Customer)
        )
        filter_fields = fields.keys()


class CustomerSerializer(BulkSerializerMixin, ModelSerializer):
    class Meta:
        model = models.Customer
        fields = (
            "name",
            "owner",
            "description",
            "category",
            "subcategory",
            "source",
            "lastmodified",
        ) + getAttributeAPIFields(models.Customer)
        read_only_fields = ("lastmodified",) + getAttributeAPIReadOnlyFields(
            models.Customer
        )
        list_serializer_class = BulkListSerializer
        update_lookup_field = "name"
        partial = True


class CustomerAPI(frePPleListCreateAPIView):
    queryset = models.Customer.objects.all()
    serializer_class = CustomerSerializer
    filter_class = CustomerFilter


class CustomerdetailAPI(frePPleRetrieveUpdateDestroyAPIView):
    queryset = models.Customer.objects.all()
    serializer_class = CustomerSerializer


class ItemFilter(filters.FilterSet):
    class Meta:
        model = models.Item
        fields = dict(
            {
                "name": ["exact", "in", "contains"],
                "owner": ["exact", "in"],
                "description": ["exact", "in", "contains"],
                "category": ["exact", "in", "contains"],
                "subcategory": ["exact", "in", "contains"],
                "cost": ["exact", "in", "gt", "gte", "lt", "lte"],
                "volume": ["exact", "in", "gt", "gte", "lt", "lte"],
                "weight": ["exact", "in", "gt", "gte", "lt", "lte"],
                "uom": ["exact", "in", "contains"],
                "periodofcover": ["exact", "in", "gt", "gte", "lt", "lte"],
                "type": ["exact", "in"],
                "source": ["exact", "in"],
                "lastmodified": ["exact", "in", "gt", "gte", "lt", "lte"],
            },
            **getAttributeAPIFilterDefinition(models.Item)
        )
        filter_fields = fields.keys()


class ItemSerializer(BulkSerializerMixin, ModelSerializer):
    class Meta:
        model = models.Item
        fields = (
            "name",
            "owner",
            "description",
            "category",
            "subcategory",
            "cost",
            "volume",
            "weight",
            "periodofcover",
            "uom",
            "type",
            "source",
            "lastmodified",
        ) + getAttributeAPIFields(models.Item)
        read_only_fields = (
            "lastmodified",
            "periodofcover",
        ) + getAttributeAPIReadOnlyFields(models.Item)
        list_serializer_class = BulkListSerializer
        update_lookup_field = "name"
        partial = True


class ItemAPI(frePPleListCreateAPIView):
    queryset = models.Item.objects.all()
    serializer_class = ItemSerializer
    filter_class = ItemFilter


class ItemdetailAPI(frePPleRetrieveUpdateDestroyAPIView):
    queryset = models.Item.objects.all()
    serializer_class = ItemSerializer


class SupplierFilter(filters.FilterSet):
    class Meta:
        model = models.Supplier
        fields = dict(
            {
                "name": ["exact", "in", "contains"],
                "owner": ["exact", "in"],
                "description": ["exact", "in", "contains"],
                "category": ["exact", "in", "contains"],
                "subcategory": ["exact", "in", "contains"],
                "available": ["exact", "in", "gt", "gte", "lt", "lte"],
                "source": ["exact", "in"],
                "lastmodified": ["exact", "in", "gt", "gte", "lt", "lte"],
            },
            **getAttributeAPIFilterDefinition(models.Supplier)
        )
        filter_fields = fields.keys()


class SupplierSerializer(BulkSerializerMixin, ModelSerializer):
    class Meta:
        model = models.Supplier
        fields = (
            "name",
            "owner",
            "description",
            "category",
            "subcategory",
            "available",
            "source",
            "lastmodified",
        ) + getAttributeAPIFields(models.Supplier)
        read_only_fields = ("lastmodified",) + getAttributeAPIReadOnlyFields(
            models.Supplier
        )
        list_serializer_class = BulkListSerializer
        update_lookup_field = "name"
        partial = True


class SupplierAPI(frePPleListCreateAPIView):
    queryset = models.Supplier.objects.all()
    serializer_class = SupplierSerializer
    filter_class = SupplierFilter


class SupplierdetailAPI(frePPleRetrieveUpdateDestroyAPIView):
    queryset = models.Supplier.objects.all()
    serializer_class = SupplierSerializer


class ItemSupplierFilter(filters.FilterSet):
    class Meta:
        model = models.ItemSupplier
        fields = dict(
            {
                "id": ["exact", "in", "gt", "gte", "lt", "lte"],
                "item": ["exact", "in"],
                "location": ["exact", "in"],
                "supplier": ["exact", "in"],
                "leadtime": ["exact", "in", "gt", "gte", "lt", "lte"],
                "sizeminimum": ["exact", "in", "gt", "gte", "lt", "lte"],
                "sizemultiple": ["exact", "in", "gt", "gte", "lt", "lte"],
                "sizemaximum": ["exact", "in", "gt", "gte", "lt", "lte"],
                "batchwindow": ["exact", "in", "gt", "gte", "lt", "lte"],
                "hard_safety_leadtime": ["exact", "in", "gt", "gte", "lt", "lte"],
                "extra_safety_leadtime": ["exact", "in", "gt", "gte", "lt", "lte"],
                "cost": ["exact", "in", "gt", "gte", "lt", "lte"],
                "priority": ["exact", "in", "gt", "gte", "lt", "lte"],
                "effective_start": ["exact", "in", "gt", "gte", "lt", "lte"],
                "effective_end": ["exact", "in", "gt", "gte", "lt", "lte"],
                "source": ["exact", "in"],
                "lastmodified": ["exact", "in", "gt", "gte", "lt", "lte"],
            },
            **getAttributeAPIFilterDefinition(models.ItemSupplier)
        )
        filter_fields = fields.keys()


class ItemSupplierSerializer(BulkSerializerMixin, ModelSerializer):
    class Meta:
        model = models.ItemSupplier
        fields = (
            "id",
            "item",
            "location",
            "supplier",
            "leadtime",
            "sizeminimum",
            "sizemultiple",
            "sizemaximum",
            "batchwindow",
            "cost",
            "priority",
            "hard_safety_leadtime",
            "extra_safety_leadtime",
            "effective_start",
            "effective_end",
            "source",
            "lastmodified",
        ) + getAttributeAPIFields(models.ItemSupplier)
        read_only_fields = ("lastmodified",) + getAttributeAPIReadOnlyFields(
            models.ItemSupplier
        )
        list_serializer_class = BulkListSerializer
        update_lookup_field = "id"
        partial = True


class ItemSupplierAPI(frePPleListCreateAPIView):
    queryset = models.ItemSupplier.objects.all()
    serializer_class = ItemSupplierSerializer
    filter_class = ItemSupplierFilter


class ItemSupplierdetailAPI(frePPleRetrieveUpdateDestroyAPIView):
    queryset = models.ItemSupplier.objects.all()
    serializer_class = ItemSupplierSerializer


class ItemDistributionFilter(filters.FilterSet):
    class Meta:
        model = models.ItemDistribution
        fields = dict(
            {
                "id": ["exact", "in", "gt", "gte", "lt", "lte"],
                "item": ["exact", "in"],
                "location": ["exact", "in"],
                "origin": ["exact", "in"],
                "leadtime": ["exact", "in", "gt", "gte", "lt", "lte"],
                "sizeminimum": ["exact", "in", "gt", "gte", "lt", "lte"],
                "sizemultiple": ["exact", "in", "gt", "gte", "lt", "lte"],
                "sizemaximum": ["exact", "in", "gt", "gte", "lt", "lte"],
                "batchwindow": ["exact", "in", "gt", "gte", "lt", "lte"],
                "cost": ["exact", "in", "gt", "gte", "lt", "lte"],
                "priority": ["exact", "in", "gt", "gte", "lt", "lte"],
                "effective_start": ["exact", "in", "gt", "gte", "lt", "lte"],
                "effective_end": ["exact", "in", "gt", "gte", "lt", "lte"],
                "source": ["exact", "in"],
                "lastmodified": ["exact", "in", "gt", "gte", "lt", "lte"],
            },
            **getAttributeAPIFilterDefinition(models.ItemDistribution)
        )
        filter_fields = fields.keys()


class ItemDistributionSerializer(BulkSerializerMixin, ModelSerializer):
    class Meta:
        model = models.ItemDistribution
        fields = (
            "id",
            "item",
            "location",
            "origin",
            "leadtime",
            "sizeminimum",
            "sizemultiple",
            "sizemaximum",
            "batchwindow",
            "cost",
            "priority",
            "effective_start",
            "effective_end",
            "source",
            "lastmodified",
        ) + getAttributeAPIFields(models.ItemDistribution)
        read_only_fields = ("lastmodified",) + getAttributeAPIReadOnlyFields(
            models.ItemDistribution
        )
        list_serializer_class = BulkListSerializer
        update_lookup_field = "id"
        partial = True


class ItemDistributionAPI(frePPleListCreateAPIView):
    queryset = models.ItemDistribution.objects.all()
    serializer_class = ItemDistributionSerializer
    filter_class = ItemDistributionFilter


class ItemDistributiondetailAPI(frePPleRetrieveUpdateDestroyAPIView):
    queryset = models.ItemDistribution.objects.all()
    serializer_class = ItemDistributionSerializer


class OperationFilter(filters.FilterSet):
    class Meta:
        model = models.Operation
        fields = dict(
            {
                "name": ["exact", "in", "contains"],
                "type": ["exact", "in"],
                "category": ["exact", "in", "contains"],
                "subcategory": ["exact", "in", "contains"],
                "location": ["exact", "in"],
                "item": ["exact", "in"],
                "posttime": ["exact", "in", "gt", "gte", "lt", "lte"],
                "fence": ["exact", "in", "gt", "gte", "lt", "lte"],
                "sizeminimum": ["exact", "in", "gt", "gte", "lt", "lte"],
                "sizemultiple": ["exact", "in", "gt", "gte", "lt", "lte"],
                "sizemaximum": ["exact", "in", "gt", "gte", "lt", "lte"],
                "cost": ["exact", "in", "gt", "gte", "lt", "lte"],
                "duration": ["exact", "in", "gt", "gte", "lt", "lte"],
                "duration_per": ["exact", "in", "gt", "gte", "lt", "lte"],
                "search": ["exact", "in"],
                "owner": ["exact", "in"],
                "priority": ["exact", "in", "gt", "gte", "lt", "lte"],
                "effective_start": ["exact", "in", "gt", "gte", "lt", "lte"],
                "effective_end": ["exact", "in", "gt", "gte", "lt", "lte"],
                "available": ["exact", "in"],
                "source": ["exact", "in"],
                "lastmodified": ["exact", "in", "gt", "gte", "lt", "lte"],
            },
            **getAttributeAPIFilterDefinition(models.Operation)
        )
        filter_fields = fields.keys()


class OperationSerializer(BulkSerializerMixin, ModelSerializer):
    class Meta:
        model = models.Operation
        fields = (
            "name",
            "type",
            "description",
            "category",
            "subcategory",
            "item",
            "location",
            "fence",
            "posttime",
            "sizeminimum",
            "sizemultiple",
            "sizemaximum",
            "owner",
            "priority",
            "effective_start",
            "effective_end",
            "available",
            "cost",
            "duration",
            "duration_per",
            "search",
            "source",
            "lastmodified",
        ) + getAttributeAPIFields(models.Operation)
        read_only_fields = ("lastmodified",) + getAttributeAPIReadOnlyFields(
            models.Operation
        )
        list_serializer_class = BulkListSerializer
        update_lookup_field = "name"
        partial = True


class OperationAPI(frePPleListCreateAPIView):
    queryset = models.Operation.objects.all()
    serializer_class = OperationSerializer
    filter_class = OperationFilter


class OperationdetailAPI(frePPleRetrieveUpdateDestroyAPIView):
    queryset = models.Operation.objects.all()
    serializer_class = OperationSerializer


class SubOperationFilter(filters.FilterSet):
    class Meta:
        model = models.SubOperation
        fields = dict(
            {
                "id": ["exact", "in", "gt", "gte", "lt", "lte"],
                "operation": ["exact", "in"],
                "priority": ["exact", "in", "gt", "gte", "lt", "lte"],
                "suboperation": ["exact", "in"],
                "effective_start": ["exact", "in", "gt", "gte", "lt", "lte"],
                "effective_end": ["exact", "in", "gt", "gte", "lt", "lte"],
                "source": ["exact", "in"],
                "lastmodified": ["exact", "in", "gt", "gte", "lt", "lte"],
            },
            **getAttributeAPIFilterDefinition(models.SubOperation)
        )
        filter_fields = fields.keys()


class SubOperationSerializer(BulkSerializerMixin, ModelSerializer):
    class Meta:
        model = models.SubOperation
        fields = (
            "id",
            "operation",
            "priority",
            "suboperation",
            "effective_start",
            "effective_end",
            "source",
            "lastmodified",
        ) + getAttributeAPIFields(models.SubOperation)
        read_only_fields = ("lastmodified",) + getAttributeAPIReadOnlyFields(
            models.SubOperation
        )
        list_serializer_class = BulkListSerializer
        update_lookup_field = "id"
        partial = True


class SubOperationAPI(frePPleListCreateAPIView):
    queryset = models.SubOperation.objects.all()
    serializer_class = SubOperationSerializer
    filter_class = SubOperationFilter


class SubOperationdetailAPI(frePPleRetrieveUpdateDestroyAPIView):
    queryset = models.SubOperation.objects.all()
    serializer_class = SubOperationSerializer


class BufferFilter(filters.FilterSet):
    class Meta:
        model = models.Buffer
        fields = dict(
            {
                "id": ["exact", "in", "gt", "gte", "lt", "lte"],
                "category": ["exact", "in", "contains"],
                "subcategory": ["exact", "in", "contains"],
                "type": ["exact", "in"],
                "location": ["exact", "in"],
                "item": ["exact", "in"],
                "batch": ["exact", "contains"],
                "onhand": ["exact", "in", "gt", "gte", "lt", "lte"],
                "minimum": ["exact", "in", "gt", "gte", "lt", "lte"],
                "minimum_calendar": ["exact", "in", "gt", "gte", "lt", "lte"],
                "min_interval": ["exact", "in", "gt", "gte", "lt", "lte"],
                "source": ["exact", "in"],
                "lastmodified": ["exact", "in", "gt", "gte", "lt", "lte"],
            },
            **getAttributeAPIFilterDefinition(models.Buffer)
        )
        filter_fields = fields.keys()


class BufferSerializer(BulkSerializerMixin, ModelSerializer):
    class Meta:
        model = models.Buffer
        fields = (
            "id",
            "description",
            "category",
            "subcategory",
            "type",
            "location",
            "item",
            "batch",
            "onhand",
            "minimum",
            "minimum_calendar",
            "min_interval",
            "source",
            "lastmodified",
        ) + getAttributeAPIFields(models.Buffer)
        read_only_fields = ("lastmodified",) + getAttributeAPIReadOnlyFields(
            models.Buffer
        )
        list_serializer_class = BulkListSerializer
        update_lookup_field = "id"
        partial = True


class BufferAPI(frePPleListCreateAPIView):
    queryset = models.Buffer.objects.all()
    serializer_class = BufferSerializer
    filter_class = BufferFilter


class BufferdetailAPI(frePPleRetrieveUpdateDestroyAPIView):
    queryset = models.Buffer.objects.all()
    serializer_class = BufferSerializer


class SetupMatrixFilter(filters.FilterSet):
    class Meta:
        model = models.SetupMatrix
        fields = dict(
            {
                "name": ["exact", "in", "contains"],
                "source": ["exact", "in"],
                "lastmodified": ["exact", "in", "gt", "gte", "lt", "lte"],
            },
            **getAttributeAPIFilterDefinition(models.SetupMatrix)
        )
        filter_fields = fields.keys()


class SetupMatrixSerializer(BulkSerializerMixin, ModelSerializer):
    class Meta:
        model = models.SetupMatrix
        fields = ("name", "source", "lastmodified") + getAttributeAPIFields(
            models.SetupMatrix
        )
        read_only_fields = ("lastmodified",) + getAttributeAPIReadOnlyFields(
            models.SetupMatrix
        )
        list_serializer_class = BulkListSerializer
        update_lookup_field = "name"
        partial = True


class SetupMatrixAPI(frePPleListCreateAPIView):
    queryset = models.SetupMatrix.objects.all()
    serializer_class = SetupMatrixSerializer
    filter_class = SetupMatrixFilter


class SetupMatrixdetailAPI(frePPleRetrieveUpdateDestroyAPIView):
    queryset = models.SetupMatrix.objects.all()
    serializer_class = SetupMatrixSerializer


class SetupRuleFilter(filters.FilterSet):
    class Meta:
        model = models.SetupRule
        fields = dict(
            {
                "id": ["exact", "in", "contains"],
                "setupmatrix": ["exact", "in"],
                "fromsetup": ["exact", "in"],
                "tosetup": ["exact", "in"],
                "priority": ["exact", "in", "gt", "gte", "lt", "lte"],
                "duration": ["exact", "in", "gt", "gte", "lt", "lte"],
                "cost": ["exact", "in", "gt", "gte", "lt", "lte"],
                "resource": ["exact", "in"],
            },
            **getAttributeAPIFilterDefinition(models.SetupRule)
        )
        filter_fields = fields.keys()


class SetupRuleSerializer(BulkSerializerMixin, ModelSerializer):
    class Meta:
        model = models.SetupRule
        fields = (
            "id",
            "setupmatrix",
            "fromsetup",
            "tosetup",
            "priority",
            "duration",
            "cost",
            "resource",
        ) + getAttributeAPIFields(models.SetupRule)
        read_only_fields = ("lastmodified",) + getAttributeAPIReadOnlyFields(
            models.SetupRule
        )
        list_serializer_class = BulkListSerializer
        update_lookup_field = "setupmatrix"
        partial = True


class SetupRuleAPI(frePPleListCreateAPIView):
    queryset = models.SetupRule.objects.all()
    serializer_class = SetupRuleSerializer
    filter_class = SetupRuleFilter


class SetupRuledetailAPI(frePPleRetrieveUpdateDestroyAPIView):
    queryset = models.SetupRule.objects.all()
    serializer_class = SetupRuleSerializer


class ResourceFilter(filters.FilterSet):
    class Meta:
        model = models.Resource
        fields = dict(
            {
                "name": ["exact", "in", "contains"],
                "description": ["exact", "in", "contains"],
                "category": ["exact", "in", "contains"],
                "subcategory": ["exact", "in", "contains"],
                "type": ["exact", "in"],
                "maximum": ["exact", "in", "gt", "gte", "lt", "lte"],
                "maximum_calendar": ["exact", "in", "gt", "gte", "lt", "lte"],
                "available": ["exact", "in", "gt", "gte", "lt", "lte"],
                "location": ["exact", "in"],
                "owner": ["exact", "in"],
                "cost": ["exact", "in", "gt", "gte", "lt", "lte"],
                "maxearly": ["exact", "in", "gt", "gte", "lt", "lte"],
                "setupmatrix": ["exact", "in"],
                "efficiency": ["exact", "in", "gt", "gte", "lt", "lte"],
                "efficiency_calendar": ["exact", "in"],
                "constrained": ["exact"],
                "source": ["exact", "in"],
                "lastmodified": ["exact", "in", "gt", "gte", "lt", "lte"],
            },
            **getAttributeAPIFilterDefinition(models.Resource)
        )
        filter_fields = fields.keys()


class ResourceSerializer(BulkSerializerMixin, ModelSerializer):
    class Meta:
        model = models.Resource
        fields = (
            "name",
            "description",
            "category",
            "subcategory",
            "type",
            "maximum",
            "maximum_calendar",
            "available",
            "location",
            "owner",
            "cost",
            "maxearly",
            "setupmatrix",
            "setup",
            "efficiency",
            "efficiency_calendar",
            "constrained",
            "source",
            "lastmodified",
        ) + getAttributeAPIFields(models.Resource)
        read_only_fields = ("lastmodified",) + getAttributeAPIReadOnlyFields(
            models.Resource
        )
        list_serializer_class = BulkListSerializer
        update_lookup_field = "name"
        partial = True


class ResourceAPI(frePPleListCreateAPIView):
    queryset = models.Resource.objects.all()
    serializer_class = ResourceSerializer
    filter_class = ResourceFilter


class ResourcedetailAPI(frePPleRetrieveUpdateDestroyAPIView):
    queryset = models.Resource.objects.all()
    serializer_class = ResourceSerializer


class SkillFilter(filters.FilterSet):
    class Meta:
        model = models.Skill
        fields = dict(
            {
                "name": ["exact", "in", "contains"],
                "source": ["exact", "in"],
                "lastmodified": ["exact", "in", "gt", "gte", "lt", "lte"],
            },
            **getAttributeAPIFilterDefinition(models.Skill)
        )
        filter_fields = fields.keys()


class SkillSerializer(BulkSerializerMixin, ModelSerializer):
    class Meta:
        model = models.Skill
        fields = ("name", "source", "lastmodified") + getAttributeAPIFields(
            models.Skill
        )
        read_only_fields = ("lastmodified",) + getAttributeAPIReadOnlyFields(
            models.Skill
        )
        list_serializer_class = BulkListSerializer
        update_lookup_field = "name"
        partial = True


class SkillAPI(frePPleListCreateAPIView):
    queryset = models.Skill.objects.all()
    serializer_class = SkillSerializer
    filter_class = SkillFilter


class SkilldetailAPI(frePPleRetrieveUpdateDestroyAPIView):
    queryset = models.Skill.objects.all()
    serializer_class = SkillSerializer


class ResourceSkillFilter(filters.FilterSet):
    class Meta:
        model = models.ResourceSkill
        fields = dict(
            {
                "id": ["exact", "in", "gt", "gte", "lt", "lte"],
                "resource": ["exact", "in"],
                "skill": ["exact", "in"],
                "effective_start": ["exact", "in", "gt", "gte", "lt", "lte"],
                "effective_end": ["exact", "in", "gt", "gte", "lt", "lte"],
                "priority": ["exact", "in", "gt", "gte", "lt", "lte"],
                "source": ["exact", "in"],
                "lastmodified": ["exact", "in", "gt", "gte", "lt", "lte"],
            },
            **getAttributeAPIFilterDefinition(models.ResourceSkill)
        )
        filter_fields = fields.keys()


class ResourceSkillSerializer(BulkSerializerMixin, ModelSerializer):
    class Meta:
        model = models.ResourceSkill
        fields = (
            "id",
            "resource",
            "skill",
            "effective_start",
            "effective_end",
            "priority",
            "source",
            "lastmodified",
        ) + getAttributeAPIFields(models.ResourceSkill)
        read_only_fields = ("lastmodified",) + getAttributeAPIReadOnlyFields(
            models.ResourceSkill
        )
        list_serializer_class = BulkListSerializer
        update_lookup_field = "id"
        partial = True


class ResourceSkillAPI(frePPleListCreateAPIView):
    queryset = models.ResourceSkill.objects.all()
    serializer_class = ResourceSkillSerializer
    filter_class = ResourceSkillFilter


class ResourceSkilldetailAPI(frePPleRetrieveUpdateDestroyAPIView):
    queryset = models.ResourceSkill.objects.all()
    serializer_class = ResourceSkillSerializer


class OperationMaterialFilter(filters.FilterSet):
    class Meta:
        model = models.OperationMaterial
        fields = dict(
            {
                "id": ["exact", "in", "gt", "gte", "lt", "lte"],
                "quantity": ["exact", "in", "gt", "gte", "lt", "lte"],
                "quantity_fixed": ["exact", "in", "gt", "gte", "lt", "lte"],
                "transferbatch": ["exact", "in", "gt", "gte", "lt", "lte"],
                "offset": ["exact", "in", "gt", "gte", "lt", "lte"],
                "operation": ["exact", "in"],
                "item": ["exact", "in"],
                "type": ["exact", "in"],
                "effective_start": ["exact", "in", "gt", "gte", "lt", "lte"],
                "effective_end": ["exact", "in", "gt", "gte", "lt", "lte"],
                "name": ["exact", "in", "contains"],
                "priority": ["exact", "in", "gt", "gte", "lt", "lte"],
                "search": ["exact", "contains"],
                "source": ["exact", "in"],
                "lastmodified": ["exact", "in", "gt", "gte", "lt", "lte"],
            },
            **getAttributeAPIFilterDefinition(models.OperationMaterial)
        )
        filter_fields = fields.keys()


class OperationMaterialSerializer(BulkSerializerMixin, ModelSerializer):
    class Meta:
        model = models.OperationMaterial
        fields = (
            "id",
            "operation",
            "item",
            "quantity",
            "quantity_fixed",
            "transferbatch",
            "offset",
            "type",
            "effective_start",
            "effective_end",
            "name",
            "priority",
            "search",
            "source",
            "lastmodified",
        ) + getAttributeAPIFields(models.OperationMaterial)
        read_only_fields = ("lastmodified",) + getAttributeAPIReadOnlyFields(
            models.OperationMaterial
        )
        list_serializer_class = BulkListSerializer
        update_lookup_field = "id"
        partial = True


class OperationMaterialAPI(frePPleListCreateAPIView):
    queryset = models.OperationMaterial.objects.all()
    serializer_class = OperationMaterialSerializer
    filter_class = OperationMaterialFilter


class OperationMaterialdetailAPI(frePPleRetrieveUpdateDestroyAPIView):
    queryset = models.OperationMaterial.objects.all()
    serializer_class = OperationMaterialSerializer


class OperationPlanMaterialFilter(filters.FilterSet):
    class Meta:
        model = models.OperationPlanMaterial
        fields = dict(
            {
                "id": ["exact", "in", "gt", "gte", "lt", "lte"],
                "operationplan": ["exact", "in"],
                "item": ["exact", "in", "gt", "gte", "lt", "lte"],
                "location": ["exact", "in", "gt", "gte", "lt", "lte"],
                "quantity": ["exact", "in", "gt", "gte", "lt", "lte"],
                "flowdate": ["exact", "in", "gt", "gte", "lt", "lte"],
                "status": ["exact", "in", "gt", "gte", "lt", "lte"],
                "source": ["exact", "in"],
                "lastmodified": ["exact", "in", "gt", "gte", "lt", "lte"],
            },
            **getAttributeAPIFilterDefinition(models.OperationPlanMaterial)
        )
        filter_fields = fields.keys()


class OperationPlanMaterialSerializer(BulkSerializerMixin, ModelSerializer):
    class Meta:
        model = models.OperationPlanMaterial
        fields = (
            "id",
            "operationplan",
            "item",
            "location",
            "quantity",
            "flowdate",
            "status",
            "source",
            "lastmodified",
        ) + getAttributeAPIFields(models.OperationPlanMaterial)
        read_only_fields = ("lastmodified",) + getAttributeAPIReadOnlyFields(
            models.OperationPlanMaterial
        )
        list_serializer_class = BulkListSerializer
        update_lookup_field = "id"
        partial = True


class OperationPlanMaterialAPI(frePPleListCreateAPIView):
    queryset = models.OperationPlanMaterial.objects.all()
    serializer_class = OperationPlanMaterialSerializer
    filter_class = OperationPlanMaterialFilter


class OperationPlanMaterialdetailAPI(frePPleRetrieveUpdateDestroyAPIView):
    queryset = models.OperationPlanMaterial.objects.all()
    serializer_class = OperationPlanMaterialSerializer


class OperationResourceFilter(filters.FilterSet):
    class Meta:
        model = models.OperationResource
        fields = dict(
            {
                "id": ["exact", "in", "gt", "gte", "lt", "lte"],
                "operation": ["exact", "in"],
                "resource": ["exact", "in"],
                "skill": ["exact", "in"],
                "quantity": ["exact", "in", "gt", "gte", "lt", "lte"],
                "quantity_fixed": ["exact", "in", "gt", "gte", "lt", "lte"],
                "effective_start": ["exact", "in", "gt", "gte", "lt", "lte"],
                "effective_end": ["exact", "in", "gt", "gte", "lt", "lte"],
                "name": ["exact", "in", "contains"],
                "priority": ["exact", "in", "gt", "gte", "lt", "lte"],
                "search": ["exact", "contains"],
                "source": ["exact", "in"],
                "lastmodified": ["exact", "in", "gt", "gte", "lt", "lte"],
            },
            **getAttributeAPIFilterDefinition(models.OperationResource)
        )
        filter_fields = fields.keys()


class OperationResourceSerializer(BulkSerializerMixin, ModelSerializer):
    class Meta:
        model = models.OperationResource
        fields = (
            "id",
            "operation",
            "resource",
            "skill",
            "quantity",
            "quantity_fixed",
            "effective_start",
            "effective_end",
            "name",
            "priority",
            "setup",
            "search",
            "source",
            "lastmodified",
        ) + getAttributeAPIFields(models.OperationResource)
        read_only_fields = ("lastmodified",) + getAttributeAPIReadOnlyFields(
            models.OperationResource
        )
        list_serializer_class = BulkListSerializer
        update_lookup_field = "id"
        partial = True


class OperationResourceAPI(frePPleListCreateAPIView):
    queryset = models.OperationResource.objects.all()
    serializer_class = OperationResourceSerializer
    filter_class = OperationResourceFilter


class OperationResourcedetailAPI(frePPleRetrieveUpdateDestroyAPIView):
    queryset = models.OperationResource.objects.all()
    serializer_class = OperationResourceSerializer


class OperationPlanResourceFilter(filters.FilterSet):
    class Meta:
        model = models.OperationPlanResource
        fields = dict(
            {
                "id": ["exact", "in", "gt", "gte", "lt", "lte"],
                "operationplan": ["exact", "in"],
                "resource": ["exact", "in"],
                "quantity": ["exact", "in", "gt", "gte", "lt", "lte"],
                "startdate": ["exact", "in", "gt", "gte", "lt", "lte"],
                "enddate": ["exact", "in", "gt", "gte", "lt", "lte"],
                "status": ["exact", "in", "gt", "gte", "lt", "lte"],
                "setup": ["exact", "in", "gt", "gte", "lt", "lte"],
                "source": ["exact", "in"],
                "lastmodified": ["exact", "in", "gt", "gte", "lt", "lte"],
            },
            **getAttributeAPIFilterDefinition(models.OperationPlanResource)
        )
        filter_fields = fields.keys()


class OperationPlanResourceSerializer(BulkSerializerMixin, ModelSerializer):
    class Meta:
        model = models.OperationPlanResource
        fields = (
            "id",
            "operationplan",
            "resource",
            "quantity",
            "startdate",
            "enddate",
            "status",
            "setup",
            "source",
            "lastmodified",
        ) + getAttributeAPIFields(models.OperationPlanResource)
        read_only_fields = ("lastmodified",) + getAttributeAPIReadOnlyFields(
            models.OperationPlanResource
        )
        list_serializer_class = BulkListSerializer
        update_lookup_field = "id"
        partial = True


class OperationPlanResourceAPI(frePPleListCreateAPIView):
    queryset = models.OperationPlanResource.objects.all()
    serializer_class = OperationPlanResourceSerializer
    filter_class = OperationPlanResourceFilter


class OperationPlanResourcedetailAPI(frePPleRetrieveUpdateDestroyAPIView):
    queryset = models.OperationPlanResource.objects.all()
    serializer_class = OperationPlanResourceSerializer


class ManufacturingOrderFilter(filters.FilterSet):
    class Meta:
        model = models.ManufacturingOrder
        fields = dict(
            {
                "reference": ["exact", "in", "contains"],
                "status": ["exact", "in"],
                "operation": ["exact", "in"],
                "quantity": ["exact", "in", "gt", "gte", "lt", "lte"],
                "quantity_completed": ["exact", "in", "gt", "gte", "lt", "lte"],
                "startdate": ["exact", "in", "gt", "gte", "lt", "lte"],
                "enddate": ["exact", "in", "gt", "gte", "lt", "lte"],
                "batch": ["exact", "in", "contains"],
                "criticality": ["exact", "in", "gt", "gte", "lt", "lte"],
                "delay": ["exact", "in", "gt", "gte", "lt", "lte"],
                "plan": [],
                "owner": ["exact", "in"],
                "source": ["exact", "in"],
                "lastmodified": ["exact", "in", "gt", "gte", "lt", "lte"],
            },
            **getAttributeAPIFilterDefinition(models.OperationPlan)
        )
        filter_fields = fields.keys()


class ManufacturingOrderSerializer(BulkSerializerMixin, ModelSerializer):
    class OperationPlanResourceNestedSerializer(BulkSerializerMixin, ModelSerializer):
        class Meta:
            model = models.OperationPlanResource
            fields = ("resource", "quantity", "setup")
            list_serializer_class = BulkListSerializer
            partial = True

    class OperationPlanMaterialNestedSerializer(BulkSerializerMixin, ModelSerializer):
        class Meta:
            model = models.OperationPlanMaterial
            fields = ("item", "quantity", "flowdate")
            list_serializer_class = BulkListSerializer
            partial = True

    resources = OperationPlanResourceNestedSerializer(many=True, required=False)
    materials = OperationPlanMaterialNestedSerializer(many=True, required=False)

    def create(self, validated_data):
        # Normal processing
        opplanreslist = validated_data.pop("resources", [])
        opplanmatlist = validated_data.pop("materials", [])
        mo = super().create(validated_data)
        if opplanreslist:
            self._processOperationPlanResource(mo, opplanreslist)
        if opplanmatlist:
            self._processOperationPlanMaterial(mo, opplanmatlist)
        return mo

    def update(self, instance, validated_data):
        # Normal processing
        opplanreslist = validated_data.pop("resources", [])
        opplanmatlist = validated_data.pop("materials", [])
        mo = super().update(instance, validated_data)
        if opplanreslist:
            self._processOperationPlanResource(mo, opplanreslist)
        if opplanmatlist:
            self._processOperationPlanMaterial(mo, opplanmatlist)
        return mo

    def _processOperationPlanResource(self, mo, opplanreslist):
        database = mo._state.db
        # TODO: check if top loop (line just below) is needed
        for opplanres in opplanreslist:
            for rec in opplanreslist:
                if "resource" in rec:
                    try:
                        rec_res = (
                            models.Resource.objects.all()
                            .using(database)
                            .get(name=rec["resource"])
                        )
                        rec_topres = (
                            models.Resource.objects.all()
                            .using(database)
                            .get(lvl=0, lft__lte=rec_res.lft, rght__gte=rec_res.rght)
                        )
                        found = False
                        for opplanres in (
                            mo.resources.all()
                            .using(database)
                            .select_related("resource")
                        ):
                            topres = (
                                models.Resource.objects.all()
                                .using(database)
                                .get(
                                    lvl=0,
                                    lft__lte=opplanres.resource.lft,
                                    rght__gte=opplanres.resource.rght,
                                )
                            )
                            if topres == rec_topres:
                                opplanres.resource = rec_res
                                if "quantity" in rec:
                                    opplanres.quantity = rec["quantity"]
                                opplanres.save(
                                    using=database,
                                    update_fields=["resource", "quantity"],
                                )
                                found = True
                                break
                        if not found:
                            models.OperationPlanResource(
                                operationplan=mo,
                                resource=rec_res,
                                quantity=rec.get("quantity", 1),
                                startdate=mo.startdate,
                                enddate=mo.enddate,
                            ).save(using=database)
                    except Exception as e:
                        logger.error("REST API error saving manufacturing order:", e)

    def _processOperationPlanMaterial(self, mo, opplanmatlist):
        database = mo._state.db

        # prepare a dict from operationmaterial records
        # where key is name and value is list of items

        qs = (
            models.OperationMaterial.objects.all()
            .using(database)
            .filter(operation=mo.operation)
            .filter(name__isnull=False)
            .values("name", "item")
        )
        dict = {}
        for rec in qs:
            if rec["name"] not in dict:
                dict[rec["name"]] = [rec["item"]]
            else:
                dict[rec["name"]].append(rec["item"])

        # iterate over the opplanmatlist records to see if there are alternates
        for rec in opplanmatlist:
            if "item" in rec:
                try:
                    Found = False
                    for opplanmat in mo.materials.all().using(database):
                        # find lists where item is:

                        for k in dict.keys():
                            if (
                                rec["item"].name in dict[k]
                                and opplanmat.item.name in dict[k]
                            ) or rec["item"].name == opplanmat.item.name:

                                opplanmat.item = rec["item"]
                                if "quantity" in rec:
                                    opplanmat.quantity = rec["quantity"]
                                if "flowdate" in rec:
                                    opplanmat.flowdate = rec["flowdate"]
                                opplanmat.save(
                                    using=database,
                                    update_fields=["item", "quantity", "flowdate"],
                                )
                                Found = True
                                break
                        if Found:
                            break

                    if not Found:
                        models.OperationPlanMaterial(
                            operationplan=mo,
                            item=rec["item"],
                            quantity=rec.get("quantity", 1),
                            flowdate=rec.get(
                                "flowdate",
                                mo.enddate
                                if rec.get("quantity", 1) > 0
                                else mo.startdate,
                            ),
                        ).save(using=database)
                except Exception as e:
                    logger.error("REST API error saving manufacturing order:", e)

    class Meta:
        model = models.ManufacturingOrder
        fields = (
            "reference",
            "status",
            "operation",
            "quantity",
            "quantity_completed",
            "startdate",
            "enddate",
            "batch",
            "criticality",
            "delay",
            "plan",
            "owner",
            "source",
            "lastmodified",
            "resources",
            "materials",
        ) + getAttributeAPIFields(models.OperationPlan)
        read_only_fields = ("lastmodified",) + getAttributeAPIReadOnlyFields(
            models.OperationPlan
        )
        list_serializer_class = BulkListSerializer
        update_lookup_field = "reference"
        partial = True


class ManufacturingOrderAPI(frePPleListCreateAPIView):
    queryset = models.ManufacturingOrder.objects.all()
    serializer_class = ManufacturingOrderSerializer
    filter_class = ManufacturingOrderFilter


class ManufacturingOrderdetailAPI(frePPleRetrieveUpdateDestroyAPIView):
    queryset = models.ManufacturingOrder.objects.all()
    serializer_class = ManufacturingOrderSerializer


class DistributionOrderFilter(filters.FilterSet):
    class Meta:
        model = models.DistributionOrder
        fields = dict(
            {
                "status": ["exact", "in"],
                "reference": ["exact", "in", "contains"],
                "item": ["exact", "in"],
                "origin": ["exact", "in"],
                "destination": ["exact", "in"],
                "quantity": ["exact", "in", "gt", "gte", "lt", "lte"],
                "startdate": ["exact", "in", "gt", "gte", "lt", "lte"],
                "enddate": ["exact", "in", "gt", "gte", "lt", "lte"],
                "batch": ["exact", "in", "contains"],
                "criticality": ["exact", "in", "gt", "gte", "lt", "lte"],
                "delay": ["exact", "in", "gt", "gte", "lt", "lte"],
                "plan": [],
                "source": ["exact", "in"],
                "lastmodified": ["exact", "in", "gt", "gte", "lt", "lte"],
            },
            **getAttributeAPIFilterDefinition(models.OperationPlan)
        )
        filter_fields = fields.keys()


class DistributionOrderSerializer(BulkSerializerMixin, ModelSerializer):
    class Meta:
        model = models.DistributionOrder
        fields = (
            "reference",
            "status",
            "item",
            "origin",
            "destination",
            "quantity",
            "startdate",
            "enddate",
            "batch",
            "criticality",
            "delay",
            "plan",
            "source",
            "lastmodified",
        ) + getAttributeAPIFields(models.OperationPlan)
        read_only_fields = ("lastmodified",) + getAttributeAPIReadOnlyFields(
            models.OperationPlan
        )
        list_serializer_class = BulkListSerializer
        update_lookup_field = "reference"
        partial = True


class DistributionOrderAPI(frePPleListCreateAPIView):
    queryset = models.DistributionOrder.objects.all()
    serializer_class = DistributionOrderSerializer
    filter_class = DistributionOrderFilter


class DistributionOrderdetailAPI(frePPleRetrieveUpdateDestroyAPIView):
    queryset = models.DistributionOrder.objects.all()
    serializer_class = DistributionOrderSerializer


class PurchaseOrderFilter(filters.FilterSet):
    class Meta:
        model = models.PurchaseOrder
        fields = dict(
            {
                "reference": ["exact", "in", "contains"],
                "status": ["exact", "in"],
                "item": ["exact", "in"],
                "supplier": ["exact", "in"],
                "location": ["exact", "in"],
                "quantity": ["exact", "in", "gt", "gte", "lt", "lte"],
                "startdate": ["exact", "in", "gt", "gte", "lt", "lte"],
                "enddate": ["exact", "in", "gt", "gte", "lt", "lte"],
                "batch": ["exact", "in", "contains"],
                "criticality": ["exact", "in", "gt", "gte", "lt", "lte"],
                "delay": ["exact", "in", "gt", "gte", "lt", "lte"],
                "plan": [],
                "source": ["exact", "in"],
                "lastmodified": ["exact", "in", "gt", "gte", "lt", "lte"],
            },
            **getAttributeAPIFilterDefinition(models.OperationPlan)
        )
        filter_fields = fields.keys()


class PurchaseOrderSerializer(BulkSerializerMixin, ModelSerializer):
    class Meta:
        model = models.PurchaseOrder
        fields = (
            "reference",
            "status",
            "item",
            "supplier",
            "location",
            "quantity",
            "startdate",
            "enddate",
            "batch",
            "criticality",
            "batch",
            "delay",
            "plan",
            "source",
            "lastmodified",
        ) + getAttributeAPIFields(models.OperationPlan)
        read_only_fields = ("lastmodified",) + getAttributeAPIReadOnlyFields(
            models.OperationPlan
        )
        list_serializer_class = BulkListSerializer
        update_lookup_field = "reference"
        partial = True


class PurchaseOrderAPI(frePPleListCreateAPIView):
    queryset = models.PurchaseOrder.objects.all()
    serializer_class = PurchaseOrderSerializer
    filter_class = PurchaseOrderFilter


class PurchaseOrderdetailAPI(frePPleRetrieveUpdateDestroyAPIView):
    queryset = models.PurchaseOrder.objects.all()
    serializer_class = PurchaseOrderSerializer


class DeliveryOrderFilter(filters.FilterSet):
    class Meta:
        model = models.DeliveryOrder
        fields = dict(
            {
                "reference": ["exact", "in", "contains"],
                "status": ["exact", "in"],
                "item": ["exact", "in"],
                "demand": ["exact", "in"],
                "location": ["exact", "in"],
                "quantity": ["exact", "in", "gt", "gte", "lt", "lte"],
                "startdate": ["exact", "in", "gt", "gte", "lt", "lte"],
                "enddate": ["exact", "in", "gt", "gte", "lt", "lte"],
                "due": ["exact", "in", "gt", "gte", "lt", "lte"],
                "batch": ["exact", "in", "contains"],
                "delay": ["exact", "in", "gt", "gte", "lt", "lte"],
                "plan": [],
                "source": ["exact", "in"],
                "lastmodified": ["exact", "in", "gt", "gte", "lt", "lte"],
            },
            **getAttributeAPIFilterDefinition(models.OperationPlan)
        )
        filter_fields = fields.keys()


class DeliveryOrderSerializer(BulkSerializerMixin, ModelSerializer):
    class Meta:
        model = models.DeliveryOrder
        fields = (
            "reference",
            "status",
            "demand",
            "item",
            "location",
            "quantity",
            "startdate",
            "enddate",
            "due",
            "batch",
            "delay",
            "plan",
            "source",
            "lastmodified",
        ) + getAttributeAPIFields(models.OperationPlan)
        read_only_fields = ("lastmodified",) + getAttributeAPIReadOnlyFields(
            models.OperationPlan
        )
        list_serializer_class = BulkListSerializer
        update_lookup_field = "reference"
        partial = True


class DeliveryOrderAPI(frePPleListCreateAPIView):
    queryset = models.DeliveryOrder.objects.all()
    serializer_class = DeliveryOrderSerializer
    filter_class = DeliveryOrderFilter


class DeliveryOrderdetailAPI(frePPleRetrieveUpdateDestroyAPIView):
    queryset = models.DeliveryOrder.objects.all()
    serializer_class = DeliveryOrderSerializer


class DemandFilter(filters.FilterSet):
    class Meta:
        model = models.Demand
        fields = dict(
            {
                "name": ["exact", "in", "contains"],
                "description": ["exact", "in", "contains"],
                "category": ["exact", "in", "contains"],
                "subcategory": ["exact", "in", "contains"],
                "item": ["exact", "in"],
                "customer": ["exact", "in"],
                "location": ["exact", "in"],
                "due": ["exact", "in", "gt", "gte", "lt", "lte"],
                "status": ["exact", "in"],
                "operation": ["exact", "in"],
                "quantity": ["exact", "in", "gt", "gte", "lt", "lte"],
                "priority": ["exact", "in", "gt", "gte", "lt", "lte"],
                "batch": ["exact", "in", "contains"],
                "delay": ["exact", "in", "gt", "gte", "lt", "lte"],
                "plannedquantity": ["exact", "in", "gt", "gte", "lt", "lte"],
                "deliverydate": ["exact", "in", "gt", "gte", "lt", "lte"],
                "plan": [],
                "minshipment": ["exact", "in", "gt", "gte", "lt", "lte"],
                "maxlateness": ["exact", "in", "gt", "gte", "lt", "lte"],
                "owner": ["exact", "in"],
            },
            **getAttributeAPIFilterDefinition(models.Demand)
        )
        filter_fields = fields.keys()


class DemandSerializer(BulkSerializerMixin, ModelSerializer):
    class Meta:
        model = models.Demand
        fields = (
            "name",
            "description",
            "category",
            "subcategory",
            "item",
            "customer",
            "location",
            "due",
            "status",
            "operation",
            "quantity",
            "priority",
            "batch",
            "delay",
            "plannedquantity",
            "deliverydate",
            "plan",
            "minshipment",
            "maxlateness",
            "owner",
            "policy",
        ) + getAttributeAPIFields(models.Demand)
        read_only_fields = ("lastmodified",) + getAttributeAPIReadOnlyFields(
            models.Demand
        )
        list_serializer_class = BulkListSerializer
        update_lookup_field = "name"
        partial = True


class DemandAPI(frePPleListCreateAPIView):
    queryset = models.Demand.objects.all()
    serializer_class = DemandSerializer
    filter_class = DemandFilter


class DemanddetailAPI(frePPleRetrieveUpdateDestroyAPIView):
    queryset = models.Demand.objects.all()
    serializer_class = DemandSerializer
