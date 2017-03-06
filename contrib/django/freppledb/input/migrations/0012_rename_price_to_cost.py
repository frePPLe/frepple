# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

  dependencies = [
      ('input', '0011_demand_priority'),
  ]

  operations = [
    migrations.AddField(
        model_name='item',
        name='cost',
        field=models.DecimalField(null=True, blank=True, help_text='Cost of the item', max_digits=15, decimal_places=6, verbose_name='cost'),
    ),
    migrations.RunSQL(
        '''
        update item
        set cost = price
          '''
        ),
    migrations.RemoveField(
        model_name='item',
        name='price',
    ),
  ]
