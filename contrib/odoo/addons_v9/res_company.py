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

from openerp import api, models
from openerp.osv import osv
from openerp.osv import fields

logger = logging.getLogger(__name__)

try:
   import jwt
except:
   logger.error('PyJWT module has not been installed. Please install the library from https://pypi.python.org/pypi/PyJWT')


class res_company(models.Model):
  _name = 'res.company'
  _inherit = 'res.company'

  _columns = {
    'manufacturing_warehouse': fields.many2one('stock.warehouse', 'Manufacturing warehouse', ondelete='set null'),
    'calendar': fields.many2one('resource.calendar', 'Calendar', ondelete='set null'),
    'cmdline': fields.char('Command line', size=128),
    'webtoken_key': fields.char('Webtoken key', size=128),
    'frepple_server': fields.char('frePPLe web server', size=128),
    }

  _defaults = {
    'cmdline': lambda *a: 'frepplectl runplan --env=odoo_read,supply,odoo_write'
    }

  @api.model
  def getFreppleURL(self):
    '''
    Create an authorization header trusted by frePPLe
    '''
    webtoken = jwt.encode({
      'exp': round(time.time()) + 600,
      'user': self.env.user.login,
      'navbar': self.env.context.get("navbar", True)
      },
      self.env.user.company_id.webtoken_key,
      algorithm='HS256').decode('ascii')
    url = self.env.context.get("url", "/")
    logger.warn("%s%s?webtoken=%s" % (self.env.user.company_id.frepple_server, url, webtoken))
    return "%s%s?webtoken=%s" % (self.env.user.company_id.frepple_server, url, webtoken)


res_company()
