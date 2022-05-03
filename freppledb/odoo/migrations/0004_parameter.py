#
# Copyright (C) 2020 by frePPLe bv
#
# All information contained herein is, and remains the property of frePPLe.
# You are allowed to use and modify the source code, as long as the software is used
# within your company.
# You are not allowed to distribute the software, either in the form of source code
# or in the form of compiled binaries.
#

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [("odoo", "0003_parameters")]

    operations = [
        migrations.RunSQL(
            """
            insert into common_parameter
            (name, value, description, lastmodified)
            values
            ('odoo.singlecompany','0','Odoo connector: When false (the default) the connector downloads all allowed companies. When true the connector only downloads the data of the configured odoo.company.', now())
            on conflict(name) do nothing
            """
        )
    ]
