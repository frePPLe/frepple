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
from datetime import datetime

from django.db import migrations, models
import django.contrib.auth.models
import freppledb.common.fields
import django.core.validators
import django.utils.timezone
from django.conf import settings


def createAdminUser(apps, schema_editor):
  if not schema_editor.connection.alias == 'default':
    return
  from django.contrib.auth import get_user_model
  User = get_user_model()
  usr = User.objects.create_superuser('admin', 'your@company.com', 'admin')
  usr.first_name = 'admin'
  usr.last_name = 'admin'
  usr.date_joined = datetime(2000, 1, 1)
  usr.horizontype = True
  usr.horizonlength = 6
  usr.horizonunit = "month"
  usr.language = "auto"
  usr.save()


class Migration(migrations.Migration):

    replaces = [('common', '0002_defaultuser'), ('common', '0003_wizard'), ('common', '0006_permission_names'), ('common', '0007_preferences')]

    dependencies = [
      ('contenttypes', '0002_remove_content_type_name'),
      ('auth', '0006_require_contenttypes_0002'),
    ]

    operations = [        
        migrations.RunPython(
            code=createAdminUser,
        ),
        migrations.CreateModel(
            name='Wizard',
            fields=[
                ('name', models.CharField(serialize=False, verbose_name='name', primary_key=True, max_length=300)),
                ('sequenceorder', models.IntegerField(help_text='Model completion level', verbose_name='progress')),
                ('url_doc', models.URLField(blank=True, max_length=500, verbose_name='documentation URL', null=True)),
                ('url_internaldoc', models.URLField(blank=True, max_length=500, verbose_name='wizard URL', null=True)),
                ('status', models.BooleanField(default=True)),
                ('owner', models.ForeignKey(blank=True, related_name='xchildren', verbose_name='owner', to='common.Wizard', help_text='Hierarchical parent', null=True)),
            ],
            options={
                'db_table': 'common_wizard',
                'ordering': ['sequenceorder'],
            },
        ),
        migrations.CreateModel(
            name='UserPreference',
            fields=[
                ('id', models.AutoField(serialize=False, verbose_name='identifier', primary_key=True)),
                ('property', models.CharField(max_length=100)),
                ('value', freppledb.common.fields.JSONField(max_length=1000)),
                ('user', models.ForeignKey(related_name='preferences', verbose_name='user', to=settings.AUTH_USER_MODEL, null=True, editable=False)),
            ],
            options={
                'verbose_name_plural': 'preferences',
                'verbose_name': 'preference',
                'db_table': 'common_preference',
            },
        ),
        migrations.AlterUniqueTogether(
            name='userpreference',
            unique_together=set([('user', 'property')]),
        ),           
    ]
