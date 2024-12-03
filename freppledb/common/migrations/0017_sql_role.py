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

from django.conf import settings
from django.db import migrations, connections


def grant_read_access(apps, schema_editor):
    db = schema_editor.connection.alias
    role = settings.DATABASES[db].get("SQL_ROLE", "report_role")
    if role:
        with connections[db].cursor() as cursor:
            cursor.execute("select count(*) from pg_roles where rolname = lower(%s)", (role,))
            if not cursor.fetchone()[0]:
                cursor.execute(
                    "create role %s with nologin noinherit role current_user" % (role,)
                )
            for table in [
                "common_parameter",
                "common_bucket",
                "common_bucketdetail",
                "common_comment",
            ]:
                cursor.execute("grant select on table %s to %s" % (table, role))


class Migration(migrations.Migration):
    dependencies = [("common", "0016_meta")]
    operations = [migrations.RunPython(grant_read_access)]
