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
from django.conf import settings


class Migration(migrations.Migration):

    dependencies = [
        ('common', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='Task',
            fields=[
                ('id', models.AutoField(editable=False, primary_key=True, verbose_name='identifier', serialize=False)),
                ('name', models.CharField(editable=False, verbose_name='name', db_index=True, max_length=20)),
                ('submitted', models.DateTimeField(editable=False, verbose_name='submitted')),
                ('started', models.DateTimeField(null=True, editable=False, verbose_name='started', blank=True)),
                ('finished', models.DateTimeField(null=True, editable=False, verbose_name='submitted', blank=True)),
                ('arguments', models.TextField(null=True, editable=False, verbose_name='arguments', max_length=200)),
                ('status', models.CharField(editable=False, verbose_name='status', max_length=20)),
                ('message', models.TextField(null=True, editable=False, verbose_name='message', max_length=200)),
                ('user', models.ForeignKey(verbose_name='user', null=True, editable=False, blank=True, to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'db_table': 'execute_log',
                'verbose_name': 'task',
                'verbose_name_plural': 'tasks',
            },
        ),
    ]
