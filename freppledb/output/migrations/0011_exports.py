#
# Copyright (C) 2024 by frePPLe bv
#
# Permission is hereby granted, free of charge, to any person obtaining
# a copy of this software and associated documentation files (the
# "Software"), to deal in the Software without restriction, including
# without limitation the rights to use, copy, modify, merge, publish,
# distribute, sublicense, and/or sell copies of the Software, and to
# permit persons to whom the Software is furnished to do so, subject to
# the following conditions:
#
# The above copyright notice and this permission notice shall be
# included in all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND,
# EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF
# MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND
# NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE
# LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION
# OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION
# WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.
#

from django.db import migrations
from django.conf import settings


class Migration(migrations.Migration):
    dependencies = [
        ("output", "0010_squash_70"),
        ("execute", "0010_dataexport"),
    ]

    operations = [
        migrations.RunSQL(
            """
            insert into execute_export
               (name, sql, report, arguments)
               values (
                  'purchaseorder.csv.gz',
                  'select
                     source, lastmodified, reference, status , reference, quantity,
                     to_char(startdate,''%s HH24:MI:SS'') as "ordering date",
                     to_char(enddate,''%s HH24:MI:SS'') as "receipt date",
                     criticality, EXTRACT(EPOCH FROM delay) as delay,
                     owner_id, item_id, location_id, supplier_id
                   from operationplan
                   where status <> ''confirmed'' and type=''PO''
                   ',
                   null,
                   null
                ), (
                    'distributionorder.csv.gz',
                    'select
                       source, lastmodified, reference, status, reference, quantity,
                       to_char(startdate,''%s HH24:MI:SS'') as "ordering date",
                       to_char(enddate,''%s HH24:MI:SS'') as "receipt date",
                       criticality, EXTRACT(EPOCH FROM delay) as delay,
                       plan, destination_id, item_id, origin_id
                     from operationplan
                     where status <> ''confirmed'' and type = ''DO''
                    ',
                    null,
                    null
                ), (
                    'manufacturingorder.csv.gz',
                    'select
                      source, lastmodified, reference, status, reference, quantity,
                      to_char(startdate,''%s HH24:MI:SS'') as startdate,
                      to_char(enddate,''%s HH24:MI:SS'') as enddate,
                      criticality, EXTRACT(EPOCH FROM delay) as delay,
                      operation_id, owner_id, plan, item_id, batch
                    from operationplan
                    where status <> ''confirmed'' and type = ''MO''
                    ',
                    null,
                    null
                ), (
                    'problems.csv.gz',
                    'select
                       entity, owner, name, description,
                       to_char(startdate,''%s HH24:MI:SS'') as startdate,
                       to_char(enddate,''%s HH24:MI:SS'') as enddate
                     from out_problem
                     where name <> ''material excess''
                     order by entity, name, startdate
                    ',
                    null,
                    null
                ), (
                    'operationplanmaterial.csv.gz',
                    'select
                       item_id as item, location_id as location, quantity,
                       to_char(flowdate,''%s HH24:MI:SS'') as date, onhand,
                       operationplan_id as operationplan, status
                     from operationplanmaterial
                     order by item_id, location_id, flowdate, quantity desc
                    ',
                    null,
                    null
                ), (
                    'operationplanresource.csv.gz',
                    'select
                        operationplanresource.resource_id as resource,
                        to_char(operationplan.startdate,''%s HH24:MI:SS'') as startdate,
                        to_char(operationplan.enddate,''%s HH24:MI:SS'') as enddate,
                        operationplanresource.setup,
                        operationplanresource.operationplan_id as operationplan,
                        operationplan.status
                    from operationplanresource
                    inner join operationplan on operationplan.reference = operationplanresource.operationplan_id
                    order by operationplanresource.resource_id, operationplan.startdate,
                       operationplanresource.quantity
                    ',
                    null,
                    null
                ), (
                    'capacityreport.csv.gz',
                    null,
                    'freppledb.output.views.resource.OverviewReport',
                    '{"buckets": "week", "horizontype": true, "horizonunit": "month", "horizonlength": 6}'
                ), (
                    'inventoryreport.csv.gz',
                    null,
                    'freppledb.output.views.buffer.OverviewReport',
                    '{"buckets": "week", "horizontype": true, "horizonunit": "month", "horizonlength": 6}'
                )
            on conflict (name) do nothing
            """
            % ((settings.DATE_FORMAT_JS,) * 11),
            """
            delete from execute_export where name in (
               'purchaseorder.csv.gz',
               'distributionorder.csv.gz',
               'manufacturingorder.csv.gz',
               'problems.csv.gz',
               'operationplanmaterial.csv.gz',
               'operationplanresource.csv.gz',
               'capacityreport.csv.gz',
               'inventoryreport.csv.gz'
               )
            """,
        ),
    ]
