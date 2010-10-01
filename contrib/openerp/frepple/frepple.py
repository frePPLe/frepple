# -*- encoding: utf-8 -*-

from osv import fields
from osv import osv
from tools.translate import _


class frepple_setupmatrix(osv.osv):
    _name = "frepple.setupmatrix"
    _description = "Setup matrix"
    _columns = {
        'name': fields.char('Name', size=32, required=True),
        'active': fields.boolean('Active'),
        'logic': fields.selection([('max','Order to Max'),('price','Best price (not yet active!)')], 'Reordering Mode', required=True),
        'warehouse_id': fields.many2one('stock.warehouse', 'Warehouse', required=True, ondelete="cascade"),
        'location_id': fields.many2one('stock.location', 'Location', required=True, ondelete="cascade"),
        'product_id': fields.many2one('product.product', 'Product', required=True, domain=[('type','=','product')], ondelete="cascade"),
        'product_uom': fields.many2one('product.uom', 'Product UOM', required=True),
        'product_min_qty': fields.float('Min Quantity', required=True,
            help="When the virtual stock goes belong the Min Quantity, Open ERP generates "\
            "a procurement to bring the virtual stock to the Max Quantity."),
        'product_max_qty': fields.float('Max Quantity', required=True,
            help="When the virtual stock goes belong the Min Quantity, Open ERP generates "\
            "a procurement to bring the virtual stock to the Max Quantity."),
        'qty_multiple': fields.integer('Qty Multiple', required=True,
            help="The procurement quantity will by rounded up to this multiple."),
    }
    _defaults = {
        'active': lambda *a: 1,
        'logic': lambda *a: 'max',
        'qty_multiple': lambda *a: 1,
        'name': lambda x,y,z,c: x.pool.get('ir.sequence').get(y,z,'frepple.setupmatrix') or '',
        'product_uom': lambda sel, cr, uid, context: context.get('product_uom', False),
    }
    
    _sql_constraints = [
        ( 'qty_multiple_check', 'CHECK( qty_multiple > 0 )', _('Qty Multiple must be greater than zero.')),
    ]
    
    def onchange_warehouse_id(self, cr, uid, ids, warehouse_id, context={}):
        if warehouse_id:
            w=self.pool.get('stock.warehouse').browse(cr,uid,warehouse_id, context)
            v = {'location_id':w.lot_stock_id.id}
            return {'value': v}
        return {}
    def onchange_product_id(self, cr, uid, ids, product_id, context={}):
        if product_id:
            prod=self.pool.get('product.product').browse(cr,uid,product_id)
            v = {'product_uom':prod.uom_id.id}
            return {'value': v}
        return {}
    def copy(self, cr, uid, id, default=None,context={}):
        if not default:
            default = {}
        default.update({
            'name': self.pool.get('ir.sequence').get(cr, uid, 'frepple.setupmatrix') or '',
        })
        return super(frepple_setupmatrix, self).copy(cr, uid, id, default, context)
frepple_setupmatrix()


class frepple_product(osv.osv):
    _name = 'product.template'
    _inherit = 'product.template'
    _description = 'frePPLe extension of a product'
    _columns = {
        'frepple_field1': fields.char('Name', size=40),
    }
    _defaults = {
        'frepple_field1': lambda *a: "turbo",
    }
frepple_product()


# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
