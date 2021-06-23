#
# Copyright (C) 2021 by frePPLe bv
#
# All information contained herein is, and remains the property of frePPLe.
# You are allowed to use and modify the source code, as long as the software is used
# within your company.
# You are not allowed to distribute the software, either in the form of source code
# or in the form of compiled binaries.
#

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ("common", "0027_last_currentdate"),
    ]

    operations = [
        migrations.AlterModelOptions(
            name="comment",
            options={
                "ordering": ("id",),
                "default_permissions": ("add",),
            },
        ),
    ]
