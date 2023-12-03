#
# Copyright (C) 2021 by frePPLe bv
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

from ...auth import getWebserviceAuthorization

from django.core.management.base import BaseCommand
from django.db import DEFAULT_DB_ALIAS

from freppledb import __version__


class Command(BaseCommand):
    help = """
    This command generates an API authentication token for a user.
    """

    requires_system_checks = []

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
            secret=None,
            user=options["user"],
            exp=options["expiry"] * 86400,
        )
        if options["verbosity"]:
            print(
                "Access token for %s, valid for %s days:"
                % (options["user"], options["expiry"])
            )
        return token
