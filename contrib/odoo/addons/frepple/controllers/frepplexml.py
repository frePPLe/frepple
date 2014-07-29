import openerp
from werkzeug.exceptions import MethodNotAllowed

from openerp.addons.frepple.controllers.outbound import exporter
from openerp.addons.frepple.controllers.inbound import importer


class XMLController(openerp.addons.web.http.Controller):
  _cp_path = "/frepple"

  @openerp.addons.web.http.httprequest
  def xml(self, req, **kwargs):
    if req.httprequest.method == 'GET':
      # Returning an iterator to stream the response back to the client and
      # to save memory on the server side
      return req.make_response(
        exporter(req, **kwargs).run(),
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

