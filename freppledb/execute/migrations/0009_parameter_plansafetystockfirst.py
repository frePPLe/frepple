#
# Copyright (C) 2024 by frePPLe bv
#
# All information contained herein is, and remains the property of frePPLe.
# You are allowed to use and modify the source code, as long as the software is used
# within your company.
# You are not allowed to distribute the software, either in the form of source code
# or in the form of compiled binaries.
#

from django.db import migrations


class Migration(migrations.Migration):
    dependencies = [("execute", "0008_squash_70")]

    operations = [
        migrations.RunSQL(
            """
            delete from common_parameter
            where name in ('plan.planSafetyStockFirst', 'plan.calendar', 'allowsplits')
            """
        )
    ]
