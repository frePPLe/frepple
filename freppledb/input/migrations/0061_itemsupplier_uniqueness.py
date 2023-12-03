# Copyright (C) 2021 by frePPLe bv
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

from django.db import migrations, connections, models


def cleanBadRecords(apps, schema_editor):
    db = schema_editor.connection.alias
    with connections[db].cursor() as cursor:
        # delete records that will fail with the new indexes
        cursor.execute(
            """
            with cte as
            (
            select id, row_number() over(partition by item_id, supplier_id, effective_start order by cost) as rn
            from itemsupplier
            where location_id is null
            )
            delete from itemsupplier
            using cte
            where itemsupplier.id = cte.id
            and cte.rn > 1
            """
        )


class Migration(migrations.Migration):
    dependencies = [
        ("input", "0060_remove_like_indexes"),
    ]

    operations = [
        migrations.RunPython(cleanBadRecords),
        migrations.AddConstraint(
            model_name="itemsupplier",
            constraint=models.UniqueConstraint(
                condition=models.Q(location__isnull=True),
                fields=("item", "supplier", "effective_start"),
                name="itemsupplier_partial2",
            ),
        ),
    ]
