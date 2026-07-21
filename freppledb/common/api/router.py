#
# Copyright (C) 2026 by frePPLe bv
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

from django.db import connections
from django.http import Http404

from rest_framework import views
from rest_framework.routers import DynamicRoute, Route, SimpleRouter


class BulkCompatibleRouter(SimpleRouter):
    """
    Keep frePPLe's collection-level PUT/PATCH/DELETE support while using routers.
    """

    routes = [
        Route(
            url=r"^{prefix}{trailing_slash}$",
            mapping={
                "get": "list",
                "post": "create",
                "put": "update",
                "patch": "partial_update",
                "delete": "bulk_destroy",
            },
            name="{basename}-list",
            detail=False,
            initkwargs={"suffix": "List"},
        ),
        DynamicRoute(
            url=r"^{prefix}/{url_path}{trailing_slash}$",
            name="{basename}-{url_name}",
            detail=False,
            initkwargs={},
        ),
        Route(
            url=r"^{prefix}/{lookup}{trailing_slash}$",
            mapping={
                "get": "retrieve",
                "put": "update",
                "patch": "partial_update",
                "delete": "destroy",
            },
            name="{basename}-detail",
            detail=True,
            initkwargs={"suffix": "Instance"},
        ),
        DynamicRoute(
            url=r"^{prefix}/{lookup}/{url_path}{trailing_slash}$",
            name="{basename}-{url_name}",
            detail=True,
            initkwargs={},
        ),
    ]

    def register(self, app, name, list_api, detail_api):
        class RoutedAPI(list_api):
            # Preserve historic behavior where primary keys can include '/'.
            lookup_value_regex = ".+"

            def _coerce_single_payload_to_bulk(self, request, kwargs):
                payload = request.data
                if isinstance(payload, list):
                    return

                if isinstance(payload, dict) and "pk" in kwargs:
                    unique_fields = getattr(self, "unique_fields", None) or []
                    if unique_fields and unique_fields[0] not in payload:
                        payload = dict(payload)
                        payload[unique_fields[0]] = kwargs["pk"]

                request._full_data = [payload]

            def create(self, request, *args, **kwargs):
                # Keep backward-compatible behavior for collection POST requests:
                # force single-object payloads through the bulk create code path.
                if "pk" not in kwargs and not isinstance(request.data, list):
                    request._full_data = [request.data]
                return list_api.create(self, request, *args, **kwargs)

            def get_object(self):
                # DRF metadata inspects PUT on collection routes during OPTIONS.
                # Return Http404 there so metadata skips object-level action details.
                if "pk" not in self.kwargs:
                    raise Http404
                return detail_api.get_object(self)

            def retrieve(self, request, *args, **kwargs):
                return detail_api.retrieve(self, request, *args, **kwargs)

            def update(self, request, *args, **kwargs):
                if "pk" in kwargs:
                    self._coerce_single_payload_to_bulk(request, kwargs)
                    original_pk = self.kwargs.pop("pk", None)
                    try:
                        return list_api.update(self, request, *args, **kwargs)
                    finally:
                        if original_pk is not None:
                            self.kwargs["pk"] = original_pk
                return list_api.update(self, request, *args, **kwargs)

            def partial_update(self, request, *args, **kwargs):
                if "pk" in kwargs:
                    self._coerce_single_payload_to_bulk(request, kwargs)
                    original_pk = self.kwargs.pop("pk", None)
                    try:
                        return list_api.partial_update(self, request, *args, **kwargs)
                    finally:
                        if original_pk is not None:
                            self.kwargs["pk"] = original_pk
                return list_api.partial_update(self, request, *args, **kwargs)

            def destroy(self, request, *args, **kwargs):
                return detail_api.destroy(self, request, *args, **kwargs)

        super().register(
            f"api/{app}/{name}",
            RoutedAPI,
            basename=f"api-{app}-{name}",
        )


rest_api_router = BulkCompatibleRouter(trailing_slash=True)


# Monkeypatching to work around a DRF inefficiency
def _drf_set_rollback():
    for db in connections.all(initialized_only=True):
        if db.settings_dict["ATOMIC_REQUESTS"] and db.in_atomic_block:
            db.set_rollback(True)


views.set_rollback = _drf_set_rollback
