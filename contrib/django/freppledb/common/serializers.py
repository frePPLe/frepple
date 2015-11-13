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

from django.views.decorators.csrf import csrf_protect, csrf_exempt

import freppledb.common.models


class frePPleListCreateAPIView(generics.ListCreateAPIView):
    def get_queryset(self):
      return super(frePPleListCreateAPIView, self).get_queryset().using(self.request.database)

class frePPleRetrieveUpdateDestroyAPIView(generics.RetrieveUpdateDestroyAPIView):
    def get_queryset(self):
      return super(frePPleRetrieveUpdateDestroyAPIView, self).get_queryset().using(self.request.database)


class BucketSerializer(serializers.ModelSerializer):
    class Meta:
      model = freppledb.common.models.Bucket
      fields = ('name', 'description', 'level', 'source', 'lastmodified')
class BucketREST(frePPleListCreateAPIView):
    queryset = freppledb.common.models.Bucket.objects.all()#.using(request.database)
    serializer_class = BucketSerializer
class BucketdetailREST(frePPleRetrieveUpdateDestroyAPIView):
    queryset = freppledb.common.models.Bucket.objects.all()#.using(request.database)
    serializer_class = BucketSerializer



class BucketDetailSerializer(serializers.ModelSerializer):
    class Meta:
      model = freppledb.common.models.BucketDetail
      fields = ('bucket', 'name', 'startdate', 'enddate', 'source', 'lastmodified')
class BucketDetailREST(frePPleListCreateAPIView):
    queryset = freppledb.common.models.BucketDetail.objects.all()#.using(request.database)
    serializer_class = BucketDetailSerializer
class BucketDetaildetailREST(frePPleRetrieveUpdateDestroyAPIView):
    queryset = freppledb.common.models.BucketDetail.objects.all()#.using(request.database)
    serializer_class = BucketDetailSerializer



class CommentSerializer(serializers.ModelSerializer):
    class Meta:
      model = freppledb.common.models.Comment
      fields = ('id', 'content_type', 'object_pk', 'content_object', 'comment')
class CommentREST(frePPleListCreateAPIView):
    queryset = freppledb.common.models.Comment.objects.all()#.using(request.database)
    serializer_class = CommentSerializer
class CommentdetailREST(frePPleRetrieveUpdateDestroyAPIView):
    queryset = freppledb.common.models.Comment.objects.all()#.using(request.database)
    serializer_class = CommentSerializer


class ParameterSerializer(serializers.ModelSerializer):
    class Meta:
      model = freppledb.common.models.Parameter
      fields = ('name', 'value', 'description', 'source', 'lastmodified')
class ParameterREST(frePPleListCreateAPIView):
    queryset = freppledb.common.models.Parameter.objects.all()#.using(request.database)
    serializer_class = ParameterSerializer
class ParameterdetailREST(frePPleRetrieveUpdateDestroyAPIView):
    queryset = freppledb.common.models.Parameter.objects.all()#.using(request.database)
    serializer_class = ParameterSerializer


class ScenarioSerializer(serializers.ModelSerializer):
    class Meta:
      model = freppledb.common.models.Scenario
      fields = ('name', 'description', 'status', 'lastrefresh')
class ScenarioREST(frePPleListCreateAPIView):
    queryset = freppledb.common.models.Scenario.objects.all()#.using(request.database)
    serializer_class = ScenarioSerializer
class ScenariodetailREST(frePPleRetrieveUpdateDestroyAPIView):
    queryset = freppledb.common.models.Scenario.objects.all()#.using(request.database)
    serializer_class = ScenarioSerializer

