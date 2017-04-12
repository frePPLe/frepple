# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('input', '0014_operationplan_color'),
    ]

    operations = [
        migrations.AddField(
            model_name='demand',
            name='delay',
            field=models.DurationField(blank=True, editable=False, verbose_name='delay', null=True),
        ),
        migrations.AddField(
            model_name='demand',
            name='deliverydate',
            field=models.DateTimeField(blank=True, editable=False, verbose_name='delivery date', help_text='Delivery date of the demand', null=True),
        ),
        migrations.AddField(
            model_name='demand',
            name='plannedquantity',
            field=models.DecimalField(verbose_name='planned quantity', max_digits=15, null=True, blank=True, editable=False, decimal_places=6, help_text='Quantity planned for delivery'),
        ),
    ]
