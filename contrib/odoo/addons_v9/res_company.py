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
import logging
import time

from openerp.osv import osv
from openerp.osv import fields

logger = logging.getLogger(__name__)

try:
   import jwt
except:
   logger.error('PyJWT module has not been installed. Please install the library from https://pypi.python.org/pypi/PyJWT')


class res_company(osv.osv):
  _name = 'res.company'
  _inherit = 'res.company'

  _columns = {
    'manufacturing warehouse': fields.many2one('stock.warehouse', 'Manufacturing warehouse', ondelete='set null'),
    'calendar': fields.many2one('resource.calendar', 'Calendar', ondelete='set null'),
    'cmdline': fields.char('Command line', size=128)
    }

  _defaults = {
    'cmdline': lambda *a: 'frepplectl --env=odoo_read,odoo_write'
    }
    
  def getWebToken(self, cr, uid, context=None):
    # Create an authorization header trusted by frePPLe
    payload = {
      'exp': round(time.time()) + 3600,
      'user': "admin"
      }
    return jwt.encode(payload, "%@mzit!i8b*$zc&6oev96=RANDOMSTRING", algorithm='HS256').decode('ascii')


res_company()
