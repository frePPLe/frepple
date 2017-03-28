#
# Copyright (C) 2016 by frePPLe bvba
#
# All information contained herein is, and remains the property of frePPLe.
# You are allowed to use and modify the source code, as long as the software is used
# within your company.
# You are not allowed to distribute the software, either in the form of source code
# or in the form of compiled binaries.
#

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('input', '0013_operationplanmaterial'),
    ]

    operations = [
        migrations.AddField(
            model_name='operationplan',
            name='color',
            field=models.DecimalField(default='0.00', max_digits=15, decimal_places=6, blank=True, null=True, verbose_name='color'),
        ),
    ]
