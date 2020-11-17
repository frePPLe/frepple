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
    with connections[schema_editor.connection.alias].cursor() as cursor:
        cursor.execute(
            """
            select conname from pg_constraint
            inner join pg_class opplan on opplan.oid = pg_constraint.confrelid and opplan.relname = 'common_comment'
            inner join pg_class opm on opm.oid = pg_constraint.conrelid and opm.relname = 'common_notification'
            inner join pg_attribute on attname = 'comment_id' and attrelid = opm.oid and pg_attribute.attnum = any(conkey)
            """
        )
        cursor.execute(
            "alter table common_notification drop constraint %s" % cursor.fetchone()[0]
        )
        cursor.execute(
            """
            alter table common_notification
            add foreign key (comment_id)
            references public.common_comment(id) match simple
            on update no action
            on delete cascade
            deferrable initially deferred
            """
        )


class Migration(migrations.Migration):

    dependencies = [("common", "0020_notifications")]

    operations = [migrations.RunPython(recreateConstraintsCascade)]
