# -*- coding: utf-8 -*-
#
# Copyright (C) 2014 by frePPLe bvba
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
import openerp
from werkzeug.exceptions import MethodNotAllowed
from werkzeug.wrappers import Response

from openerp.addons.frepple.controllers.outbound import exporter
from openerp.addons.frepple.controllers.inbound import importer


class XMLController(openerp.addons.web.http.Controller):
  _cp_path = "/frepple"

  @openerp.addons.web.http.httprequest
  def xml(self, req, **kwargs):
    if req.httprequest.method == 'GET':
      # Returning an iterator to stream the response back to the client and
      # to save memory on the server side
      try:
        xp = exporter(req, **kwargs)
      except:
        return Response(
           'Login with Odoo user name and password', 401,
           headers=[('WWW-Authenticate', 'Basic realm="odoo"')]
           )
      return req.make_response(
        xp.run(),
        [
          ('Content-Type', 'application/xml;charset=utf8'),
          ('Cache-Control', 'no-cache, no-store, must-revalidate'),
          ('Pragma', 'no-cache'),
          ('Expires', '0')
        ])
    elif req.httprequest.method == 'POST':
        return req.make_response(
          importer(req, **kwargs).run(),
          [
            ('Content-Type', 'text/plain'),
            ('Cache-Control', 'no-cache, no-store, must-revalidate'),
            ('Pragma', 'no-cache'),
            ('Expires', '0')
          ])
    else:
      raise MethodNotAllowed()
