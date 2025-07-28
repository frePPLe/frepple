#
# Copyright (C) 2024 by frePPLe bv
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

import django.apps
from django.core.management.base import BaseCommand
from django.db import DEFAULT_DB_ALIAS, connections
from django.db.models import Q

from freppledb import __version__
from freppledb.common.models import Scenario
from freppledb.common.utils import get_databases


class Command(BaseCommand):
    help = """
    This command will apply a change of the report user to the database schema.
    """

    requires_system_checks = []

    def get_version(self):
        return __version__

    def handle(self, **options):
        for sc in (
            Scenario.objects.using(DEFAULT_DB_ALIAS)
            .filter(Q(status="In use") | Q(name=DEFAULT_DB_ALIAS))
            .only("name")
        ):
            role = get_databases()[sc.name].get("SQL_ROLE", "report_role")
            if role:
                with connections[sc.name].cursor() as cursor:
                    cursor.execute(
                        "select count(*) from pg_roles where rolname = lower(%s)",
                        (role,),
                    )
                    if not cursor.fetchone()[0]:
                        cursor.execute(
                            "create role %s with login noinherit role current_user"
                            % (role,)
                        )
                    for model in django.apps.apps.get_models():
                        if (
                            getattr(model, "allow_report_manager_access", False)
                            and not model._meta.proxy
                        ):
                            print(
                                f"Grant select on table {model._meta.db_table} to {role}"
                            )
                            cursor.execute(
                                "grant select on table %s to %s"
                                % (model._meta.db_table, role)
                            )
