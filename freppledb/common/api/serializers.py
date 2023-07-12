#
# Copyright (C) 2015-2017 by frePPLe bv
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

from rest_framework.serializers import ModelSerializer as DefaultModelSerializer
from rest_framework.validators import UniqueValidator, UniqueTogetherValidator

from freppledb.boot import getAttributes


class ModelSerializer(DefaultModelSerializer):
    """
    The django model serializer extends the default implementation with the
    following capabilities:
      - Ability to work with natural keys.
      - Support for create-or-update on the POST method.
        The default POST method only supports create.
        The PUT method remains update-only.
      - Enable partial updates by default
    """

    def __init__(self, *args, **kwargs):
        DefaultModelSerializer.__init__(self, *args, **kwargs)

        # Cache the name of the primary key
        self.pk = self.Meta.model._meta.pk.name.lower()

        # Cache the natural key
        if hasattr(self.Meta.model.objects, "get_by_natural_key"):
            if self.Meta.model._meta.unique_together:
                self.natural_key = self.Meta.model._meta.unique_together[0]
            elif hasattr(self.Meta.model, "natural_key") and isinstance(
                self.Meta.model.natural_key, tuple
            ):
                self.natural_key = self.Meta.model.natural_key
            else:
                self.natural_key = None
        else:
            self.natural_key = None

        # Strip out the uniqueness validators on primary keys.
        # We don't need them with our find-or-create feature.
        for i in self.fields:
            if i == self.pk or (self.natural_key and i in self.natural_key):
                self.fields[i].required = False
            if i == self.pk:
                self.fields[i].validators = [
                    i
                    for i in self.fields[i].validators
                    if not isinstance(i, UniqueValidator)
                ]

        # Strip out the uniqueness validators on natural keys.
        # We don't need them with our find-or-create feature.
        self.validators = [
            i
            for i in self.validators
            if not isinstance(i, UniqueTogetherValidator)
            or not i.fields == self.natural_key
        ]

    def create(self, validated_data):
        if self.pk in validated_data or not self.natural_key:
            # Find or create based on primary key or models without primary key
            try:
                instance = self.Meta.model.objects.using(
                    self.context["request"].database
                ).get(pk=validated_data[self.pk])
                return super().update(instance, validated_data)
            except (self.Meta.model.DoesNotExist, KeyError):
                return super().create(validated_data)
        else:
            # Find or create using natural keys
            key = []
            for x in self.natural_key:
                key.append(validated_data.get(x, None))
            # Try to find an existing record using the natural key
            try:
                instance = self.Meta.model.objects.get_by_natural_key(*key)
                return super().update(instance, validated_data)
            except self.Meta.model.DoesNotExist:
                return super().create(validated_data)


def getAttributeAPIFilterDefinition(cls):
    flt = {}
    for fld in getAttributes(cls):
        if fld[2] in (
            "number",
            "integer",
            "date",
            "datetime",
            "duration",
            "time",
        ):
            flt[fld[0]] = ["exact", "in", "gt", "gte", "lt", "lte"]
        elif fld[2] == "string":
            flt[fld[0]] = ["exact", "in", "contains"]
        elif fld[2] == "boolean":
            flt[fld[0]] = [
                "exact",
            ]
    return flt


def getAttributeAPIFields(cls):
    return tuple(i[0] for i in getAttributes(cls))


def getAttributeAPIReadOnlyFields(cls):
    return tuple(i[0] for i in getAttributes(cls) if not i[3])
