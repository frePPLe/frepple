#
# Copyright (C) 2015 by frePPLe bvba
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
import datetime

from django.conf import settings
from django.core.management import call_command
from django.db import models, migrations
import django.utils.timezone

import freppledb.common.fields


def loadParameters(apps, schema_editor):
  call_command('loaddata', "parameters.json", app_label="input")


class Migration(migrations.Migration):

    dependencies = [
        ('common', '0001_initial'),
        ('admin', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='Buffer',
            fields=[
                ('lft', models.PositiveIntegerField(editable=False, blank=True, null=True, db_index=True)),
                ('rght', models.PositiveIntegerField(editable=False, blank=True, null=True)),
                ('lvl', models.PositiveIntegerField(editable=False, blank=True, null=True)),
                ('name', models.CharField(help_text='Unique identifier', serialize=False, verbose_name='name', max_length=settings.NAMESIZE, primary_key=True)),
                ('source', models.CharField(blank=True, null=True, max_length=settings.CATEGORYSIZE, db_index=True, verbose_name='source')),
                ('lastmodified', models.DateTimeField(editable=False, verbose_name='last modified', db_index=True, default=django.utils.timezone.now)),
                ('description', models.CharField(blank=True, null=True, max_length=settings.DESCRIPTIONSIZE, verbose_name='description')),
                ('category', models.CharField(blank=True, null=True, max_length=settings.CATEGORYSIZE, db_index=True, verbose_name='category')),
                ('subcategory', models.CharField(blank=True, null=True, max_length=settings.CATEGORYSIZE, db_index=True, verbose_name='subcategory')),
                ('type', models.CharField(max_length=20, default='default', null=True, choices=[('default', 'Default'), ('infinite', 'Infinite'), ('procure', 'Procure')], blank=True, verbose_name='type')),
                ('onhand', models.DecimalField(help_text='current inventory', max_digits=settings.MAX_DIGITS, decimal_places=settings.DECIMAL_PLACES, default='0.00', null=True, blank=True, verbose_name='onhand')),
                ('minimum', models.DecimalField(help_text='Safety stock', max_digits=settings.MAX_DIGITS, decimal_places=settings.DECIMAL_PLACES, default='0.00', null=True, blank=True, verbose_name='minimum')),
                ('carrying_cost', models.DecimalField(help_text='Cost of holding inventory in this buffer, expressed as an annual percentage of the item price.', max_digits=settings.MAX_DIGITS, decimal_places=settings.DECIMAL_PLACES, null=True, blank=True, verbose_name='carrying cost')),
                ('leadtime', freppledb.common.fields.DurationField(help_text='Leadtime for supplier of a procure buffer', max_digits=settings.MAX_DIGITS, decimal_places=settings.DECIMAL_PLACES, null=True, blank=True, verbose_name='leadtime')),
                ('fence', freppledb.common.fields.DurationField(help_text='Frozen fence for creating new procurements', max_digits=settings.MAX_DIGITS, decimal_places=settings.DECIMAL_PLACES, null=True, blank=True, verbose_name='fence')),
                ('min_inventory', models.DecimalField(help_text='Inventory level that triggers replenishment of a procure buffer', max_digits=settings.MAX_DIGITS, decimal_places=settings.DECIMAL_PLACES, null=True, blank=True, verbose_name='min_inventory')),
                ('max_inventory', models.DecimalField(help_text='Inventory level to which a procure buffer is replenished', max_digits=settings.MAX_DIGITS, decimal_places=settings.DECIMAL_PLACES, null=True, blank=True, verbose_name='max_inventory')),
                ('min_interval', freppledb.common.fields.DurationField(help_text='Minimum time interval between replenishments of a procure buffer', max_digits=settings.MAX_DIGITS, decimal_places=settings.DECIMAL_PLACES, null=True, blank=True, verbose_name='min_interval')),
                ('max_interval', freppledb.common.fields.DurationField(help_text='Maximum time interval between replenishments of a procure buffer', max_digits=settings.MAX_DIGITS, decimal_places=settings.DECIMAL_PLACES, null=True, blank=True, verbose_name='max_interval')),
                ('size_minimum', models.DecimalField(help_text='Minimum size of replenishments of a procure buffer', max_digits=settings.MAX_DIGITS, decimal_places=settings.DECIMAL_PLACES, null=True, blank=True, verbose_name='size_minimum')),
                ('size_multiple', models.DecimalField(help_text='Replenishments of a procure buffer are a multiple of this quantity', max_digits=settings.MAX_DIGITS, decimal_places=settings.DECIMAL_PLACES, null=True, blank=True, verbose_name='size_multiple')),
                ('size_maximum', models.DecimalField(help_text='Maximum size of replenishments of a procure buffer', max_digits=settings.MAX_DIGITS, decimal_places=settings.DECIMAL_PLACES, null=True, blank=True, verbose_name='size_maximum')),
            ],
            options={
                'ordering': ['name'],
                'verbose_name': 'buffer',
                'abstract': False,
                'db_table': 'buffer',
                'verbose_name_plural': 'buffers',
            },
        ),
        migrations.CreateModel(
            name='Calendar',
            fields=[
                ('source', models.CharField(blank=True, null=True, max_length=settings.CATEGORYSIZE, db_index=True, verbose_name='source')),
                ('lastmodified', models.DateTimeField(editable=False, verbose_name='last modified', db_index=True, default=django.utils.timezone.now)),
                ('name', models.CharField(serialize=False, verbose_name='name', max_length=settings.NAMESIZE, primary_key=True)),
                ('description', models.CharField(blank=True, null=True, max_length=settings.DESCRIPTIONSIZE, verbose_name='description')),
                ('category', models.CharField(blank=True, null=True, max_length=settings.CATEGORYSIZE, db_index=True, verbose_name='category')),
                ('subcategory', models.CharField(blank=True, null=True, max_length=settings.CATEGORYSIZE, db_index=True, verbose_name='subcategory')),
                ('defaultvalue', models.DecimalField(help_text='Value to be used when no entry is effective', max_digits=settings.MAX_DIGITS, decimal_places=settings.DECIMAL_PLACES, default='0.00', null=True, blank=True, verbose_name='default value')),
            ],
            options={
                'ordering': ['name'],
                'verbose_name': 'calendar',
                'abstract': False,
                'db_table': 'calendar',
                'verbose_name_plural': 'calendars',
            },
        ),
        migrations.CreateModel(
            name='CalendarBucket',
            fields=[
                ('source', models.CharField(blank=True, null=True, max_length=settings.CATEGORYSIZE, db_index=True, verbose_name='source')),
                ('lastmodified', models.DateTimeField(editable=False, verbose_name='last modified', db_index=True, default=django.utils.timezone.now)),
                ('id', models.AutoField(serialize=False, primary_key=True, verbose_name='identifier')),
                ('startdate', models.DateTimeField(blank=True, null=True, verbose_name='start date')),
                ('enddate', models.DateTimeField(blank=True, verbose_name='end date', null=True, default=datetime.datetime(2030, 12, 31, 0, 0))),
                ('value', models.DecimalField(decimal_places=settings.DECIMAL_PLACES, max_digits=settings.MAX_DIGITS, verbose_name='value', blank=True, default='0.00')),
                ('priority', models.IntegerField(blank=True, verbose_name='priority', null=True, default=0)),
                ('monday', models.BooleanField(verbose_name='Monday', default=True)),
                ('tuesday', models.BooleanField(verbose_name='Tuesday', default=True)),
                ('wednesday', models.BooleanField(verbose_name='Wednesday', default=True)),
                ('thursday', models.BooleanField(verbose_name='Thursday', default=True)),
                ('friday', models.BooleanField(verbose_name='Friday', default=True)),
                ('saturday', models.BooleanField(verbose_name='Saturday', default=True)),
                ('sunday', models.BooleanField(verbose_name='Sunday', default=True)),
                ('starttime', models.TimeField(blank=True, verbose_name='start time', null=True, default=datetime.time(0, 0))),
                ('endtime', models.TimeField(blank=True, verbose_name='end time', null=True, default=datetime.time(23, 59, 59))),
                ('calendar', models.ForeignKey(to='input.Calendar', related_name='buckets', verbose_name='calendar')),
            ],
            options={
                'ordering': ['calendar', 'id'],
                'verbose_name': 'calendar bucket',
                'abstract': False,
                'db_table': 'calendarbucket',
                'verbose_name_plural': 'calendar buckets',
            },
        ),
        migrations.CreateModel(
            name='Customer',
            fields=[
                ('lft', models.PositiveIntegerField(editable=False, blank=True, null=True, db_index=True)),
                ('rght', models.PositiveIntegerField(editable=False, blank=True, null=True)),
                ('lvl', models.PositiveIntegerField(editable=False, blank=True, null=True)),
                ('name', models.CharField(help_text='Unique identifier', serialize=False, verbose_name='name', max_length=settings.NAMESIZE, primary_key=True)),
                ('source', models.CharField(blank=True, null=True, max_length=settings.CATEGORYSIZE, db_index=True, verbose_name='source')),
                ('lastmodified', models.DateTimeField(editable=False, verbose_name='last modified', db_index=True, default=django.utils.timezone.now)),
                ('description', models.CharField(blank=True, null=True, max_length=settings.DESCRIPTIONSIZE, verbose_name='description')),
                ('category', models.CharField(blank=True, null=True, max_length=settings.CATEGORYSIZE, db_index=True, verbose_name='category')),
                ('subcategory', models.CharField(blank=True, null=True, max_length=settings.CATEGORYSIZE, db_index=True, verbose_name='subcategory')),
                ('owner', models.ForeignKey(help_text='Hierarchical parent', null=True, to='input.Customer', blank=True, related_name='xchildren', verbose_name='owner')),
            ],
            options={
                'ordering': ['name'],
                'verbose_name': 'customer',
                'abstract': False,
                'db_table': 'customer',
                'verbose_name_plural': 'customers',
            },
        ),
        migrations.CreateModel(
            name='Demand',
            fields=[
                ('lft', models.PositiveIntegerField(editable=False, blank=True, null=True, db_index=True)),
                ('rght', models.PositiveIntegerField(editable=False, blank=True, null=True)),
                ('lvl', models.PositiveIntegerField(editable=False, blank=True, null=True)),
                ('name', models.CharField(help_text='Unique identifier', serialize=False, verbose_name='name', max_length=settings.NAMESIZE, primary_key=True)),
                ('source', models.CharField(blank=True, null=True, max_length=settings.CATEGORYSIZE, db_index=True, verbose_name='source')),
                ('lastmodified', models.DateTimeField(editable=False, verbose_name='last modified', db_index=True, default=django.utils.timezone.now)),
                ('description', models.CharField(blank=True, null=True, max_length=settings.DESCRIPTIONSIZE, verbose_name='description')),
                ('category', models.CharField(blank=True, null=True, max_length=settings.CATEGORYSIZE, db_index=True, verbose_name='category')),
                ('subcategory', models.CharField(blank=True, null=True, max_length=settings.CATEGORYSIZE, db_index=True, verbose_name='subcategory')),
                ('due', models.DateTimeField(help_text='Due date of the demand', verbose_name='due')),
                ('status', models.CharField(help_text='Status of the demand. Only "open" demands are planned', max_length=10, default='open', null=True, choices=[('inquiry', 'Inquiry'), ('quote', 'Quote'), ('open', 'Open'), ('closed', 'Closed'), ('canceled', 'Canceled')], blank=True, verbose_name='status')),
                ('quantity', models.DecimalField(max_digits=settings.MAX_DIGITS, decimal_places=settings.DECIMAL_PLACES, verbose_name='quantity')),
                ('priority', models.PositiveIntegerField(help_text='Priority of the demand (lower numbers indicate more important demands)', choices=[(1, '1'), (2, '2'), (3, '3'), (4, '4'), (5, '5'), (6, '6'), (7, '7'), (8, '8'), (9, '9'), (10, '10'), (11, '11'), (12, '12'), (13, '13'), (14, '14'), (15, '15'), (16, '16'), (17, '17'), (18, '18'), (19, '19'), (20, '20')], verbose_name='priority', default=10)),
                ('minshipment', models.DecimalField(help_text='Minimum shipment quantity when planning this demand', max_digits=settings.MAX_DIGITS, decimal_places=settings.DECIMAL_PLACES, null=True, blank=True, verbose_name='minimum shipment')),
                ('maxlateness', freppledb.common.fields.DurationField(help_text='Maximum lateness allowed when planning this demand', max_digits=settings.MAX_DIGITS, decimal_places=settings.DECIMAL_PLACES, null=True, blank=True, verbose_name='maximum lateness')),
                ('customer', models.ForeignKey(null=True, to='input.Customer', blank=True, verbose_name='customer')),
            ],
            options={
                'ordering': ['name'],
                'verbose_name': 'demand',
                'abstract': False,
                'db_table': 'demand',
                'verbose_name_plural': 'demands',
            },
        ),
        migrations.CreateModel(
            name='Flow',
            fields=[
                ('source', models.CharField(blank=True, null=True, max_length=settings.CATEGORYSIZE, db_index=True, verbose_name='source')),
                ('lastmodified', models.DateTimeField(editable=False, verbose_name='last modified', db_index=True, default=django.utils.timezone.now)),
                ('id', models.AutoField(serialize=False, primary_key=True, verbose_name='identifier')),
                ('quantity', models.DecimalField(help_text='Quantity to consume or produce per operationplan unit', max_digits=settings.MAX_DIGITS, verbose_name='quantity', decimal_places=settings.DECIMAL_PLACES, default='1.00')),
                ('type', models.CharField(help_text='Consume/produce material at the start or the end of the operationplan', max_length=20, default='start', null=True, choices=[('start', 'Start'), ('end', 'End'), ('fixed_start', 'Fixed start'), ('fixed_end', 'Fixed end')], blank=True, verbose_name='type')),
                ('effective_start', models.DateTimeField(help_text='Validity start date', blank=True, null=True, verbose_name='effective start')),
                ('effective_end', models.DateTimeField(help_text='Validity end date', blank=True, null=True, verbose_name='effective end')),
                ('name', models.CharField(help_text='Optional name of this flow', blank=True, null=True, max_length=settings.NAMESIZE, verbose_name='name')),
                ('alternate', models.CharField(help_text='Puts the flow in a group of alternate flows', blank=True, null=True, max_length=settings.NAMESIZE, verbose_name='alternate')),
                ('priority', models.IntegerField(help_text='Priority of this flow in a group of alternates', blank=True, verbose_name='priority', null=True, default=1)),
                ('search', models.CharField(help_text='Method to select preferred alternate', max_length=20, null=True, choices=[('PRIORITY', 'priority'), ('MINCOST', 'minimum cost'), ('MINPENALTY', 'minimum penalty'), ('MINCOSTPENALTY', 'minimum cost plus penalty')], blank=True, verbose_name='search mode')),
            ],
            options={
                'verbose_name': 'flow',
                'abstract': False,
                'db_table': 'flow',
                'verbose_name_plural': 'flows',
            },
        ),
        migrations.CreateModel(
            name='Item',
            fields=[
                ('lft', models.PositiveIntegerField(editable=False, blank=True, null=True, db_index=True)),
                ('rght', models.PositiveIntegerField(editable=False, blank=True, null=True)),
                ('lvl', models.PositiveIntegerField(editable=False, blank=True, null=True)),
                ('name', models.CharField(help_text='Unique identifier', serialize=False, verbose_name='name', max_length=settings.NAMESIZE, primary_key=True)),
                ('source', models.CharField(blank=True, null=True, max_length=settings.CATEGORYSIZE, db_index=True, verbose_name='source')),
                ('lastmodified', models.DateTimeField(editable=False, verbose_name='last modified', db_index=True, default=django.utils.timezone.now)),
                ('description', models.CharField(blank=True, null=True, max_length=settings.DESCRIPTIONSIZE, verbose_name='description')),
                ('category', models.CharField(blank=True, null=True, max_length=settings.CATEGORYSIZE, db_index=True, verbose_name='category')),
                ('subcategory', models.CharField(blank=True, null=True, max_length=settings.CATEGORYSIZE, db_index=True, verbose_name='subcategory')),
                ('price', models.DecimalField(help_text='Selling price of the item', max_digits=settings.MAX_DIGITS, decimal_places=settings.DECIMAL_PLACES, null=True, blank=True, verbose_name='price')),
            ],
            options={
                'ordering': ['name'],
                'verbose_name': 'item',
                'abstract': False,
                'db_table': 'item',
                'verbose_name_plural': 'items',
            },
        ),
        migrations.CreateModel(
            name='Load',
            fields=[
                ('source', models.CharField(blank=True, null=True, max_length=settings.CATEGORYSIZE, db_index=True, verbose_name='source')),
                ('lastmodified', models.DateTimeField(editable=False, verbose_name='last modified', db_index=True, default=django.utils.timezone.now)),
                ('id', models.AutoField(serialize=False, primary_key=True, verbose_name='identifier')),
                ('quantity', models.DecimalField(max_digits=settings.MAX_DIGITS, verbose_name='quantity', decimal_places=settings.DECIMAL_PLACES, default='1.00')),
                ('effective_start', models.DateTimeField(help_text='Validity start date', blank=True, null=True, verbose_name='effective start')),
                ('effective_end', models.DateTimeField(help_text='Validity end date', blank=True, null=True, verbose_name='effective end')),
                ('name', models.CharField(help_text='Optional name of this load', blank=True, null=True, max_length=settings.NAMESIZE, verbose_name='name')),
                ('alternate', models.CharField(help_text='Puts the load in a group of alternate loads', blank=True, null=True, max_length=settings.NAMESIZE, verbose_name='alternate')),
                ('priority', models.IntegerField(help_text='Priority of this load in a group of alternates', blank=True, verbose_name='priority', null=True, default=1)),
                ('setup', models.CharField(help_text='Setup required on the resource for this operation', blank=True, null=True, max_length=settings.NAMESIZE, verbose_name='setup')),
                ('search', models.CharField(help_text='Method to select preferred alternate', max_length=20, null=True, choices=[('PRIORITY', 'priority'), ('MINCOST', 'minimum cost'), ('MINPENALTY', 'minimum penalty'), ('MINCOSTPENALTY', 'minimum cost plus penalty')], blank=True, verbose_name='search mode')),
            ],
            options={
                'verbose_name': 'load',
                'abstract': False,
                'db_table': 'resourceload',
                'verbose_name_plural': 'loads',
            },
        ),
        migrations.CreateModel(
            name='Location',
            fields=[
                ('lft', models.PositiveIntegerField(editable=False, blank=True, null=True, db_index=True)),
                ('rght', models.PositiveIntegerField(editable=False, blank=True, null=True)),
                ('lvl', models.PositiveIntegerField(editable=False, blank=True, null=True)),
                ('name', models.CharField(help_text='Unique identifier', serialize=False, verbose_name='name', max_length=settings.NAMESIZE, primary_key=True)),
                ('source', models.CharField(blank=True, null=True, max_length=settings.CATEGORYSIZE, db_index=True, verbose_name='source')),
                ('lastmodified', models.DateTimeField(editable=False, verbose_name='last modified', db_index=True, default=django.utils.timezone.now)),
                ('description', models.CharField(blank=True, null=True, max_length=settings.DESCRIPTIONSIZE, verbose_name='description')),
                ('category', models.CharField(blank=True, null=True, max_length=settings.CATEGORYSIZE, db_index=True, verbose_name='category')),
                ('subcategory', models.CharField(blank=True, null=True, max_length=settings.CATEGORYSIZE, db_index=True, verbose_name='subcategory')),
                ('available', models.ForeignKey(help_text='Calendar defining the working hours and holidays of this location', null=True, to='input.Calendar', blank=True, verbose_name='available')),
                ('owner', models.ForeignKey(help_text='Hierarchical parent', null=True, to='input.Location', blank=True, related_name='xchildren', verbose_name='owner')),
            ],
            options={
                'ordering': ['name'],
                'verbose_name': 'location',
                'abstract': False,
                'db_table': 'location',
                'verbose_name_plural': 'locations',
            },
        ),
        migrations.CreateModel(
            name='Operation',
            fields=[
                ('source', models.CharField(blank=True, null=True, max_length=settings.CATEGORYSIZE, db_index=True, verbose_name='source')),
                ('lastmodified', models.DateTimeField(editable=False, verbose_name='last modified', db_index=True, default=django.utils.timezone.now)),
                ('name', models.CharField(serialize=False, verbose_name='name', max_length=settings.NAMESIZE, primary_key=True)),
                ('type', models.CharField(max_length=20, default='fixed_time', null=True, choices=[('fixed_time', 'fixed_time'), ('time_per', 'time_per'), ('routing', 'routing'), ('alternate', 'alternate'), ('split', 'split')], blank=True, verbose_name='type')),
                ('description', models.CharField(blank=True, null=True, max_length=settings.DESCRIPTIONSIZE, verbose_name='description')),
                ('category', models.CharField(blank=True, null=True, max_length=settings.CATEGORYSIZE, db_index=True, verbose_name='category')),
                ('subcategory', models.CharField(blank=True, null=True, max_length=settings.CATEGORYSIZE, db_index=True, verbose_name='subcategory')),
                ('fence', freppledb.common.fields.DurationField(help_text='Operationplans within this time window from the current day are expected to be released to production ERP', max_digits=settings.MAX_DIGITS, decimal_places=settings.DECIMAL_PLACES, null=True, blank=True, verbose_name='release fence')),
                ('posttime', freppledb.common.fields.DurationField(help_text='A delay time to be respected as a soft constraint after ending the operation', max_digits=settings.MAX_DIGITS, decimal_places=settings.DECIMAL_PLACES, null=True, blank=True, verbose_name='post-op time')),
                ('sizeminimum', models.DecimalField(help_text='A minimum quantity for operationplans', max_digits=settings.MAX_DIGITS, decimal_places=settings.DECIMAL_PLACES, default='1.0', null=True, blank=True, verbose_name='size minimum')),
                ('sizemultiple', models.DecimalField(help_text='A multiple quantity for operationplans', max_digits=settings.MAX_DIGITS, decimal_places=settings.DECIMAL_PLACES, null=True, blank=True, verbose_name='size multiple')),
                ('sizemaximum', models.DecimalField(help_text='A maximum quantity for operationplans', max_digits=settings.MAX_DIGITS, decimal_places=settings.DECIMAL_PLACES, null=True, blank=True, verbose_name='size maximum')),
                ('cost', models.DecimalField(help_text='Cost per operationplan unit', max_digits=settings.MAX_DIGITS, decimal_places=settings.DECIMAL_PLACES, null=True, blank=True, verbose_name='cost')),
                ('duration', freppledb.common.fields.DurationField(help_text='A fixed duration for the operation', max_digits=settings.MAX_DIGITS, decimal_places=settings.DECIMAL_PLACES, null=True, blank=True, verbose_name='duration')),
                ('duration_per', freppledb.common.fields.DurationField(help_text='A variable duration for the operation', max_digits=settings.MAX_DIGITS, decimal_places=settings.DECIMAL_PLACES, null=True, blank=True, verbose_name='duration per unit')),
                ('search', models.CharField(help_text='Method to select preferred alternate', max_length=20, null=True, choices=[('PRIORITY', 'priority'), ('MINCOST', 'minimum cost'), ('MINPENALTY', 'minimum penalty'), ('MINCOSTPENALTY', 'minimum cost plus penalty')], blank=True, verbose_name='search mode')),
                ('location', models.ForeignKey(null=True, to='input.Location', blank=True, verbose_name='location')),
            ],
            options={
                'ordering': ['name'],
                'verbose_name': 'operation',
                'abstract': False,
                'db_table': 'operation',
                'verbose_name_plural': 'operations',
            },
        ),
        migrations.CreateModel(
            name='OperationPlan',
            fields=[
                ('source', models.CharField(blank=True, null=True, max_length=settings.CATEGORYSIZE, db_index=True, verbose_name='source')),
                ('lastmodified', models.DateTimeField(editable=False, verbose_name='last modified', db_index=True, default=django.utils.timezone.now)),
                ('id', models.IntegerField(help_text='Unique identifier of an operationplan', serialize=False, primary_key=True, verbose_name='identifier')),
                ('quantity', models.DecimalField(max_digits=settings.MAX_DIGITS, verbose_name='quantity', decimal_places=settings.DECIMAL_PLACES, default='1.00')),
                ('startdate', models.DateTimeField(help_text='start date', verbose_name='start date')),
                ('enddate', models.DateTimeField(help_text='end date', verbose_name='end date')),
                ('locked', models.BooleanField(help_text='Prevent or allow changes', verbose_name='locked', default=True)),
                ('operation', models.ForeignKey(to='input.Operation', verbose_name='operation')),
                ('owner', models.ForeignKey(help_text='Hierarchical parent', null=True, to='input.OperationPlan', blank=True, related_name='xchildren', verbose_name='owner')),
            ],
            options={
                'ordering': ['id'],
                'verbose_name': 'operationplan',
                'abstract': False,
                'db_table': 'operationplan',
                'verbose_name_plural': 'operationplans',
            },
        ),
        migrations.CreateModel(
            name='Resource',
            fields=[
                ('lft', models.PositiveIntegerField(editable=False, blank=True, null=True, db_index=True)),
                ('rght', models.PositiveIntegerField(editable=False, blank=True, null=True)),
                ('lvl', models.PositiveIntegerField(editable=False, blank=True, null=True)),
                ('name', models.CharField(help_text='Unique identifier', serialize=False, verbose_name='name', max_length=settings.NAMESIZE, primary_key=True)),
                ('source', models.CharField(blank=True, null=True, max_length=settings.CATEGORYSIZE, db_index=True, verbose_name='source')),
                ('lastmodified', models.DateTimeField(editable=False, verbose_name='last modified', db_index=True, default=django.utils.timezone.now)),
                ('description', models.CharField(blank=True, null=True, max_length=settings.DESCRIPTIONSIZE, verbose_name='description')),
                ('category', models.CharField(blank=True, null=True, max_length=settings.CATEGORYSIZE, db_index=True, verbose_name='category')),
                ('subcategory', models.CharField(blank=True, null=True, max_length=settings.CATEGORYSIZE, db_index=True, verbose_name='subcategory')),
                ('type', models.CharField(max_length=20, default='default', null=True, choices=[('default', 'Default'), ('buckets', 'Buckets'), ('infinite', 'Infinite')], blank=True, verbose_name='type')),
                ('maximum', models.DecimalField(help_text='Size of the resource', max_digits=settings.MAX_DIGITS, decimal_places=settings.DECIMAL_PLACES, default='1.00', null=True, blank=True, verbose_name='maximum')),
                ('cost', models.DecimalField(help_text='Cost for using 1 unit of the resource for 1 hour', max_digits=settings.MAX_DIGITS, decimal_places=settings.DECIMAL_PLACES, null=True, blank=True, verbose_name='cost')),
                ('maxearly', freppledb.common.fields.DurationField(help_text='Time window before the ask date where we look for available capacity', max_digits=settings.MAX_DIGITS, decimal_places=0, null=True, blank=True, verbose_name='max early')),
                ('setup', models.CharField(help_text='Setup of the resource at the start of the plan', blank=True, null=True, max_length=settings.NAMESIZE, verbose_name='setup')),
                ('location', models.ForeignKey(null=True, to='input.Location', blank=True, verbose_name='location')),
                ('maximum_calendar', models.ForeignKey(help_text='Calendar defining the resource size varying over time', null=True, to='input.Calendar', blank=True, verbose_name='maximum calendar')),
                ('owner', models.ForeignKey(help_text='Hierarchical parent', null=True, to='input.Resource', blank=True, related_name='xchildren', verbose_name='owner')),
            ],
            options={
                'ordering': ['name'],
                'verbose_name': 'resource',
                'abstract': False,
                'db_table': 'resource',
                'verbose_name_plural': 'resources',
            },
        ),
        migrations.CreateModel(
            name='ResourceSkill',
            fields=[
                ('source', models.CharField(blank=True, null=True, max_length=settings.CATEGORYSIZE, db_index=True, verbose_name='source')),
                ('lastmodified', models.DateTimeField(editable=False, verbose_name='last modified', db_index=True, default=django.utils.timezone.now)),
                ('id', models.AutoField(serialize=False, primary_key=True, verbose_name='identifier')),
                ('effective_start', models.DateTimeField(help_text='Validity start date', blank=True, null=True, verbose_name='effective start')),
                ('effective_end', models.DateTimeField(help_text='Validity end date', blank=True, null=True, verbose_name='effective end')),
                ('priority', models.IntegerField(help_text='Priority of this skill in a group of alternates', blank=True, verbose_name='priority', null=True, default=1)),
                ('resource', models.ForeignKey(to='input.Resource', related_name='skills', verbose_name='resource')),
            ],
            options={
                'ordering': ['resource', 'skill'],
                'verbose_name_plural': 'resource skills',
                'abstract': False,
                'db_table': 'resourceskill',
                'verbose_name': 'resource skill',
            },
        ),
        migrations.CreateModel(
            name='SetupMatrix',
            fields=[
                ('source', models.CharField(blank=True, null=True, max_length=settings.CATEGORYSIZE, db_index=True, verbose_name='source')),
                ('lastmodified', models.DateTimeField(editable=False, verbose_name='last modified', db_index=True, default=django.utils.timezone.now)),
                ('name', models.CharField(serialize=False, verbose_name='name', max_length=settings.NAMESIZE, primary_key=True)),
            ],
            options={
                'ordering': ['name'],
                'verbose_name': 'setup matrix',
                'abstract': False,
                'db_table': 'setupmatrix',
                'verbose_name_plural': 'setup matrices',
            },
        ),
        migrations.CreateModel(
            name='SetupRule',
            fields=[
                ('id', models.AutoField(serialize=False, verbose_name='ID', primary_key=True, auto_created=True)),
                ('source', models.CharField(blank=True, null=True, max_length=settings.CATEGORYSIZE, db_index=True, verbose_name='source')),
                ('lastmodified', models.DateTimeField(editable=False, verbose_name='last modified', db_index=True, default=django.utils.timezone.now)),
                ('priority', models.IntegerField(verbose_name='priority')),
                ('fromsetup', models.CharField(help_text='Name of the old setup (wildcard characters are supported)', blank=True, null=True, max_length=settings.NAMESIZE, verbose_name='from setup')),
                ('tosetup', models.CharField(help_text='Name of the new setup (wildcard characters are supported)', blank=True, null=True, max_length=settings.NAMESIZE, verbose_name='to setup')),
                ('duration', freppledb.common.fields.DurationField(help_text='Duration of the changeover', max_digits=settings.MAX_DIGITS, decimal_places=0, null=True, blank=True, verbose_name='duration')),
                ('cost', models.DecimalField(help_text='Cost of the conversion', max_digits=settings.MAX_DIGITS, decimal_places=settings.DECIMAL_PLACES, null=True, blank=True, verbose_name='cost')),
                ('setupmatrix', models.ForeignKey(to='input.SetupMatrix', related_name='rules', verbose_name='setup matrix')),
            ],
            options={
                'ordering': ['priority'],
                'verbose_name_plural': 'setup matrix rules',
                'abstract': False,
                'db_table': 'setuprule',
                'verbose_name': 'setup matrix rule',
            },
        ),
        migrations.CreateModel(
            name='Skill',
            fields=[
                ('source', models.CharField(blank=True, null=True, max_length=settings.CATEGORYSIZE, db_index=True, verbose_name='source')),
                ('lastmodified', models.DateTimeField(editable=False, verbose_name='last modified', db_index=True, default=django.utils.timezone.now)),
                ('name', models.CharField(help_text='Unique identifier', serialize=False, verbose_name='name', max_length=settings.NAMESIZE, primary_key=True)),
            ],
            options={
                'ordering': ['name'],
                'verbose_name': 'skill',
                'abstract': False,
                'db_table': 'skill',
                'verbose_name_plural': 'skills',
            },
        ),
        migrations.CreateModel(
            name='SubOperation',
            fields=[
                ('source', models.CharField(blank=True, null=True, max_length=settings.CATEGORYSIZE, db_index=True, verbose_name='source')),
                ('lastmodified', models.DateTimeField(editable=False, verbose_name='last modified', db_index=True, default=django.utils.timezone.now)),
                ('id', models.AutoField(serialize=False, primary_key=True, verbose_name='identifier')),
                ('priority', models.IntegerField(help_text='Sequence of this operation among the suboperations. Negative values are ignored.', verbose_name='priority', default=1)),
                ('effective_start', models.DateTimeField(help_text='Validity start date', blank=True, null=True, verbose_name='effective start')),
                ('effective_end', models.DateTimeField(help_text='Validity end date', blank=True, null=True, verbose_name='effective end')),
                ('operation', models.ForeignKey(help_text='Parent operation', to='input.Operation', related_name='suboperations', verbose_name='operation')),
                ('suboperation', models.ForeignKey(help_text='Child operation', to='input.Operation', related_name='superoperations', verbose_name='suboperation')),
            ],
            options={
                'ordering': ['operation', 'priority', 'suboperation'],
                'verbose_name': 'suboperation',
                'abstract': False,
                'db_table': 'suboperation',
                'verbose_name_plural': 'suboperations',
            },
        ),
        migrations.CreateModel(
            name='Supplier',
            fields=[
                ('lft', models.PositiveIntegerField(editable=False, blank=True, null=True, db_index=True)),
                ('rght', models.PositiveIntegerField(editable=False, blank=True, null=True)),
                ('lvl', models.PositiveIntegerField(editable=False, blank=True, null=True)),
                ('name', models.CharField(help_text='Unique identifier', serialize=False, verbose_name='name', max_length=settings.NAMESIZE, primary_key=True)),
                ('source', models.CharField(blank=True, null=True, max_length=settings.CATEGORYSIZE, db_index=True, verbose_name='source')),
                ('lastmodified', models.DateTimeField(editable=False, verbose_name='last modified', db_index=True, default=django.utils.timezone.now)),
                ('description', models.CharField(blank=True, null=True, max_length=settings.DESCRIPTIONSIZE, verbose_name='description')),
                ('category', models.CharField(blank=True, null=True, max_length=settings.CATEGORYSIZE, db_index=True, verbose_name='category')),
                ('subcategory', models.CharField(blank=True, null=True, max_length=settings.CATEGORYSIZE, db_index=True, verbose_name='subcategory')),
                ('owner', models.ForeignKey(help_text='Hierarchical parent', null=True, to='input.Supplier', blank=True, related_name='xchildren', verbose_name='owner')),
            ],
            options={
                'ordering': ['name'],
                'verbose_name': 'supplier',
                'abstract': False,
                'db_table': 'supplier',
                'verbose_name_plural': 'suppliers',
            },
        ),
        migrations.AddField(
            model_name='resourceskill',
            name='skill',
            field=models.ForeignKey(to='input.Skill', related_name='resources', verbose_name='skill'),
        ),
        migrations.AddField(
            model_name='resource',
            name='setupmatrix',
            field=models.ForeignKey(help_text='Setup matrix defining the conversion time and cost', null=True, to='input.SetupMatrix', blank=True, verbose_name='setup matrix'),
        ),
        migrations.AddField(
            model_name='load',
            name='operation',
            field=models.ForeignKey(to='input.Operation', related_name='loads', verbose_name='operation'),
        ),
        migrations.AddField(
            model_name='load',
            name='resource',
            field=models.ForeignKey(to='input.Resource', related_name='loads', verbose_name='resource'),
        ),
        migrations.AddField(
            model_name='load',
            name='skill',
            field=models.ForeignKey(related_name='loads', null=True, to='input.Skill', blank=True, verbose_name='skill'),
        ),
        migrations.AddField(
            model_name='item',
            name='operation',
            field=models.ForeignKey(help_text='Default operation used to ship a demand for this item', null=True, to='input.Operation', blank=True, verbose_name='delivery operation'),
        ),
        migrations.AddField(
            model_name='item',
            name='owner',
            field=models.ForeignKey(help_text='Hierarchical parent', null=True, to='input.Item', blank=True, related_name='xchildren', verbose_name='owner'),
        ),
        migrations.AddField(
            model_name='flow',
            name='operation',
            field=models.ForeignKey(to='input.Operation', related_name='flows', verbose_name='operation'),
        ),
        migrations.AddField(
            model_name='flow',
            name='thebuffer',
            field=models.ForeignKey(to='input.Buffer', related_name='flows', verbose_name='buffer'),
        ),
        migrations.AddField(
            model_name='demand',
            name='item',
            field=models.ForeignKey(null=True, to='input.Item', blank=True, verbose_name='item'),
        ),
        migrations.AddField(
            model_name='demand',
            name='operation',
            field=models.ForeignKey(help_text='Operation used to satisfy this demand', null=True, to='input.Operation', blank=True, related_name='used_demand', verbose_name='delivery operation'),
        ),
        migrations.AddField(
            model_name='demand',
            name='owner',
            field=models.ForeignKey(help_text='Hierarchical parent', null=True, to='input.Demand', blank=True, related_name='xchildren', verbose_name='owner'),
        ),
        migrations.AddField(
            model_name='buffer',
            name='item',
            field=models.ForeignKey(to='input.Item', null=True, verbose_name='item'),
        ),
        migrations.AddField(
            model_name='buffer',
            name='location',
            field=models.ForeignKey(null=True, to='input.Location', blank=True, verbose_name='location'),
        ),
        migrations.AddField(
            model_name='buffer',
            name='minimum_calendar',
            field=models.ForeignKey(help_text='Calendar storing a time-dependent safety stock profile', null=True, to='input.Calendar', blank=True, verbose_name='minimum calendar'),
        ),
        migrations.AddField(
            model_name='buffer',
            name='owner',
            field=models.ForeignKey(help_text='Hierarchical parent', null=True, to='input.Buffer', blank=True, related_name='xchildren', verbose_name='owner'),
        ),
        migrations.AddField(
            model_name='buffer',
            name='producing',
            field=models.ForeignKey(help_text='Operation to replenish the buffer', null=True, to='input.Operation', blank=True, related_name='used_producing', verbose_name='producing'),
        ),
        migrations.AlterUniqueTogether(
            name='setuprule',
            unique_together=set([('setupmatrix', 'priority')]),
        ),
        migrations.AlterUniqueTogether(
            name='resourceskill',
            unique_together=set([('resource', 'skill')]),
        ),
        migrations.AlterUniqueTogether(
            name='load',
            unique_together=set([('operation', 'resource')]),
        ),
        migrations.AlterUniqueTogether(
            name='flow',
            unique_together=set([('operation', 'thebuffer')]),
        ),
        migrations.RunPython(loadParameters),
    ]
