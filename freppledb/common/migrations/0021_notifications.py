#
# Copyright (C) 2020 by frePPLe bv
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
