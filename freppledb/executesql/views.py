#
# Copyright (C) 2019 by frePPLe bv
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

import json
import logging

from django.conf import settings
from django.contrib.admin.views.decorators import staff_member_required
from django.db import transaction, connections
from django.http import (
    StreamingHttpResponse,
    HttpResponseNotAllowed,
    Http404,
    HttpResponseForbidden,
)
from django.shortcuts import render
from django.utils.decorators import method_decorator
from django.utils.translation import gettext_lazy as _
from django.views.decorators.cache import never_cache
from django.views.decorators.csrf import csrf_protect
from django.views.generic import View

from freppledb.common.utils import get_databases

logger = logging.getLogger(__name__)


class ExecuteSQL(View):
    template = "executesql/executesql.html"
    reportkey = "executesql.executesql"
    help_url = "user-interface/executesql.html"

    @classmethod
    def has_permission(cls, user):
        return user.is_superuser

    @classmethod
    def get(reportclass, request, *args, **kwargs):
        request.prefs = request.user.getPreference(
            reportclass.reportkey, database=request.database
        )
        return render(
            request,
            reportclass.template,
            {
                "title": _("Execute SQL"),
                "reportkey": reportclass.reportkey,
                "reportclass": ExecuteSQL,
            },
        )

    @method_decorator(staff_member_required)
    @method_decorator(csrf_protect)
    @method_decorator(never_cache)
    def dispatch(self, request, *args, **kwargs):
        if not self.has_permission(request.user):
            return HttpResponseForbidden("<h1>%s</h1>" % _("Permission denied"))
        return super().dispatch(request, *args, **kwargs)

    @classmethod
    def post(reportclass, request, *args, **kwargs):
        def runQuery():
            try:
                with connections[
                    (
                        request.database
                        if f"{request.database}_report" not in get_databases(True)
                        else f"{request.database}_report"
                    )
                ].cursor() as cursor:

                    with transaction.atomic():
                        sql = request.read().decode(
                            request.encoding or settings.DEFAULT_CHARSET
                        )
                        cursor.execute(sql)
                        if cursor.description:
                            columns = [desc[0] for desc in cursor.description]
                            yield """{
                              "rowcount": %s,
                              "status": "ok",
                              "columns": %s,
                              "data": [
                            """ % (
                                cursor.rowcount,
                                json.dumps(columns),
                            )
                            first = True
                            for result in cursor.fetchall():
                                if first:
                                    yield json.dumps(
                                        {ind: str(i) for ind, i in enumerate(result)}
                                    )
                                    first = False
                                else:
                                    yield ",%s" % json.dumps(
                                        {ind: str(i) for ind, i in enumerate(result)}
                                    )
                            yield "]}"
                        elif cursor.rowcount:
                            yield '{"rowcount": %s, "status": "Updated %s rows"}' % (
                                cursor.rowcount,
                                cursor.rowcount,
                            )
                        else:
                            yield '{"rowcount": %s, "status": "Done"}' % cursor.rowcount
            except GeneratorExit:
                pass
            except Exception as e:
                yield json.dumps({"status": str(e)})

        # Allow only post from superusers
        if not request.user.is_superuser:
            return HttpResponseNotAllowed(
                ["post"], content="Only a superuser can execute SQL statements"
            )
        if (
            request.method != "POST"
            or request.headers.get("x-requested-with") != "XMLHttpRequest"
        ):
            raise Http404("Only ajax post requests allowed")

        return StreamingHttpResponse(
            content_type="application/json; charset=%s" % settings.DEFAULT_CHARSET,
            streaming_content=runQuery(),
        )
