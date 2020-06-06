#
# Copyright (C) 2020 by frePPLe bv
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

from django.db import migrations, connections


def recreateConstraintsCascade(apps, schema_editor):
    def getConstraint(cursor, tableName):
        cursor.execute(
            """
            select conname from pg_constraint
            inner join pg_class opplan on opplan.oid = pg_constraint.confrelid and opplan.relname = 'operationplan'
            inner join pg_class opm on opm.oid = pg_constraint.conrelid and opm.relname = %s
            inner join pg_attribute on attname = 'operationplan_id' and attrelid = opm.oid and pg_attribute.attnum = any(conkey)
            """,
            (tableName,),
        )
        return cursor.fetchone()[0]

    with connections[schema_editor.connection.alias].cursor() as cursor:
        cursor.execute(
            "alter table operationplanmaterial drop constraint %s"
            % (getConstraint(cursor, "operationplanmaterial"),)
        )
        cursor.execute(
            "alter table operationplanresource drop constraint %s"
            % (getConstraint(cursor, "operationplanresource"),)
        )
        cursor.execute(
            """
            alter table operationplanresource
            ADD FOREIGN KEY (operationplan_id)
            REFERENCES public.operationplan (reference) MATCH SIMPLE
            ON UPDATE NO ACTION
            ON DELETE CASCADE
            DEFERRABLE INITIALLY DEFERRED
            """
        )
        cursor.execute(
            """
            alter table operationplanmaterial
                ADD FOREIGN KEY (operationplan_id)
                REFERENCES public.operationplan (reference) MATCH SIMPLE
                ON UPDATE NO ACTION
                ON DELETE CASCADE
                DEFERRABLE INITIALLY DEFERRED
            """
        )


class Migration(migrations.Migration):
    dependencies = [("input", "0044_squashed_60")]
    operations = [migrations.RunPython(recreateConstraintsCascade)]
