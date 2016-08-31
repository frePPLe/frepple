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
import os.path
import subprocess

from openerp import api
from openerp.osv import fields, osv

logger = logging.getLogger(__name__)


class frepple_plan(osv.osv_memory):
  _name = 'frepple.plan'
  _description = 'Create a material and capacity constrained plan'

  _columns = {
    'company': fields.many2one('res.company', 'Company')
    }


  def run_frepple(self, cr, uid, cmdline, context=None):
    '''
    Action triggered from the scheduler, or launched in a seperate thread
    when planning is triggered manually.
    '''
    logger.info("Start frePPLe planning")
    status = subprocess.call(cmdline, shell=True)
    logger.info("Finished frePPLe planning")


  def generate_plan(self, cr, uid, ids, context=None):
    for proc in self.browse(cr, uid, ids, context=context):
      threaded_calculation = threading.Thread(
        target=self.run_frepple,
        args=(cr, uid, proc.company.cmdline)
        )
      threaded_calculation.start()
    return {'type': 'ir.actions.act_window_close'}


frepple_plan()
