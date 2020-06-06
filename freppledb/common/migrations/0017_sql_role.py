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

from django.conf import settings
from django.db import migrations, connections


def grant_read_access(apps, schema_editor):
    db = schema_editor.connection.alias
    role = settings.DATABASES[db].get("SQL_ROLE", "report_role")
    if role:
        with connections[db].cursor() as cursor:
            cursor.execute("select count(*) from pg_roles where rolname = %s", (role,))
            if not cursor.fetchone()[0]:
                cursor.execute("create role %s with nologin noinherit" % (role,))
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
