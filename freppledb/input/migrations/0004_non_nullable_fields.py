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
from django.db.models import Q, Count


def CheckReadyForMigration(apps, schema_editor):
  db = schema_editor.connection.alias
  Demand = apps.get_model("input", "Demand")
  cnt = Demand.objects.all().using(db).filter(
    Q(location__isnull=True) | Q(item__isnull=True) | Q(customer__isnull=True)
    ).count()
  if cnt:
    print('''

      Pre-migration check fails!
      The location, item and customer fields in the demand table can't be null any longer.

      There are %s records violating this new constraint.
      You will need to manually update these fields in your data before you can continue with the migration.
      ''' % cnt)
    raise ValueError("Manual migration required")
  Buffer = apps.get_model("input", "Buffer")
  cnt1 = Buffer.objects.all().using(db).filter(
    Q(item__isnull=True) | Q(location__isnull=True)
    ).count()
  cnt2 = Buffer.objects.values('item', 'location').annotate(Count('name')).filter(name__count__gt=1).count()
  if cnt1 or cnt2:
    print('''

      Pre-migration check fails!
      The item and location fields in the buffer table can't be null any longer.
      These combination of these fields also need to be unique together.

      There are %s records having a null item or location field.
      There are %s records violating the uniqueness constraint.
      You will need to manually update these fields in your data before you can continue with the migration.
      ''' % (cnt1, cnt2))
    raise ValueError("Manual migration required")


def CheckReadyForMigrationReverse(apps, schema_editor):
  return


class Migration(migrations.Migration):

  dependencies = [
    ('input', '0003_fence_for_po_and_do'),
  ]

  operations = [
    migrations.RunPython(CheckReadyForMigration, CheckReadyForMigrationReverse),
    migrations.AlterField(
      model_name='buffer',
      name='item',
      field=models.ForeignKey(verbose_name='item', to='input.Item'),
    ),
    migrations.AlterField(
      model_name='buffer',
      name='location',
      field=models.ForeignKey(verbose_name='location', to='input.Location'),
    ),
    migrations.AlterField(
      model_name='demand',
      name='customer',
      field=models.ForeignKey(verbose_name='customer', to='input.Customer'),
    ),
    migrations.AlterField(
      model_name='demand',
      name='item',
      field=models.ForeignKey(verbose_name='item', to='input.Item'),
    ),
    migrations.AlterField(
      model_name='demand',
      name='location',
      field=models.ForeignKey(verbose_name='location', to='input.Location'),
    ),
    migrations.AlterUniqueTogether(
      name='buffer',
      unique_together=set([('item', 'location')]),
    ),
  ]
