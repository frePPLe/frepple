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
from openerp.osv import osv
from openerp.osv import fields

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

res_company()
