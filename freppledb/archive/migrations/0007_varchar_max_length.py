#
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

from django.db import migrations, models, connections


def recreateConstraintsCascade(apps, schema_editor):
    def getConstraint(cursor, tableName):
        cursor.execute(
            """
            select conname from pg_constraint
            inner join pg_class opplan on opplan.oid = pg_constraint.confrelid and opplan.relname = 'ax_manager'
            inner join pg_class opm on opm.oid = pg_constraint.conrelid and opm.relname = %s
            inner join pg_attribute on attname = 'snapshot_date_id' and attrelid = opm.oid and pg_attribute.attnum = any(conkey)
            """,
            (tableName,),
        )
        return cursor.fetchone()[0]

    with connections[schema_editor.connection.alias].cursor() as cursor:
        cursor.execute(
            "alter table ax_demand drop constraint %s"
            % (getConstraint(cursor, "ax_demand"),)
        )
        cursor.execute(
            "alter table ax_buffer drop constraint %s"
            % (getConstraint(cursor, "ax_buffer"),)
        )
        cursor.execute(
            "alter table ax_operationplan drop constraint %s"
            % (getConstraint(cursor, "ax_operationplan"),)
        )
        cursor.execute(
            """
            alter table ax_demand
            ADD FOREIGN KEY (snapshot_date_id)
            REFERENCES public.ax_manager (snapshot_date) MATCH SIMPLE
            ON UPDATE NO ACTION
            ON DELETE CASCADE
            DEFERRABLE INITIALLY DEFERRED
            """
        )
        cursor.execute(
            """
            alter table ax_buffer
            ADD FOREIGN KEY (snapshot_date_id)
            REFERENCES public.ax_manager (snapshot_date) MATCH SIMPLE
            ON UPDATE NO ACTION
            ON DELETE CASCADE
            DEFERRABLE INITIALLY DEFERRED
            """
        )
        cursor.execute(
            """
            alter table ax_operationplan
            ADD FOREIGN KEY (snapshot_date_id)
            REFERENCES public.ax_manager (snapshot_date) MATCH SIMPLE
            ON UPDATE NO ACTION
            ON DELETE CASCADE
            DEFERRABLE INITIALLY DEFERRED
            """
        )


class Migration(migrations.Migration):
    dependencies = [
        ("archive", "0006_archive_duration"),
    ]

    operations = [
        migrations.AlterField(
            model_name="archivedbuffer",
            name="batch",
            field=models.CharField(blank=True, null=True, verbose_name="batch"),
        ),
        migrations.AlterField(
            model_name="archivedbuffer",
            name="item",
            field=models.CharField(db_index=True, verbose_name="item"),
        ),
        migrations.AlterField(
            model_name="archivedbuffer",
            name="location",
            field=models.CharField(db_index=True, verbose_name="location"),
        ),
        migrations.AlterField(
            model_name="archiveddemand",
            name="customer",
            field=models.CharField(db_index=True, verbose_name="customer"),
        ),
        migrations.AlterField(
            model_name="archiveddemand",
            name="item",
            field=models.CharField(db_index=True, verbose_name="item"),
        ),
        migrations.AlterField(
            model_name="archiveddemand",
            name="location",
            field=models.CharField(db_index=True, verbose_name="location"),
        ),
        migrations.AlterField(
            model_name="archiveddemand",
            name="name",
            field=models.CharField(verbose_name="name"),
        ),
        migrations.AlterField(
            model_name="archiveddemand",
            name="quantityplanned",
            field=models.DecimalField(
                blank=True,
                decimal_places=8,
                max_digits=20,
                null=True,
                verbose_name="planned quantity",
            ),
        ),
        migrations.AlterField(
            model_name="archiveddemand",
            name="status",
            field=models.CharField(blank=True, null=True, verbose_name="status"),
        ),
        migrations.AlterField(
            model_name="archivedoperationplan",
            name="batch",
            field=models.CharField(blank=True, null=True, verbose_name="batch"),
        ),
        migrations.AlterField(
            model_name="archivedoperationplan",
            name="demand",
            field=models.CharField(blank=True, null=True, verbose_name="demand"),
        ),
        migrations.AlterField(
            model_name="archivedoperationplan",
            name="destination",
            field=models.CharField(
                blank=True, db_index=True, null=True, verbose_name="destination"
            ),
        ),
        migrations.AlterField(
            model_name="archivedoperationplan",
            name="item",
            field=models.CharField(db_index=True, verbose_name="item"),
        ),
        migrations.AlterField(
            model_name="archivedoperationplan",
            name="location",
            field=models.CharField(blank=True, null=True, verbose_name="location"),
        ),
        migrations.AlterField(
            model_name="archivedoperationplan",
            name="name",
            field=models.CharField(
                blank=True, db_index=True, null=True, verbose_name="name"
            ),
        ),
        migrations.AlterField(
            model_name="archivedoperationplan",
            name="operation",
            field=models.CharField(blank=True, null=True, verbose_name="operation"),
        ),
        migrations.AlterField(
            model_name="archivedoperationplan",
            name="origin",
            field=models.CharField(blank=True, null=True, verbose_name="origin"),
        ),
        migrations.AlterField(
            model_name="archivedoperationplan",
            name="owner",
            field=models.CharField(blank=True, null=True, verbose_name="owner"),
        ),
        migrations.AlterField(
            model_name="archivedoperationplan",
            name="reference",
            field=models.CharField(verbose_name="reference"),
        ),
        migrations.AlterField(
            model_name="archivedoperationplan",
            name="status",
            field=models.CharField(blank=True, null=True, verbose_name="status"),
        ),
        migrations.AlterField(
            model_name="archivedoperationplan",
            name="supplier",
            field=models.CharField(blank=True, null=True, verbose_name="supplier"),
        ),
        migrations.AlterField(
            model_name="archivedoperationplan",
            name="type",
            field=models.CharField(db_index=True, verbose_name="type"),
        ),
        migrations.RunPython(recreateConstraintsCascade, migrations.RunPython.noop),
    ]
