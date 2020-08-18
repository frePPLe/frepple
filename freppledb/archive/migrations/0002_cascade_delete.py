#
# Copyright (C) 2020 by frePPLe bv
#
# All information contained herein is, and remains the property of frePPLe.
# You are allowed to use and modify the source code, as long as the software is used
# within your company.
# You are not allowed to distribute the software, either in the form of source code
# or in the form of compiled binaries.
#

from django.db import migrations, connections


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
    dependencies = [("archive", "0001_initial")]
    operations = [migrations.RunPython(recreateConstraintsCascade)]
