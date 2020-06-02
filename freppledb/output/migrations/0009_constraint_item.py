#
# Copyright (C) 2020 by frePPLe bvba
#
# All information contained herein is, and remains the property of frePPLe.
# You are allowed to use and modify the source code, as long as the software is used
# within your company.
# You are not allowed to distribute the software, either in the form of source code
# or in the form of compiled binaries.
#

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [("output", "0008_sql_role")]

    operations = [
        migrations.AlterModelOptions(
            name="constraint",
            options={
                "default_permissions": [],
                "ordering": ["item", "startdate"],
                "verbose_name": "constraint",
                "verbose_name_plural": "constraints",
            },
        ),
        migrations.AlterField(
            model_name="constraint",
            name="demand",
            field=models.CharField(
                db_index=True, max_length=300, null=True, verbose_name="demand"
            ),
        ),
        migrations.AddField(
            model_name="constraint",
            name="forecast",
            field=models.CharField(
                db_index=True, max_length=300, null=True, verbose_name="forecast"
            ),
        ),
        migrations.AddField(
            model_name="constraint",
            name="item",
            field=models.CharField(
                db_index=True, max_length=300, null=True, verbose_name="item"
            ),
        ),
    ]
