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

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('common', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='Constraint',
            fields=[
                ('id', models.AutoField(auto_created=True, verbose_name='ID', serialize=False, primary_key=True)),
                ('demand', models.CharField(verbose_name='demand', db_index=True, max_length=300)),
                ('entity', models.CharField(verbose_name='entity', db_index=True, max_length=15)),
                ('owner', models.CharField(verbose_name='owner', db_index=True, max_length=300)),
                ('name', models.CharField(verbose_name='name', db_index=True, max_length=20)),
                ('description', models.CharField(verbose_name='description', max_length=1000)),
                ('startdate', models.DateTimeField(verbose_name='start date', db_index=True)),
                ('enddate', models.DateTimeField(verbose_name='end date', db_index=True)),
                ('weight', models.DecimalField(verbose_name='weight', max_digits=15, decimal_places=4)),
            ],
            options={
                'db_table': 'out_constraint',
                'ordering': ['demand', 'startdate'],
                'verbose_name_plural': 'constraints',
                'verbose_name': 'constraint',
            },
        ),
        migrations.CreateModel(
            name='Demand',
            fields=[
                ('id', models.AutoField(auto_created=True, verbose_name='ID', serialize=False, primary_key=True)),
                ('demand', models.CharField(null=True, verbose_name='demand', db_index=True, max_length=300)),
                ('item', models.CharField(null=True, verbose_name='item', db_index=True, max_length=300)),
                ('customer', models.CharField(null=True, verbose_name='customer', db_index=True, max_length=300)),
                ('due', models.DateTimeField(verbose_name='due', db_index=True)),
                ('quantity', models.DecimalField(max_digits=15, verbose_name='demand quantity', default='0.00', decimal_places=4)),
                ('planquantity', models.DecimalField(null=True, max_digits=15, verbose_name='planned quantity', default='0.00', decimal_places=4)),
                ('plandate', models.DateTimeField(null=True, verbose_name='planned date', db_index=True)),
                ('operationplan', models.IntegerField(null=True, verbose_name='operationplan', db_index=True)),
            ],
            options={
                'db_table': 'out_demand',
                'ordering': ['id'],
                'verbose_name_plural': 'demands',
                'verbose_name': 'demand',
            },
        ),
        migrations.CreateModel(
            name='DemandPegging',
            fields=[
                ('id', models.AutoField(auto_created=True, verbose_name='ID', serialize=False, primary_key=True)),
                ('demand', models.CharField(verbose_name='demand', db_index=True, max_length=300)),
                ('level', models.IntegerField(verbose_name='level')),
                ('operationplan', models.IntegerField(verbose_name='operationplan', db_index=True)),
                ('quantity', models.DecimalField(max_digits=15, verbose_name='quantity', default='0.00', decimal_places=4)),
            ],
            options={
                'db_table': 'out_demandpegging',
                'ordering': ['id'],
                'verbose_name_plural': 'demand peggings',
                'verbose_name': 'demand pegging',
            },
        ),
        migrations.CreateModel(
            name='FlowPlan',
            fields=[
                ('id', models.AutoField(auto_created=True, verbose_name='ID', serialize=False, primary_key=True)),
                ('thebuffer', models.CharField(verbose_name='buffer', db_index=True, max_length=300)),
                ('quantity', models.DecimalField(verbose_name='quantity', max_digits=15, decimal_places=4)),
                ('flowdate', models.DateTimeField(verbose_name='date', db_index=True)),
                ('onhand', models.DecimalField(verbose_name='onhand', max_digits=15, decimal_places=4)),
            ],
            options={
                'db_table': 'out_flowplan',
                'ordering': ['thebuffer', 'flowdate'],
                'verbose_name_plural': 'flowplans',
                'verbose_name': 'flowplan',
            },
        ),
        migrations.CreateModel(
            name='LoadPlan',
            fields=[
                ('id', models.AutoField(auto_created=True, verbose_name='ID', serialize=False, primary_key=True)),
                ('theresource', models.CharField(verbose_name='resource', db_index=True, max_length=300)),
                ('quantity', models.DecimalField(verbose_name='quantity', max_digits=15, decimal_places=4)),
                ('startdate', models.DateTimeField(verbose_name='startdate', db_index=True)),
                ('enddate', models.DateTimeField(verbose_name='enddate', db_index=True)),
                ('setup', models.CharField(null=True, verbose_name='setup', max_length=300)),
            ],
            options={
                'db_table': 'out_loadplan',
                'ordering': ['theresource', 'startdate'],
                'verbose_name_plural': 'loadplans',
                'verbose_name': 'loadplan',
            },
        ),
        migrations.CreateModel(
            name='OperationPlan',
            fields=[
                ('id', models.IntegerField(primary_key=True, verbose_name='identifier', serialize=False)),
                ('operation', models.CharField(null=True, verbose_name='operation', db_index=True, max_length=300)),
                ('quantity', models.DecimalField(max_digits=15, verbose_name='quantity', default='1.00', decimal_places=4)),
                ('unavailable', models.DecimalField(max_digits=15, verbose_name='unavailable', default='0.00', decimal_places=4)),
                ('startdate', models.DateTimeField(verbose_name='startdate', db_index=True)),
                ('enddate', models.DateTimeField(verbose_name='enddate', db_index=True)),
                ('criticality', models.DecimalField(null=True, verbose_name='criticality', max_digits=15, decimal_places=4)),
                ('locked', models.BooleanField(verbose_name='locked', default=True)),
                ('owner', models.IntegerField(null=True, blank=True, verbose_name='owner', db_index=True)),
            ],
            options={
                'db_table': 'out_operationplan',
                'verbose_name': 'operationplan',
                'verbose_name_plural': 'operationplans',
            },
        ),
        migrations.CreateModel(
            name='Problem',
            fields=[
                ('id', models.AutoField(auto_created=True, verbose_name='ID', serialize=False, primary_key=True)),
                ('entity', models.CharField(verbose_name='entity', db_index=True, max_length=15)),
                ('owner', models.CharField(verbose_name='owner', db_index=True, max_length=300)),
                ('name', models.CharField(verbose_name='name', db_index=True, max_length=20)),
                ('description', models.CharField(verbose_name='description', max_length=1000)),
                ('startdate', models.DateTimeField(verbose_name='start date', db_index=True)),
                ('enddate', models.DateTimeField(verbose_name='end date', db_index=True)),
                ('weight', models.DecimalField(verbose_name='weight', max_digits=15, decimal_places=4)),
            ],
            options={
                'db_table': 'out_problem',
                'ordering': ['startdate'],
                'verbose_name_plural': 'problems',
                'verbose_name': 'problem',
            },
        ),
        migrations.CreateModel(
            name='ResourceSummary',
            fields=[
                ('id', models.AutoField(auto_created=True, verbose_name='ID', serialize=False, primary_key=True)),
                ('theresource', models.CharField(verbose_name='resource', max_length=300)),
                ('startdate', models.DateTimeField(verbose_name='startdate')),
                ('available', models.DecimalField(null=True, verbose_name='available', max_digits=15, decimal_places=4)),
                ('unavailable', models.DecimalField(null=True, verbose_name='unavailable', max_digits=15, decimal_places=4)),
                ('setup', models.DecimalField(null=True, verbose_name='setup', max_digits=15, decimal_places=4)),
                ('load', models.DecimalField(null=True, verbose_name='load', max_digits=15, decimal_places=4)),
                ('free', models.DecimalField(null=True, verbose_name='free', max_digits=15, decimal_places=4)),
            ],
            options={
                'db_table': 'out_resourceplan',
                'ordering': ['theresource', 'startdate'],
                'verbose_name_plural': 'resource summaries',
                'verbose_name': 'resource summary',
            },
        ),
        migrations.AlterUniqueTogether(
            name='resourcesummary',
            unique_together=set([('theresource', 'startdate')]),
        ),
        migrations.AddField(
            model_name='loadplan',
            name='operationplan',
            field=models.ForeignKey(related_name='loadplans', verbose_name='operationplan', to='output.OperationPlan'),
        ),
        migrations.AddField(
            model_name='flowplan',
            name='operationplan',
            field=models.ForeignKey(related_name='flowplans', verbose_name='operationplan', to='output.OperationPlan'),
        ),
    ]
