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
import threading
import subprocess

from odoo import api, models, fields

logger = logging.getLogger(__name__)


class frepple_plan(models.TransientModel):
    '''Frepple plan'''

    _name = 'frepple.plan'
    _description = 'Create a material and capacity constrained plan'

    company = fields.Many2one('res.company', string='Company', index=True)

    @api.model
    def run_frepple(self, cmdline):
        '''
        Action triggered from the scheduler, or launched in a seperate thread
        when planning is triggered manually.
        '''
        logger.info("Start frePPLe planning")
        status = subprocess.call(cmdline, shell=True)
        logger.info("Finished frePPLe planning")

    @api.multi
    def generate_plan(self):
        ''' Generate plan '''
        for proc in self:
            threaded_calculation = threading.Thread(
                target=self.run_frepple,
                args=(self.cr, self.user.id, proc.company.cmdline)
                )
            threaded_calculation.start()
        return {'type': 'ir.actions.act_window_close'}
