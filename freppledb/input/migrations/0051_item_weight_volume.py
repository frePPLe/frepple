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

from django.db import migrations, models, connections


def rename_existing_columns(apps, schema_editor):
    db = schema_editor.connection.alias
    with connections[db].cursor() as cursor:
        cursor.execute(
            """
            select count(*)
            from information_schema.columns
            where table_name='item' and column_name='volume'
            """
        )
        if cursor.fetchone()[0]:
            cursor.execute("alter table item rename column volume to original_volume")
        cursor.execute(
            """
            select count(*)
            from information_schema.columns
            where table_name='item' and column_name='weight'
            """
        )
        if cursor.fetchone()[0]:
            cursor.execute("alter table item rename column weight to original_weight")


def copy_existing_data(apps, schema_editor):
    db = schema_editor.connection.alias
    with connections[db].cursor() as cursor:
        cursor.execute(
            """
            select column_name
            from information_schema.columns
            where table_name='item'
            and column_name in ('original_volume', 'original_weight')
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
            and column_name in ('original_volume', 'original_weight')
            """
        )
        cols = ["drop column %s" % c[0] for c in cursor.fetchall()]
        if cols:
            cursor.execute("alter table item %s" % ", ".join(cols))


class Migration(migrations.Migration):
    dependencies = [
        ("input", "0050_operationmaterial_offset"),
    ]

    operations = [
        migrations.RunPython(rename_existing_columns),
        migrations.AddField(
            model_name="item",
            name="volume",
            field=models.DecimalField(
                blank=True,
                decimal_places=8,
                help_text="Volume of the item",
                max_digits=20,
                null=True,
                verbose_name="volume",
            ),
        ),
        migrations.AddField(
            model_name="item",
            name="weight",
            field=models.DecimalField(
                blank=True,
                decimal_places=8,
                help_text="Weight of the item",
                max_digits=20,
                null=True,
                verbose_name="weight",
            ),
        ),
        migrations.RunPython(copy_existing_data),
        migrations.RunPython(drop_temp_columns),
    ]
