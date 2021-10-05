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

from django.db import migrations, models, connections


def rename_existing_columns(apps, schema_editor):
    db = schema_editor.connection.alias
    with connections[db].cursor() as cursor:
        cursor.execute(
            """
            select count(*)
            from information_schema.columns
            where table_name='item' and column_name='uom'
            """
        )
        if cursor.fetchone()[0]:
            cursor.execute("alter table item rename column volume to original_uom")


def copy_existing_data(apps, schema_editor):
    db = schema_editor.connection.alias
    with connections[db].cursor() as cursor:
        cursor.execute(
            """
            select column_name
            from information_schema.columns
            where table_name='item'
            and column_name='original_uom'
            """
        )
        cols = ["%s=%s" % (c[0][9:], c[0]) for c in cursor.fetchall()]
        if cols:
            cursor.execute("update item set %s" % ", ".join(cols))


def drop_temp_columns(apps, schema_editor):
    db = schema_editor.connection.alias
    with connections[db].cursor() as cursor:
        cursor.execute(
            """
            select column_name
            from information_schema.columns
            where table_name='item'
            and column_name='original_uom'
            """
        )
        cols = ["drop column %s" % c[0] for c in cursor.fetchall()]
        if cols:
            cursor.execute("alter table item %s" % ", ".join(cols))


class Migration(migrations.Migration):

    dependencies = [
        ("input", "0058_nullable_unique_fields"),
    ]

    operations = [
        migrations.RunPython(rename_existing_columns),
        migrations.AddField(
            model_name="item",
            name="uom",
            field=models.CharField(
                blank=True, max_length=20, null=True, verbose_name="unit of measure"
            ),
        ),
        migrations.RunPython(copy_existing_data),
        migrations.RunPython(drop_temp_columns),
    ]
