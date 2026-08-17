#
# Copyright (C) 2015-2026 by frePPLe bv
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

from rest_framework.renderers import BrowsableAPIRenderer


class freppleBrowsableAPI(BrowsableAPIRenderer):
    """
    Customized rendered for the browsable API:
      - added the 'title' variable to the context to make the breadcrumbs work
    """

    def get_context(self, data, accepted_media_type, renderer_context):
        ctx = super().get_context(data, accepted_media_type, renderer_context)
        serializer_class = getattr(ctx["view"], "serializer_class", None)
        if serializer_class:
            ctx["name"] = serializer_class.Meta.model._meta.model_name
        if hasattr(ctx["view"], "list"):
            ctx["title"] = "List API for %s" % ctx["name"]
        else:
            ctx["title"] = "Detail API for %s" % ctx["name"]
        return ctx

    def get_filter_form(self, data, view, request):
        """
        Returns a dictionary with the filters that are available for this view.
        """
        filterset_class = getattr(view, "filterset_class", None)
        if not filterset_class:
            return None
        filterset = filterset_class(request.GET, queryset=view.get_queryset())
        results = {}
        for filter_name, filter_field in filterset.filters.items():
            form_field = filterset.form[filter_name]
            field_name = filter_field.field_name
            if field_name not in results:
                results[field_name] = {
                    "name": field_name,
                    "label": str(filter_field.label or field_name),
                    "filters": [],
                }
            results[field_name]["filters"].append(
                {"name": filter_name, "lookup_expr": str(filter_field.lookup_expr)}
            )
        return results

    def render(self, data, accepted_media_type=None, renderer_context=None):
        if isinstance(data, list) and renderer_context["request"].method in (
            "POST",
            "PUT",
            "PATCH",
        ):
            # Workaround for a 500-error when posting a list update in the user interface
            data = data[0]
        return super().render(data, accepted_media_type, renderer_context)
