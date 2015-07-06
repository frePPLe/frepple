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
from django.conf import settings
from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('common', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='Constraint',
            fields=[
                ('id', models.AutoField(verbose_name='ID', auto_created=True, primary_key=True, serialize=False)),
                ('demand', models.CharField(verbose_name='demand', db_index=True, max_length=settings.NAMESIZE)),
                ('entity', models.CharField(verbose_name='entity', db_index=True, max_length=15)),
                ('owner', models.CharField(verbose_name='owner', db_index=True, max_length=settings.NAMESIZE)),
                ('name', models.CharField(verbose_name='name', db_index=True, max_length=settings.CATEGORYSIZE)),
                ('description', models.CharField(verbose_name='description', max_length=80)),
                ('startdate', models.DateTimeField(verbose_name='start date', db_index=True)),
                ('enddate', models.DateTimeField(verbose_name='end date', db_index=True)),
                ('weight', models.DecimalField(verbose_name='weight', decimal_places=settings.DECIMAL_PLACES, max_digits=settings.MAX_DIGITS)),
            ],
            options={
                'verbose_name': 'constraint',
                'db_table': 'out_constraint',
                'ordering': ['demand', 'startdate'],
                'verbose_name_plural': 'constraints',
            },
        ),
        migrations.CreateModel(
            name='Demand',
            fields=[
                ('id', models.AutoField(verbose_name='ID', auto_created=True, primary_key=True, serialize=False)),
                ('demand', models.CharField(verbose_name='demand', db_index=True, null=True, max_length=settings.NAMESIZE)),
                ('item', models.CharField(verbose_name='item', db_index=True, null=True, max_length=settings.NAMESIZE)),
                ('customer', models.CharField(verbose_name='customer', db_index=True, null=True, max_length=settings.NAMESIZE)),
                ('due', models.DateTimeField(verbose_name='due', db_index=True)),
                ('quantity', models.DecimalField(verbose_name='demand quantity', decimal_places=settings.DECIMAL_PLACES, max_digits=settings.MAX_DIGITS, default='0.00')),
                ('planquantity', models.DecimalField(verbose_name='planned quantity', null=True, decimal_places=settings.DECIMAL_PLACES, max_digits=settings.MAX_DIGITS, default='0.00')),
                ('plandate', models.DateTimeField(verbose_name='planned date', db_index=True, null=True)),
                ('operationplan', models.IntegerField(verbose_name='operationplan', db_index=True, null=True)),
            ],
            options={
                'verbose_name': 'demand',
                'db_table': 'out_demand',
                'ordering': ['id'],
                'verbose_name_plural': 'demands',
            },
        ),
        migrations.CreateModel(
            name='DemandPegging',
            fields=[
                ('id', models.AutoField(verbose_name='ID', auto_created=True, primary_key=True, serialize=False)),
                ('demand', models.CharField(verbose_name='demand', db_index=True, max_length=settings.NAMESIZE)),
                ('level', models.IntegerField(verbose_name='level')),
                ('operationplan', models.IntegerField(verbose_name='operationplan', db_index=True)),
                ('quantity', models.DecimalField(verbose_name='quantity', decimal_places=settings.DECIMAL_PLACES, max_digits=settings.MAX_DIGITS, default='0.00')),
            ],
            options={
                'verbose_name': 'demand pegging',
                'db_table': 'out_demandpegging',
                'ordering': ['id'],
                'verbose_name_plural': 'demand peggings',
            },
        ),
        migrations.CreateModel(
            name='FlowPlan',
            fields=[
                ('id', models.AutoField(verbose_name='ID', auto_created=True, primary_key=True, serialize=False)),
                ('thebuffer', models.CharField(verbose_name='buffer', db_index=True, max_length=settings.NAMESIZE)),
                ('quantity', models.DecimalField(verbose_name='quantity', decimal_places=settings.DECIMAL_PLACES, max_digits=settings.MAX_DIGITS)),
                ('flowdate', models.DateTimeField(verbose_name='date', db_index=True)),
                ('onhand', models.DecimalField(verbose_name='onhand', decimal_places=settings.DECIMAL_PLACES, max_digits=settings.MAX_DIGITS)),
            ],
            options={
                'verbose_name': 'flowplan',
                'db_table': 'out_flowplan',
                'ordering': ['thebuffer', 'flowdate'],
                'verbose_name_plural': 'flowplans',
            },
        ),
        migrations.CreateModel(
            name='LoadPlan',
            fields=[
                ('id', models.AutoField(verbose_name='ID', auto_created=True, primary_key=True, serialize=False)),
                ('theresource', models.CharField(verbose_name='resource', db_index=True, max_length=settings.NAMESIZE)),
                ('quantity', models.DecimalField(verbose_name='quantity', decimal_places=settings.DECIMAL_PLACES, max_digits=settings.MAX_DIGITS)),
                ('startdate', models.DateTimeField(verbose_name='startdate', db_index=True)),
                ('enddate', models.DateTimeField(verbose_name='enddate', db_index=True)),
                ('setup', models.CharField(verbose_name='setup', null=True, max_length=settings.NAMESIZE)),
            ],
            options={
                'verbose_name': 'loadplan',
                'db_table': 'out_loadplan',
                'ordering': ['theresource', 'startdate'],
                'verbose_name_plural': 'loadplans',
            },
        ),
        migrations.CreateModel(
            name='OperationPlan',
            fields=[
                ('id', models.IntegerField(verbose_name='identifier', primary_key=True, serialize=False)),
                ('operation', models.CharField(verbose_name='operation', db_index=True, null=True, max_length=settings.NAMESIZE)),
                ('quantity', models.DecimalField(verbose_name='quantity', decimal_places=settings.DECIMAL_PLACES, max_digits=settings.MAX_DIGITS, default='1.00')),
                ('unavailable', models.DecimalField(verbose_name='unavailable', decimal_places=settings.DECIMAL_PLACES, max_digits=settings.MAX_DIGITS, default='0.00')),
                ('startdate', models.DateTimeField(verbose_name='startdate', db_index=True)),
                ('enddate', models.DateTimeField(verbose_name='enddate', db_index=True)),
                ('criticality', models.DecimalField(verbose_name='criticality', null=True, decimal_places=settings.DECIMAL_PLACES, max_digits=settings.MAX_DIGITS)),
                ('locked', models.BooleanField(verbose_name='locked', default=True)),
                ('owner', models.IntegerField(verbose_name='owner', db_index=True, blank=True, null=True)),
            ],
            options={
                'verbose_name': 'operationplan',
                'db_table': 'out_operationplan',
                'verbose_name_plural': 'operationplans',
            },
        ),
        migrations.CreateModel(
            name='Problem',
            fields=[
                ('id', models.AutoField(verbose_name='ID', auto_created=True, primary_key=True, serialize=False)),
                ('entity', models.CharField(verbose_name='entity', db_index=True, max_length=15)),
                ('owner', models.CharField(verbose_name='owner', db_index=True, max_length=settings.NAMESIZE)),
                ('name', models.CharField(verbose_name='name', db_index=True, max_length=settings.CATEGORYSIZE)),
                ('description', models.CharField(verbose_name='description', max_length=settings.NAMESIZE + 20)),
                ('startdate', models.DateTimeField(verbose_name='start date', db_index=True)),
                ('enddate', models.DateTimeField(verbose_name='end date', db_index=True)),
                ('weight', models.DecimalField(verbose_name='weight', decimal_places=settings.DECIMAL_PLACES, max_digits=settings.MAX_DIGITS)),
            ],
            options={
                'verbose_name': 'problem',
                'db_table': 'out_problem',
                'ordering': ['startdate'],
                'verbose_name_plural': 'problems',
            },
        ),
        migrations.CreateModel(
            name='ResourceSummary',
            fields=[
                ('id', models.AutoField(verbose_name='ID', auto_created=True, primary_key=True, serialize=False)),
                ('theresource', models.CharField(verbose_name='resource', max_length=settings.NAMESIZE)),
                ('startdate', models.DateTimeField(verbose_name='startdate')),
                ('available', models.DecimalField(verbose_name='available', null=True, decimal_places=settings.DECIMAL_PLACES, max_digits=settings.MAX_DIGITS)),
                ('unavailable', models.DecimalField(verbose_name='unavailable', null=True, decimal_places=settings.DECIMAL_PLACES, max_digits=settings.MAX_DIGITS)),
                ('setup', models.DecimalField(verbose_name='setup', null=True, decimal_places=settings.DECIMAL_PLACES, max_digits=settings.MAX_DIGITS)),
                ('load', models.DecimalField(verbose_name='load', null=True, decimal_places=settings.DECIMAL_PLACES, max_digits=settings.MAX_DIGITS)),
                ('free', models.DecimalField(verbose_name='free', null=True, decimal_places=settings.DECIMAL_PLACES, max_digits=settings.MAX_DIGITS)),
            ],
            options={
                'verbose_name': 'resource summary',
                'db_table': 'out_resourceplan',
                'ordering': ['theresource', 'startdate'],
                'verbose_name_plural': 'resource summaries',
            },
        ),
        migrations.AlterUniqueTogether(
            name='resourcesummary',
            unique_together=set([('theresource', 'startdate')]),
        ),
        migrations.AddField(
            model_name='loadplan',
            name='operationplan',
            field=models.ForeignKey(verbose_name='operationplan', related_name='loadplans', to='output.OperationPlan'),
        ),
        migrations.AddField(
            model_name='flowplan',
            name='operationplan',
            field=models.ForeignKey(verbose_name='operationplan', related_name='flowplans', to='output.OperationPlan'),
        ),
    ]
