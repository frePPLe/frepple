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

from odoo import api, models, fields, exceptions

_logger = logging.getLogger(__name__)

try:
    import jwt
except:
    _logger.error('PyJWT module has not been installed. Please install the library from https://pypi.python.org/pypi/PyJWT')


FREPPLE_CMD = 'frepplectl runplan --env=odoo_read,supply,odoo_write'

class ResCompany(models.Model):
    ''' Company '''

    _name = 'res.company'
    _inherit = 'res.company'

    manufacturing_warehouse = fields.Many2one('stock.warehouse', 'Manufacturing warehouse', ondelete='set null')
    calendar = fields.Many2one('resource.calendar', 'Calendar', ondelete='set null')
    cmdline = fields.Char('Command line', size=128, default=lambda *a: FREPPLE_CMD)
    webtoken_key = fields.Char('Webtoken key', size=128)
    frepple_server = fields.Char('frePPLe web server', size=128)


    @api.model
    def getFreppleURL(self):
        '''
        Create an authorization header trusted by frePPLe
        '''
        user_company_webtoken = self.env.user.company_id.webtoken_key
        if not user_company_webtoken:
          raise exceptions.except_orm("FrePPLe company web token not configured")
        encode_params = dict(exp=round(time.time()) + 600,
                             user=self.env.user.login,
                             navbar=self.env.context.get("navbar", True))
        webtoken = jwt.encode(encode_params,
                              user_company_webtoken,
                              algorithm='HS256').decode('ascii')
        _url = self.env.context.get("url", "/")
        server = self.env.user.company_id.frepple_server
        if not server:
          raise exceptions.except_orm("FrePPLe server utl not configured")
        url = "%s%s?webtoken=%s" % (server, _url, webtoken)
        return url


class MrpConfigSettings(models.TransientModel):
    _name = 'mrp.config.settings'
    _inherit = 'mrp.config.settings'

    manufacturing_warehouse = fields.Many2one(related='company_id.manufacturing_warehouse', string='Manufacturing warehouse')
    calendar = fields.Many2one(related='company_id.calendar', string='Calendar')
    cmdline = fields.Char(related='company_id.cmdline', string='Command line')
    webtoken_key = fields.Char(related='company_id.webtoken_key', string='Webtoken key')
    frepple_server = fields.Char(related='company_id.frepple_server', string='frePPLe web server')
