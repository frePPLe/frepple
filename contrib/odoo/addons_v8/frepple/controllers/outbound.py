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
from xml.sax.saxutils import quoteattr
from datetime import datetime, timedelta
from operator import itemgetter

from openerp.modules.registry import RegistryManager

logger = logging.getLogger(__name__)


class exporter(object):
    def __init__(self, req, **kwargs):
        self.req = req
        self.database = kwargs.get('database', None)
        authmeth, auth = req.httprequest.headers['authorization'].split(' ', 1)
        if authmeth.lower() != 'basic':
            raise Exception("No authentication header")
        auth = auth.strip().decode('base64')
        user, password = auth.split(':', 1)
        if not self.database or not user or not password:
            raise Exception("Authentication error")
        if not self.req.session.authenticate(self.database, user, password):
            raise Exception("Odoo authentication failed")
        if 'language' in kwargs:
            # If not set we use the default language of the user
            self.req.session.context['lang'] = kwargs['language']
        self.company = kwargs.get('company', None)

        # The mode argument defines differen types of runs:
        #  - Mode 1:
        #    This mode returns all data that is loaded with every planning run.
        #    Currently this mode transfers all objects, except closed sales orders.
        #  - Mode 2:
        #    This mode returns data that is loaded that changes infrequently and
        #    can be transferred during automated scheduled runs at a quiet moment.
        #    Currently this mode transfers only closed sales orders.
        #
        # Normally an Odoo object should be exported by only a single mode.
        # Exporting a certain object with BOTH modes 1 and 2 will only create extra
        # processing time for the connector without adding any benefits. On the other
        # hand it won't break things either.
        #
        # Which data elements belong to each mode can vary between implementations.
        self.mode = kwargs.get('mode', 1)


    def run(self):
        # Load some auxiliary data in memory
        self.load_company()
        self.load_uom()

        # Header.
        # The source attribute is set to 'odoo_<mode>', such that all objects created or
        # updated from the data are also marked as from originating from odoo.
        yield '<?xml version="1.0" encoding="UTF-8" ?>\n'
        yield '<plan xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" source="odoo_%s">\n' % self.mode

        # Main content.
        # The order of the entities is important. First one needs to create the
        # objects before they are referenced by other objects.
        # If multiple types of an entity exists (eg operation_time_per,
        # operation_alternate, operation_alternate, etc) the reference would
        # automatically create an object, potentially of the wrong type.
        if self.mode == 1:
            for i in self.export_calendar():
                yield i
        for i in self.export_locations():  # tuyo
            yield i
        for i in self.export_customers():
            yield i
        if self.mode == 1:
            for i in self.export_suppliers():
                yield i
            for i in self.export_workcenters():
                yield i
        for i in self.export_items():
            yield i
        if self.mode == 1:
            for i in self.export_boms():
                yield i
        for i in self.export_salesorders():
            yield i
        if self.mode == 1:
            for i in self.export_purchaseorders():
                yield i
            for i in self.export_manufacturingorders():
                yield i
            for i in self.export_orderpoints():
                yield i
            for i in self.export_onhand():
                yield i

        # Footer
        yield '</plan>\n'


    def load_company(self):
        m = self.req.session.model('res.company')
        ids = m.search([('name', '=', self.company)], context=self.req.session.context)
        fields = ['security_lead', 'po_lead', 'manufacturing_lead', 'calendar', 'manufacturing warehouse']
        self.company_id = 0
        for i in m.read(ids, fields, self.req.session.context):
            self.company_id = i['id']
            self.security_lead = int(i['security_lead'])
            self.po_lead = i['po_lead']
            self.manufacturing_lead = i['manufacturing_lead']
            self.calendar = i['calendar'] and i['calendar'][1] or "Working hours"
            self.mfg_location = i['manufacturing warehouse'] and i['manufacturing warehouse'][1] or self.company
        if not self.company_id:
            logger.warning("Can't find company '%s'" % self.company)
            self.company_id = None
            self.security_lead = 0
            self.po_lead = 0
            self.manufacturing_lead = 0
            self.calendar = "Working hours"
            self.mfg_location = self.company


    def load_uom(self):
        '''
Loading units of measures into a dictinary for fast lookups.

All quantities are sent to frePPLe as numbers, expressed in the default
unit of measure of the uom dimension.
'''
        m = self.req.session.model('product.uom')
        # We also need to load INactive UOMs, because there still might be records
        # using the inactive UOM. Questionable practice, but can happen...
        ids = m.search(['|', ('active', '=', 1), ('active', '=', 0)], context=self.req.session.context)
        fields = ['factor', 'uom_type', 'category_id', 'name']
        self.uom = {}
        self.uom_categories = {}
        for i in m.read(ids, fields, self.req.session.context):
            if i['uom_type'] == 'reference':
                f = 1.0
                self.uom_categories[i['category_id'][0]] = i['id']
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
        if not uom_id:
            return qty
        return qty * self.uom[uom_id]['factor']


    def export_calendar(self):
        '''
Build a calendar with a) holidays and b) working hours.

The holidays are obtained from the hr.holidays.public.line model.
If the hr module isn't installed, no public holidays will be defined.

The working hours are extracted from a resource.calendar model.
The calendar to use is configured with the company parameter "calendar".
If left unspecified we assume 24*7 working hours.

The odoo model is not ideal and nice for frePPLe, and the current mapping
is an as-good-as-it-gets workaround.

Mapping:
res.company.calendar  -> calendar.name
(if no working hours are defined then 1 else 0) -> calendar.default_value

resource.calendar.attendance.date_from -> calendar_bucket.start
'1' -> calendar_bucket.value
resource.calendar.attendance.dayofweek -> calendar_bucket.days
resource.calendar.attendance.hour_from -> calendar_bucket.startime
resource.calendar.attendance.hour_to -> calendar_bucket.endtime
computed -> calendar_bucket.priority

hr.holidays.public.line.start -> calendar_bucket.start
hr.holidays.public.line.start + 1 day -> calendar_bucket.end
'0' -> calendar_bucket.value
'1' -> calendar_bucket.priority
'''
        yield '<!-- calendar -->\n'
        yield '<calendars>\n'
        try:
            m = self.req.session.model('resource.calendar')
            ids = m.search([('name', '=', self.calendar)], context=self.req.session.context)
            c = m.read(ids, ['attendance_ids'], self.req.session.context)
            m = self.req.session.model('resource.calendar.attendance')
            fields = ['dayofweek', 'date_from', 'hour_from', 'hour_to']
            buckets = []
            for i in m.read(c[0]['attendance_ids'], fields, self.req.session.context):
                strt = datetime.strptime(i['date_from'] or "2000-01-01", '%Y-%m-%d')
                buckets.append((strt,
                                '<bucket start="%sT00:00:00" value="1" days="%s" priority="%%s" starttime="%s" endtime="%s"/>\n' % (
                                    strt.strftime("%Y-%m-%d"),
                                    2 ** ((int(i['dayofweek']) + 1) % 7),
                                    # In odoo, monday = 0. In frePPLe, sunday = 0.
                                    'PT%dM' % round(i['hour_from'] * 60), 'PT%dM' % round(i['hour_to'] * 60)
                                )))
            if len(buckets) > 0:
                # Sort by start date.
                # Required to assure that records with a later start date get a
                # lower priority in frePPLe.
                buckets.sort(key=itemgetter(0))
                priority = 1000
                yield '<calendar name=%s default="0"><buckets>\n' % quoteattr(self.calendar)
                for i in buckets:
                    yield i[1] % priority
                    priority -= 1
            else:
                # No entries. We'll assume 24*7 availability.
                yield '<calendar name=%s default="1"><buckets>\n' % quoteattr(self.calendar)
        except:
            # Exception happens if the resource module isn't installed.
            yield '<!-- Working hours are assumed to be 24*7. -->\n'
            yield '<calendar name=%s default="1"><buckets>\n' % quoteattr(self.calendar)
        try:
            m = self.req.session.model('hr.holidays.public.line')
            ids = m.search([], context=self.req.session.context)
            fields = ['date']
            for i in m.read(ids, fields, self.req.session.context):
                nd = datetime.strptime(i['date'], '%Y-%m-%d') + timedelta(days=1)
                yield '<bucket start="%sT00:00:00" end="%sT00:00:00" value="0" priority="1"/>\n' % (
                    i['date'], nd.strftime("%Y-%m-%d"))
        except:
            # Exception happens if the hr module is not installed
            yield '<!-- No holidays since the HR module is not installed -->\n'
        yield '</buckets></calendar></calendars>\n'


    def export_locations(self):
        '''
Generate a list of warehouse locations to frePPLe, based on the
stock.warehouse model.

We assume the location name to be unique. This is NOT guarantueed by Odoo.

The field subategory is used to store the id of the warehouse. This makes
it easier for frePPLe to send back planning results directly with an
odoo location identifier.

FrePPLe is not interested in the locations odoo defines with a warehouse.
This methods also populates a map dictionary between these locations and
warehouse they belong to.

Mapping:
stock.warehouse.name -> location.name
stock.warehouse.id -> location.subcategory
'''
        self.map_locations = {}
        self.warehouses = set()
        childlocs = {}
        m = self.req.session.model('stock.warehouse')
        ids = m.search([], context=self.req.session.context)
        if ids:
            yield '<!-- warehouses -->\n'
            yield '<locations>\n'
            fields = ['name', 'wh_input_stock_loc_id', 'wh_output_stock_loc_id', 'wh_pack_stock_loc_id', 'wh_qc_stock_loc_id', 'view_location_id']
            for i in m.read(ids, fields, self.req.session.context):
                yield '<location name=%s subcategory="%s"><available name=%s/></location>\n' % (
                    quoteattr(i['name']), i['id'], quoteattr(self.calendar)
                )
                childlocs[i['wh_input_stock_loc_id'][0]] = i['name']
                childlocs[i['wh_output_stock_loc_id'][0]] = i['name']
                childlocs[i['wh_pack_stock_loc_id'][0]] = i['name']
                childlocs[i['wh_qc_stock_loc_id'][0]] = i['name']
                childlocs[i['view_location_id'][0]] = i['name']
                self.warehouses.add(i['name'])
            yield '</locations>\n'

            # Populate a mapping location-to-warehouse name for later lookups
            fields = ['child_ids']
            parent_loc = {}
            m = self.req.session.model('stock.location')
            ids = m.search([], context=self.req.session.context)
            for i in m.read(ids, fields= ['location_id'], context=self.req.session.context):
                if i['location_id']:
                    parent_loc[i['id']] = i['location_id'][0]

            marked = {}

            def fnd_parent(loc_id):  # go up the parent chain to find the warehouse
                if not marked.get(loc_id):  # ensures O(N) iterations instead of O(N^2)
                    if childlocs.get(loc_id):
                        return childlocs[loc_id]
                    if parent_loc.get(loc_id):
                        parent = fnd_parent(parent_loc[loc_id])
                        if parent > 0:
                            return parent
                marked[loc_id] = True
                return -1

            for loc_id in ids:
                parent = fnd_parent(loc_id)
                if parent > 0:
                    self.map_locations[loc_id] = parent

    def export_customers(self):
        '''
Generate a list of customers to frePPLe, based on the res.partner model.
We filter on res.partner where customer = True.

Mapping:
res.partner.id res.partner.name -> customer.name
'''
        self.map_customers = {}
        m = self.req.session.model('res.partner')
        ids = m.search([('customer', '=', True)], context=self.req.session.context)
        if ids:
            yield '<!-- customers -->\n'
            yield '<customers>\n'
            fields = ['name']
            for i in m.read(ids, fields, self.req.session.context):
                name = '%d %s' % (i['id'], i['name'])
                yield '<customer name=%s/>\n' % quoteattr(name)
                self.map_customers[i['id']] = name
            yield '</customers>\n'

    def export_suppliers(self):
        '''
Generate a list of suppliers for frePPLe, based on the res.partner model.
We filter on res.supplier where supplier = True.

Mapping:
res.partner.id res.partner.name -> supplier.name
'''
        self.map_suppliers = {}
        m = self.req.session.model('res.partner')
        s_ids = m.search([('supplier', '=', True)], context=self.req.session.context)
        if s_ids:
            yield '<!-- suppliers -->\n'
            yield '<suppliers>\n'
            fields = ['name']
            for i in m.read(s_ids, fields, self.req.session.context):
                name = '%d %s' % (i['id'], i['name'])
                yield '<supplier name=%s/>\n' % quoteattr(name)
                self.map_suppliers[i['id']] = name
            yield '</suppliers>\n'

    def export_workcenters(self):
        '''
Send the workcenter list to frePPLe, based one the mrp.workcenter model.

We assume the workcenter name is unique. Odoo does NOT guarantuee that.

Mapping:
mrp.workcenter.name -> resource.name
mrp.workcenter.costs_hour -> resource.cost
mrp.workcenter.capacity_per_cycle / mrp.workcenter.time_cycle -> resource.maximum
'''
        self.map_workcenters = {}
        m = self.req.session.model('mrp.workcenter')
        ids = m.search([], context=self.req.session.context)
        fields = ['name', 'costs_hour', 'capacity_per_cycle', 'time_cycle']
        if ids:
            yield '<!-- workcenters -->\n'
            yield '<resources>\n'
            for i in m.read(ids, fields, self.req.session.context):
                name = i['name']
                self.map_workcenters[i['id']] = name
                yield '<resource name=%s maximum="%s" cost="%f"><location name=%s/></resource>\n' % (
                    quoteattr(name), i['capacity_per_cycle'] / (i['time_cycle'] or 1),
                    i['costs_hour'], quoteattr(self.mfg_location)
                )
            yield '</resources>\n'


    def export_items(self):
        '''
Send the list of products to frePPLe, based on the product.product model.
For purchased items we also create a procurement buffer in each warehouse.

Mapping:
[product.product.code] product.product.name -> item.name
product.product.product_tmpl_id.list_price -> item.cost
product.product.id , product.product.product_tmpl_id.uom_id -> item.subcategory

If product.product.product_tmpl_id.purchase_ok and product.product.product_tmpl_id.supply_method == 'buy':
stock.warehouse.name -> buffer.location
[product.product.code] product.product.name @ stock.warehouse.name -> buffer.name
product.product.product_tmpl_id.produce_delay -> buffer.leadtime
'buffer_procure' -> buffer.type
'''
        # Read the product templates
        self.product_product = {}
        self.product_template_product = {}
        self.procured_buffers = set()
        m = self.req.session.model('product.template')
        # fields = ['purchase_ok', 'procure_method', 'supply_method', 'produce_delay', 'list_price', 'uom_id']
        fields = ['purchase_ok', 'route_ids', 'produce_delay', 'list_price', 'uom_id', 'seller_ids', 'standard_price']
        ids = m.search([], context=self.req.session.context)
        self.product_templates = {}
        for i in m.read(ids, fields, self.req.session.context):
            self.product_templates[i['id']] = i

        # Read the stock location routes
        rts = self.req.session.model('stock.location.route')
        fields = ['name']
        ids = rts.search([], context=self.req.session.context)
        stock_location_routes = {}
        for i in rts.read(ids, fields, self.req.session.context):
            stock_location_routes[i['id']] = i

        # Read the products
        m = self.req.session.model('product.product')
        ids = m.search([], context=self.req.session.context)
        s = self.req.session.model('product.supplierinfo')
        s_fields=['name', 'delay', 'min_qty']
        supplier = {}
        if ids:
            yield '<!-- products -->\n'
            yield '<items>\n'
            fields = ['id','name', 'code', 'product_tmpl_id', 'seller_ids']
            data = [i for i in m.read(ids, fields, self.req.session.context)]
            for i in data:
                tmpl = self.product_templates[i['product_tmpl_id'][0]]
                if i['code']:
                    name = u'[%s] %s' % (i['code'], i['name'])
                else:
                    name = i['name']
                prod_obj = {'name': name, 'template': i['product_tmpl_id'][0]}
                self.product_product[i['id']] = prod_obj
                self.product_template_product[i['product_tmpl_id'][0]] = prod_obj
                yield '<item name=%s cost="%f" subcategory="%s,%s">\n' % (
                    quoteattr(name),
                    (tmpl['list_price'] or 0) / self.convert_qty_uom(1.0, tmpl['uom_id'][0], i['id']),
                    self.uom_categories[self.uom[tmpl['uom_id'][0]]['category']], i['id']
                )

                if tmpl['seller_ids']:
                    yield '<itemsuppliers>\n'
                    for sup in s.read(tmpl['seller_ids'], s_fields, self.req.session.context):
                        name = '%d %s' % (sup['name'][0], sup['name'][1])
                        yield '<itemsupplier>\n'
                        yield '<supplier name=%s/><leadtime>P%dD</leadtime><priority>1</priority><size_minimum>%f</size_minimum><cost>%f</cost>\n' %(
                            quoteattr(name), sup['delay'], sup['min_qty'], tmpl['standard_price'])
                        yield '</itemsupplier>\n'


                    yield '</itemsuppliers>\n'
                yield '</item>\n'
            yield '</items>\n'
            # Create procurement buffers for procured items
            # NEW : change buffer product into default product
            yield '<buffers>\n'
            for i in data:
                tmpl = self.product_templates[i['product_tmpl_id'][0]]
                supply_buy = len(filter(lambda r: r['name'] == 'Buy', map(lambda id: stock_location_routes[id],tmpl['route_ids']))) > 0
                if tmpl['purchase_ok'] and supply_buy: # tmpl['supply_method'] == 'buy':  # odoo now uses routes
                    for j in self.warehouses:
                        buf = u'%s @ %s' % (self.product_product[i['id']]['name'], j)
                        operation = u'%d %s @ %s' % (i['id'], i['name'], str(j))
                        self.procured_buffers.add(buf)
                        yield '<buffer name=%s leadtime="P%sD" xsi:type="buffer_procure"><item name=%s/><location name=%s/></buffer>\n' % (
                            quoteattr(buf), int(tmpl['produce_delay'] + self.po_lead),
                            quoteattr(self.product_product[i['id']]['name']), quoteattr(j)
                        )
            yield '</buffers>\n'

    def export_boms(self):
        '''
Exports mrp.routings, mrp.routing.workcenter and mrp.bom records into
frePPLe operations, flows, buffers and loads.

Not supported yet: a) parent boms, b) phantom boms, c) subproducts,
d) routing steps.

Mapping:
'''
        yield '<!-- bills of material -->\n'
        yield '<buffers>\n'
        self.operations = set()

        # Read all active manufacturing routings
        m = self.req.session.model('mrp.routing')
        ids = m.search([], context=self.req.session.context)
        fields = ['location_id']
        mrp_routings = {}
        for i in m.read(ids, fields, self.req.session.context):
            mrp_routings[i['id']] = i['location_id']

        # Read all workcenters of all routings
        mrp_routing_workcenters = {}
        m = self.req.session.model('mrp.routing.workcenter')
        ids = m.search([], context=self.req.session.context)
        fields = ['routing_id', 'workcenter_id', 'sequence', 'cycle_nbr', 'hour_nbr']
        for i in m.read(ids, fields, self.req.session.context):
            if i['routing_id'][0] in mrp_routing_workcenters:
                mrp_routing_workcenters[i['routing_id'][0]].append((i['workcenter_id'][1], i['cycle_nbr'],))
            else:
                mrp_routing_workcenters[i['routing_id'][0]] = [(i['workcenter_id'][1], i['cycle_nbr'],)]
        # Loop over all "producing" bom records
        m = self.req.session.model('mrp.bom')
        m_lines = self.req.session.model('mrp.bom.line')
        ids = m.search([], context=self.req.session.context)
        fields = [
            'name', 'product_qty', 'product_uom', 'date_start', 'date_stop',
            'product_efficiency', 'product_tmpl_id', 'routing_id', 'type',
            'product_rounding', 'bom_line_ids'
        ]
        fields2 = [
            'product_qty', 'product_uom', 'date_start', 'date_stop', 'product_id',
            'routing_id', 'type', 'product_rounding'
        ]

        product = self.req.session.model('product.template')
        product_ids = product.search([('bom_ids','!=',False)], context=self.req.session.context)
        product_field = ['bom_ids', 'id', 'name']
        product_bom = {}
        operation_bom = {}
        buffer_bom = {}
        for i in product.read(product_ids, product_field, self.req.session.context):
#             store product_id that have more than one BOM to create an alternate operation
            if len(i['bom_ids']) > 1:
                if i['id'] in product_bom:
                    product_bom[i['id']].append((i['bom_ids'], i['name']))
                else :
                    product_bom[i['id']] = [(i['bom_ids'], i['name'])]

        for i in m.read(ids, fields, self.req.session.context):
            duration_hour = 0
            duration_per = 0
            type = ""
            producing = ""
            # Determine the location
            if i['routing_id']:
                location = mrp_routings.get(i['routing_id'][0], None)
                if not location:
                    location = self.mfg_location
                else:
                    location = location[1]
            else:
                location = self.mfg_location

            # Determine operation name and item
            operation = u'%d %s @ %s' % (i['id'], i['name'], location)
            self.operations.add(operation)
            product_buf = self.product_template_product.get(i['product_tmpl_id'][0], None) # TODO avoid multiple bom on single template
            if not product_buf:
                continue
            buf_name = u'%s @ %s' % (product_buf['name'], location)
            uom_factor = self.convert_qty_uom(1.0, i['product_uom'][0], i['product_tmpl_id'][0])

            # Build buffer and its producing operation
            yield '<buffer name=%s><item name=%s/><location name=%s/>\n' % (
                quoteattr(buf_name), quoteattr(product_buf['name']), quoteattr(location)
            )
            yield '<producing name=%s size_multiple="%s" duration="PT%dH" posttime="P%dD" xsi:type="operation_fixed_time"><location name=%s/>\n' % (
                quoteattr(operation), (i['product_rounding'] * uom_factor) or 1,
                int(self.product_templates[self.product_product[i['product_tmpl_id'][0]]['template']]['produce_delay']),
                self.manufacturing_lead,
                quoteattr(location)
            )
            yield '<flows>\n'
            if i['product_tmpl_id'][0] not in product_bom:
#                 if the operation is suboperation of alternate operation, the current operation doesn't need flow_end
                yield '<flow xsi:type="flow_end" quantity="%f"%s%s><buffer name=%s/></flow>\n' % (
                    i['product_qty'] * i['product_efficiency'] * uom_factor,
                    i['date_start'] and (' effective_start="%s"' % i['date_start']) or "",
                    i['date_stop'] and (' effective_end="%s"' % i['date_stop']) or "",
                    quoteattr(buf_name)
                )

            # Build consuming flows. If the same component is consumed multiple times in the same
            # BOM we sum up all quantities in a single flow.
            fl = {}
            for j in m_lines.read(i['bom_line_ids'], fields2, self.req.session.context):
                product = self.product_product.get(j['product_id'][0], None)
                if not product:
                    continue
                if j['product_id'][0] in fl:
                    fl[j['product_id'][0]].append(j)
                else:
                    fl[j['product_id'][0]] = [j]
            for j in fl:
                product = self.product_product[j]
                buf = u'%s @ %s' % (product['name'], location)
                qty = sum(
                    self.convert_qty_uom(k['product_qty'], k['product_uom'][0], k['product_id'][0])
                    for k in fl[j]
                )
                yield '<flow xsi:type="flow_start" quantity="-%f"%s%s><buffer name=%s/></flow>\n' % (
                    qty, fl[j][0]['date_start'] and (' effective_start="%s"' % fl[j][0]['date_start']) or "",
                    fl[j][0]['date_stop'] and (' effective_end="%s"' % fl[j][0]['date_stop']) or "",
                    quoteattr(buf)
                )
            yield '</flows>\n'

            # Create loads
            if i['routing_id']:
                yield '<loads>\n'
                for j in mrp_routing_workcenters.get(i['routing_id'][0], []):
                    yield '<load quantity="%f"><resource name=%s/></load>\n' % (j[1], quoteattr(j[0]))
                yield '</loads>\n'

            # Footer
            yield '</producing>\n'
            if i['product_tmpl_id'][0] in product_bom:
#                 here to store all needed field value in alternate operations,
#                 because alternate operation will create outside of this loop
                if i['id'] in product_bom[i['product_tmpl_id'][0]][0][0]:
                    if i['product_tmpl_id'][0] in operation_bom:
                        operation_bom[i['product_tmpl_id'][0]].append(str(operation))
                    else :
                        operation_bom[i['product_tmpl_id'][0]] = [str(operation)]

                    buffer_bom[i['product_tmpl_id'][0]] = [(str(buf_name), product_buf['name'], location)]
            yield '</buffer>\n'

        yield '<!-- alternate operations -->\n'
        for i in product_bom:
            yield '<buffer name="%s">\n' % (buffer_bom[i][0][0])
            yield '<item name="%s"/>' % (buffer_bom[i][0][1])
            yield '<location name="%s"/>' % (buffer_bom[i][0][2])
            yield '<producing name="alternate of %s" xsi:type="operation_alternate" search="PRIORITY">\n' % (product_bom[i][0][1])
            yield '<location name="%s"/>' % (buffer_bom[i][0][2])
            yield '<flows><flow xsi:type="flow_end">\n'
            yield '<buffer name="%s"/>\n' % (buffer_bom[i][0][0])
            yield '<quantity>1</quantity></flow></flows>\n'
            yield '<suboperations>\n'
            for o in operation_bom[i]:
                yield '<suboperation><operation name="%s"/><priority>1</priority></suboperation>\n' % (o)
            yield '</suboperations>\n'
            yield '</producing>\n'
            yield '</buffer>\n'

        yield '</buffers>\n'


    def export_salesorders(self):
        '''
Send confirmed sales order lines as demand to frePPLe, using the
sale.order and sale.order.line models.

Each order is linked to a warehouse, which is used as the location in
frePPLe.

Only orders in the status 'confirmed' are extracted.

The picking policy 'complete' is supported at the sales order line
level only in frePPLe. FrePPLe doesn't allow yet to coordinate the
delivery of multiple lines in a sales order (except with hacky
modeling construct).
The field requested_date is only available when sale_order_dates is
installed.

Mapping:
sale.order.name ' ' sale.order.line.id -> demand.name
sales.order.requested_date -> demand.due
'1' -> demand.priority
[product.product.code] product.product.name -> demand.item
sale.order.partner_id.name -> demand.customer
convert sale.order.line.product_uom_qty and sale.order.line.product_uom  -> demand.quantity
'Ship' [sale.order.product_id.code] sale.order.product_id.name @ stock.warehouse.name -> demand->operation
(if sale.order.picking_policy = 'one' then same as demand.quantity else 1) -> demand.minshipment
product.product.name @ stock.warehouse.name -> buffer.name
'''
        # Get a dict with all shops and their warehouse
        # shops = {}
        # m = self.req.session.model('sale.shop')
        # ids = m.search([], context=self.req.session.context)
        # fields = ['name', 'warehouse_id']
        # for i in m.read(ids, fields, self.req.session.context):
        #     shops[i['id']] = i['warehouse_id'][1]

        # Get all sales order lines
        m = self.req.session.model('sale.order.line')
        ids = m.search([('state', 'in', ['draft', 'confirmed'])], context=self.req.session.context)
        fields = ['state', 'product_id', 'product_uom_qty', 'product_uom', 'order_id']
        so_line = [i for i in m.read(ids, fields, self.req.session.context)]

        # Get all sales orders
        m = self.req.session.model('sale.order')
        ids = [i['order_id'][0] for i in so_line]
        fields = ['partner_id', 'requested_date', 'date_order', 'picking_policy', 'warehouse_id', 'picking_ids']
        # for python 2.7:
        # so = { j['id']: j for j in m.read(ids, fields, self.req.session.context) }
        pick = self.req.session.model('stock.picking')
        p_fields = ['move_lines', 'sale_id', 'state']

        move = self.req.session.model('stock.move')
        m_fields = ['product_id', 'product_uom_qty']
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
            location = j['warehouse_id'][1] # index 1 is a wild guess, it seems to work
            customer = self.map_customers.get(j['partner_id'][0], None)
            if not customer or not location or not product:
                # Not interested in this sales order...
                continue

            operation = u'Ship %s @ %s' % (product['name'], location)
            buf = u'%s @ %s' % (product['name'], location)
            due = j.get('requested_date', False) or j['date_order']
            qty = self.convert_qty_uom(i['product_uom_qty'], i['product_uom'][0], i['product_id'][0])
            minship = j['picking_policy'] == 'one' and qty or 1.0
            priority = 1
            deliveries.update([(operation, buf, product['name'], location,)])
#             export draft sale order
            if i['state'] == 'draft':
                yield '<demand name=%s quantity="%s" due="%s" priority="%s" minshipment="%s" maxlateness="P0D" status="quote"><item name=%s/><customer name=%s/><location name=%s/><operation name=%s/></demand>\n' % (
                    quoteattr(name), qty, due.replace(' ', 'T'),  # TODO find a better way around this ugly hack (maybe get the datetime object from the database)
                    priority, minship, quoteattr(product['name']),
                    quoteattr(customer), quoteattr(location), quoteattr(operation)
                )
            if j['picking_ids'] :
#                 here to export sale order line based on DO line status,
#                 if DO line is done then demand status is closed
#                 if DO line is cancel, it will skip the current DO line
#                 else demand status is open
                pick_number = 0
                state = {}
                for p in pick.read(j['picking_ids'], p_fields, self.req.session.context):
                    p_ids = p['move_lines']
                    product_id = i['product_id'][0]
                    mv_ids = move.search([('id', 'in', p_ids), ('product_id','=', product_id)], context=self.req.session.context)

                    status = ''
                    if p['state'] == 'done':
                        if self.mode == 1:
                          # Closed orders aren't transferred during a small run of mode 1
                          continue
                        status = 'closed'
                    elif p['state'] == 'cancel':
                        continue
                    else:
                        status = 'open'

                    for mv in move.read(mv_ids, m_fields, self.req.session.context):
                        pick_number = pick_number + 1
                        name = u'%s %d %d' % (i['order_id'][1], i['id'], pick_number)
                        yield '<demand name=%s quantity="%s" due="%s" priority="%s" minshipment="%s" maxlateness="P0D" status="%s"><item name=%s/><customer name=%s/><location name=%s/><operation name=%s/></demand>\n' % (
                            quoteattr(name), mv['product_uom_qty'], due.replace(' ', 'T'),  # TODO find a better way around this ugly hack (maybe get the datetime object from the database)
                            priority, minship,status, quoteattr(product['name']),
                            quoteattr(customer), quoteattr(location), quoteattr(operation)
                        )

        yield '</demands>\n'

        # Create delivery operations
        if deliveries:
            yield '<!-- shipping operations -->\n'
            yield '<operations>\n'
            for i in deliveries:
                yield '<operation name=%s posttime="P%sD"><flows><flow xsi:type="flow_start" quantity="-1"><buffer name=%s><item name=%s/><location name=%s/></buffer></flow></flows></operation>\n' % (
                    quoteattr(i[0]), self.security_lead, quoteattr(i[1]), quoteattr(i[2]), quoteattr(i[3]))
            yield '</operations>\n'


    def export_purchaseorders(self):
        '''
Send all open purchase orders to frePPLe, using the purchase.order and
purchase.order.line models.

Only purchase order lines in state 'confirmed' are extracted. The state of the
purchase order header must be "approved".

Mapping:
'Purchase ' purchase.order.line.product.name ' @ ' purchase.order.location_id.name -> operationplan.operation
convert purchase.order.line.product_uom_qty and purchase.order.line.product_uom -> operationplan.quantity
purchase.order.date_planned -> operationplan.end
purchase.order.date_planned -> operationplan.start
'1' -> operationplan.locked
'''
        m = self.req.session.model('purchase.order.line')
        ids = m.search([('state', '=', 'confirmed')], context=self.req.session.context)
        fields = ['name', 'date_planned', 'product_id', 'product_qty', 'product_uom', 'order_id']
        po_line = [i for i in m.read(ids, fields, self.req.session.context)]

        # Get all purchase orders
        m = self.req.session.model('purchase.order')
        ids = [i['order_id'][0] for i in po_line]
        fields = ['name', 'location_id', 'partner_id', 'state', 'shipped']
        # for python 2.7:
        # po = { j['id']: j for j in m.read(ids, fields, self.req.session.context) }
        po = {}
        for i in m.read(ids, fields, self.req.session.context):
            po[i['id']] = i

        # Create purchasing operations
        dd = []
        deliveries = set()
        yield '<!-- purchase operations -->\n'
        yield '<operations>\n'
        for i in po_line:
            if not i['product_id']:
                continue
            item = self.product_product.get(i['product_id'][0], None)
            j = po[i['order_id'][0]]
            location = j['location_id'] and self.map_locations.get(j['location_id'][0], None) or None
            if location and item and j['state'] == 'approved' and not j['shipped']:
                operation = u'Purchase %s @ %s' % (item['name'], location)
                buf = u'%s @ %s' % (item['name'], location)
                due = i['date_planned']
                qty = self.convert_qty_uom(i['product_qty'], i['product_uom'][0], i['product_id'][0])
                if not buf in deliveries and not buf in self.procured_buffers:
                    yield '<operation name=%s><flows><flow xsi:type="flow_end" quantity="1"><buffer name=%s><item name=%s/><location name=%s/></buffer></flow></flows></operation>\n' % (
                        quoteattr(operation), quoteattr(buf), quoteattr(item['name']), quoteattr(location)
                    )
                    deliveries.update([buf])
                dd.append((quoteattr(operation), due, due, qty))
        yield '</operations>\n'

        # Create purchasing operationplans
        yield '<!-- open purchase order lines -->\n'
        yield '<operationplans>\n'
        #for i in dd:
        #    yield '<operationplan operation=%s start="%sT00:00:00" end="%sT00:00:00" quantity="%f" locked="true"/>\n' % i
        yield '</operationplans>\n'


    def export_manufacturingorders(self):
        '''
Extracting work in progress to frePPLe, using the mrp.production model.

We extract workorders in the states 'in_production' and 'confirmed', and
which have a bom specified.

Mapping:
mrp.production.bom_id mrp.production.bom_id.name @ mrp.production.location_dest_id -> operationplan.operation
convert mrp.production.product_qty and mrp.production.product_uom -> operationplan.quantity
mrp.production.date_planned -> operationplan.end
mrp.production.date_planned -> operationplan.start
'1' -> operationplan.locked
'''
        yield '<!-- manufacturing orders in progress -->\n'
        yield '<operationplans>\n'
        m = self.req.session.model('mrp.production')
        ids = m.search(['|', ('state', '=', 'in_production'), ('state', '=', 'confirmed')],
                       context=self.req.session.context)
        fields = ['bom_id', 'date_start', 'date_planned', 'name', 'state', 'product_qty', 'product_uom',
                  'location_dest_id', 'product_id']
        for i in m.read(ids, fields, self.req.session.context):
            if i['state'] in ('in_production', 'confirmed', 'ready') and i['bom_id']:
                # Open orders
                location = self.map_locations.get(i['location_dest_id'][0], None)
                operation = u'%d %s @ %s' % (i['bom_id'][0], i['bom_id'][1], location)
                try:
                    startdate = datetime.strptime(i['date_start'] or i['date_planned'], '%Y-%m-%d %H:%M:%S')
                except:
                    continue
                if not location or not operation in self.operations:
                    continue
                qty = self.convert_qty_uom(i['product_qty'], i['product_uom'][0], i['product_id'][0])
                yield '<operationplan operation=%s start="%s" end="%s" quantity="%s" locked="true"/>\n' % (
                    quoteattr(operation), startdate, startdate, qty
                )
        yield '</operationplans>\n'


    def export_orderpoints(self):
        '''
Defining order points for frePPLe, based on the stock.warehouse.orderpoint
model.

Mapping:
stock.warehouse.orderpoint.product.name ' @ ' stock.warehouse.orderpoint.location_id.name -> buffer.name
stock.warehouse.orderpoint.location_id.name -> buffer.location
stock.warehouse.orderpoint.product.name -> buffer.item
convert stock.warehouse.orderpoint.product_min_qty -> buffer.mininventory
convert stock.warehouse.orderpoint.product_max_qty -> buffer.maxinventory
convert stock.warehouse.orderpoint.qty_multiple -> buffer->size_multiple
'''
        m = self.req.session.model('stock.warehouse.orderpoint')
        ids = m.search([], context=self.req.session.context)
        fields = ['warehouse_id', 'product_id', 'product_min_qty', 'product_max_qty', 'product_uom', 'qty_multiple']
        if ids:
            yield '<!-- order points -->\n'
            yield '<buffers>\n'
            for i in m.read(ids, fields, self.req.session.context):
                item = self.product_product.get(i['product_id'] and i['product_id'][0] or 0, None)
                if not item:
                    continue
                uom_factor = self.convert_qty_uom(1.0, i['product_uom'][0], i['product_id'][0])
                name = u'%s @ %s' % (item['name'], i['warehouse_id'][1])
                if name in self.procured_buffers:
                    # Procured material
                    yield '<buffer name=%s xsi:type="buffer_procure" mininventory="%f" maxinventory="%f" size_multiple="%f"><item name=%s/><location name=%s/></buffer>' % (
                        quoteattr(name), i['product_min_qty'] * uom_factor,
                        i['product_max_qty'] * uom_factor, i['qty_multiple'] * uom_factor,
                        quoteattr(item['name']), quoteattr(i['warehouse_id'][1])
                    )
                else:
                    # Manufactured material
                    # We only respect the minimum
                    yield '<buffer name=%s minimum="%f"><item name=%s/><location name=%s/></buffer>' % (
                        quoteattr(name), i['product_min_qty'] * uom_factor,
                        quoteattr(item['name']), quoteattr(i['warehouse_id'][1])
                    )
            yield '</buffers>\n'


    def export_onhand(self):
        '''
Extracting all on hand inventories to frePPLe.

We're bypassing the ORM for performance reasons.

Mapping:
stock.report.prodlots.product_id.name @ stock.report.prodlots.location_id.name -> buffer.name
stock.report.prodlots.product_id.name -> buffer.item
stock.report.prodlots.location_id.name -> buffer.location
sum(stock.report.prodlots.qty) -> buffer.onhand
'''
        yield '<!-- inventory -->\n'
        yield '<buffers>\n'
        cr = RegistryManager.get(self.database).cursor()
        try:
            cr.execute('SELECT product_id, location_id, sum(qty) '
                       'FROM stock_quant '
                       'WHERE qty > 0 '
                       'GROUP BY product_id, location_id')
            for i in cr.fetchall():
                item = self.product_product.get(i[0], None)
                location = self.map_locations.get(i[1], None)
                if location and item:
                    yield '<buffer name=%s onhand="%f"><item name=%s/><location name=%s/></buffer>\n' % (
                        quoteattr(u'%s @ %s' % (item['name'], location)),
                        i[2], quoteattr(item['name']), quoteattr(location)
                    )
        finally:
            cr.close()
        yield '</buffers>\n'
