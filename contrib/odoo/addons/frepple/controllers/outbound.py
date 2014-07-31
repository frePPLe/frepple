# -*- coding: utf-8 -*-
#
# Copyright (C) 2014 by Johan De Taeye, frePPLe bvba
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
from xml.sax.saxutils import quoteattr
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)


class exporter(object):

  calendar_name = "working hours"

  def __init__(self, req, **kwargs):
    self.req = req
    self.database = kwargs.get('database', None)
    authmeth, auth = req.httprequest.headers['authorization'].split(' ', 1)
    if authmeth.lower() != 'basic':
      raise Exception("No authentication header")
    auth = auth.strip().decode('base64')
    self.user, password = auth.split(':', 1)
    if not self.database or not self.user or not password:
      raise Exception("Authentication error")
    if not self.req.session.authenticate(self.database, self.user, password):
      raise Exception("Odoo authentication failed")
    # TODO set the language on the context
    self.language = kwargs.get('language', 'en_US')
    self.company = kwargs.get('company', None)


  def run(self):
    # Load some auxilary data in memory
    self.load_company()
    self.load_uom()

    # Header
    yield '<?xml version="1.0" encoding="UTF-8" ?>\n'
    yield '<plan xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" source="odoo">\n'

    # Main content
    for i in self.export_calendar(): yield i
    for i in self.export_locations(): yield i
    for i in self.export_customers(): yield i
    for i in self.export_workcenters(): yield i
    for i in self.export_items(): yield i
    for i in self.export_boms(): yield i
    for i in self.export_salesorders(): yield i
    for i in self.export_purchaseorders(): yield i
    for i in self.export_manufacturingorders(): yield i
    for i in self.export_orderpoints(): yield i
    for i in self.export_onhand(): yield i

    # Footer
    yield '</plan>\n'


  def load_company(self):
    m = self.req.session.model('res.company')
    ids = m.search([('name','=',self.company)], context=self.req.session.context)
    fields = ['security_lead','po_lead','manufacturing_lead']
    self.company_id = 0
    for i in m.read(ids, fields, self.req.session.context):
      self.company_id = i['id']
      self.security_lead = int(i['security_lead'])
      self.po_lead = i['po_lead']
      self.manufacturing_lead = i['manufacturing_lead']
    if not self.company_id:
      logger.warning("Can't find company '%s'" % self.company)
      self.company_id = None
      self.security_lead = 0
      self.po_lead = 0
      self.manufacturing_lead = 0


  def load_uom(self):
    '''
    Loading units of measures into a dictinary for fast lookups.
    '''
    m = self.req.session.model('product.uom')
    # We also need to load INactive UOMs, because there still might be records
    # using the inactive UOM. Questionable practice, ahum...
    ids = m.search(['|',('active', '=', 1),('active', '=', 0)], context=self.req.session.context)
    fields = ['factor','uom_type','category_id','name']
    self.uom = {}
    for i in m.read(ids, fields, self.req.session.context):
      if i['uom_type'] == 'reference':
        f = 1.0
      elif i['uom_type'] == 'bigger':
        f = i['factor']
      else:
        if i['factor'] > 0:
          f = 1 / i['factor']
        else:
          f = 1.0
      self.uom[i['id']] = {'factor': f, 'category': i['category_id'][0], 'name': i['name']}


  def convert_qty_uom(self, qty, uom_id, product_id=None):
    '''
    Convert a quantity to the reference uom of the product.
    The default implementation doesn't consider the product at all, and just
    converts to the reference unit of the uom category.
    '''
    if not uom_id: return qty
    return qty * self.uom[uom_id]['factor']


  def export_salesorders(self):
    # Get a dict with all shops and their warehouse
    shops = {}
    m = self.req.session.model('sale.shop')
    ids = m.search([], context=self.req.session.context)
    fields = ['name', 'warehouse_id']
    for i in m.read(ids, fields, self.req.session.context):
      shops[i['id']] = i['warehouse_id'][1]

    # Get all sales order lines
    m = self.req.session.model('sale.order.line')
    ids = m.search([('state','=','confirmed')], context=self.req.session.context)
    fields = ['state', 'type', 'product_id', 'product_uom_qty', 'product_uom', 'order_id']
    so_line = [ i for i in m.read(ids, fields, self.req.session.context) ]

    # Get all sales orders
    m = self.req.session.model('sale.order')
    ids = [i['order_id'][0] for i in so_line]
    fields = ['partner_id', 'requested_date', 'date_order', 'picking_policy', 'shop_id']
    # for python 2.7:
    #so = { j['id']: j for j in m.read(ids, fields, self.req.session.context) }
    so = {}
    for i in m.read(ids, fields, self.req.session.context):
      so[i['id']] = i

    # Generate the demand records
    deliveries = set()
    yield '<!-- sales order lines -->\n'
    yield '<demands>\n'
    for i in so_line:
      name = u'%s %d' % (i['order_id'][1], i['id'])
      product = self.product_product.get(i['product_id'][0], None)
      j = so[i['order_id'][0]]
      location = shops.get(j['shop_id'][0], None)
      customer = self.map_customers.get(j['partner_id'][0], None)
      if not customer or not location or not product:
        # Not interested in this sales order...
        continue
      operation = u'Ship %s @ %s' % (product['name'], location)
      buf = u'%s @ %s' % (product['name'], location)
      due = j['requested_date'] or j['date_order']
      qty = i['product_uom_qty'] # self.convert_qty_uom(i['product_uom_qty'], i['product_uom'][0], i['product_id'][0])
      minship = j['picking_policy'] == 'one' and qty or 1.0
      priority = 1
      deliveries.update([(operation,buf,product['name'],location,),])
      yield '<demand name=%s quantity="%s" due="%sT00:00:00" priority="%s" minshipment="%s"><item name=%s/><customer name=%s/><operation name=%s/></demand>\n' % (quoteattr(name), qty, due, priority, minship, quoteattr(product['name']), quoteattr(customer), quoteattr(operation))
    yield '</demands>\n'

    # Create delivery operations
    if deliveries:
      yield '<!-- shipping operations -->\n'
      yield '<operations>\n'
      for i in deliveries:
        yield '<operation name=%s posttime="P%sD"><flows><flow xsi:type="flow_start" quantity="-1"><buffer name=%s><item name=%s/><location name=%s/></buffer></flow></flows></operation>\n' % (quoteattr(i[0]), self.security_lead, quoteattr(i[1]), quoteattr(i[2]), quoteattr(i[3]))
      yield '</operations>\n'


  def export_workcenters(self):
    self.map_workcenters = {}
    m = self.req.session.model('mrp.workcenter')
    ids = m.search([], context=self.req.session.context)
    fields = ['name','costs_hour','capacity_per_cycle','time_cycle']
    if ids:
      yield '<!-- workcenters -->\n'
      yield '<resources>\n'
      for i in m.read(ids, fields, self.req.session.context):
        name = i['name']
        self.map_workcenters[i['id']] = name
        yield '<resource name=%s maximum="%s" cost="%s"/>\n' % (quoteattr(name), i['capacity_per_cycle'] / (i['time_cycle'] or 1), i['costs_hour'])
      yield '</resources>\n'


  def export_customers(self):
    # Extracts customers
    self.map_customers = {}
    m = self.req.session.model('res.partner')
    ids = m.search([('customer','=',True),], context=self.req.session.context)
    if ids:
      yield '<!-- customers -->\n'
      yield '<customers>\n'
      fields = ['name']
      for i in m.read(ids, fields, self.req.session.context):
        name = '%d %s' % (i['id'],i['name'])
        yield '<customer name=%s/>\n' % quoteattr(name)
        self.map_customers[i['id']] = name
      yield '</customers>\n'


  def export_items(self):
    # Extracts products

    # Read the product templates
    self.product_product = {}
    self.procured_buffers = set()
    m = self.req.session.model('product.template')
    fields = ['purchase_ok','procure_method','supply_method','produce_delay','list_price','uom_id']
    ids = m.search([], context=self.req.session.context)
    self.product_templates = {}
    for i in m.read(ids, fields, self.req.session.context):
      self.product_templates[i['id']] = i

    # Read the products
    m = self.req.session.model('product.product')
    ids = m.search([], context=self.req.session.context)
    if ids:
      yield '<!-- products -->\n'
      yield '<items>\n'
      fields = ['name', 'code', 'product_tmpl_id']
      data = [ i for i in m.read(ids, fields, self.req.session.context) ]
      for i in data:
        if i['code']:
          name = u'[%s] %s' % (i['code'], i['name'])
        else:
          name = i['name']
        self.product_product[i['id']] = {'name': name, 'template': i['product_tmpl_id'][0]}
        yield '<item name=%s price="%s" subcategory="%s,%s"/>\n' % (
            quoteattr(name),
            (self.product_templates[i['product_tmpl_id'][0]]['list_price'] or 0) / self.convert_qty_uom(1.0, self.product_templates[i['product_tmpl_id'][0]]['uom_id'][0], i['id']),
            self.product_templates[i['product_tmpl_id'][0]]['uom_id'][0], i['id']
            )
      yield '</items>\n'

      # Create procurement buffers for procured items
      yield '<buffers>\n'
      for i in data:
        tmpl = self.product_templates[i['product_tmpl_id'][0]]
        if tmpl['purchase_ok'] and tmpl['supply_method'] == 'buy':
          for j in self.warehouses:
            buf = u'%s @ %s' % (self.product_product[i['id']]['name'], j)
            self.procured_buffers.add(buf)
            yield '<buffer name=%s leadtime="P%sD" xsi:type="buffer_procure"><item name=%s/><location name=%s/></buffer>\n' % (
              quoteattr(buf), int(tmpl['produce_delay'] + self.po_lead),
              quoteattr(self.product_product[i['id']]['name']), quoteattr(j)
              )
      yield '</buffers>\n'


  def export_locations(self):
    # Extract locations
    self.map_locations = {}
    self.warehouses = set()
    childlocs = {}
    m = self.req.session.model('stock.warehouse')
    ids = m.search([], context=self.req.session.context)
    if ids:
      yield '<!-- warehouses -->\n'
      yield '<locations>\n'
      fields = ['name', 'lot_stock_id', 'lot_input_id', 'lot_output_id']
      for i in m.read(ids, fields, self.req.session.context):
        yield '<location name=%s subcategory="%s"><available name=%s/></location>\n' % (
          quoteattr(i['name']), i['id'], quoteattr(self.calendar_name)
          )
        childlocs[i['lot_stock_id'][0]] = i['name']
        childlocs[i['lot_input_id'][0]] = i['name']
        childlocs[i['lot_output_id'][0]] = i['name']
        self.warehouses.add(i['name'])
      yield '</locations>\n'

      # Populate a mapping location-to-warehouse name for later lookups
      fields = ['child_ids']
      m = self.req.session.model('stock.location')
      ids = m.search([], context=self.req.session.context)
      for j in m.read(childlocs.keys(), fields):
        self.map_locations[j['id']] = childlocs[j['id']]
        for k in j['child_ids']:
          self.map_locations[k] = childlocs[j['id']]


  def export_purchaseorders(self):
    # Get all purchase order lines
    m = self.req.session.model('purchase.order.line')
    ids = m.search([], context=self.req.session.context)
    fields = ['name', 'date_planned', 'product_id', 'product_qty', 'product_uom', 'order_id']
    po_line = [ i for i in m.read(ids, fields, self.req.session.context) ]

    # Get all purchase orders
    m = self.req.session.model('purchase.order')
    ids = [i['order_id'][0] for i in po_line]
    fields = ['name', 'location_id', 'partner_id', 'state', 'shipped']
    # for python 2.7:
    #po = { j['id']: j for j in m.read(ids, fields, self.req.session.context) }
    po = {}
    for i in m.read(ids, fields, self.req.session.context):
      po[i['id']] = i

    # Create purchasing operations
    dd = []
    deliveries = set()
    yield '<!-- purchase operations -->\n'
    yield '<operations>\n'
    for i in po_line:
      if not i['product_id']: continue
      item = self.product_product.get(i['product_id'][0], None)
      j = po[i['order_id'][0]]
      location = j['location_id'] and self.map_locations.get(j['location_id'][0], None) or None
      if location and item and j['state'] in ('approved','draft') and not j['shipped']:
        operation = u'Purchase %s @ %s' % (item['name'], location)
        buf = u'%s @ %s' % (item['name'], location)
        due = i['date_planned']
        qty = self.convert_qty_uom(i['product_qty'], i['product_uom'][0], i['product_id'][0])
        if not buf in deliveries and not buf in self.procured_buffers:
          yield '<operation name=%s><flows><flow xsi:type="flow_end" quantity="1"><buffer name=%s><item name=%s/><location name=%s/></buffer></flow></flows></operation>\n' % (
            quoteattr(operation), quoteattr(buf), quoteattr(item['name']), quoteattr(location)
            )
          deliveries.update([buf,])
        dd.append( (quoteattr(operation), i['id'], due, due, qty) )
    yield '</operations>\n'

    # Create purchasing operationplans
    yield '<!-- open purchase order lines -->\n'
    yield '<operationplans>\n'
    for i in dd:
      yield '<operationplan operation=%s id="%s" start="%sT00:00:00" end="%sT00:00:00" quantity="%s" locked="true"/>\n' % i
    yield '</operationplans>\n'


  def export_calendar(self):
    # Extracts calendar
    yield '<!-- calendar -->\n'
    yield '<calendars>\n'
    yield '<calendar name=%s default="1"><buckets>\n' % quoteattr(self.calendar_name)
    try:
      m = self.req.session.model('hr.holidays.public.line')
      ids = m.search([], context=self.req.session.context)
      fields = ['date']
      for i in m.read(ids, fields, self.req.session.context):
        nd = datetime.strptime(i['date'], '%Y-%m-%d') + timedelta(days=1)
        yield '<bucket start="%sT00:00:00" end="%sT00:00:00" value="0" priority="1"/>\n' % (i['date'], nd.strftime("%Y-%m-%d"))
    except:
      # Exception happens if there hr module is not installed
      yield '<!-- No buckets are exported since the HR module is not installed -->\n'
    yield '</buckets></calendar></calendars>\n'


  def export_boms(self):
    yield '<!-- bills of material -->\n'
    yield '<buffers>\n'
    self.operations = set()

    # Read all active manufacturing routings
    m = self.req.session.model('mrp.routing')
    ids = m.search([], context=self.req.session.context)
    fields = ['location_id',]
    mrp_routings = {}
    for i in m.read(ids, fields, self.req.session.context):
      mrp_routings[i['id']] = i['location_id']

    # Read all workcenters of all routings
    mrp_routing_workcenters = {}
    m = self.req.session.model('mrp.routing.workcenter')
    ids = m.search([], context=self.req.session.context)
    fields = ['routing_id','workcenter_id','sequence','cycle_nbr','hour_nbr',]
    for i in m.read(ids, fields, self.req.session.context):
      if i['routing_id'][0] in mrp_routing_workcenters:
        mrp_routing_workcenters[i['routing_id'][0]].append( (i['workcenter_id'][1], i['cycle_nbr'],) )
      else:
        mrp_routing_workcenters[i['routing_id'][0]] = [ (i['workcenter_id'][1], i['cycle_nbr'],), ]

    # Loop over all "producing" bom records
    m = self.req.session.model('mrp.bom')
    ids = m.search([('bom_id','=',False)], context=self.req.session.context)
    fields = ['name', 'active', 'product_qty', 'product_uom', 'date_start', 'date_stop',
      'product_efficiency', 'product_id', 'routing_id', 'bom_id', 'type', 'sub_products',
      'product_rounding', 'bom_lines']
    fields2 = ['product_qty', 'product_uom', 'date_start', 'date_stop', 'product_id', 'routing_id',
      'type', 'sub_products', 'product_rounding',]
    for i in m.read(ids, fields, self.req.session.context):
      # TODO Handle routing steps
      # Determine the location
      if i['routing_id']:
        location = mrp_routings.get(i['routing_id'][0], None) or "Your Company" #self.odoo_production_location
      else:
        location = "Your Company" #self.odoo_production_location

      # Determine operation name and item
      operation = u'%d %s @ %s' % (i['id'], i['name'], location)
      self.operations.add(operation)
      product = self.product_product.get(i['product_id'][0], None)
      if not product: continue
      buf = u'%s @ %s' % (product['name'], location)
      uom_factor = self.convert_qty_uom(1.0, i['product_uom'][0], i['product_id'][0])

      # Build buffer and its producing operation
      yield '<buffer name=%s><item name=%s/><location name=%s/>\n' % (quoteattr(buf), quoteattr(product['name']), quoteattr(location))
      yield '<producing name=%s size_multiple="%s" xsi:type="operation_fixed_time"><location name=%s/>\n' % (quoteattr(operation), (i['product_rounding'] * uom_factor) or 1, quoteattr(location))
      yield '<flows><flow xsi:type="flow_end" quantity="%s"%s%s><buffer name=%s/></flow>\n' % (i['product_qty'] * i['product_efficiency'] * uom_factor, i['date_start'] and (' effective_start="%s"' % i['date_start']) or "", i['date_stop'] and (' effective_end="%s"' % i['date_stop']) or "", quoteattr(buf))
      for j in m.read(i['bom_lines'], fields2, self.req.session.context):
        product = self.product_product.get(j['product_id'][0], None)
        if not product: continue
        buf = u'%s @ %s' % (product['name'], location)
        qty = self.convert_qty_uom(j['product_qty'], j['product_uom'][0], j['product_id'][0])
        yield '<flow xsi:type="flow_start" quantity="-%s"%s%s><buffer name=%s/></flow>\n' % (qty, j['date_start'] and (' effective_start="%s"' % j['date_start']) or "", j['date_stop'] and (' effective_end="%s"' % j['date_stop']) or "", quoteattr(buf))
      yield '</flows>\n'
      if i['routing_id']:
        yield '<loads>\n'
        for j in mrp_routing_workcenters.get(i['routing_id'][0],[]):
          yield '<load quantity="%s"><resource name=%s/></load>\n' % (j[1], quoteattr(j[0]))
        yield '</loads>\n'
      yield '<duration>P%sD</duration>\n' % int(self.product_templates[self.product_product[i['product_id'][0]]['template']]['produce_delay'] + self.manufacturing_lead)
      yield '</producing></buffer>\n'
    yield '</buffers>\n'


  def export_manufacturingorders(self):
    yield '<!-- manufacturing orders in progress -->\n'
    yield '<operationplans>\n'
    m = self.req.session.model('mrp.production')
    ids = m.search(['|',('state','=','in_production'),('state','=','confirmed')], context=self.req.session.context)
    fields = ['bom_id','date_start','date_planned','name','state','product_qty','product_uom','location_dest_id', 'product_id']
    for i in m.read(ids, fields, self.req.session.context):
      identifier = i['id'] + 1000000   # Adding a million to distinguish POs and MOs
      if i['state'] in ('in_production','confirmed','ready') and i['bom_id']:
        # Open orders
        location = self.map_locations.get(i['location_dest_id'][0],None)
        operation = u'%d %s @ %s' % (i['bom_id'][0], i['bom_id'][1], location)
        try: startdate = datetime.strptime(i['date_start'] or i['date_planned'], '%Y-%m-%d %H:%M:%S')
        except: continue
        if not location or not operation in self.operations: continue
        qty = self.convert_qty_uom(i['product_qty'], i['product_uom'][0], i['product_id'][0])
        yield '<operationplan id="%s" operation=%s start="%s" end="%s" quantity="%s" locked="true"/>\n' % (identifier, quoteattr(operation), startdate, startdate, qty)
    yield '</operationplans>\n'


  def export_orderpoints(self):
    m = self.req.session.model('stock.warehouse.orderpoint')
    ids = m.search([], context=self.req.session.context)
    fields = ['warehouse_id', 'product_id', 'product_min_qty', 'product_max_qty', 'product_uom', 'qty_multiple']
    if ids:
      yield '<!-- order points -->\n'
      yield '<buffers>\n'
      for i in m.read(ids, fields, self.req.session.context):
        item = self.product_product.get(i['product_id'] and i['product_id'][0] or 0, None)
        if not item: continue
        uom_factor = self.convert_qty_uom(1.0, i['product_uom'][0], i['product_id'][0])
        name = u'%s @ %s' % (item['name'], i['warehouse_id'][1])
        if name in self.procured_buffers:
          # Procured material
          yield '<buffer name=%s><item name=%s/><location name=%s/></buffer>' % (quoteattr(name), quoteattr(item['name']), quoteattr(i['warehouse_id'][1]))

      yield '</buffers>\n'
#        TODO if True:
#         else:
#           # Manufactured material
#           yield '<buffer><item name=%s/><location name=%s/></buffer>'
# #         orderpoints.append( (i['product_min_qty']*uom_factor, i['product_min_qty']*uom_factor,
# #           i['product_max_qty']*uom_factor, i['qty_multiple']*uom_factor,
# #           i['product_id'][1], ) )
#       yield '</buffers>'
# #     cursor.executemany(
#       "update buf \
#         set minimum=%s, min_inventory=%s, max_inventory=%s, size_multiple=%s \
#         where item_id=%s and location_id=%s and subcategory='odoo'",
#       orderpoints
#       )


  def export_onhand(self):
    # Get all purchase order lines
    data = {}
    m = self.req.session.model('stock.report.prodlots')
    ids = m.search([('qty','>',0)], context=self.req.session.context)
    fields = ['prodlot_id', 'location_id', 'qty', 'product_id']
    for i in m.read(ids, fields, self.req.session.context):
      location = self.map_locations.get(i['location_id'] and i['location_id'][0] or 0, None)
      item = self.product_product.get(i['product_id'] and i['product_id'][0] or 0, None)
      if location and item:
        name = u'%s @ %s' % (item['name'], location)
        if name in data:
          data[name] = (data[name][0] + i['qty'], item['name'], location)
        else:
          data[name] = (i['qty'], item['name'], location)

    # Output buf inventories
    yield '<!-- inventory -->\n'
    yield '<buffers>\n'
    for i,j in data.iteritems():
      yield '<buffer name=%s onhand="%s"><item name=%s/><location name=%s/></buffer>\n' % (quoteattr(i), j[0], quoteattr(j[1]), quoteattr(j[2]))
    yield '</buffers>\n'
