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
from rest_framework.response import Response
from rest_framework import status, viewsets, generics, permissions, renderers
from rest_framework.decorators import api_view, detail_route

import freppledb.input.models

from django.views.decorators.csrf import csrf_protect, csrf_exempt
from rest_framework.generics import GenericAPIView

class api:
  model = None
  serializer = None

  @classmethod
  @csrf_exempt
  def rest_api(cls, request):
    '''
    All configurable parameters serialized.
    '''
    if request.method == 'GET':
      basequeryset = cls.model.objects.all().using(request.database)
      serializer = cls.serializer(basequeryset, many=True)
      print(serializer, request.database)
      return Response(serializer.data)

    elif request.method == 'POST':
      return Response(serializer.errors)

#===============================================================================
#
# @api_view(['GET', 'POST'])
# class ParameterList_REST(viewsets.ModelViewSet):
#   '''
#   All configurable parameters serialized.
#   '''
#   basequeryset = Parameter.objects.all().using(request.database)
#   serializer_class = serializers.frepple_serializer
#   permission_classes = (permissions.IsAuthenticatedOrReadOnly, IsOwnerOrReadOnly,)
#
#   @detail_route(renderer_classes=[renderers.StaticHTMLRenderer])
#   def highlight(self, request, *args, **kwargs):
#       snippet = self.get_object()
#       return Response(snippet.highlighted)
#
#   def perform_create(self, serializer):
#       serializer.save(owner=self.request.user)
#===============================================================================
#===============================================================================
# from rest_framework import serializers
# import freppledb.common.models
#
#
# class ParameterSerializer(serializers.ModelSerializer): # serializers.ModelSerializer):
#   class Meta:
#       model = freppledb.common.models.Parameter
#       fields = ('name', 'value', 'description')
#
#
#===============================================================================
#===============================================================================
# class frepple_serializer(serializers.ModelSerializer):
#   @classmethod
#   @csrf_exempt
#   def rest(cls, request, args=None):
#     '''
#     All configurable parameters serialized.
#     '''
#     if request.method == 'GET':
#       if args:
#         try:
#           obj = cls.Meta.model.objects.all().using(request.database).get(pk=args)
#         except cls.Meta.model.DoesNotExist:
#           return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
#         serializer = cls(obj)
#       else:
#         basequeryset = cls.Meta.model.objects.all().using(request.database)
#         serializer = cls(basequeryset, many=True)
#         print(serializer, request.database)
#       return Response(serializer.data)
#
#     elif request.method == 'POST':
#       return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
#===============================================================================



class CalendarSerializer(serializers.ModelSerializer):
    class Meta:
      model = freppledb.input.models.Calendar
      fields = ('name', 'description', 'category', 'subcategory', 'defaultvalue', 'source', 'lastmodified')
class CalendarREST(generics.ListCreateAPIView):
    queryset = freppledb.input.models.Calendar.objects.all()#.using(request.database)
    serializer_class = CalendarSerializer
class CalendardetailREST(generics.ListCreateAPIView):
    queryset = freppledb.input.models.Calendar.objects.all()#.using(request.database)
    serializer_class = CalendarSerializer


class CalendarBucketSerializer(serializers.ModelSerializer):
    class Meta:
      model = freppledb.input.models.CalendarBucket
      fields = ('id', 'calendar', 'startdate', 'enddate', 'value', 'priority', 'monday', 'tuesday', 'wednesday',
                'thursday', 'friday', 'saturday', 'sunday', 'starttime', 'endtime', 'source', 'lastmodified')
class CalendarBucketREST(generics.ListCreateAPIView):
    queryset = freppledb.input.models.CalendarBucket.objects.all()#.using(request.database)
    serializer_class = CalendarBucketSerializer
class CalendarBucketdetailREST(generics.ListCreateAPIView):
    queryset = freppledb.input.models.CalendarBucket.objects.all()#.using(request.database)
    serializer_class = CalendarBucketSerializer


class LocationSerializer(serializers.ModelSerializer):
    class Meta:
      model = freppledb.input.models.Location
      fields = ('name', 'description', 'category', 'subcategory', 'available', 'source', 'lastmodified')
class LocationREST(generics.ListCreateAPIView):
    queryset = freppledb.input.models.Location.objects.all()#.using(request.database)
    serializer_class = LocationSerializer
class LocationdetailREST(generics.RetrieveUpdateDestroyAPIView):
    queryset = freppledb.input.models.Location.objects.all()#.using(request.database)
    serializer_class = LocationSerializer

class CustomerSerializer(serializers.ModelSerializer):
    class Meta:
      model = freppledb.input.models.Customer
      fields = ( 'name', 'description', 'category', 'subcategory', 'source', 'lastmodified')
class CustomerREST(generics.ListCreateAPIView):
    queryset = freppledb.input.models.Customer.objects.all()#.using(request.database)
    serializer_class = CustomerSerializer
class CustomerdetailREST(generics.RetrieveUpdateDestroyAPIView):
    queryset = freppledb.input.models.Customer.objects.all()#.using(request.database)
    serializer_class = CustomerSerializer

class ItemSerializer(serializers.ModelSerializer):
    class Meta:
      model = freppledb.input.models.Item
      fields = ('name', 'owner', 'description', 'category', 'subcategory', 'operation', 'price', 'source', 'lastmodified')
class ItemREST(generics.ListCreateAPIView):
    queryset = freppledb.input.models.Item.objects.all()#.using(request.database)
    serializer_class = ItemSerializer
class ItemdetailREST(generics.RetrieveUpdateDestroyAPIView):
    queryset = freppledb.input.models.Item.objects.all()#.using(request.database)
    serializer_class = ItemSerializer

class SupplierSerializer(serializers.ModelSerializer):
    class Meta:
      model = freppledb.input.models.Supplier
      fields = ('name', 'owner', 'description', 'category', 'subcategory', 'source', 'lastmodified')
class SupplierREST(generics.ListCreateAPIView):
    queryset = freppledb.input.models.Supplier.objects.all()#.using(request.database)
    serializer_class = SupplierSerializer
class SupplierdetailREST(generics.RetrieveUpdateDestroyAPIView):
    queryset = freppledb.input.models.Supplier.objects.all()#.using(request.database)
    serializer_class = SupplierSerializer


class ItemSupplierSerializer(serializers.ModelSerializer):
    class Meta:
      model = freppledb.input.models.ItemSupplier
      fields = ('id', 'item', 'location', 'supplier', 'leadtime', 'sizeminimum', 'sizemultiple',
                 'cost', 'priority', 'effective_start', 'effective_end', 'source', 'lastmodified')
class ItemSupplierREST(generics.ListCreateAPIView):
    queryset = freppledb.input.models.ItemSupplier.objects.all()#.using(request.database)
    serializer_class = ItemSupplierSerializer
class ItemSupplierdetailREST(generics.RetrieveUpdateDestroyAPIView):
    queryset = freppledb.input.models.ItemSupplier.objects.all()#.using(request.database)
    serializer_class = ItemSupplierSerializer


class ItemDistributionSerializer(serializers.ModelSerializer):
    class Meta:
      model = freppledb.input.models.ItemDistribution
      fields = ('id', 'item', 'location', 'origin', 'leadtime', 'sizeminimum', 'sizemultiple',
                 'cost', 'priority', 'effective_start', 'effective_end', 'source', 'lastmodified')
class ItemDistributionREST(generics.ListCreateAPIView):
    queryset = freppledb.input.models.ItemDistribution.objects.all()#.using(request.database)
    serializer_class = ItemDistributionSerializer
class ItemDistributiondetailREST(generics.RetrieveUpdateDestroyAPIView):
    queryset = freppledb.input.models.ItemDistribution.objects.all()#.using(request.database)
    serializer_class = ItemDistributionSerializer


class OperationSerializer(serializers.ModelSerializer):
    class Meta:
      model = freppledb.input.models.Operation
      fields = ('name', 'type', 'description', 'category', 'subcategory', 'location', 'fence',
                'posttime', 'sizeminimum', 'sizemultiple', 'sizemaximum',
                 'cost', 'duration', 'duration_per', 'search', 'source', 'lastmodified')
class OperationREST(generics.ListCreateAPIView):
    queryset = freppledb.input.models.Operation.objects.all()#.using(request.database)
    serializer_class = OperationSerializer
class OperationdetailREST(generics.RetrieveUpdateDestroyAPIView):
    queryset = freppledb.input.models.Operation.objects.all()#.using(request.database)
    serializer_class = OperationSerializer


class SubOperationSerializer(serializers.ModelSerializer):
    class Meta:
      model = freppledb.input.models.SubOperation
      fields = ('id','operation', 'priority', 'suboperation', 'effective_start', 'effective_end', 'source', 'lastmodified')
class SubOperationREST(generics.ListCreateAPIView):
    queryset = freppledb.input.models.SubOperation.objects.all()#.using(request.database)
    serializer_class = SubOperationSerializer
class SubOperationdetailREST(generics.RetrieveUpdateDestroyAPIView):
    queryset = freppledb.input.models.SubOperation.objects.all()#.using(request.database)
    serializer_class = SubOperationSerializer


class BufferSerializer(serializers.ModelSerializer):
    class Meta:
      model = freppledb.input.models.Buffer
      fields = ('name', 'description', 'category', 'subcategory', 'type', 'location', 'item',
                'onhand', 'minimum', 'minimum_calendar', 'producing', 'leadtime', 'fence',
                'min_inventory', 'max_inventory', 'min_interval', 'max_interval',
                'size_minimum', 'size_multiple', 'size_maximum', 'source', 'lastmodified')
class BufferREST(generics.ListCreateAPIView):
    queryset = freppledb.input.models.Buffer.objects.all()#.using(request.database)
    serializer_class = BufferSerializer
class BufferdetailREST(generics.RetrieveUpdateDestroyAPIView):
    queryset = freppledb.input.models.Buffer.objects.all()#.using(request.database)
    serializer_class = BufferSerializer



class SetupMatrixSerializer(serializers.ModelSerializer):
    class Meta:
      model = freppledb.input.models.SetupMatrix
      fields = ('name', 'source', 'lastmodified')
class SetupMatrixREST(generics.ListCreateAPIView):
    queryset = freppledb.input.models.SetupMatrix.objects.all()#.using(request.database)
    serializer_class = SetupMatrixSerializer
class SetupMatrixdetailREST(generics.RetrieveUpdateDestroyAPIView):
    queryset = freppledb.input.models.SetupMatrix.objects.all()#.using(request.database)
    serializer_class = SetupMatrixSerializer


class SetupRuleSerializer(serializers.ModelSerializer):
    class Meta:
      model = freppledb.input.models.SetupRule
      fields = ('setupmatrix', 'fromsetup', 'tosetup', 'duration', 'cost')
class SetupRuleREST(generics.ListCreateAPIView):
    queryset = freppledb.input.models.SetupRule.objects.all()#.using(request.database)
    serializer_class = SetupRuleSerializer
class SetupRuledetailREST(generics.RetrieveUpdateDestroyAPIView):
    queryset = freppledb.input.models.SetupRule.objects.all()#.using(request.database)
    serializer_class = SetupRuleSerializer


class ResourceSerializer(serializers.ModelSerializer):
    class Meta:
      model = freppledb.input.models.Resource
      fields = ('name', 'description', 'category', 'subcategory', 'type', 'maximum', 'maximum_calendar',
                'location',  'cost', 'maxearly', 'setupmatrix', 'setup', 'source', 'lastmodified')
class ResourceREST(generics.ListCreateAPIView):
    queryset = freppledb.input.models.Resource.objects.all()#.using(request.database)
    serializer_class = ResourceSerializer
class ResourcedetailREST(generics.RetrieveUpdateDestroyAPIView):
    queryset = freppledb.input.models.Resource.objects.all()#.using(request.database)
    serializer_class = ResourceSerializer


class SkillSerializer(serializers.ModelSerializer):
    class Meta:
      model = freppledb.input.models.Skill
      fields = ('name', 'source', 'lastmodified')
class SkillREST(generics.ListCreateAPIView):
    queryset = freppledb.input.models.Skill.objects.all()#.using(request.database)
    serializer_class = SkillSerializer
class SkilldetailREST(generics.RetrieveUpdateDestroyAPIView):
    queryset = freppledb.input.models.Skill.objects.all()#.using(request.database)
    serializer_class = SkillSerializer


class ResourceSkillSerializer(serializers.ModelSerializer):
    class Meta:
      model = freppledb.input.models.ResourceSkill
      fields = ('id', 'skill', 'effective_start', 'effective_end', 'priority', 'source', 'lastmodified')
class ResourceSkillREST(generics.ListCreateAPIView):
    queryset = freppledb.input.models.ResourceSkill.objects.all()#.using(request.database)
    serializer_class = ResourceSkillSerializer
class ResourceSkilldetailREST(generics.RetrieveUpdateDestroyAPIView):
    queryset = freppledb.input.models.ResourceSkill.objects.all()#.using(request.database)
    serializer_class = ResourceSkillSerializer


class FlowSerializer(serializers.ModelSerializer):
    class Meta:
      model = freppledb.input.models.Flow
      fields = ('id', 'operation', 'thebuffer', 'quantity', 'type', 'effective_start', 'effective_end',
                'name', 'alternate', 'priority', 'search', 'source', 'lastmodified')
class FlowREST(generics.ListCreateAPIView):
    queryset = freppledb.input.models.Flow.objects.all()#.using(request.database)
    serializer_class = FlowSerializer
class FlowdetailREST(generics.RetrieveUpdateDestroyAPIView):
    queryset = freppledb.input.models.Flow.objects.all()#.using(request.database)
    serializer_class = FlowSerializer


class LoadSerializer(serializers.ModelSerializer):
    class Meta:
      model = freppledb.input.models.Load
      fields = ('id', 'operation', 'resource', 'skill', 'quantity', 'effective_start', 'effective_end',
                'name', 'alternate', 'priority', 'setup', 'search', 'source', 'lastmodified')
class LoadREST(generics.ListCreateAPIView):
    queryset = freppledb.input.models.Load.objects.all()#.using(request.database)
    serializer_class = LoadSerializer
class LoaddetailREST(generics.RetrieveUpdateDestroyAPIView):
    queryset = freppledb.input.models.Load.objects.all()#.using(request.database)
    serializer_class = LoadSerializer


class OperationPlanSerializer(serializers.ModelSerializer):
    class Meta:
      model = freppledb.input.models.OperationPlan
      fields = ('id', 'status', 'reference', 'operation', 'quantity', 'startdate', 'enddate',
                'criticality', 'owner', 'source', 'lastmodified')
class OperationPlanREST(generics.ListCreateAPIView):
    queryset = freppledb.input.models.OperationPlan.objects.all()#.using(request.database)
    serializer_class = OperationPlanSerializer
class OperationPlandetailREST(generics.RetrieveUpdateDestroyAPIView):
    queryset = freppledb.input.models.OperationPlan.objects.all()#.using(request.database)
    serializer_class = OperationPlanSerializer


class DistributionOrderSerializer(serializers.ModelSerializer):
    class Meta:
      model = freppledb.input.models.DistributionOrder
      fields = ('id', 'reference', 'status', 'item', 'origin', 'destination', 'quantity',
                'startdate', 'enddate', 'consume_material', 'criticality', 'source', 'lastmodified')
class DistributionOrderREST(generics.ListCreateAPIView):
    queryset = freppledb.input.models.DistributionOrder.objects.all()#.using(request.database)
    serializer_class = DistributionOrderSerializer
class DistributionOrderdetailREST(generics.RetrieveUpdateDestroyAPIView):
    queryset = freppledb.input.models.DistributionOrder.objects.all()#.using(request.database)
    serializer_class = DistributionOrderSerializer


class PurchaseOrderSerializer(serializers.ModelSerializer):
    class Meta:
      model = freppledb.input.models.PurchaseOrder
      fields = ('id', 'reference', 'status', 'item', 'supplier', 'location', 'quantity',
                'startdate', 'enddate', 'criticality', 'source', 'lastmodified')
class PurchaseOrderREST(generics.ListCreateAPIView):
    queryset = freppledb.input.models.PurchaseOrder.objects.all()#.using(request.database)
    serializer_class = PurchaseOrderSerializer
class PurchaseOrderdetailREST(generics.RetrieveUpdateDestroyAPIView):
    queryset = freppledb.input.models.PurchaseOrder.objects.all()#.using(request.database)
    serializer_class = PurchaseOrderSerializer


class DemandSerializer(serializers.ModelSerializer):
    class Meta:
      model = freppledb.input.models.Demand
      fields = ('name', 'description', 'category', 'subcategory', 'item', 'location', 'due',
                'status', 'operation', 'quantity', 'priority', 'minshipment', 'maxlateness')
class DemandREST(generics.ListCreateAPIView):
    queryset = freppledb.input.models.Demand.objects.all()#.using(request.database)
    serializer_class = DemandSerializer
class DemanddetailREST(generics.RetrieveUpdateDestroyAPIView):
    queryset = freppledb.input.models.Demand.objects.all()#.using(request.database)
    serializer_class = DemandSerializer

