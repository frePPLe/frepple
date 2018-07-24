#
# Copyright (C) 2015 by frePPLe bvba
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

from freppledb.common.api.views import frePPleListCreateAPIView, frePPleRetrieveUpdateDestroyAPIView
import freppledb.input.models

from rest_framework_bulk.drf3.serializers import BulkListSerializer, BulkSerializerMixin
from django_filters import rest_framework as filters
from freppledb.common.api.serializers import ModelSerializer


class CalendarFilter(filters.FilterSet):
  class Meta:
    model = freppledb.input.models.Calendar
    fields = {'name': ['exact', 'in', 'contains', ], 'description': ['exact', 'contains', ],
              'category': ['exact', 'contains', ], 'subcategory': ['exact', 'contains', ],
              'defaultvalue': ['exact', 'in', 'gt', 'gte', 'lt', 'lte', ], 'source': ['exact', 'in', ],
              'lastmodified': ['exact', 'in', 'gt', 'gte', 'lt', 'lte', ], }
    filter_fields = ('name', 'description', 'category', 'subcategory', 'defaultvalue', 'source', 'lastmodified')


class CalendarSerializer(BulkSerializerMixin, ModelSerializer):
    class Meta:
      model = freppledb.input.models.Calendar
      fields = ('name', 'description', 'category', 'subcategory', 'defaultvalue', 'source', 'lastmodified')
      list_serializer_class = BulkListSerializer
      update_lookup_field = 'name'
      partial = True


class CalendarAPI(frePPleListCreateAPIView):
    queryset = freppledb.input.models.Calendar.objects.all()
    serializer_class = CalendarSerializer
    filter_class = CalendarFilter


class CalendardetailAPI(frePPleRetrieveUpdateDestroyAPIView):
    queryset = freppledb.input.models.Calendar.objects.all()
    serializer_class = CalendarSerializer


class CalendarBucketFilter(filters.FilterSet):
  class Meta:
    model = freppledb.input.models.CalendarBucket
    fields = {'id': ['exact', 'in', 'gt', 'gte', 'lt', 'lte', ], 'calendar': ['exact', 'in', ],
              'value': ['exact', 'in', 'gt', 'gte', 'lt', 'lte', ], 'priority': ['exact', 'in', 'gt', 'gte', 'lt', 'lte', ],
              'startdate': ['exact', 'in', 'gt', 'gte', 'lt', 'lte', ], 'enddate': ['exact', 'in', 'gt', 'gte', 'lt', 'lte', ],
              'monday': ['exact', ], 'tuesday': ['exact', ], 'wednesday': ['exact', ], 'thursday': ['exact', ],
              'friday': ['exact', ], 'saturday': ['exact', ], 'sunday': ['exact', ], 'starttime': ['exact', 'in', 'gt', 'gte', 'lt', 'lte', ],
              'endtime': ['exact', 'in', 'gt', 'gte', 'lt', 'lte', ], 'source': ['exact', 'in', ],
              'lastmodified': ['exact', 'in', 'gt', 'gte', 'lt', 'lte', ]}

    filter_fields = ('name', 'description', 'category', 'subcategory', 'defaultvalue', 'source', 'lastmodified')


class CalendarBucketSerializer(BulkSerializerMixin, ModelSerializer):
    class Meta:
      model = freppledb.input.models.CalendarBucket
      fields = ('id', 'calendar', 'startdate', 'enddate', 'value', 'priority', 'monday', 'tuesday', 'wednesday',
                'thursday', 'friday', 'saturday', 'sunday', 'starttime', 'endtime', 'source', 'lastmodified')
      list_serializer_class = BulkListSerializer
      update_lookup_field = 'id'
      partial = True


class CalendarBucketAPI(frePPleListCreateAPIView):
    queryset = freppledb.input.models.CalendarBucket.objects.all()
    fields = ('id', 'calendar', 'startdate', 'enddate', 'value', 'priority', 'monday', 'tuesday', 'wednesday',
              'thursday', 'friday', 'saturday', 'sunday', 'starttime', 'endtime', 'source', 'lastmodified')
    serializer_class = CalendarBucketSerializer
    filter_class = CalendarBucketFilter


class CalendarBucketdetailAPI(frePPleRetrieveUpdateDestroyAPIView):
    queryset = freppledb.input.models.CalendarBucket.objects.all()
    serializer_class = CalendarBucketSerializer


class LocationFilter(filters.FilterSet):
  class Meta:
    model = freppledb.input.models.Location
    fields = {
      'name': ['exact', 'in', 'contains'],
      'owner': ['exact', 'in'],
      'description': ['exact', 'contains'],
      'category': ['exact', 'contains'],
      'subcategory': ['exact', 'contains'],
      'available': ['exact', 'in', 'gt', 'gte', 'lt', 'lte'],
      'source': ['exact', 'in'],
      'lastmodified': ['exact', 'in', 'gt', 'gte', 'lt', 'lte'],
      }
    filter_fields = ('name', 'owner', 'description', 'category', 'subcategory', 'available', 'source', 'lastmodified')


class LocationSerializer(BulkSerializerMixin, ModelSerializer):
    class Meta:
      model = freppledb.input.models.Location
      fields = ('name', 'owner', 'description', 'category', 'subcategory', 'available', 'source', 'lastmodified')
      list_serializer_class = BulkListSerializer
      update_lookup_field = 'name'
      partial = True


class LocationAPI(frePPleListCreateAPIView):
    queryset = freppledb.input.models.Location.objects.all()
    serializer_class = LocationSerializer
    filter_class = LocationFilter


class LocationdetailAPI(frePPleRetrieveUpdateDestroyAPIView):
    queryset = freppledb.input.models.Location.objects.all()
    serializer_class = LocationSerializer


class CustomerFilter(filters.FilterSet):
  class Meta:
    model = freppledb.input.models.Customer
    fields = {
      'name': ['exact', 'in', 'contains'],
      'owner': ['exact', 'in'],
      'description': ['exact', 'contains'],
      'category': ['exact', 'contains'],
      'subcategory': ['exact', 'contains'],
      'source': ['exact', 'in'],
      'lastmodified': ['exact', 'in', 'gt', 'gte', 'lt', 'lte'],
      }
    filter_fields = ('name', 'owner', 'description', 'category', 'subcategory', 'available', 'source', 'lastmodified')


class CustomerSerializer(BulkSerializerMixin, ModelSerializer):
    class Meta:
      model = freppledb.input.models.Customer
      fields = ( 'name', 'owner', 'description', 'category', 'subcategory', 'source', 'lastmodified')
      list_serializer_class = BulkListSerializer
      update_lookup_field = 'name'
      partial = True


class CustomerAPI(frePPleListCreateAPIView):
    queryset = freppledb.input.models.Customer.objects.all()
    serializer_class = CustomerSerializer
    filter_class = CustomerFilter


class CustomerdetailAPI(frePPleRetrieveUpdateDestroyAPIView):
    queryset = freppledb.input.models.Customer.objects.all()
    serializer_class = CustomerSerializer


class ItemFilter(filters.FilterSet):
  class Meta:
    model = freppledb.input.models.Item
    fields = {
      'name': ['exact', 'in', 'contains'],
      'owner': ['exact', 'in'],
      'description': ['exact', 'contains'],
      'category': ['exact', 'contains'],
      'subcategory': ['exact', 'contains'],
      'cost': ['exact', 'in', 'gt', 'gte', 'lt', 'lte'],
      'source': ['exact', 'in'],
      'lastmodified': ['exact', 'in', 'gt', 'gte', 'lt', 'lte'],
      }
    filter_fields = ('name', 'owner', 'description', 'category', 'subcategory', 'cost', 'source', 'lastmodified')


class ItemSerializer(BulkSerializerMixin, ModelSerializer):
    class Meta:
      model = freppledb.input.models.Item
      fields = ('name', 'owner', 'description', 'category', 'subcategory', 'cost', 'source', 'lastmodified')
      list_serializer_class = BulkListSerializer
      update_lookup_field = 'name'
      partial = True


class ItemAPI(frePPleListCreateAPIView):
    queryset = freppledb.input.models.Item.objects.all()
    serializer_class = ItemSerializer
    filter_class = ItemFilter


class ItemdetailAPI(frePPleRetrieveUpdateDestroyAPIView):
    queryset = freppledb.input.models.Item.objects.all()
    serializer_class = ItemSerializer


class SupplierFilter(filters.FilterSet):
  class Meta:
    model = freppledb.input.models.Supplier
    fields = {
      'name': ['exact', 'in', 'contains'],
      'owner': ['exact', 'in'],
      'description': ['exact', 'contains'],
      'category': ['exact', 'contains'],
      'subcategory': ['exact', 'contains'],
      'source': ['exact', 'in'],
      'lastmodified': ['exact', 'in', 'gt', 'gte', 'lt', 'lte'],
      }
    filter_fields = ('name', 'description', 'category', 'subcategory', 'available', 'source', 'lastmodified')


class SupplierSerializer(BulkSerializerMixin, ModelSerializer):
    class Meta:
      model = freppledb.input.models.Supplier
      fields = ('name', 'owner', 'description', 'category', 'subcategory', 'source', 'lastmodified')
      list_serializer_class = BulkListSerializer
      update_lookup_field = 'name'
      partial = True


class SupplierAPI(frePPleListCreateAPIView):
    queryset = freppledb.input.models.Supplier.objects.all()
    serializer_class = SupplierSerializer
    filter_fields = ('name', 'owner', 'description', 'category', 'subcategory', 'source', 'lastmodified')
    filter_class = SupplierFilter


class SupplierdetailAPI(frePPleRetrieveUpdateDestroyAPIView):
    queryset = freppledb.input.models.Supplier.objects.all()
    serializer_class = SupplierSerializer


class ItemSupplierFilter(filters.FilterSet):
  class Meta:
    model = freppledb.input.models.ItemSupplier
    fields = {'id': ['exact', 'in', 'gt', 'gte', 'lt', 'lte', ], 'item': ['exact', 'in', ],
              'location': ['exact', 'in', ], 'supplier': ['exact', 'in', ],
              'leadtime': ['exact', 'in', 'gt', 'gte', 'lt', 'lte', ], 'sizeminimum': ['exact', 'in', 'gt', 'gte', 'lt', 'lte', ],
              'sizemultiple': ['exact', 'in', 'gt', 'gte', 'lt', 'lte', ], 'cost': ['exact', 'in', 'gt', 'gte', 'lt', 'lte', ],
              'priority': ['exact', 'in', 'gt', 'gte', 'lt', 'lte', ], 'effective_start': ['exact', 'in', 'gt', 'gte', 'lt', 'lte', ],
              'effective_end': ['exact', 'in', 'gt', 'gte', 'lt', 'lte', ],
              'source': ['exact', 'in', ], 'lastmodified': ['exact', 'in', 'gt', 'gte', 'lt', 'lte', ], }

    filter_fields = ('id', 'item', 'location', 'supplier', 'leadtime', 'sizeminimum', 'sizemultiple',
                     'cost', 'priority', 'effective_start', 'effective_end', 'source', 'lastmodified')


class ItemSupplierSerializer(BulkSerializerMixin, ModelSerializer):
    class Meta:
      model = freppledb.input.models.ItemSupplier
      fields = ('id', 'item', 'location', 'supplier', 'leadtime', 'sizeminimum', 'sizemultiple',
                'cost', 'priority', 'effective_start', 'effective_end', 'source', 'lastmodified')
      list_serializer_class = BulkListSerializer
      update_lookup_field = 'id'
      partial = True


class ItemSupplierAPI(frePPleListCreateAPIView):
    queryset = freppledb.input.models.ItemSupplier.objects.all()
    serializer_class = ItemSupplierSerializer
    filter_class = ItemSupplierFilter


class ItemSupplierdetailAPI(frePPleRetrieveUpdateDestroyAPIView):
    queryset = freppledb.input.models.ItemSupplier.objects.all()
    serializer_class = ItemSupplierSerializer


class ItemDistributionFilter(filters.FilterSet):
  class Meta:
    model = freppledb.input.models.ItemDistribution
    fields = {'id': ['exact', 'in', 'gt', 'gte', 'lt', 'lte', ], 'item': ['exact', 'in', ],
              'location': ['exact', 'in', ], 'origin': ['exact', 'in', ],
              'leadtime': ['exact', 'in', 'gt', 'gte', 'lt', 'lte', ], 'sizeminimum': ['exact', 'in', 'gt', 'gte', 'lt', 'lte', ],
              'sizemultiple': ['exact', 'in', 'gt', 'gte', 'lt', 'lte', ], 'cost': ['exact', 'in', 'gt', 'gte', 'lt', 'lte', ],
              'priority': ['exact', 'in', 'gt', 'gte', 'lt', 'lte', ], 'effective_start': ['exact', 'in', 'gt', 'gte', 'lt', 'lte', ],
              'effective_end': ['exact', 'in', 'gt', 'gte', 'lt', 'lte', ],
              'source': ['exact', 'in', ], 'lastmodified': ['exact', 'in', 'gt', 'gte', 'lt', 'lte', ], }

    filter_fields = ('id', 'item', 'location', 'origin', 'leadtime', 'sizeminimum', 'sizemultiple',
                     'cost', 'priority', 'effective_start', 'effective_end', 'source', 'lastmodified')


class ItemDistributionSerializer(BulkSerializerMixin, ModelSerializer):
    class Meta:
      model = freppledb.input.models.ItemDistribution
      fields = (
        'id', 'item', 'location', 'origin', 'leadtime', 'sizeminimum', 'sizemultiple',
        'cost', 'priority', 'effective_start', 'effective_end', 'source', 'lastmodified'
        )
      list_serializer_class = BulkListSerializer
      update_lookup_field = 'id'
      partial = True


class ItemDistributionAPI(frePPleListCreateAPIView):
    queryset = freppledb.input.models.ItemDistribution.objects.all()
    serializer_class = ItemDistributionSerializer
    filter_class = ItemDistributionFilter


class ItemDistributiondetailAPI(frePPleRetrieveUpdateDestroyAPIView):
    queryset = freppledb.input.models.ItemDistribution.objects.all()
    serializer_class = ItemDistributionSerializer


class OperationFilter(filters.FilterSet):
  class Meta:
    model = freppledb.input.models.Operation
    fields = {'name': ['exact', 'contains', ], 'type': ['exact', 'in', ],
              'category': ['exact', 'contains', ], 'subcategory': ['exact', 'contains', ],
              'location': ['exact', 'in', ], 'item': ['exact', 'in', ],
              'posttime': ['exact', 'in', 'gt', 'gte', 'lt', 'lte', ],
              'fence': ['exact', 'in', 'gt', 'gte', 'lt', 'lte', ],
              'sizeminimum': ['exact', 'in', 'gt', 'gte', 'lt', 'lte', ],
              'sizemultiple': ['exact', 'in', 'gt', 'gte', 'lt', 'lte', ],
              'sizemaximum': ['exact', 'in', 'gt', 'gte', 'lt', 'lte', ],
              'cost': ['exact', 'in', 'gt', 'gte', 'lt', 'lte', ],
              'duration': ['exact', 'in', 'gt', 'gte', 'lt', 'lte', ],
              'duration_per': ['exact', 'in', 'gt', 'gte', 'lt', 'lte', ],
              'search': ['exact', 'in', ],
              'effective_start': ['exact', 'in', 'gt', 'gte', 'lt', 'lte', ],
              'effective_end': ['exact', 'in', 'gt', 'gte', 'lt', 'lte', ],
              'source': ['exact', 'in', ],
              'lastmodified': ['exact', 'in', 'gt', 'gte', 'lt', 'lte', ], }

    filter_fields = (
      'name', 'type', 'description', 'category', 'subcategory', 'item', 'location', 'fence',
      'posttime', 'sizeminimum', 'sizemultiple', 'sizemaximum', 'effective_start', 'effective_end',
      'cost', 'duration', 'duration_per', 'search', 'source', 'lastmodified'
      )


class OperationSerializer(BulkSerializerMixin, ModelSerializer):
  class Meta:
    model = freppledb.input.models.Operation
    fields = (
      'name', 'type', 'description', 'category', 'subcategory', 'item', 'location', 'fence',
      'posttime', 'sizeminimum', 'sizemultiple', 'sizemaximum', 'effective_start', 'effective_end',
      'cost', 'duration', 'duration_per', 'search', 'source', 'lastmodified'
      )
    list_serializer_class = BulkListSerializer
    update_lookup_field = 'name'
    partial = True


class OperationAPI(frePPleListCreateAPIView):
  queryset = freppledb.input.models.Operation.objects.all()
  serializer_class = OperationSerializer
  filter_class = OperationFilter


class OperationdetailAPI(frePPleRetrieveUpdateDestroyAPIView):
  queryset = freppledb.input.models.Operation.objects.all()
  serializer_class = OperationSerializer


class SubOperationFilter(filters.FilterSet):
  class Meta:
    model = freppledb.input.models.SubOperation
    fields = {
      'id': ['exact', 'in', 'gt', 'gte', 'lt', 'lte', ],
      'operation': ['exact', 'in', ],
      'priority': ['exact', 'in', 'gt', 'gte', 'lt', 'lte', ],
      'suboperation': ['exact', 'in', ],
      'effective_start': ['exact', 'in', 'gt', 'gte', 'lt', 'lte', ],
      'effective_end': ['exact', 'in', 'gt', 'gte', 'lt', 'lte', ],
      'source': ['exact', 'in', ],
      'lastmodified': ['exact', 'in', 'gt', 'gte', 'lt', 'lte', ],
      }

    filter_fields = ('id', 'operation', 'priority', 'suboperation', 'effective_start', 'effective_end', 'source', 'lastmodified')


class SubOperationSerializer(BulkSerializerMixin, ModelSerializer):
    class Meta:
      model = freppledb.input.models.SubOperation
      fields = ('id', 'operation', 'priority', 'suboperation', 'effective_start', 'effective_end', 'source', 'lastmodified')
      list_serializer_class = BulkListSerializer
      update_lookup_field = 'id'
      partial = True


class SubOperationAPI(frePPleListCreateAPIView):
    queryset = freppledb.input.models.SubOperation.objects.all()
    serializer_class = SubOperationSerializer
    filter_class = SubOperationFilter


class SubOperationdetailAPI(frePPleRetrieveUpdateDestroyAPIView):
    queryset = freppledb.input.models.SubOperation.objects.all()
    serializer_class = SubOperationSerializer


class BufferFilter(filters.FilterSet):
  class Meta:
    model = freppledb.input.models.Buffer
    fields = {'name': ['exact', 'in', 'contains', ], 'description': ['exact', 'contains', ],
              'category': ['exact', 'contains', ], 'subcategory': ['exact', 'contains', ],
              'type': ['exact', 'in', ], 'location': ['exact', 'in', ], 'item': ['exact', 'in', ],
              'onhand': ['exact', 'in', 'gt', 'gte', 'lt', 'lte', ], 'minimum': ['exact', 'in', 'gt', 'gte', 'lt', 'lte', ],
              'minimum_calendar': ['exact', 'in', 'gt', 'gte', 'lt', 'lte', ], 'min_interval': ['exact', 'in', 'gt', 'gte', 'lt', 'lte', ],
              'source': ['exact', 'in', ], 'lastmodified': ['exact', 'in', 'gt', 'gte', 'lt', 'lte', ], }

    filter_fields = (
      'name', 'description', 'category', 'subcategory', 'type', 'location',
      'item', 'onhand', 'minimum', 'minimum_calendar', 'min_interval',
      'source', 'lastmodified'
      )


class BufferSerializer(BulkSerializerMixin, ModelSerializer):
    class Meta:
      model = freppledb.input.models.Buffer
      fields = (
        'name', 'description', 'category', 'subcategory', 'type', 'location',
        'item', 'onhand', 'minimum', 'minimum_calendar', 'min_interval',
        'source', 'lastmodified'
        )
      list_serializer_class = BulkListSerializer
      update_lookup_field = 'name'
      partial = True


class BufferAPI(frePPleListCreateAPIView):
  queryset = freppledb.input.models.Buffer.objects.all()
  serializer_class = BufferSerializer
  filter_fields = (
    'name', 'description', 'category', 'subcategory', 'type', 'location',
    'item', 'onhand', 'minimum', 'minimum_calendar', 'min_interval',
    'source', 'lastmodified'
    )
  filter_class = BufferFilter


class BufferdetailAPI(frePPleRetrieveUpdateDestroyAPIView):
  queryset = freppledb.input.models.Buffer.objects.all()
  serializer_class = BufferSerializer


class SetupMatrixFilter(filters.FilterSet):
  class Meta:
    model = freppledb.input.models.SetupMatrix
    fields = {'name': ['exact', 'in', 'contains', ],
              'source': ['exact', 'in', ], 'lastmodified': ['exact', 'in', 'gt', 'gte', 'lt', 'lte', ], }

    filter_fields = (
      'name', 'source', 'lastmodified'
      )


class SetupMatrixSerializer(BulkSerializerMixin, ModelSerializer):
  class Meta:
    model = freppledb.input.models.SetupMatrix
    fields = ('name', 'source', 'lastmodified')
    list_serializer_class = BulkListSerializer
    update_lookup_field = 'name'
    partial = True


class SetupMatrixAPI(frePPleListCreateAPIView):
  queryset = freppledb.input.models.SetupMatrix.objects.all()
  serializer_class = SetupMatrixSerializer
  filter_class = SetupMatrixFilter


class SetupMatrixdetailAPI(frePPleRetrieveUpdateDestroyAPIView):
  queryset = freppledb.input.models.SetupMatrix.objects.all()
  serializer_class = SetupMatrixSerializer


class SetupRuleFilter(filters.FilterSet):
  class Meta:
    model = freppledb.input.models.SetupRule
    fields = {
      'id': ['exact', 'in', 'contains', ],
      'setupmatrix': ['exact', 'in', ],
      'fromsetup': ['exact', 'in', ],
      'tosetup': ['exact', 'in', ],
      'priority': ['exact', 'in', 'gt', 'gte', 'lt', 'lte', ],
      'duration': ['exact', 'in', 'gt', 'gte', 'lt', 'lte', ],
      'cost': ['exact', 'in', 'gt', 'gte', 'lt', 'lte', ],
      }

    filter_fields = ('id', 'setupmatrix', 'fromsetup', 'tosetup', 'priority', 'duration', 'cost')


class SetupRuleSerializer(BulkSerializerMixin, ModelSerializer):
  class Meta:
    model = freppledb.input.models.SetupRule
    fields = ('id', 'setupmatrix', 'fromsetup', 'tosetup', 'priority', 'duration', 'cost')
    list_serializer_class = BulkListSerializer
    update_lookup_field = 'setupmatrix'
    partial = True


class SetupRuleAPI(frePPleListCreateAPIView):
  queryset = freppledb.input.models.SetupRule.objects.all()
  serializer_class = SetupRuleSerializer
  filter_class = SetupRuleFilter


class SetupRuledetailAPI(frePPleRetrieveUpdateDestroyAPIView):
  queryset = freppledb.input.models.SetupRule.objects.all()
  serializer_class = SetupRuleSerializer


class ResourceFilter(filters.FilterSet):
  class Meta:
    model = freppledb.input.models.Resource
    fields = {
      'name': ['exact', 'in', 'contains', ], 'description': ['exact', 'contains', ],
      'category': ['exact', 'contains', ], 'subcategory': ['exact', 'contains', ],
      'type': ['exact', 'in', ], 'maximum': ['exact', 'in', 'gt', 'gte', 'lt', 'lte', ],
      'maximum_calendar': ['exact', 'in', 'gt', 'gte', 'lt', 'lte', ], 'location': ['exact', 'in', ],
      'cost': ['exact', 'in', 'gt', 'gte', 'lt', 'lte', ], 'maxearly': ['exact', 'in', 'gt', 'gte', 'lt', 'lte', ],
      'setupmatrix': ['exact', 'in', ], 'setupmatrix': ['exact', 'in', ],
      'source': ['exact', 'in', ], 'lastmodified': ['exact', 'in', 'gt', 'gte', 'lt', 'lte', ],
      }

    filter_fields = ('name', 'description', 'category', 'subcategory', 'type', 'maximum', 'maximum_calendar',
                     'location', 'cost', 'maxearly', 'setupmatrix', 'setup', 'source', 'lastmodified')


class ResourceSerializer(BulkSerializerMixin, ModelSerializer):
  class Meta:
    model = freppledb.input.models.Resource
    fields = (
      'name', 'description', 'category', 'subcategory', 'type', 'maximum',
      'maximum_calendar', 'location', 'cost', 'maxearly', 'setupmatrix',
      'setup', 'efficiency', 'source', 'lastmodified'
      )
    list_serializer_class = BulkListSerializer
    update_lookup_field = 'name'
    partial = True


class ResourceAPI(frePPleListCreateAPIView):
  queryset = freppledb.input.models.Resource.objects.all()
  serializer_class = ResourceSerializer
  filter_class = ResourceFilter


class ResourcedetailAPI(frePPleRetrieveUpdateDestroyAPIView):
  queryset = freppledb.input.models.Resource.objects.all()
  serializer_class = ResourceSerializer


class SkillFilter(filters.FilterSet):
  class Meta:
    model = freppledb.input.models.Skill
    fields = {'name': ['exact', 'in', 'contains', ], 'source': ['exact', 'in', ],
              'lastmodified': ['exact', 'in', 'gt', 'gte', 'lt', 'lte', ], }

    filter_fields = ('name', 'source', 'lastmodified')


class SkillSerializer(BulkSerializerMixin, ModelSerializer):
  class Meta:
    model = freppledb.input.models.Skill
    fields = ('name', 'source', 'lastmodified')
    list_serializer_class = BulkListSerializer
    update_lookup_field = 'name'
    partial = True


class SkillAPI(frePPleListCreateAPIView):
  queryset = freppledb.input.models.Skill.objects.all()
  serializer_class = SkillSerializer
  filter_class = SkillFilter


class SkilldetailAPI(frePPleRetrieveUpdateDestroyAPIView):
  queryset = freppledb.input.models.Skill.objects.all()
  serializer_class = SkillSerializer


class ResourceSkillFilter(filters.FilterSet):
  class Meta:
    model = freppledb.input.models.ResourceSkill
    fields = {
      'id': ['exact', 'in', 'gt', 'gte', 'lt', 'lte', ],
      'resource': ['exact', 'in', ],
      'skill': ['exact', 'in', ],
      'effective_start': ['exact', 'in', 'gt', 'gte', 'lt', 'lte', ],
      'effective_end': ['exact', 'in', 'gt', 'gte', 'lt', 'lte', ],
      'priority': ['exact', 'in', 'gt', 'gte', 'lt', 'lte', ],
      'source': ['exact', 'in', ],
      'lastmodified': ['exact', 'in', 'gt', 'gte', 'lt', 'lte', ]
      }

    filter_fields = ('id', 'resource', 'skill', 'effective_start', 'effective_end', 'priority', 'source', 'lastmodified')


class ResourceSkillSerializer(BulkSerializerMixin, ModelSerializer):
  class Meta:
    model = freppledb.input.models.ResourceSkill
    fields = ('id', 'resource', 'skill', 'effective_start', 'effective_end', 'priority', 'source', 'lastmodified')
    list_serializer_class = BulkListSerializer
    update_lookup_field = 'id'
    partial = True


class ResourceSkillAPI(frePPleListCreateAPIView):
  queryset = freppledb.input.models.ResourceSkill.objects.all()
  serializer_class = ResourceSkillSerializer
  filter_class = ResourceSkillFilter


class ResourceSkilldetailAPI(frePPleRetrieveUpdateDestroyAPIView):
  queryset = freppledb.input.models.ResourceSkill.objects.all()
  serializer_class = ResourceSkillSerializer


class OperationMaterialFilter(filters.FilterSet):
  class Meta:
    model = freppledb.input.models.OperationMaterial
    fields = {
      'id': ['exact', 'in', 'gt', 'gte', 'lt', 'lte', ],
      'quantity': ['exact', 'in', 'gt', 'gte', 'lt', 'lte', ],
      'quantity_fixed': ['exact', 'in', 'gt', 'gte', 'lt', 'lte', ],
      'transferbatch': ['exact', 'in', 'gt', 'gte', 'lt', 'lte', ],
      'operation': ['exact', 'in', ],
      'item': ['exact', 'in', ],
      'type': ['exact', 'in', ],
      'effective_start': ['exact', 'in', 'gt', 'gte', 'lt', 'lte', ],
      'effective_end': ['exact', 'in', 'gt', 'gte', 'lt', 'lte', ],
      'name': ['exact', 'in', 'contains', ],
      'priority': ['exact', 'in', 'gt', 'gte', 'lt', 'lte', ],
      'search': ['exact', 'contains', ],
      'source': ['exact', 'in', ],
      'lastmodified': ['exact', 'in', 'gt', 'gte', 'lt', 'lte', ],
      }

    filter_fields = (
      'id', 'operation', 'item', 'quantity', 'quantity_fixed', 'transferbatch', 'type',
      'effective_start', 'effective_end', 'name', 'priority', 'search',
      'source', 'lastmodified'
      )


class OperationMaterialSerializer(BulkSerializerMixin, ModelSerializer):
    class Meta:
      model = freppledb.input.models.OperationMaterial
      fields = (
        'id', 'operation', 'item', 'quantity', 'quantity_fixed', 'transferbatch', 'type',
        'effective_start', 'effective_end', 'name', 'priority', 'search',
        'source', 'lastmodified'
        )
      list_serializer_class = BulkListSerializer
      update_lookup_field = 'id'
      partial = True


class OperationMaterialAPI(frePPleListCreateAPIView):
    queryset = freppledb.input.models.OperationMaterial.objects.all()
    serializer_class = OperationMaterialSerializer
    filter_class = OperationMaterialFilter


class OperationMaterialdetailAPI(frePPleRetrieveUpdateDestroyAPIView):
    queryset = freppledb.input.models.OperationMaterial.objects.all()
    serializer_class = OperationMaterialSerializer


class OperationResourceFilter(filters.FilterSet):
  class Meta:
    model = freppledb.input.models.OperationResource
    fields = {
      'id': ['exact', 'in', 'gt', 'gte', 'lt', 'lte', ], 'operation': ['exact', 'in', ],
      'resource': ['exact', 'in', ], 'skill': ['exact', 'in', ], 'quantity': ['exact', 'in', 'gt', 'gte', 'lt', 'lte', ],
      'effective_start': ['exact', 'in', 'gt', 'gte', 'lt', 'lte', ], 'effective_end': ['exact', 'in', 'gt', 'gte', 'lt', 'lte', ],
      'name': ['exact', 'in', 'contains', ], 'priority': ['exact', 'in', 'gt', 'gte', 'lt', 'lte', ],
      'search': ['exact', 'contains', ],
      'source': ['exact', 'in', ], 'lastmodified': ['exact', 'in', 'gt', 'gte', 'lt', 'lte', ],
      }

    filter_fields = (
      'id', 'operation', 'resource', 'skill', 'quantity', 'effective_start', 'effective_end',
      'name', 'priority', 'setup', 'search', 'source', 'lastmodified'
      )


class OperationResourceSerializer(BulkSerializerMixin, ModelSerializer):
    class Meta:
      model = freppledb.input.models.OperationResource
      fields = ('id', 'operation', 'resource', 'skill', 'quantity', 'effective_start', 'effective_end',
                'name', 'priority', 'setup', 'search', 'source', 'lastmodified')
      list_serializer_class = BulkListSerializer
      update_lookup_field = 'id'
      partial = True


class OperationResourceAPI(frePPleListCreateAPIView):
    queryset = freppledb.input.models.OperationResource.objects.all()
    serializer_class = OperationResourceSerializer
    filter_class = OperationResourceFilter


class OperationResourcedetailAPI(frePPleRetrieveUpdateDestroyAPIView):
    queryset = freppledb.input.models.OperationResource.objects.all()
    serializer_class = OperationResourceSerializer


class ManufacturingOrderFilter(filters.FilterSet):
  class Meta:
    model = freppledb.input.models.ManufacturingOrder
    fields = {'id': ['exact', 'in', 'gt', 'gte', 'lt', 'lte', ], 'status': ['exact', 'in', ],
              'reference': ['exact', 'in', 'contains', ], 'operation': ['exact', 'in', ],
              'quantity': ['exact', 'in', 'gt', 'gte', 'lt', 'lte', ],
              'startdate': ['exact', 'in', 'gt', 'gte', 'lt', 'lte', ], 'enddate': ['exact', 'in', 'gt', 'gte', 'lt', 'lte', ],
              'criticality': ['exact', 'in', 'gt', 'gte', 'lt', 'lte', ], 'delay': ['exact', 'in', 'gt', 'gte', 'lt', 'lte', ],
              'plan': ['exact', 'in', 'contains', ], 'owner': ['exact', 'in'],
              'source': ['exact', 'in', ], 'lastmodified': ['exact', 'in', 'gt', 'gte', 'lt', 'lte', ], }

    filter_fields = ('id', 'status', 'reference', 'operation', 'quantity', 'startdate', 'enddate',
                     'criticality', 'delay', 'plan', 'owner', 'source', 'lastmodified')


class ManufacturingOrderSerializer(BulkSerializerMixin, ModelSerializer):
    class Meta:
      model = freppledb.input.models.ManufacturingOrder
      fields = ('id', 'status', 'reference', 'operation', 'quantity', 'startdate', 'enddate',
                'criticality', 'delay', 'plan', 'owner', 'source', 'lastmodified')
      list_serializer_class = BulkListSerializer
      update_lookup_field = 'id'
      partial = True


class ManufacturingOrderAPI(frePPleListCreateAPIView):
    queryset = freppledb.input.models.ManufacturingOrder.objects.all()
    serializer_class = ManufacturingOrderSerializer
    filter_class = ManufacturingOrderFilter


class ManufacturingOrderdetailAPI(frePPleRetrieveUpdateDestroyAPIView):
    queryset = freppledb.input.models.ManufacturingOrder.objects.all()
    serializer_class = ManufacturingOrderSerializer


class DistributionOrderFilter(filters.FilterSet):
  class Meta:
    model = freppledb.input.models.DistributionOrder
    fields = {'id': ['exact', 'in', 'gt', 'gte', 'lt', 'lte', ], 'status': ['exact', 'in', ],
              'reference': ['exact', 'in', 'contains', ], 'item': ['exact', 'in', ],
              'origin': ['exact', 'in', ], 'destination': ['exact', 'in', ],
              'quantity': ['exact', 'in', 'gt', 'gte', 'lt', 'lte', ],
              'startdate': ['exact', 'in', 'gt', 'gte', 'lt', 'lte', ], 'enddate': ['exact', 'in', 'gt', 'gte', 'lt', 'lte', ],
              'criticality': ['exact', 'in', 'gt', 'gte', 'lt', 'lte', ], 'delay': ['exact', 'in', 'gt', 'gte', 'lt', 'lte', ],
              'plan': ['exact', 'in', 'contains', ],
              'source': ['exact', 'in', ], 'lastmodified': ['exact', 'in', 'gt', 'gte', 'lt', 'lte', ], }

    filter_fields = ('id', 'status', 'reference', 'item', 'origin', 'destination', 'quantity',
                     'startdate', 'enddate', 'criticality', 'delay', 'plan', 'source', 'lastmodified')


class DistributionOrderSerializer(BulkSerializerMixin, ModelSerializer):
    class Meta:
      model = freppledb.input.models.DistributionOrder
      fields = ('id', 'reference', 'status', 'item', 'origin', 'destination', 'quantity',
                'startdate', 'enddate', 'criticality', 'delay', 'plan', 'source', 'lastmodified')
      list_serializer_class = BulkListSerializer
      update_lookup_field = 'id'
      partial = True


class DistributionOrderAPI(frePPleListCreateAPIView):
    queryset = freppledb.input.models.DistributionOrder.objects.all()
    serializer_class = DistributionOrderSerializer
    filter_class = DistributionOrderFilter


class DistributionOrderdetailAPI(frePPleRetrieveUpdateDestroyAPIView):
    queryset = freppledb.input.models.DistributionOrder.objects.all()
    serializer_class = DistributionOrderSerializer


class PurchaseOrderFilter(filters.FilterSet):
  class Meta:
    model = freppledb.input.models.PurchaseOrder
    fields = {'id': ['exact', 'in', 'gt', 'gte', 'lt', 'lte', ], 'status': ['exact', 'in', ],
              'reference': ['exact', 'in', 'contains', ], 'item': ['exact', 'in', ],
              'supplier': ['exact', 'in', ], 'location': ['exact', 'in', ],
              'quantity': ['exact', 'in', 'gt', 'gte', 'lt', 'lte', ],
              'startdate': ['exact', 'in', 'gt', 'gte', 'lt', 'lte', ], 'enddate': ['exact', 'in', 'gt', 'gte', 'lt', 'lte', ],
              'criticality': ['exact', 'in', 'gt', 'gte', 'lt', 'lte', ], 'delay': ['exact', 'in', 'gt', 'gte', 'lt', 'lte', ],
              'plan': ['exact', 'in', 'contains', ],
              'source': ['exact', 'in', ], 'lastmodified': ['exact', 'in', 'gt', 'gte', 'lt', 'lte', ], }

    filter_fields = ('id', 'reference', 'status', 'item', 'supplier', 'location', 'quantity',
                     'startdate', 'enddate', 'criticality', 'delay', 'plan', 'source', 'lastmodified')


class PurchaseOrderSerializer(BulkSerializerMixin, ModelSerializer):
    class Meta:
      model = freppledb.input.models.PurchaseOrder
      fields = ('id', 'reference', 'status', 'item', 'supplier', 'location', 'quantity',
                'startdate', 'enddate', 'criticality', 'delay', 'plan', 'source', 'lastmodified')
      list_serializer_class = BulkListSerializer
      update_lookup_field = 'id'
      partial = True


class PurchaseOrderAPI(frePPleListCreateAPIView):
    queryset = freppledb.input.models.PurchaseOrder.objects.all()
    serializer_class = PurchaseOrderSerializer
    filter_class = PurchaseOrderFilter


class PurchaseOrderdetailAPI(frePPleRetrieveUpdateDestroyAPIView):
    queryset = freppledb.input.models.PurchaseOrder.objects.all()
    serializer_class = PurchaseOrderSerializer


class DeliveryOrderFilter(filters.FilterSet):
  class Meta:
    model = freppledb.input.models.DeliveryOrder
    fields = {'id': ['exact', 'in', 'gt', 'gte', 'lt', 'lte', ], 'status': ['exact', 'in', ],
              'reference': ['exact', 'in', 'contains', ], 'item': ['exact', 'in', ],
              'demand': ['exact', 'in', ], 'location': ['exact', 'in', ],
              'quantity': ['exact', 'in', 'gt', 'gte', 'lt', 'lte', ],
              'startdate': ['exact', 'in', 'gt', 'gte', 'lt', 'lte', ], 'enddate': ['exact', 'in', 'gt', 'gte', 'lt', 'lte', ],
              'delay': ['exact', 'in', 'gt', 'gte', 'lt', 'lte', ],
              'plan': ['exact', 'in', 'contains', ],
              'source': ['exact', 'in', ], 'lastmodified': ['exact', 'in', 'gt', 'gte', 'lt', 'lte', ], }

    filter_fields = ('id', 'reference', 'status', 'demand', 'item', 'location', 'quantity',
                     'startdate', 'enddate', 'due', 'delay', 'plan', 'source', 'lastmodified')


class DeliveryOrderSerializer(BulkSerializerMixin, ModelSerializer):
    class Meta:
      model = freppledb.input.models.DeliveryOrder
      fields = ('id', 'reference', 'status', 'demand', 'item', 'location', 'quantity',
                'startdate', 'enddate', 'due', 'delay', 'plan', 'source', 'lastmodified')
      list_serializer_class = BulkListSerializer
      update_lookup_field = 'id'
      partial = True


class DeliveryOrderAPI(frePPleListCreateAPIView):
    queryset = freppledb.input.models.DeliveryOrder.objects.all()
    serializer_class = DeliveryOrderSerializer
    filter_class = DeliveryOrderFilter


class DeliveryOrderdetailAPI(frePPleRetrieveUpdateDestroyAPIView):
    queryset = freppledb.input.models.DeliveryOrder.objects.all()
    serializer_class = DeliveryOrderSerializer


class DemandFilter(filters.FilterSet):
  class Meta:
    model = freppledb.input.models.Demand
    fields = {'name': ['exact', 'in', 'contains', ], 'description': ['exact', 'in', 'contains', ],
              'category': ['exact', 'in', 'contains', ], 'subcategory': ['exact', 'in', 'contains', ],
              'item': ['exact', 'in', ], 'customer': ['exact', 'in', ], 'location': ['exact', 'in', ],
              'due': ['exact', 'in', 'gt', 'gte', 'lt', 'lte', ], 'status': ['exact', 'in', ],
              'operation': ['exact', 'in', ], 'quantity': ['exact', 'in', 'gt', 'gte', 'lt', 'lte', ],
              'priority': ['exact', 'in', 'gt', 'gte', 'lt', 'lte', ], 'delay': ['exact', 'in', 'gt', 'gte', 'lt', 'lte', ],
              'plannedquantity': ['exact', 'in', 'gt', 'gte', 'lt', 'lte', ], 'deliverydate': ['exact', 'in', 'gt', 'gte', 'lt', 'lte', ],
              'plan': ['exact', 'in', 'contains', ], 'minshipment': ['exact', 'in', 'gt', 'gte', 'lt', 'lte', ],
              'maxlateness': ['exact', 'in', 'gt', 'gte', 'lt', 'lte', ], }

    filter_fields = ('name', 'description', 'category', 'subcategory', 'item', 'customer', 'location', 'due',
                     'status', 'operation', 'quantity', 'priority', 'delay', 'plannedquantity', 'deliverydate',
                     'plan', 'minshipment', 'maxlateness')


class DemandSerializer(BulkSerializerMixin, ModelSerializer):
    class Meta:
      model = freppledb.input.models.Demand
      fields = ('name', 'description', 'category', 'subcategory', 'item', 'customer', 'location', 'due',
                'status', 'operation', 'quantity', 'priority', 'delay', 'plannedquantity', 'deliverydate', 'plan', 'minshipment', 'maxlateness')
      list_serializer_class = BulkListSerializer
      update_lookup_field = 'name'
      partial = True


class DemandAPI(frePPleListCreateAPIView):
    queryset = freppledb.input.models.Demand.objects.all()
    serializer_class = DemandSerializer
    filter_class = DemandFilter


class DemanddetailAPI(frePPleRetrieveUpdateDestroyAPIView):
    queryset = freppledb.input.models.Demand.objects.all()
    serializer_class = DemandSerializer
