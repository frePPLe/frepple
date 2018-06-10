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

from django.db import migrations, models
from django.db.models import F, Q

from freppledb.common.fields import JSONField


def CheckReadyForMigration(apps, schema_editor):
  msg = []
  db = schema_editor.connection.alias
  Buffer = apps.get_model("input", "Buffer")
  cnt = Buffer.objects.all().using(db).filter(type="procure").count()
  if cnt:
    msg.append('\nYour model has %d buffers of type "procure", which is obsoleted.' % cnt)
    msg.append('You will need to migrate the data to the itemsupplier table.')
  Operation = apps.get_model("input", "Operation")
  cnt = Operation.objects.all().using(db).filter(location__isnull=True).count()
  if cnt:
    msg.append('\nThe location field in the operation table can\'t be null any longer.')
    msg.append('You will need to update the %d violating records in the operation table.' % cnt)
  Flow = apps.get_model("input", "Flow")
  cnt = Flow.objects.all().using(db).filter(~Q(thebuffer__location__name=F('operation__location__name')))
  if cnt:
    msg.append('\nAn operation can only have flows inside the same location from now on.')
    msg.append('You will need to change the %s operations and use itemdistributions to move material between locations.' % cnt)
  if msg:
    print('\nPre-migration check fails!\n')
    for m in msg:
      print(m)
    raise ValueError("Manual migration required")


def CheckReadyForMigrationReverse(apps, schema_editor):
  return


class Migration(migrations.Migration):

  dependencies = [
    ('input', '0004_non_nullable_fields'),
  ]

  operations = [
    # Validate prerequisites
    migrations.RunPython(CheckReadyForMigration, CheckReadyForMigrationReverse),

    # Removing fields that were already deprecated for a longer time and already not in use
    migrations.RemoveField(
      model_name='flow',
      name='alternate',
    ),
    migrations.RemoveField(
      model_name='load',
      name='alternate',
    ),

    #
    migrations.AlterField(
      model_name='calendarbucket',
      name='calendar',
      field=models.ForeignKey(to='input.Calendar', related_name='buckets', verbose_name='Calendar'),
    ),

    # Obsoleting buffers of type "procure"
    migrations.RemoveField(model_name='buffer', name='fence'),
    migrations.RemoveField(model_name='buffer', name='leadtime'),
    migrations.RemoveField(model_name='buffer', name='max_inventory'),
    migrations.RemoveField(model_name='buffer', name='min_inventory'),
    migrations.RemoveField(model_name='buffer', name='max_interval'),
    migrations.RemoveField(model_name='buffer', name='size_maximum'),
    migrations.RemoveField(model_name='buffer', name='size_minimum'),
    migrations.RemoveField(model_name='buffer', name='size_multiple'),
    migrations.AlterField(
      model_name='buffer',
      name='type',
      field=models.CharField(default='default', choices=[('default', 'Default'), ('infinite', 'Infinite')], verbose_name='type', max_length=20, null=True, blank=True),
    ),

    # Renaming load to operationresource
    migrations.RenameModel('load', 'operationresource'),
    migrations.AlterModelTable(name='operationresource', table='operationresource'),
    migrations.AlterModelOptions(
      name='operationresource',
      options={'verbose_name_plural': 'operation resources', 'verbose_name': 'operation resource'},
    ),
    migrations.AlterUniqueTogether(
      name='operationresource',
      unique_together=set([('operation', 'resource', 'effective_start')]),
    ),
    migrations.AlterField(
      model_name='operationresource',
      name='operation',
      field=models.ForeignKey(verbose_name='operation', related_name='operationresources', to='input.Operation'),
    ),
    migrations.AlterField(
      model_name='operationresource',
      name='resource',
      field=models.ForeignKey(verbose_name='resource', related_name='operationresources', to='input.Resource'),
    ),
    migrations.AlterField(
      model_name='operationresource',
      name='skill',
      field=models.ForeignKey(blank=True, related_name='operationresources', null=True, verbose_name='skill', to='input.Skill'),
    ),

    # Renaming flow to operationmaterial
    migrations.RenameModel('flow', 'operationmaterial'),
    migrations.AlterModelTable(name='operationmaterial', table='operationmaterial'),
    migrations.AlterModelOptions(
      name='operationmaterial',
      options={'verbose_name_plural': 'operation materials', 'verbose_name': 'operation material'},
    ),

    # OperationMaterial refers to an item now, and no longer a buffer
    migrations.AddField(
      model_name='operationmaterial',
      name='item',
      field=models.ForeignKey(verbose_name='item', to='input.Item', related_name='operationmaterials', null=True),
      preserve_default=False,
    ),
    migrations.RunSQL(
      '''
      update operationmaterial
      set item_id = (
        select buffer.item_id from buffer
        where buffer.name = operationmaterial.thebuffer_id
        )
      ''',
      '''
      update operationmaterial
      set thebuffer_id = (
        select buffer.name from buffer
        inner join operation
          on operationmaterial.operation_id = operation.name
        where buffer.item_id = operationmaterial.item_id
          and buffer.location_id = operation.location_id
        )
        '''
      ),
    migrations.AlterField(
      model_name='operationmaterial',
      name='item',
      field=models.ForeignKey(related_name='operationmaterials', to='input.Item', verbose_name='item'),
    ),
    migrations.AlterUniqueTogether(
      name='operationmaterial',
      unique_together=set([('operation', 'item', 'effective_start')]),
    ),
    migrations.RemoveField(
      model_name='operationmaterial',
      name='thebuffer',
    ),
    migrations.AlterField(
      model_name='operationmaterial',
      name='operation',
      field=models.ForeignKey(verbose_name='operation', related_name='operationmaterials', to='input.Operation'),
    ),

    # Changing all fields with durations to be of type "interval" rather than "number"
    migrations.RunSQL(
      "alter table buffer alter column min_interval type interval using min_interval * '1 sec'::interval",
      "alter table buffer alter column min_interval type numeric(15,4) using extract(epoch from min_interval)",
      state_operations=[
        migrations.AlterField(
          model_name='buffer',
          name='min_interval',
          field=models.DurationField(help_text='Batching window for grouping replenishments in batches', verbose_name='min_interval', blank=True, null=True),
          )
        ]
      ),
    migrations.RunSQL(
      "alter table demand alter column maxlateness type interval using maxlateness * '1 sec'::interval",
      "alter table demand alter column maxlateness type numeric(15,4) using extract(epoch from maxlateness)",
      state_operations=[
        migrations.AlterField(
          model_name='demand',
          name='maxlateness',
          field=models.DurationField(help_text='Maximum lateness allowed when planning this demand', blank=True, verbose_name='maximum lateness', null=True)
          )
        ]
      ),
    migrations.RunSQL(
      "alter table itemdistribution alter column fence type interval using fence * '1 sec'::interval",
      "alter table itemdistribution alter column fence type numeric(15,4) using extract(epoch from fence)",
      state_operations=[
        migrations.AlterField(
          model_name='itemdistribution',
          name='fence',
          field=models.DurationField(help_text='Frozen fence for creating new shipments', blank=True, verbose_name='fence', null=True)
          )
        ]
      ),
    migrations.RunSQL(
      "alter table itemdistribution alter column leadtime type interval using leadtime * '1 sec'::interval",
      "alter table itemdistribution alter column leadtime type numeric(15,4) using extract(epoch from leadtime)",
      state_operations=[
        migrations.AlterField(
          model_name='itemdistribution',
          name='leadtime',
          field=models.DurationField(help_text='lead time', blank=True, verbose_name='lead time', null=True)
          )
        ]
      ),
    migrations.RunSQL(
      "alter table itemsupplier alter column fence type interval using fence * '1 sec'::interval",
      "alter table itemsupplier alter column fence type numeric(15,4) using extract(epoch from fence)",
      state_operations=[
       migrations.AlterField(
          model_name='itemsupplier',
          name='fence',
          field=models.DurationField(help_text='Frozen fence for creating new procurements', blank=True, verbose_name='fence', null=True)
          )
        ]
      ),
    migrations.RunSQL(
      "alter table itemsupplier alter column leadtime type interval using leadtime * '1 sec'::interval",
      "alter table itemsupplier alter column leadtime type numeric(15,4) using extract(epoch from leadtime)",
      state_operations=[
        migrations.AlterField(
          model_name='itemsupplier',
          name='leadtime',
          field=models.DurationField(help_text='Purchasing lead time', blank=True, verbose_name='lead time', null=True)
          )
        ]
      ),
    migrations.RunSQL(
      "alter table operation alter column duration type interval using duration * '1 sec'::interval",
      "alter table operation alter column duration type numeric(15,4) using extract(epoch from duration)",
      state_operations=[
        migrations.AlterField(
          model_name='operation',
          name='duration',
          field=models.DurationField(help_text='A fixed duration for the operation', blank=True, verbose_name='duration', null=True)
          )
        ]
      ),
    migrations.RunSQL(
      "alter table operation alter column duration_per type interval using duration_per * '1 sec'::interval",
      "alter table operation alter column duration_per type numeric(15,4) using extract(epoch from duration_per)",
      state_operations=[
        migrations.AlterField(
          model_name='operation',
          name='duration_per',
          field=models.DurationField(help_text='A variable duration for the operation', blank=True, verbose_name='duration per unit', null=True)
          )
        ]
      ),
    migrations.RunSQL(
      "alter table operation alter column fence type interval using fence * '1 sec'::interval",
      "alter table operation alter column fence type numeric(15,4) using extract(epoch from fence)",
      state_operations=[
        migrations.AlterField(
          model_name='operation',
          name='fence',
          field=models.DurationField(help_text='Operationplans within this time window from the current day are expected to be released to production ERP', blank=True, verbose_name='release fence', null=True)
          )
        ]
      ),
    migrations.RunSQL(
      "alter table operation alter column posttime type interval using posttime * '1 sec'::interval",
      "alter table operation alter column posttime type numeric(15,4) using extract(epoch from posttime)",
      state_operations=[
        migrations.AlterField(
          model_name='operation',
          name='posttime',
          field=models.DurationField(help_text='A delay time to be respected as a soft constraint after ending the operation', blank=True, verbose_name='post-op time', null=True)
          )
        ]
      ),
    migrations.RunSQL(
      "alter table resource alter column maxearly type interval using maxearly * '1 sec'::interval",
      "alter table resource alter column maxearly type numeric(15,4) using extract(epoch from maxearly)",
      state_operations=[
        migrations.AlterField(
          model_name='resource',
          name='maxearly',
          field=models.DurationField(help_text='Time window before the ask date where we look for available capacity', blank=True, verbose_name='max early', null=True)
          )
        ]
      ),
    migrations.RunSQL(
      "alter table setuprule alter column duration type interval using duration * '1 sec'::interval",
      "alter table setuprule alter column duration type numeric(15,4) using extract(epoch from duration)",
      state_operations=[
        migrations.AlterField(
          model_name='setuprule',
          name='duration',
          field=models.DurationField(help_text='Duration of the changeover', blank=True, verbose_name='duration', null=True)
          )
        ]
      ),
    migrations.AlterField(
      model_name='item',
      name='operation',
      field=models.ForeignKey(related_name='operation', verbose_name='delivery operation', to='input.Operation', blank=True, null=True, help_text='Default operation used to ship a demand for this item'),
    ),

    # Renaming model output.flowplan to operationplanmaterial
    migrations.CreateModel(
      name='OperationPlanMaterial',
      fields=[
        ('id', models.AutoField(verbose_name='ID', primary_key=True, serialize=False, auto_created=True)),
        ('buffer', models.CharField(db_index=True, verbose_name='buffer', max_length=300)),
        ('quantity', models.DecimalField(verbose_name='quantity', decimal_places=4, max_digits=15)),
        ('flowdate', models.DateTimeField(db_index=True, verbose_name='date')),
        ('onhand', models.DecimalField(verbose_name='onhand', decimal_places=4, max_digits=15)),
        ('operationplan', models.ForeignKey(verbose_name='operationplan', to='input.OperationPlan')),
      ],
      options={
        'verbose_name': 'operationplan material',
        'db_table': 'operationplanmaterial',
        'ordering': ['buffer', 'flowdate'],
        'verbose_name_plural': 'operationplan materials',
      },
    ),

    # Renaming model output.loadplan to operationplanresource
    migrations.CreateModel(
      name='OperationPlanResource',
      fields=[
        ('id', models.AutoField(verbose_name='ID', primary_key=True, serialize=False, auto_created=True)),
        ('resource', models.CharField(db_index=True, verbose_name='resource', max_length=300)),
        ('quantity', models.DecimalField(verbose_name='quantity', decimal_places=4, max_digits=15)),
        ('startdate', models.DateTimeField(db_index=True, verbose_name='startdate')),
        ('enddate', models.DateTimeField(db_index=True, verbose_name='enddate')),
        ('setup', models.CharField(verbose_name='setup', max_length=300, null=True)),
        ('operationplan', models.ForeignKey(verbose_name='operationplan', to='input.OperationPlan')),
      ],
      options={
        'verbose_name': 'operationplan resource',
        'db_table': 'operationplanresource',
        'ordering': ['resource', 'startdate'],
        'verbose_name_plural': 'operationplan resources',
      },
    ),

    # Operation.location field is no longer nullable
    migrations.AlterField(
      model_name='operation',
      name='location',
      field=models.ForeignKey(verbose_name='location', to='input.Location'),
    ),

    # New JSON field to store plan information
    migrations.AddField(
      model_name='demand',
      name='plan',
      field=JSONField(default='{}', editable=False, null=True, blank=True),
    ),

    # Operationplan table now unifies output.operation_plan, purchase_order
    # and distribution_order.
    # Proxy models provide visibility on a subset of the operationplans.
    migrations.AddField(
      model_name='operationplan',
      name='plan',
      field=JSONField(default='{}', editable=False, null=True, blank=True),
    ),
    migrations.AddField(
      model_name='operationplan',
      name='destination',
      field=models.ForeignKey(to='input.Location', blank=True, related_name='destinations', null=True, verbose_name='destination'),
    ),
    migrations.AddField(
      model_name='operationplan',
      name='item',
      field=models.ForeignKey(to='input.Item', blank=True, null=True, verbose_name='item'),
    ),
    migrations.AddField(
      model_name='operationplan',
      name='location',
      field=models.ForeignKey(to='input.Location', blank=True, null=True, verbose_name='location'),
    ),
    migrations.AddField(
      model_name='operationplan',
      name='origin',
      field=models.ForeignKey(to='input.Location', blank=True, related_name='origins', null=True, verbose_name='origin'),
    ),
    migrations.AddField(
      model_name='operationplan',
      name='supplier',
      field=models.ForeignKey(to='input.Supplier', blank=True, null=True, verbose_name='supplier'),
    ),
    migrations.AddField(
      model_name='operationplan',
      name='type',
      field=models.CharField(help_text='Order type', db_index=True, verbose_name='type', choices=[('STCK', 'inventory'), ('MO', 'manufacturing order'), ('PO', 'purchase order'), ('DO', 'distribution order'), ('DLVR', 'customer shipment')], max_length=5, default='MO'),
      preserve_default=False,
    ),
    migrations.AddField(
      model_name='operationplan',
      name='demand',
      field=models.ForeignKey(to='input.Demand', blank=True, null=True, verbose_name='demand'),
    ),
    migrations.AddField(
      model_name='operationplan',
      name='name',
      field=models.CharField(db_index=True, null=True, max_length=1000),
    ),
    migrations.AddField(
      model_name='operationplan',
      name='due',
      field=models.DateTimeField(db_index=False, blank=True, null=True, verbose_name='due'),
    ),
    migrations.AddField(
      model_name='operationplan',
      name='delay',
      field=models.DurationField(verbose_name='delay', editable=False, blank=True, null=True),
    ),
    migrations.AlterField(
      model_name='operationplan',
      name='operation',
      field=models.ForeignKey(to='input.Operation', blank=True, null=True, verbose_name='operation'),
    ),
    migrations.AlterField(
      model_name='operationplan',
      name='status',
      field=models.CharField(blank=True, choices=[('proposed', 'proposed'), ('approved', 'approved'), ('confirmed', 'confirmed'), ('closed', 'closed')], null=True, verbose_name='status', help_text='Status of the order', max_length=20),
    ),

    # Remove the operation field from item
    migrations.RunSQL(
     '''
     update demand
     set operation_id = item.operation_id
     from item
     where demand.operation_id is null
       and item.operation_id is not null
       and item.name = demand.item_id
     ''',
     migrations.RunSQL.noop
    ),
    migrations.RemoveField(
      model_name='item',
      name='operation',
    ),

  ]
