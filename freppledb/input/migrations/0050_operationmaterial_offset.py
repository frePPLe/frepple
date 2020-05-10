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

    dependencies = [("input", "0049_parameter_completed")]

    operations = [
        migrations.AddField(
            model_name="operationmaterial",
            name="offset",
            field=models.DurationField(
                blank=True,
                null=True,
                verbose_name="offset",
                help_text="Time offset from the start or end to consume or produce material",
            ),
        )
    ]
