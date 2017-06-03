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
import django.utils.timezone


class Migration(migrations.Migration):

    dependencies = [
        ('input', '0008_number_precision'),
    ]

    operations = [
        migrations.AddField(
            model_name='operationplanmaterial',
            name='lastmodified',
            field=models.DateTimeField(db_index=True, verbose_name='last modified', default=django.utils.timezone.now, editable=False),
        ),
        migrations.AddField(
            model_name='operationplanmaterial',
            name='source',
            field=models.CharField(db_index=True, max_length=300, blank=True, null=True, verbose_name='source'),
        ),
        migrations.AddField(
            model_name='operationplanmaterial',
            name='status',
            field=models.CharField(help_text='Status of the OperationPlanMaterial', choices=[('proposed', 'proposed'), ('confirmed', 'confirmed')], max_length=20, blank=True, null=True, verbose_name='status'),
        ),
        migrations.AddField(
            model_name='operationplanresource',
            name='lastmodified',
            field=models.DateTimeField(db_index=True, verbose_name='last modified', default=django.utils.timezone.now, editable=False),
        ),
        migrations.AddField(
            model_name='operationplanresource',
            name='source',
            field=models.CharField(db_index=True, max_length=300, blank=True, null=True, verbose_name='source'),
        ),
        migrations.AddField(
            model_name='operationplanresource',
            name='status',
            field=models.CharField(help_text='Status of the OperationPlanResource', choices=[('proposed', 'proposed'), ('confirmed', 'confirmed')], max_length=20, blank=True, null=True, verbose_name='status'),
        ),
    ]
