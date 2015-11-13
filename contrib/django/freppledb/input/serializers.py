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

from rest_framework import serializers

from freppledb.common.api.views import frePPleListCreateAPIView, frePPleRetrieveUpdateDestroyAPIView
import freppledb.input.models


class CalendarSerializer(serializers.ModelSerializer):
    class Meta:
      model = freppledb.input.models.Calendar
      fields = ('name', 'description', 'category', 'subcategory', 'defaultvalue', 'source', 'lastmodified')
class CalendarAPI(frePPleListCreateAPIView):
    queryset = freppledb.input.models.Calendar.objects.all()
    serializer_class = CalendarSerializer
class CalendardetailAPI(frePPleRetrieveUpdateDestroyAPIView):
    queryset = freppledb.input.models.Calendar.objects.all()
    serializer_class = CalendarSerializer


class CalendarBucketSerializer(serializers.ModelSerializer):
    class Meta:
      model = freppledb.input.models.CalendarBucket
      fields = ('id', 'calendar', 'startdate', 'enddate', 'value', 'priority', 'monday', 'tuesday', 'wednesday',
                'thursday', 'friday', 'saturday', 'sunday', 'starttime', 'endtime', 'source', 'lastmodified')
class CalendarBucketAPI(frePPleListCreateAPIView):
    queryset = freppledb.input.models.CalendarBucket.objects.all()
    serializer_class = CalendarBucketSerializer
class CalendarBucketdetailAPI(frePPleRetrieveUpdateDestroyAPIView):
    queryset = freppledb.input.models.CalendarBucket.objects.all()
    serializer_class = CalendarBucketSerializer


class LocationSerializer(serializers.ModelSerializer):
    class Meta:
      model = freppledb.input.models.Location
      fields = ('name', 'description', 'category', 'subcategory', 'available', 'source', 'lastmodified')
class LocationAPI(frePPleListCreateAPIView):
    queryset = freppledb.input.models.Location.objects.all()
    serializer_class = LocationSerializer
class LocationdetailAPI(frePPleRetrieveUpdateDestroyAPIView):
    queryset = freppledb.input.models.Location.objects.all()
    serializer_class = LocationSerializer


class CustomerSerializer(serializers.ModelSerializer):
    class Meta:
      model = freppledb.input.models.Customer
      fields = ( 'name', 'description', 'category', 'subcategory', 'source', 'lastmodified')
class CustomerAPI(frePPleListCreateAPIView):
    queryset = freppledb.input.models.Customer.objects.all()
    serializer_class = CustomerSerializer
class CustomerdetailAPI(frePPleRetrieveUpdateDestroyAPIView):
    queryset = freppledb.input.models.Customer.objects.all()
    serializer_class = CustomerSerializer


class ItemSerializer(serializers.ModelSerializer):
    class Meta:
      model = freppledb.input.models.Item
      fields = ('name', 'owner', 'description', 'category', 'subcategory', 'operation', 'price', 'source', 'lastmodified')
class ItemAPI(frePPleListCreateAPIView):
    queryset = freppledb.input.models.Item.objects.all()
    serializer_class = ItemSerializer
class ItemdetailAPI(frePPleRetrieveUpdateDestroyAPIView):
    queryset = freppledb.input.models.Item.objects.all()
    serializer_class = ItemSerializer


class SupplierSerializer(serializers.ModelSerializer):
    class Meta:
      model = freppledb.input.models.Supplier
      fields = ('name', 'owner', 'description', 'category', 'subcategory', 'source', 'lastmodified')
class SupplierAPI(frePPleListCreateAPIView):
    queryset = freppledb.input.models.Supplier.objects.all()
    serializer_class = SupplierSerializer
class SupplierdetailAPI(frePPleRetrieveUpdateDestroyAPIView):
    queryset = freppledb.input.models.Supplier.objects.all()
    serializer_class = SupplierSerializer


class ItemSupplierSerializer(serializers.ModelSerializer):
    class Meta:
      model = freppledb.input.models.ItemSupplier
      fields = ('id', 'item', 'location', 'supplier', 'leadtime', 'sizeminimum', 'sizemultiple',
                 'cost', 'priority', 'effective_start', 'effective_end', 'source', 'lastmodified')
class ItemSupplierAPI(frePPleListCreateAPIView):
    queryset = freppledb.input.models.ItemSupplier.objects.all()
    serializer_class = ItemSupplierSerializer
class ItemSupplierdetailAPI(frePPleRetrieveUpdateDestroyAPIView):
    queryset = freppledb.input.models.ItemSupplier.objects.all()
    serializer_class = ItemSupplierSerializer


class ItemDistributionSerializer(serializers.ModelSerializer):
    class Meta:
      model = freppledb.input.models.ItemDistribution
      fields = ('id', 'item', 'location', 'origin', 'leadtime', 'sizeminimum', 'sizemultiple',
                 'cost', 'priority', 'effective_start', 'effective_end', 'source', 'lastmodified')
class ItemDistributionAPI(frePPleListCreateAPIView):
    queryset = freppledb.input.models.ItemDistribution.objects.all()
    serializer_class = ItemDistributionSerializer
class ItemDistributiondetailAPI(frePPleRetrieveUpdateDestroyAPIView):
    queryset = freppledb.input.models.ItemDistribution.objects.all()
    serializer_class = ItemDistributionSerializer


class OperationSerializer(serializers.ModelSerializer):
    class Meta:
      model = freppledb.input.models.Operation
      fields = ('name', 'type', 'description', 'category', 'subcategory', 'location', 'fence',
                'posttime', 'sizeminimum', 'sizemultiple', 'sizemaximum',
                 'cost', 'duration', 'duration_per', 'search', 'source', 'lastmodified')
class OperationAPI(frePPleListCreateAPIView):
    queryset = freppledb.input.models.Operation.objects.all()
    serializer_class = OperationSerializer
class OperationdetailAPI(frePPleRetrieveUpdateDestroyAPIView):
    queryset = freppledb.input.models.Operation.objects.all()
    serializer_class = OperationSerializer


class SubOperationSerializer(serializers.ModelSerializer):
    class Meta:
      model = freppledb.input.models.SubOperation
      fields = ('id','operation', 'priority', 'suboperation', 'effective_start', 'effective_end', 'source', 'lastmodified')
class SubOperationAPI(frePPleListCreateAPIView):
    queryset = freppledb.input.models.SubOperation.objects.all()
    serializer_class = SubOperationSerializer
class SubOperationdetailAPI(frePPleRetrieveUpdateDestroyAPIView):
    queryset = freppledb.input.models.SubOperation.objects.all()
    serializer_class = SubOperationSerializer


class BufferSerializer(serializers.ModelSerializer):
    class Meta:
      model = freppledb.input.models.Buffer
      fields = ('name', 'description', 'category', 'subcategory', 'type', 'location', 'item',
                'onhand', 'minimum', 'minimum_calendar', 'producing', 'leadtime', 'fence',
                'min_inventory', 'max_inventory', 'min_interval', 'max_interval',
                'size_minimum', 'size_multiple', 'size_maximum', 'source', 'lastmodified')
class BufferAPI(frePPleListCreateAPIView):
    queryset = freppledb.input.models.Buffer.objects.all()
    serializer_class = BufferSerializer
class BufferdetailAPI(frePPleRetrieveUpdateDestroyAPIView):
    queryset = freppledb.input.models.Buffer.objects.all()
    serializer_class = BufferSerializer


class SetupMatrixSerializer(serializers.ModelSerializer):
    class Meta:
      model = freppledb.input.models.SetupMatrix
      fields = ('name', 'source', 'lastmodified')
class SetupMatrixAPI(frePPleListCreateAPIView):
    queryset = freppledb.input.models.SetupMatrix.objects.all()
    serializer_class = SetupMatrixSerializer
class SetupMatrixdetailAPI(frePPleRetrieveUpdateDestroyAPIView):
    queryset = freppledb.input.models.SetupMatrix.objects.all()
    serializer_class = SetupMatrixSerializer


class SetupRuleSerializer(serializers.ModelSerializer):
    class Meta:
      model = freppledb.input.models.SetupRule
      fields = ('setupmatrix', 'fromsetup', 'tosetup', 'duration', 'cost')
class SetupRuleAPI(frePPleListCreateAPIView):
    queryset = freppledb.input.models.SetupRule.objects.all()
    serializer_class = SetupRuleSerializer
class SetupRuledetailAPI(frePPleRetrieveUpdateDestroyAPIView):
    queryset = freppledb.input.models.SetupRule.objects.all()
    serializer_class = SetupRuleSerializer


class ResourceSerializer(serializers.ModelSerializer):
    class Meta:
      model = freppledb.input.models.Resource
      fields = ('name', 'description', 'category', 'subcategory', 'type', 'maximum', 'maximum_calendar',
                'location',  'cost', 'maxearly', 'setupmatrix', 'setup', 'source', 'lastmodified')
class ResourceAPI(frePPleListCreateAPIView):
    queryset = freppledb.input.models.Resource.objects.all()
    serializer_class = ResourceSerializer
class ResourcedetailAPI(frePPleRetrieveUpdateDestroyAPIView):
    queryset = freppledb.input.models.Resource.objects.all()
    serializer_class = ResourceSerializer


class SkillSerializer(serializers.ModelSerializer):
    class Meta:
      model = freppledb.input.models.Skill
      fields = ('name', 'source', 'lastmodified')
class SkillAPI(frePPleListCreateAPIView):
    queryset = freppledb.input.models.Skill.objects.all()
    serializer_class = SkillSerializer
class SkilldetailAPI(frePPleRetrieveUpdateDestroyAPIView):
    queryset = freppledb.input.models.Skill.objects.all()
    serializer_class = SkillSerializer


class ResourceSkillSerializer(serializers.ModelSerializer):
    class Meta:
      model = freppledb.input.models.ResourceSkill
      fields = ('id', 'skill', 'effective_start', 'effective_end', 'priority', 'source', 'lastmodified')
class ResourceSkillAPI(frePPleListCreateAPIView):
    queryset = freppledb.input.models.ResourceSkill.objects.all()
    serializer_class = ResourceSkillSerializer
class ResourceSkilldetailAPI(frePPleRetrieveUpdateDestroyAPIView):
    queryset = freppledb.input.models.ResourceSkill.objects.all()
    serializer_class = ResourceSkillSerializer


class FlowSerializer(serializers.ModelSerializer):
    class Meta:
      model = freppledb.input.models.Flow
      fields = ('id', 'operation', 'thebuffer', 'quantity', 'type', 'effective_start', 'effective_end',
                'name', 'alternate', 'priority', 'search', 'source', 'lastmodified')
class FlowAPI(frePPleListCreateAPIView):
    queryset = freppledb.input.models.Flow.objects.all()
    serializer_class = FlowSerializer
class FlowdetailAPI(frePPleRetrieveUpdateDestroyAPIView):
    queryset = freppledb.input.models.Flow.objects.all()
    serializer_class = FlowSerializer


class LoadSerializer(serializers.ModelSerializer):
    class Meta:
      model = freppledb.input.models.Load
      fields = ('id', 'operation', 'resource', 'skill', 'quantity', 'effective_start', 'effective_end',
                'name', 'alternate', 'priority', 'setup', 'search', 'source', 'lastmodified')
class LoadAPI(frePPleListCreateAPIView):
    queryset = freppledb.input.models.Load.objects.all()
    serializer_class = LoadSerializer
class LoaddetailAPI(frePPleRetrieveUpdateDestroyAPIView):
    queryset = freppledb.input.models.Load.objects.all()
    serializer_class = LoadSerializer


class OperationPlanSerializer(serializers.ModelSerializer):
    class Meta:
      model = freppledb.input.models.OperationPlan
      fields = ('id', 'status', 'reference', 'operation', 'quantity', 'startdate', 'enddate',
                'criticality', 'owner', 'source', 'lastmodified')
class OperationPlanAPI(frePPleListCreateAPIView):
    queryset = freppledb.input.models.OperationPlan.objects.all()
    serializer_class = OperationPlanSerializer
class OperationPlandetailAPI(frePPleRetrieveUpdateDestroyAPIView):
    queryset = freppledb.input.models.OperationPlan.objects.all()
    serializer_class = OperationPlanSerializer


class DistributionOrderSerializer(serializers.ModelSerializer):
    class Meta:
      model = freppledb.input.models.DistributionOrder
      fields = ('id', 'reference', 'status', 'item', 'origin', 'destination', 'quantity',
                'startdate', 'enddate', 'consume_material', 'criticality', 'source', 'lastmodified')
class DistributionOrderAPI(frePPleListCreateAPIView):
    queryset = freppledb.input.models.DistributionOrder.objects.all()
    serializer_class = DistributionOrderSerializer
class DistributionOrderdetailAPI(frePPleRetrieveUpdateDestroyAPIView):
    queryset = freppledb.input.models.DistributionOrder.objects.all()
    serializer_class = DistributionOrderSerializer


class PurchaseOrderSerializer(serializers.ModelSerializer):
    class Meta:
      model = freppledb.input.models.PurchaseOrder
      fields = ('id', 'reference', 'status', 'item', 'supplier', 'location', 'quantity',
                'startdate', 'enddate', 'criticality', 'source', 'lastmodified')
class PurchaseOrderAPI(frePPleListCreateAPIView):
    queryset = freppledb.input.models.PurchaseOrder.objects.all()
    serializer_class = PurchaseOrderSerializer
class PurchaseOrderdetailAPI(frePPleRetrieveUpdateDestroyAPIView):
    queryset = freppledb.input.models.PurchaseOrder.objects.all()
    serializer_class = PurchaseOrderSerializer


class DemandSerializer(serializers.ModelSerializer):
    class Meta:
      model = freppledb.input.models.Demand
      fields = ('name', 'description', 'category', 'subcategory', 'item', 'location', 'due',
                'status', 'operation', 'quantity', 'priority', 'minshipment', 'maxlateness')
class DemandAPI(frePPleListCreateAPIView):
    queryset = freppledb.input.models.Demand.objects.all()
    serializer_class = DemandSerializer
class DemanddetailAPI(frePPleRetrieveUpdateDestroyAPIView):
    queryset = freppledb.input.models.Demand.objects.all()
    serializer_class = DemandSerializer
