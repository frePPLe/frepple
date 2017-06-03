#
# Copyright (C) 2016 by frePPLe bvba
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

from django.db import migrations


class Migration(migrations.Migration):

  dependencies = [
    ('input', '0006_new_data_model_2'),
    ('common', '0003_wizard'),
  ]

  operations = [
    migrations.RunSQL(
      '''
      insert into common_wizard
      (name, sequenceorder, url_doc, url_internaldoc, status, owner_id)
      values
      ('Introduction', 100, '/user-guide/modeling-wizard/concepts.html', null, false, 'Introduction'),
      ('Master data', 200, '/user-guide/modeling-wizard/master-data/index.html', null, false, null),
      ('Locations', 210, '/user-guide/modeling-wizard/master-data/locations.html', '/data/input/location/', false, 'Master data'),
      ('Items', 220, '/user-guide/modeling-wizard/master-data/items.html', '/data/input/item/', false, 'Master data'),
      ('Customers', 230, '/user-guide/modeling-wizard/master-data/customers.html', '/data/input/customer/', false, 'Master data'),
      ('Sales orders', 240, '/user-guide/modeling-wizard/master-data/sales-orders.html', '/data/input/demand/', false, 'Master data'),
      ('Buffers', 250, '/user-guide/modeling-wizard/master-data/buffers.html', '/data/input/buffer/', false, 'Master data'),
      ('Purchasing', 300, '/user-guide/modeling-wizard/purchasing/index.html', null, false, null),
      ('Suppliers', 310, '/user-guide/modeling-wizard/purchasing/suppliers.html', '/data/input/supplier/', false, 'Purchasing'),
      ('Item suppliers', 320, '/user-guide/modeling-wizard/purchasing/item-suppliers.html', '/data/input/itemsupplier/', false, 'Purchasing'),
      ('Purchase orders', 330, '/user-guide/modeling-wizard/purchasing/purchase-orders.html', '/data/input/purchaseorder/', false, 'Purchasing'),
      ('Distribution', 400, '/user-guide/modeling-wizard/distribution/index.html', null, false, null),
      ('Item distributions', 410, '/user-guide/modeling-wizard/distribution/item-distributions.html', '/data/input/itemdistribution/', false, 'Distribution'),
      ('Distribution orders', 420, '/user-guide/modeling-wizard/purchasing/purchase-orders.html', '/data/input/distributionorder/', false, 'Distribution'),
      ('Manufacturing BOM', 700, '/user-guide/modeling-wizard/manufacturing-bom/index.html', null, false, null),
      ('Operations', 710, '/user-guide/modeling-wizard/manufacturing-bom/operations.html', '/data/input/operation/', false, 'Manufacturing BOM'),
      ('Operation materials', 720, '/user-guide/modeling-wizard/manufacturing-bom/operation-materials.html', '/data/input/operationmaterial/', false, 'Manufacturing BOM'),
      ('Manufacturing orders', 730, '/user-guide/modeling-wizard/manufacturing-bom/manufacturing-orders.html', '/data/input/manufacturingorder/', false, 'Manufacturing BOM'),
      ('Manufacturing Capacity', 800, '/user-guide/modeling-wizard/manufacturing-capacity/index.html', null, false, null),
      ('Resources', 810, '/user-guide/modeling-wizard/manufacturing-capacity/resources.html', '/data/input/resource/', false, 'Manufacturing Capacity'),
      ('Operation Resources', 820, '/user-guide/modeling-wizard/manufacturing-capacity/operation-resources.html', '/data/input/operationresource/', false, 'Manufacturing Capacity'),
      ('Plan generation', 900, '/user-guide/modeling-wizard/generate-plan.html', '/execute/', false, 'Plan generation')
      ''',
      '''
      delete from common_wizard where name in (
         'Introduction', 'Master data', 'Locations', 'Items', 'Customers', 'Sales orders', 'Purchasing', 'Suppliers',
         'Item suppliers', 'Purchase orders', 'Distribution', 'Suppliers', 'Distribution orders', 'Manufacturing BOM',
         'Operations', 'Operation materials', 'Manufacturing orders', 'Manufacturing Capacity', 'Resources',
         'Operation Resources', 'Plan generation'
         )
      '''
    ),
  ]