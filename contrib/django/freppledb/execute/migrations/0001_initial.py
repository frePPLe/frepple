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
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('common', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='Task',
            fields=[
                ('id', models.AutoField(verbose_name='identifier', primary_key=True, editable=False, serialize=False)),
                ('name', models.CharField(max_length=20, db_index=True, verbose_name='name', editable=False)),
                ('submitted', models.DateTimeField(verbose_name='submitted', editable=False)),
                ('started', models.DateTimeField(null=True, blank=True, verbose_name='started', editable=False)),
                ('finished', models.DateTimeField(null=True, blank=True, verbose_name='submitted', editable=False)),
                ('arguments', models.TextField(null=True, max_length=200, verbose_name='arguments', editable=False)),
                ('status', models.CharField(max_length=20, verbose_name='status', editable=False)),
                ('message', models.TextField(null=True, max_length=200, verbose_name='message', editable=False)),
                ('user', models.ForeignKey(blank=True, verbose_name='user', editable=False, null=True, to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'db_table': 'execute_log',
                'verbose_name': 'task',
                'verbose_name_plural': 'tasks',
            },
        ),
    ]
