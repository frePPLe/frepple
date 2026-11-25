#
# Copyright (C) 2025 by frePPLe bv
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

from django.db import migrations, models


class Migration(migrations.Migration):

    replaces = [
        ("output", "0011_exports"),
        ("output", "0012_resourcesummary_load_confirmed"),
        ("output", "0013_varchar_max_length"),
        ("output", "0014_constraint_and_problem_weight"),
        ("output", "0014_constraint_and_problem_weight_corrected"),
    ]

    dependencies = [
        ("execute", "0010_dataexport"),
        ("output", "0010_squash_70"),
    ]

    operations = [
        migrations.RunSQL(
            sql="""insert into execute_export
  (name, sql, report, arguments)
  values (
    'purchaseorder.csv.gz',
    'select
       source, lastmodified, reference, status , reference, quantity,
       to_char(startdate,''YYYY-MM-DD HH24:MI:SS'') as "ordering date",
       to_char(enddate,''YYYY-MM-DD HH24:MI:SS'') as "receipt date",
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
       to_char(startdate,''YYYY-MM-DD HH24:MI:SS'') as "ordering date",
       to_char(enddate,''YYYY-MM-DD HH24:MI:SS'') as "receipt date",
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
      to_char(startdate,''YYYY-MM-DD HH24:MI:SS'') as startdate,
      to_char(enddate,''YYYY-MM-DD HH24:MI:SS'') as enddate,
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
        to_char(startdate,''YYYY-MM-DD HH24:MI:SS'') as startdate,
        to_char(enddate,''YYYY-MM-DD HH24:MI:SS'') as enddate
     from out_problem
     where name <> ''material excess''
     order by entity, name, startdate
    ',
    null,
    null
  ), (
    'operationplanmaterial.csv.gz',
    'select
        operationplanmaterial.item_id as item,
        operationplanmaterial.location_id as location,
        operationplanmaterial.quantity,
        to_char(operationplanmaterial.flowdate,''YYYY-MM-DD HH24:MI:SS'') as date,
        operationplanmaterial.onhand,
        operationplan_id as operationplan,
        operationplan.status
    from operationplanmaterial
    inner join operationplan on operationplan.reference = operationplanmaterial.operationplan_id
    order by operationplanmaterial.item_id, operationplanmaterial.location_id,
    operationplanmaterial.flowdate, operationplanmaterial.quantity desc
    ',
    null,
    null
  ), (
    'operationplanresource.csv.gz',
    'select
        operationplanresource.resource_id as resource,
        to_char(operationplan.startdate,''YYYY-MM-DD HH24:MI:SS'') as startdate,
        to_char(operationplan.enddate,''YYYY-MM-DD HH24:MI:SS'') as enddate,
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
""",
            reverse_sql="""
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
        migrations.AddField(
            model_name="resourcesummary",
            name="load_confirmed",
            field=models.DecimalField(
                decimal_places=8,
                max_digits=20,
                null=True,
                verbose_name="confirmed load",
            ),
        ),
        migrations.AlterField(
            model_name="constraint",
            name="demand",
            field=models.CharField(db_index=True, null=True, verbose_name="demand"),
        ),
        migrations.AlterField(
            model_name="constraint",
            name="description",
            field=models.CharField(verbose_name="description"),
        ),
        migrations.AlterField(
            model_name="constraint",
            name="entity",
            field=models.CharField(db_index=True, verbose_name="entity"),
        ),
        migrations.AlterField(
            model_name="constraint",
            name="forecast",
            field=models.CharField(db_index=True, null=True, verbose_name="forecast"),
        ),
        migrations.AlterField(
            model_name="constraint",
            name="item",
            field=models.CharField(db_index=True, null=True, verbose_name="item"),
        ),
        migrations.AlterField(
            model_name="constraint",
            name="name",
            field=models.CharField(db_index=True, verbose_name="name"),
        ),
        migrations.AlterField(
            model_name="constraint",
            name="owner",
            field=models.CharField(db_index=True, verbose_name="owner"),
        ),
        migrations.AlterField(
            model_name="problem",
            name="description",
            field=models.CharField(verbose_name="description"),
        ),
        migrations.AlterField(
            model_name="problem",
            name="entity",
            field=models.CharField(db_index=True, verbose_name="entity"),
        ),
        migrations.AlterField(
            model_name="problem",
            name="name",
            field=models.CharField(db_index=True, verbose_name="name"),
        ),
        migrations.AlterField(
            model_name="problem",
            name="owner",
            field=models.CharField(db_index=True, verbose_name="owner"),
        ),
        migrations.AlterField(
            model_name="resourcesummary",
            name="resource",
            field=models.CharField(verbose_name="resource"),
        ),
        migrations.RemoveField(
            model_name="constraint",
            name="weight",
        ),
        migrations.RemoveField(
            model_name="problem",
            name="weight",
        ),
    ]
