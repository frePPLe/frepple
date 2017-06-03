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


class Migration(migrations.Migration):

    dependencies = [
        ('common', '0002_defaultuser'),
    ]

    operations = [
        migrations.CreateModel(
            name='Wizard',
            fields=[
                ('name', models.CharField(max_length=300, verbose_name='name', primary_key=True, serialize=False)),
                ('sequenceorder', models.IntegerField(verbose_name='progress', help_text='Model completion level')),
                ('url_doc', models.URLField(blank=True, null=True, verbose_name='documentation URL', max_length=500)),
                ('url_internaldoc', models.URLField(blank=True, null=True, verbose_name='wizard URL', max_length=500)),
                ('status', models.BooleanField(default=True)),
                ('owner', models.ForeignKey(blank=True, verbose_name='owner', null=True, related_name='xchildren', help_text='Hierarchical parent', to='common.Wizard')),
            ],
            options={
                'db_table': 'common_wizard',
                'ordering': ['sequenceorder'],
            },
        ),
    ]
