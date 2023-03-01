#
# Copyright (C) 2021 by frePPLe bv
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
from django.core.management.commands.migrate import Command as StdCommand
from django.db import connections
from django.db.utils import DEFAULT_DB_ALIAS


class Command(StdCommand):
    def create_parser(self, prog_name, subcommand, **kwargs):
        kwargs["conflict_handler"] = "resolve"
        return super().create_parser(prog_name, subcommand, **kwargs)

    def add_arguments(self, parser):
        super().add_arguments(parser)
        parser.add_argument(
            "--database",
            help="Nominates a database to synchronize. Defaults to all scenarios that are in use.",
        )

    def handle(self, *args, **options):
        # Warn about optional apps that are not activated.
        # freppledb.common.apps already checks for required apps.
        missing_apps = [
            i
            for i in ["freppledb.wizard", "freppledb.metrics", "freppledb.debugreport"]
            if i not in settings.INSTALLED_APPS
        ]
        if missing_apps:
            print(
                "\n"
                "Warning:\n"
                "  The following apps are not activated in the INSTALLED_APPS setting in your djangosettings.py file.\n"
                "  This is fine and can be intentional, but could also be an oversight.\n"
                "  Missing: %s\n" % ",".join(missing_apps)
            )

        db = options["database"]
        if db:
            # Database was specified
            super().handle(*args, **options)
            return

        try:
            with connections[DEFAULT_DB_ALIAS].cursor() as cursor:
                cursor.execute(
                    """
                    select name 
                    from common_scenario 
                    where status='In use' or name = %s
                    """,
                    (DEFAULT_DB_ALIAS,),
                )
                for i in cursor.fetchall():
                    try:
                        print("Start migrating database %s" % i[0].upper())
                        options["database"] = i[0]
                        super().handle(*args, **options)
                        print("Successfully migrated database %s" % i[0].upper())
                    except Exception as e:
                        print("ERROR migrating database %s: %s" % (i[0].upper(), e))
        except Exception:
            options["database"] = DEFAULT_DB_ALIAS
            super().handle(*args, **options)
