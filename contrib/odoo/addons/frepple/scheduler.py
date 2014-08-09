import threading
import os.path
import subprocess

from openerp.osv import fields, osv


class frepple_plan(osv.osv_memory):
    _name = 'frepple.plan'
    _description = 'Create a material and capacity constrained plan'

    _columns = {
        'constrained': fields.boolean('Constrained', help='Run a constrained plan.'),
    }

    _defaults = {
         'constrained': lambda *a: True,
    }

    def _generate_plan(self, cr, uid, ids, context=None):
        """
        @param self: The object pointer.
        @param cr: A database cursor
        @param uid: ID of the user currently logged in
        @param ids: List of IDs selected
        @param context: A standard dictionary
        """
        status = subprocess.call(
          ["frepple", os.path.join(os.path.dirname(os.path.realpath(__file__)), "frepple_commands.py")],
          shell=False
          )
        return {}

    def generate_plan(self, cr, uid, ids, context=None):
        """
        @param self: The object pointer.
        @param cr: A database cursor
        @param uid: ID of the user currently logged in
        @param ids: List of IDs selected
        @param context: A standard dictionary
        """
        threaded_calculation = threading.Thread(target=self._generate_plan, args=(cr, uid, context))
        threaded_calculation.start()
        return {'type': 'ir.actions.act_window_close'}

frepple_plan()
