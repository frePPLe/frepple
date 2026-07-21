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


from django.contrib.admin.views.decorators import staff_member_required
from django.shortcuts import render
from django.utils.translation import gettext_lazy as _
from django.views.decorators.csrf import csrf_protect

from rest_framework import generics, permissions, status
from rest_framework.response import Response
from django_bulk_drf import BulkModelViewSet
from django_filters.rest_framework import DjangoFilterBackend

from freppledb.common.models import User
from freppledb.common.auth import getWebserviceAuthorization


@staff_member_required
@csrf_protect
def APIIndexView(request):
    try:
        exp = int(request.GET.get("exp", "3"))
    except Exception:
        exp = 3
    if exp > 7:
        exp = 7
    return render(
        request,
        "rest_framework/index.html",
        context={
            "exp": exp,
            "url": request.build_absolute_uri(f"{request.prefix}/api/input/demand/"),
            "request": request,
            "title": _("REST API Help"),
            "token": getWebserviceAuthorization(
                user=request.user.username, exp=exp * 86400, database=request.database
            ),
        },
    )


class frepplePermissionClass(permissions.DjangoModelPermissions):
    def has_permission(self, request, view):
        self.perms_map["GET"] = ["%(app_label)s.view_%(model_name)s"]
        self.perms_map["OPTIONS"] = ["%(app_label)s.view_%(model_name)s"]
        self.perms_map["HEAD"] = ["%(app_label)s.view_%(model_name)s"]

        # match the permissions on the correct database
        if not hasattr(request.user, "_state"):
            return False
        request.user._state.db = request.database

        # Django is not checking if user is active or superuser on the scenario
        try:
            thisuser = (
                User.objects.all().using(request.database).get(username=request.user)
            )
            request.user.is_active = thisuser.is_active
            request.user.is_superuser = thisuser.is_superuser
        except Exception:
            request.user.is_active = False
            request.user.is_superuser = False

        return super().has_permission(request, view)


class frePPleBulkModelViewSet(BulkModelViewSet):
    """
    Customized API view for the REST framework:
        - Bulk operations via django-bulk-drf
        - Support for request-specific scenario database (.using(self.request.database))
        - Backward compatibility for query-parameter bulk DELETEs
        - Safety check preventing unintended full-table drops
    """

    filter_backends = (DjangoFilterBackend,)
    permission_classes = (frepplePermissionClass,)

    DEFAULT_ACTIONS = {
        "get": "list",
        "post": "create",
        "put": "update",
        "patch": "partial_update",
        "delete": "bulk_destroy",
    }

    @classmethod
    def as_view(cls, actions=None, **initkwargs):
        if actions is None:
            actions = cls.DEFAULT_ACTIONS
        return super().as_view(actions=actions, **initkwargs)

    def get_queryset(self):
        queryset = super().get_queryset().using(self.request.database)
        return queryset

    def get_serializer(self, *args, **kwargs):
        kwargs["partial"] = True
        return super().get_serializer(*args, **kwargs)

    def allow_bulk_destroy(self, qs, filtered):
        # Safety check to prevent deleting all records in the database table
        return qs.count() > filtered.count()

    def bulk_destroy(self, request, *args, **kwargs):
        if request.query_params:
            # Delete based on query parameters
            qs = self.get_queryset()
            filtered = self.filter_queryset(qs)
            if not self.allow_bulk_destroy(qs, filtered):
                return Response(
                    {
                        "detail": "Bulk delete rejected: query filter matched all records or no items filtered."
                    },
                    status=status.HTTP_400_BAD_REQUEST,
                )
            filtered.delete()
            return Response(status=status.HTTP_204_NO_CONTENT)
        else:
            # Payload body based delete
            return super().bulk_destroy(request, *args, **kwargs)

    def update(self, request, *args, **kwargs):
        """
        Handle PUT/PATCH on collection routes:
        If request data is a list, execute bulk update via super().
        If request data is a single object, wrap it in a list so bulk update processes it
        without requiring a 'pk' in the URL string.
        """
        if not isinstance(request.data, list):
            request._full_data = (
                [request.data] if hasattr(request, "_full_data") else request.data
            )
            # Standardizing input data as list for collection-level update
            if isinstance(request.data, dict):
                kwargs["many"] = True
        return super().update(request, *args, **kwargs)

    def partial_update(self, request, *args, **kwargs):
        """Pass partial=True to update method."""
        kwargs["partial"] = True
        return self.update(request, *args, **kwargs)


class frePPleRetrieveUpdateDestroyAPIView(generics.RetrieveUpdateDestroyAPIView):
    """
    Customized API view for the REST framework.
       - support for request-specific scenario database
       - add 'title' to the context of the html view
    """

    permission_classes = (frepplePermissionClass,)

    def get_queryset(self):
        if self.request.database == "default":
            return super().get_queryset()
        else:
            return super().get_queryset().using(self.request.database)
