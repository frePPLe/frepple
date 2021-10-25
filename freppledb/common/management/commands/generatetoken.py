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

from ...auth import getWebserviceAuthorization

from django.core.management.base import BaseCommand, CommandError
from django.db import DEFAULT_DB_ALIAS

from freppledb import __version__


class Command(BaseCommand):

    help = """
    This command generates an API authentication token for a user.
    """

    requires_system_checks = False

    def get_version(self):
        return __version__

    def add_arguments(self, parser):
        parser.add_argument("user", help="User running the command")
        parser.add_argument(
            "--expiry", help="Validity in days of the token", type=int, default=5
        )
        parser.add_argument(
            "--database",
            action="store",
            dest="database",
            default=DEFAULT_DB_ALIAS,
            help="Specifies the database to use",
        ),

    def handle(self, **options):
        token = getWebserviceAuthorization(
            database=options["database"],
            secret="perepe", #None,
            user=options["user"],
            exp=options["expiry"] * 86400,
        )
        if options["verbosity"]:
            print(
                "Access token for %s, valid for %s days:"
                % (options["user"], options["expiry"])
            )
        return token
