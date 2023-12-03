#
# Copyright (C) 2023 by frePPLe bv
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
from django.db.models.deletion import CASCADE

import re


def drop_varchar_pattern_like_index(appname, modelname, fieldname):
    def _drop_index(apps, schemaEditor):
        # code based on https://docs.djangoproject.com/en/1.8/_modules/django/db/backends/base/schema/#BaseDatabaseSchemaEditor.alter_field
        model = apps.get_model(appname, modelname)
        index_names = schemaEditor._constraint_names(model, index=True)
        for index_name in index_names:
            if re.search("%s_%s_.+_like" % (modelname, fieldname), index_name):
                schemaEditor.execute(
                    schemaEditor._delete_constraint_sql(
                        schemaEditor.sql_delete_index, model, index_name
                    )
                )

    return _drop_index


def dropIndexLike(apps, schema_editor):
    db = schema_editor.connection.alias
    output = []
    with connections[db].cursor() as cursor:
        cursor.execute(
            """
            with cte as (
            select
            t.relname as table_name,
            i.relname as index_name,
            array_to_string(array_agg(a.attname), ', ') as column_names
            from
            pg_class t,
            pg_class i,
            pg_index ix,
            pg_attribute a
            where
            t.oid = ix.indrelid
            and i.oid = ix.indexrelid
            and a.attrelid = t.oid
            and a.attnum = ANY(ix.indkey)
            and t.relkind = 'r'
            and i.relname like '%like'
            group by
            t.relname,
            i.relname
            )
            select cte.index_name
            from information_schema.table_constraints tco
            inner join information_schema.key_column_usage kcu
              on tco.constraint_schema = kcu.constraint_schema
              and tco.constraint_name = kcu.constraint_name
            inner join cte
              on cte.table_name = kcu.table_name
              and cte.column_names = kcu.column_name
            inner join information_schema.referential_constraints rco
              on tco.constraint_schema = rco.constraint_schema
              and tco.constraint_name = rco.constraint_name
            inner join information_schema.table_constraints rel_tco
              on tco.constraint_schema = rel_tco.constraint_schema
              and tco.constraint_name = rel_tco.constraint_name
            where tco.constraint_type = 'FOREIGN KEY'
            and kcu.table_name in ('forecast')
            group by
            kcu.table_name,
            kcu.column_name,
            cte.index_name
            """
        )
        for i in cursor:
            output.append(i[0])
        if len(output) > 0:
            cursor.execute("drop index %s" % ",".join(output))


class Migration(migrations.Migration):
    dependencies = [("forecast", "0001_initial")]

    operations = [
        migrations.RunPython(
            drop_varchar_pattern_like_index("forecast", "forecastplan", "item_id"),
            migrations.RunPython.noop,
        ),
        migrations.RunPython(
            drop_varchar_pattern_like_index("forecast", "forecastplan", "customer_id"),
            migrations.RunPython.noop,
        ),
        migrations.RunPython(
            drop_varchar_pattern_like_index("forecast", "forecastplan", "location_id"),
            migrations.RunPython.noop,
        ),
        migrations.AlterField(
            model_name="forecastplan",
            name="customer",
            field=models.ForeignKey(
                db_constraint=False,
                on_delete=CASCADE,
                to="input.Customer",
                verbose_name="customer",
            ),
        ),
        migrations.AlterField(
            model_name="forecastplan",
            name="item",
            field=models.ForeignKey(
                db_constraint=False,
                on_delete=CASCADE,
                to="input.Item",
                verbose_name="item",
            ),
        ),
        migrations.AlterField(
            model_name="forecastplan",
            name="location",
            field=models.ForeignKey(
                db_constraint=False,
                on_delete=CASCADE,
                to="input.Location",
                verbose_name="location",
            ),
        ),
        migrations.RunPython(
            code=dropIndexLike,
            reverse_code=migrations.RunPython.noop,
        ),
    ]
