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

    dependencies = [
        ('output', '0004_squashed_41'),
    ]

    operations = [
        migrations.AlterField(
            model_name='constraint',
            name='weight',
            field=models.DecimalField(decimal_places=8, max_digits=20, verbose_name='weight'),
        ),
        migrations.AlterField(
            model_name='problem',
            name='weight',
            field=models.DecimalField(decimal_places=8, max_digits=20, verbose_name='weight'),
        ),
        migrations.AlterField(
            model_name='resourcesummary',
            name='available',
            field=models.DecimalField(decimal_places=8, max_digits=20, null=True, verbose_name='available'),
        ),
        migrations.AlterField(
            model_name='resourcesummary',
            name='free',
            field=models.DecimalField(decimal_places=8, max_digits=20, null=True, verbose_name='free'),
        ),
        migrations.AlterField(
            model_name='resourcesummary',
            name='load',
            field=models.DecimalField(decimal_places=8, max_digits=20, null=True, verbose_name='load'),
        ),
        migrations.AlterField(
            model_name='resourcesummary',
            name='setup',
            field=models.DecimalField(decimal_places=8, max_digits=20, null=True, verbose_name='setup'),
        ),
        migrations.AlterField(
            model_name='resourcesummary',
            name='unavailable',
            field=models.DecimalField(decimal_places=8, max_digits=20, null=True, verbose_name='unavailable'),
        ),
    ]
