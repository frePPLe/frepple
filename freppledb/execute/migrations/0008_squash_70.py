#
# Copyright (C) 2022 by frePPLe bv
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

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion
import freppledb.common.fields


class Migration(migrations.Migration):

    replaces = [('execute', '0005_squashed_60'), ('execute', '0006_meta'), ('execute', '0007_scheduled_task')]

    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('common', '0014_squashed_60'),
    ]

    operations = [
        migrations.CreateModel(
            name='Task',
            fields=[
                ('id', models.AutoField(editable=False, primary_key=True, serialize=False, verbose_name='identifier')),
                ('name', models.CharField(db_index=True, editable=False, max_length=50, verbose_name='name')),
                ('submitted', models.DateTimeField(editable=False, verbose_name='submitted')),
                ('started', models.DateTimeField(blank=True, editable=False, null=True, verbose_name='started')),
                ('finished', models.DateTimeField(blank=True, editable=False, null=True, verbose_name='submitted')),
                ('arguments', models.TextField(editable=False, max_length=200, null=True, verbose_name='arguments')),
                ('status', models.CharField(editable=False, max_length=20, verbose_name='status')),
                ('message', models.TextField(editable=False, max_length=200, null=True, verbose_name='message')),
                ('user', models.ForeignKey(blank=True, editable=False, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='tasks', to=settings.AUTH_USER_MODEL, verbose_name='user')),
                ('logfile', models.TextField(editable=False, max_length=200, null=True, verbose_name='log file')),
                ('processid', models.IntegerField(editable=False, null=True, verbose_name='processid')),
            ],
            options={
                'db_table': 'execute_log',
                'verbose_name': 'task',
                'verbose_name_plural': 'tasks',
                'default_permissions': ['view'],
            },
        ),
        migrations.CreateModel(
            name='ScheduledTask',
            fields=[
                ('name', models.CharField(db_index=True, max_length=300, primary_key=True, serialize=False, verbose_name='name')),
                ('next_run', models.DateTimeField(blank=True, db_index=True, null=True, verbose_name='nextrun')),
                ('email_failure', models.CharField(blank=True, max_length=300, null=True, verbose_name='email_failure')),
                ('email_success', models.CharField(blank=True, max_length=300, null=True, verbose_name='email_success')),
                ('data', freppledb.common.fields.JSONBField(blank=True, default='{}', null=True)),
                ('user', models.ForeignKey(editable=False, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='schedules', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'verbose_name': 'scheduled task',
                'verbose_name_plural': 'scheduled tasks',
                'db_table': 'execute_schedule',
            },
        ),
    ]
