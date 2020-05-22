#
# Copyright (C) 2017 by frePPLe bvba
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

from django.contrib.auth.decorators import login_required
from django.http import HttpResponse, HttpResponseServerError
from django.views.decorators.csrf import csrf_protect

import logging

logger = logging.getLogger(__name__)


@login_required
@csrf_protect
def Upload(request):
    try:
        data = json.loads(request.body.decode("utf-8"))
        print(data)
        return HttpResponse("OK")
    except Exception as e:
        logger.error("Can't connect to the ERP: %s" % e)
        return HttpResponseServerError("Can't connect to the ERP")
