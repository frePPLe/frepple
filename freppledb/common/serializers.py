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
from rest_framework_bulk.serializers import BulkListSerializer, BulkSerializerMixin

from freppledb.common.api.serializers import (
    ModelSerializer,
    getAttributeAPIFields,
    getAttributeAPIReadOnlyFields,
)
from freppledb.common.api.views import (
    frePPleListCreateAPIView,
    frePPleRetrieveUpdateDestroyAPIView,
)

from . import models


class BucketFilter(filters.FilterSet):
    class Meta:
        model = models.Bucket
        fields = {
            "name": ["exact", "in", "contains"],
            "description": ["exact", "contains"],
            "level": ["exact", "in", "gt", "gte", "lt", "lte"],
            "source": ["exact", "in"],
            "lastmodified": ["exact", "in", "gt", "gte", "lt", "lte"],
        }
        filter_fields = fields.keys()


class BucketSerializer(BulkSerializerMixin, ModelSerializer):
    class Meta:
        model = models.Bucket
        fields = (
            "name",
            "description",
            "level",
            "source",
            "lastmodified",
        ) + getAttributeAPIFields(models.Bucket)
        read_only_fields = ("lastmodified",) + getAttributeAPIReadOnlyFields(
            models.Bucket
        )
        list_serializer_class = BulkListSerializer
        update_lookup_field = "name"
        partial = True


class BucketAPI(frePPleListCreateAPIView):
    queryset = models.Bucket.objects.all()
    serializer_class = BucketSerializer
    filter_class = BucketFilter


class BucketDetailFilter(filters.FilterSet):
    class Meta:
        model = models.BucketDetail
        fields = {
            "bucket": ["exact", "in"],
            "name": ["exact", "in", "contains"],
            "startdate": ["exact", "in", "gt", "gte", "lt", "lte"],
            "enddate": ["exact", "in", "gt", "gte", "lt", "lte"],
            "source": ["exact", "in"],
            "lastmodified": ["exact", "in", "gt", "gte", "lt", "lte"],
        }
        filter_fields = fields.keys()


class BucketdetailAPI(frePPleRetrieveUpdateDestroyAPIView):
    queryset = models.Bucket.objects.all()
    serializer_class = BucketSerializer
    filter_class = BucketFilter


class BucketDetailSerializer(BulkSerializerMixin, ModelSerializer):
    class Meta:
        model = models.BucketDetail
        fields = (
            "bucket",
            "name",
            "startdate",
            "enddate",
            "source",
            "lastmodified",
        ) + getAttributeAPIFields(models.BucketDetail)
        read_only_fields = ("lastmodified",) + getAttributeAPIReadOnlyFields(
            models.BucketDetail
        )


class BucketDetailAPI(frePPleListCreateAPIView):
    queryset = models.BucketDetail.objects.all()
    serializer_class = BucketDetailSerializer
    filter_class = BucketDetailFilter


class BucketDetaildetailAPI(frePPleRetrieveUpdateDestroyAPIView):
    queryset = models.BucketDetail.objects.all()
    serializer_class = BucketDetailSerializer
    filter_class = BucketDetailFilter


class AttributeFilter(filters.FilterSet):
    class Meta:
        model = models.Attribute
        fields = {
            "model": ["exact", "in"],
            "name": ["exact", "in", "contains"],
            "editable": [
                "exact",
            ],
            "initially_hidden": [
                "exact",
            ],
            "source": ["exact", "in"],
            "lastmodified": ["exact", "in", "gt", "gte", "lt", "lte"],
        }
        filter_fields = fields.keys()


class AttributeSerializer(BulkSerializerMixin, ModelSerializer):
    class Meta:
        model = models.Attribute
        fields = (
            "model",
            "name",
            "label",
            "editable",
            "initially_hidden",
            "source",
            "lastmodified",
        )
        read_only_fields = ("lastmodified",)


class AttributeAPI(frePPleListCreateAPIView):
    queryset = models.Attribute.objects.all()
    serializer_class = AttributeSerializer
    filter_class = AttributeFilter


class AttributedetailAPI(frePPleRetrieveUpdateDestroyAPIView):
    queryset = models.Attribute.objects.all()
    serializer_class = AttributeSerializer
    filter_class = AttributeFilter


class CommentSerializer(BulkSerializerMixin, ModelSerializer):
    class Meta:
        model = models.Comment
        fields = ("id", "object_pk", "comment", "lastmodified", "content_type", "user")
        read_only_fields = ("lastmodified",)
        list_serializer_class = BulkListSerializer
        update_lookup_field = "id"
        partial = True


class CommentAPI(frePPleListCreateAPIView):
    queryset = models.Comment.objects.all()
    serializer_class = CommentSerializer


class CommentdetailAPI(frePPleRetrieveUpdateDestroyAPIView):
    queryset = models.Comment.objects.all()
    serializer_class = CommentSerializer


class ParameterFilter(filters.FilterSet):
    class Meta:
        model = models.Parameter
        fields = {
            "name": ["exact", "in", "contains"],
            "description": ["exact", "contains"],
            "value": ["exact", "in", "contains"],
            "source": ["exact", "in"],
            "lastmodified": ["exact", "in", "gt", "gte", "lt", "lte"],
        }
        filter_fields = fields.keys()


class ParameterSerializer(BulkSerializerMixin, ModelSerializer):
    class Meta:
        model = models.Parameter
        fields = ("name", "source", "lastmodified", "value", "description")
        list_serializer_class = BulkListSerializer
        update_lookup_field = "name"
        partial = True


class ParameterAPI(frePPleListCreateAPIView):
    queryset = models.Parameter.objects.all()
    serializer_class = ParameterSerializer
    filter_class = ParameterFilter


class ParameterdetailAPI(frePPleRetrieveUpdateDestroyAPIView):
    queryset = models.Parameter.objects.all()
    serializer_class = ParameterSerializer
    filter_class = ParameterFilter
