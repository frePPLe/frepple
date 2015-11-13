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
import freppledb.common.models


class BucketSerializer(serializers.ModelSerializer):
    class Meta:
      model = freppledb.common.models.Bucket
      fields = ('name', 'description', 'level', 'source', 'lastmodified')
class BucketAPI(frePPleListCreateAPIView):
    queryset = freppledb.common.models.Bucket.objects.all()
    serializer_class = BucketSerializer
class BucketdetailAPI(frePPleRetrieveUpdateDestroyAPIView):
    queryset = freppledb.common.models.Bucket.objects.all()
    serializer_class = BucketSerializer


class BucketDetailSerializer(serializers.ModelSerializer):
    class Meta:
      model = freppledb.common.models.BucketDetail
      fields = ('bucket', 'name', 'startdate', 'enddate', 'source', 'lastmodified')
class BucketDetailAPI(frePPleListCreateAPIView):
    queryset = freppledb.common.models.BucketDetail.objects.all()
    serializer_class = BucketDetailSerializer
class BucketDetaildetailAPI(frePPleRetrieveUpdateDestroyAPIView):
    queryset = freppledb.common.models.BucketDetail.objects.all()
    serializer_class = BucketDetailSerializer


class CommentSerializer(serializers.ModelSerializer):
    class Meta:
      model = freppledb.common.models.Comment
      fields = ('id', 'content_type', 'object_pk', 'content_object', 'comment')
class CommentAPI(frePPleListCreateAPIView):
    queryset = freppledb.common.models.Comment.objects.all()
    serializer_class = CommentSerializer
class CommentdetailAPI(frePPleRetrieveUpdateDestroyAPIView):
    queryset = freppledb.common.models.Comment.objects.all()
    serializer_class = CommentSerializer


class ParameterSerializer(serializers.ModelSerializer):
    class Meta:
      model = freppledb.common.models.Parameter
      fields = ('name', 'value', 'description', 'source', 'lastmodified')
class ParameterAPI(frePPleListCreateAPIView):
    queryset = freppledb.common.models.Parameter.objects.all()
    serializer_class = ParameterSerializer
class ParameterdetailAPI(frePPleRetrieveUpdateDestroyAPIView):
    queryset = freppledb.common.models.Parameter.objects.all()
    serializer_class = ParameterSerializer
