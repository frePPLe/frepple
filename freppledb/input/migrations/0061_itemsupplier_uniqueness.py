# Copyright (C) 2021 by frePPLe bv
#
# This library is free software; you can redistribute it and/or modify it
# under the terms of the GNU Affero General Public License as published
# by the Free Software Foundation; either version 3 of the License, or
# (at your option) any later version.
#
# This library is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU Affero
# General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public
# License along with this program.  If not, see <http://www.gnu.org/licenses/>.
#

from django.db import migrations, connections, models


def cleanBadRecords(apps, schema_editor):
    db = schema_editor.connection.alias
    output = []
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
