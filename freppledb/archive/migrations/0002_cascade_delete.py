#
# Copyright (C) 2020 by frePPLe bv
#
# This library is free software; you can redistribute it and/or modify it
# under the terms of the GNU Affero General Public License as published
# by the Free Software Foundation; either version 3 of the License, or
#
# This library is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU Affero
# General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public
# License along with this program.  If not, see <http://www.gnu.org/licenses/>.
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
