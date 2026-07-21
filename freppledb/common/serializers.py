#
# Copyright (C) 2015 by frePPLe bv
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
from django_bulk_drf import BulkModelSerializer

from freppledb.common.api.filters import FilterSet
from freppledb.common.api.serializers import (
    getAttributeAPIFields,
    getAttributeAPIReadOnlyFields,
)
from freppledb.common.api.views import (
    frePPleBulkModelViewSet,
    frePPleRetrieveUpdateDestroyAPIView,
)

from . import models


class BucketFilter(FilterSet):
    class Meta:
        model = models.Bucket
        fields = {
            "name": ["exact", "in", "contains"],
            "description": ["exact", "contains"],
            "level": ["exact", "in", "gt", "gte", "lt", "lte"],
            "source": ["exact", "in"],
            "lastmodified": ["exact", "in", "gt", "gte", "lt", "lte"],
        }


class BucketSerializer(BulkModelSerializer):
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


class BucketAPI(frePPleBulkModelViewSet):
    def get_queryset(self):
        return models.Bucket.objects.using(self.request.database).all()

    serializer_class = BucketSerializer
    filterset_class = BucketFilter

    unique_fields = ["name"]


class BucketDetailFilter(FilterSet):
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


class BucketdetailAPI(frePPleRetrieveUpdateDestroyAPIView):
    def get_queryset(self):
        return models.Bucket.objects.using(self.request.database).all()

    serializer_class = BucketSerializer
    filterset_class = BucketFilter


class BucketDetailSerializer(BulkModelSerializer):
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


class BucketDetailAPI(frePPleBulkModelViewSet):
    def get_queryset(self):
        return models.BucketDetail.objects.using(self.request.database).all()

    serializer_class = BucketDetailSerializer
    filterset_class = BucketDetailFilter


class BucketDetaildetailAPI(frePPleRetrieveUpdateDestroyAPIView):
    def get_queryset(self):
        return models.BucketDetail.objects.using(self.request.database).all()

    serializer_class = BucketDetailSerializer
    filterset_class = BucketDetailFilter


class AttributeFilter(FilterSet):
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


class AttributeSerializer(BulkModelSerializer):
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


class AttributeAPI(frePPleBulkModelViewSet):
    def get_queryset(self):
        return models.Attribute.objects.all()

    serializer_class = AttributeSerializer
    filterset_class = AttributeFilter


class AttributedetailAPI(frePPleRetrieveUpdateDestroyAPIView):
    def get_queryset(self):
        return models.Attribute.objects.all()

    serializer_class = AttributeSerializer
    filterset_class = AttributeFilter


class CommentFilter(FilterSet):
    class Meta:
        model = models.Comment
        fields = {
            "id": ["exact", "in", "gt", "gte", "lt", "lte"],
            "object_pk": ["exact", "in", "contains"],
            "comment": ["exact", "contains"],
            "type": ["exact", "in", "contains"],
            "user": ["exact", "gt", "gte", "lt", "lte"],
            "content_type": ["exact", "gt", "gte", "lt", "lte"],
            "lastmodified": ["exact", "in", "gt", "gte", "lt", "lte"],
        }


class CommentSerializer(BulkModelSerializer):
    class Meta:
        model = models.Comment
        fields = (
            "id",
            "object_pk",
            "comment",
            "lastmodified",
            "content_type",
            "user",
            "type",
        )
        read_only_fields = ("lastmodified",)


class CommentAPI(frePPleBulkModelViewSet):
    def get_queryset(self):
        return models.Comment.objects.using(self.request.database).all()

    serializer_class = CommentSerializer
    filterset_class = CommentFilter

    unique_fields = ["id"]


class CommentdetailAPI(frePPleRetrieveUpdateDestroyAPIView):
    def get_queryset(self):
        return models.Comment.objects.using(self.request.database).all()

    serializer_class = CommentSerializer
    filterset_class = CommentFilter


class ParameterFilter(FilterSet):
    class Meta:
        model = models.Parameter
        fields = {
            "name": ["exact", "in", "contains"],
            "description": ["exact", "contains"],
            "value": ["exact", "in", "contains"],
            "source": ["exact", "in"],
            "lastmodified": ["exact", "in", "gt", "gte", "lt", "lte"],
        }


class ParameterSerializer(BulkModelSerializer):
    class Meta:
        model = models.Parameter
        fields = ("name", "source", "lastmodified", "value", "description")
        read_only_fields = ("lastmodified",)


class ParameterAPI(frePPleBulkModelViewSet):
    def get_queryset(self):
        return models.Parameter.objects.using(self.request.database).all()

    serializer_class = ParameterSerializer
    filterset_class = ParameterFilter

    unique_fields = ["name"]


class ParameterdetailAPI(frePPleRetrieveUpdateDestroyAPIView):
    def get_queryset(self):
        return models.Parameter.objects.using(self.request.database).all()

    serializer_class = ParameterSerializer
    filterset_class = ParameterFilter
