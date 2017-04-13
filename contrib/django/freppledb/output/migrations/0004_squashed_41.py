#
# Copyright (C) 2017 by frePPLe bvba
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


class Migration(migrations.Migration):

    replaces = [('output', '0001_initial'), ('output', '0002_new_data_model'), ('output', '0003_number_precision')]

    dependencies = [
        ('common', '0008_squashed_41'),
    ]

    operations = [
        migrations.CreateModel(
            name='Constraint',
            fields=[
                ('id', models.AutoField(primary_key=True, serialize=False, auto_created=True, verbose_name='ID')),
                ('demand', models.CharField(max_length=300, verbose_name='demand', db_index=True)),
                ('entity', models.CharField(max_length=15, verbose_name='entity', db_index=True)),
                ('owner', models.CharField(max_length=300, verbose_name='owner', db_index=True)),
                ('name', models.CharField(max_length=20, verbose_name='name', db_index=True)),
                ('description', models.CharField(max_length=1000, verbose_name='description')),
                ('startdate', models.DateTimeField(verbose_name='start date', db_index=True)),
                ('enddate', models.DateTimeField(verbose_name='end date', db_index=True)),
                ('weight', models.DecimalField(verbose_name='weight', decimal_places=6, max_digits=15)),
            ],
            options={
                'verbose_name': 'constraint',
                'verbose_name_plural': 'constraints',
                'db_table': 'out_constraint',
                'ordering': ['demand', 'startdate'],
            },
        ),
        migrations.CreateModel(
            name='Problem',
            fields=[
                ('id', models.AutoField(primary_key=True, serialize=False, auto_created=True, verbose_name='ID')),
                ('entity', models.CharField(max_length=15, verbose_name='entity', db_index=True)),
                ('owner', models.CharField(max_length=300, verbose_name='owner', db_index=True)),
                ('name', models.CharField(max_length=20, verbose_name='name', db_index=True)),
                ('description', models.CharField(max_length=1000, verbose_name='description')),
                ('startdate', models.DateTimeField(verbose_name='start date', db_index=True)),
                ('enddate', models.DateTimeField(verbose_name='end date', db_index=True)),
                ('weight', models.DecimalField(verbose_name='weight', decimal_places=6, max_digits=15)),
            ],
            options={
                'verbose_name': 'problem',
                'verbose_name_plural': 'problems',
                'db_table': 'out_problem',
                'ordering': ['startdate'],
            },
        ),
        migrations.CreateModel(
            name='ResourceSummary',
            fields=[
                ('id', models.AutoField(primary_key=True, serialize=False, auto_created=True, verbose_name='ID')),
                ('theresource', models.CharField(max_length=300, verbose_name='resource')),
                ('startdate', models.DateTimeField(verbose_name='startdate')),
                ('available', models.DecimalField(verbose_name='available', null=True, decimal_places=4, max_digits=15)),
                ('unavailable', models.DecimalField(verbose_name='unavailable', null=True, decimal_places=4, max_digits=15)),
                ('setup', models.DecimalField(verbose_name='setup', null=True, decimal_places=4, max_digits=15)),
                ('load', models.DecimalField(verbose_name='load', null=True, decimal_places=4, max_digits=15)),
                ('free', models.DecimalField(verbose_name='free', null=True, decimal_places=4, max_digits=15)),
            ],
            options={
                'verbose_name': 'resource summary',
                'verbose_name_plural': 'resource summaries',
                'db_table': 'out_resourceplan',
                'ordering': ['theresource', 'startdate'],
            },
        ),
        migrations.AlterUniqueTogether(
            name='resourcesummary',
            unique_together=set([('theresource', 'startdate')]),
        ),
        migrations.AlterModelOptions(
            name='resourcesummary',
            options={'verbose_name': 'resource summary', 'verbose_name_plural': 'resource summaries', 'ordering': ['resource', 'startdate']},
        ),
        migrations.RenameField(
            model_name='resourcesummary',
            old_name='theresource',
            new_name='resource',
        ),
        migrations.AlterUniqueTogether(
            name='resourcesummary',
            unique_together=set([('resource', 'startdate')]),
        ),
        migrations.AlterField(
            model_name='resourcesummary',
            name='available',
            field=models.DecimalField(verbose_name='available', null=True, decimal_places=6, max_digits=15),
        ),
        migrations.AlterField(
            model_name='resourcesummary',
            name='free',
            field=models.DecimalField(verbose_name='free', null=True, decimal_places=6, max_digits=15),
        ),
        migrations.AlterField(
            model_name='resourcesummary',
            name='load',
            field=models.DecimalField(verbose_name='load', null=True, decimal_places=6, max_digits=15),
        ),
        migrations.AlterField(
            model_name='resourcesummary',
            name='setup',
            field=models.DecimalField(verbose_name='setup', null=True, decimal_places=6, max_digits=15),
        ),
        migrations.AlterField(
            model_name='resourcesummary',
            name='unavailable',
            field=models.DecimalField(verbose_name='unavailable', null=True, decimal_places=6, max_digits=15),
        ),
    ]
