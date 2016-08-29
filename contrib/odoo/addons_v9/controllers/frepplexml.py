# -*- coding: utf-8 -*-
#
# Copyright (C) 2014-2016 by frePPLe bvba
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
import logging
import openerp
from werkzeug.exceptions import MethodNotAllowed, InternalServerError
from werkzeug.wrappers import Response

from openerp.addons.web.controllers.main import db_monodb, ensure_db

from openerp.addons.frepple.controllers.outbound import exporter
from openerp.addons.frepple.controllers.inbound import importer

logger = logging.getLogger(__name__)


class XMLController(openerp.http.Controller):
  
    def authenticate(self, req, database, language=None):
        '''
        Implements HTTP basic authentication.
        '''
        if not 'authorization' in req.httprequest.headers:
            raise Exception("No authentication header")
        authmeth, auth = req.httprequest.headers['authorization'].split(' ', 1)
        if authmeth.lower() != 'basic':
            raise Exception("Unknown authentication method")
        auth = auth.strip().decode('base64')
        user, password = auth.split(':', 1)        
        if not database or not user or not password:
            raise Exception("Missing user, password or database")          
        if not req.session.authenticate(database, user, password):
            raise Exception("Odoo authentication failed")
        if language:
            # If not set we use the default language of the user
            req.session.context['lang'] = language
            

    @openerp.http.route('/frepple/xml',  type='http', auth='none', methods=['POST','GET'])
    def xml(self, **kwargs):
        database = kwargs.get('database', None)
        if not database:
            database = db_monodb()
        req = openerp.http.request
        language = kwargs.get('language', None)
        if req.httprequest.method == 'GET':
            # Login
            database = kwargs.get('database', None)  
            req.session.db = database                    
            try:                          
                self.authenticate(req, database, language)
            except Exception as e:
                return Response(
                    'Login with Odoo user name and password', 401,
                    headers=[('WWW-Authenticate', 'Basic realm="odoo"')]
                    )
            
            # Generate data               
            try:
                xp = exporter(
                  req, 
                  database = database,
                  company = kwargs.get('company', None),
                  mode = kwargs.get('mode', 1)  
                  )
                # TODO Returning an iterator to stream the response back to the client and
                # to save memory on the server side
                return req.make_response(
                    ''.join([i for i in xp.run()]),
                    headers=[
                        ('Content-Type', 'application/xml;charset=utf8'),
                        ('Cache-Control', 'no-cache, no-store, must-revalidate'),
                        ('Pragma', 'no-cache'),
                        ('Expires', '0')
                    ])
            except Exception as e:
                logger.exception('Error generating frePPLe XML data')
                raise InternalServerError(description='Error generating frePPLe XML data: check the Odoo log file for more details')            
        elif req.httprequest.method == 'POST':
            database = req.httprequest.form.get('database', None)
            try:                          
                self.authenticate(req, database, language)
            except Exception as e:
                return Response(
                    'Login with Odoo user name and password', 401,
                    headers=[('WWW-Authenticate', 'Basic realm="odoo"')]
                    )    
            try:                 
                ip = importer(
                  req, 
                  database=database,
                  company=req.httprequest.form.get('company', None),
                  mode=req.httprequest.form.get('mode', 1)
                  )
                return req.make_response(
                    ip.run(),
                    [
                        ('Content-Type', 'text/plain'),
                        ('Cache-Control', 'no-cache, no-store, must-revalidate'),
                        ('Pragma', 'no-cache'),
                        ('Expires', '0')
                    ])
            except Exception as e:
                logger.exception('Error processing data posted by frePPLe')
                raise InternalServerError(description='Error processing data posted by frePPLe: check the Odoo log file for more details')            
        else:
            raise MethodNotAllowed('Only GET and POST requests are accepted')
        