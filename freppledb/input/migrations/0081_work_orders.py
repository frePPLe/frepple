# Copyright (C) 2025 by frePPLe bv
#
# Permission is hereby granted, free of charge, to any person obtaining
# a copy of this software and associated documentation files (the
# "Software"), to deal in the Software without restriction, including
# without limitation the rights to use, copy, modify, merge, publish,
# distribute, sublicense, and/or sell copies of the Software, and to
# permit persons to whom the Software is furnished to do so, subject to
# the following conditions:
#
# The above copyright notice and this permission notice shall be
# included in all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND,
# EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF
# MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND
# NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE
# LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION
# OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION
# WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.
#

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [("input", "0080_parameter_move_approved_early")]

    operations = [
        migrations.RunSQL(
            """
            update operationplan set type = 'WO'
            where type = 'MO' and exists
            (select 1 from operation inner join operationplan opplan on opplan.operation_id = operation.name where operation.type = 'routing' and opplan.reference = operationplan.owner_id)
            """,
            """
            update operationplan set type = 'MO' where type = 'WO'
            """,
        ),
        migrations.CreateModel(
            name="WorkOrder",
            fields=[],
            options={
                "verbose_name": "work order",
                "verbose_name_plural": "work orders",
                "proxy": True,
                "indexes": [],
                "constraints": [],
            },
            bases=("input.operationplan",),
        ),
        migrations.AlterField(
            model_name="operationplan",
            name="type",
            field=models.CharField(
                choices=[
                    ("STCK", "inventory"),
                    ("MO", "manufacturing order"),
                    ("WO", "work order"),
                    ("PO", "purchase order"),
                    ("DO", "distribution order"),
                    ("DLVR", "delivery order"),
                ],
                db_index=True,
                default="MO",
                help_text="Order type",
                verbose_name="type",
            ),
        ),
    ]
