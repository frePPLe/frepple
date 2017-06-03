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
import freppledb.common.fields
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

  dependencies = [
    ('common', '0006_permission_names'),
  ]

  operations = [
    migrations.CreateModel(
      name='UserPreference',
      fields=[
        ('id', models.AutoField(primary_key=True, verbose_name='identifier', serialize=False)),
        ('property', models.CharField(max_length=100)),
        ('value', freppledb.common.fields.JSONField(max_length=1000)),
      ],
      options={
        'verbose_name_plural': 'preferences',
        'verbose_name': 'preference',
        'db_table': 'common_preference',
      },
    ),
    migrations.AddField(
      model_name='userpreference',
      name='user',
      field=models.ForeignKey(to=settings.AUTH_USER_MODEL, editable=False, null=True, verbose_name='user', related_name='preferences'),
    ),
    migrations.AlterUniqueTogether(
      name='userpreference',
      unique_together=set([('user', 'property')]),
    ),
  ]
