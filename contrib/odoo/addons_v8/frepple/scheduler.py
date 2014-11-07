import threading
import os.path
import subprocess

from openerp.osv import fields, osv


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
    status = subprocess.call(
      cmdline,
      shell=False
      )


  def generate_plan(self, cr, uid, ids, context=None):
    for proc in self.browse(cr, uid, ids, context=context):
      threaded_calculation = threading.Thread(
        target=self.run_frepple,
        args=(cr, uid, proc.company.cmdline)
        )
      threaded_calculation.start()
    return {'type': 'ir.actions.act_window_close'}


frepple_plan()
