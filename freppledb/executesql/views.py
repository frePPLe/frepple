#
# Copyright (C) 2019 by frePPLe bvba
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

import json
import logging

from django.conf import settings
from django.contrib.admin.views.decorators import staff_member_required
from django.db import connections, transaction
from django.http import (
    StreamingHttpResponse,
    HttpResponseNotAllowed,
    Http404,
    HttpResponseForbidden,
)
from django.shortcuts import render
from django.utils.decorators import method_decorator
from django.utils.translation import gettext as _
from django.views.decorators.cache import never_cache
from django.views.decorators.csrf import csrf_protect
from django.views.generic import View

logger = logging.getLogger(__name__)


class ExecuteSQL(View):

    template = "executesql/executesql.html"
    reportkey = "executesql.executesql"

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
            {"title": _("Execute SQL statements"), "reportkey": reportclass.reportkey},
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
                with connections[request.database].cursor() as cursor:
                    with transaction.atomic():
                        sql = request.read().decode(
                            request.encoding or settings.DEFAULT_CHARSET
                        )
                        cursor.execute(sql=sql)
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
                                        dict(zip(columns, [str(i) for i in result]))
                                    )
                                    first = False
                                else:
                                    yield ",%s" % json.dumps(
                                        dict(zip(columns, [str(i) for i in result]))
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
        if request.method != "POST" or not request.is_ajax():
            raise Http404("Only ajax post requests allowed")

        return StreamingHttpResponse(
            content_type="application/json; charset=%s" % settings.DEFAULT_CHARSET,
            streaming_content=runQuery(),
        )
