#
# Copyright (C) 2007-2013 by frePPLe bv
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
from django.core.management.base import BaseCommand, CommandError

from freppledb.common.utils import get_databases


class Command(BaseCommand):
    help = """
    Create the PostgreSQL databases for frePPLe.
    """

    def add_arguments(self, parser):
        super().add_arguments(parser)
        parser.add_argument(
            "--database",
            default=None,
            help="Specify the database to recreate. When left unspecified all database will be created.",
        )
        parser.add_argument(
            "--noinput",
            action="store_false",
            dest="interactive",
            default=True,
            help="Tells frePPLe to NOT prompt the user for input of any kind.",
        )
        parser.add_argument(
            "--skip-if-exists",
            action="store_true",
            dest="skip_if_exists",
            default=False,
            help="Don't do anything if the database already exists.",
        )
        parser.add_argument(
            "--user",
            action="store",
            dest="user",
            default=None,
            help="Use a different user than defined in settings.py to create the database. "
            "This user must have the rights to drop and create databases.",
        )
        parser.add_argument(
            "--password",
            action="store",
            dest="password",
            default=None,
            help="Use a different password than defined in settings.py to create the database.",
        )

    def handle(self, *args, **options):
        # Get the list of databases to create
        databaselist = options["database"]
        if databaselist:
            if databaselist in get_databases():
                databaselist = [databaselist]
            else:
                raise CommandError("No database settings known for '%s'" % databaselist)
        else:
            databaselist = get_databases().keys()

        for database in databaselist:
            # Connect to the database
            import psycopg2

            user = options["user"] or get_databases()[database].get("USER", "")
            password = options["password"] or get_databases()[database].get(
                "PASSWORD", ""
            )
            conn_params = {"database": "template1"}
            if user:
                conn_params["user"] = user
            if password:
                conn_params["password"] = password
            database_host = get_databases()[database].get("HOST", None)
            if database_host:
                conn_params["host"] = database_host
            database_port = get_databases()[database].get("PORT", None)
            if database_port:
                conn_params["port"] = database_port
            database_name = get_databases()[database].get("NAME", None)
            if not database_name:
                raise CommandError("No database name specified")

            connection = psycopg2.connect(**conn_params)
            connection.set_isolation_level(0)  # enforce autocommit
            with connection.cursor() as cursor:
                # Check if the database exists
                cursor.execute(
                    "SELECT count(*) AS result FROM pg_database where datname = '%s'"
                    % database_name
                )
                database_exists = cursor.fetchone()[0]

                if database_exists:
                    if options["skip_if_exists"]:
                        print("Database %s already exists" % database_name.upper())
                        continue

                    # Confirm the destruction of the database
                    if options["interactive"]:
                        confirm = input(
                            "\nThe database %s is about to be IRREVERSIBLY destroyed and recreated.\n"
                            "ALL data currently in the database will be lost.\n"
                            "Are you sure you want to do this?\n"
                            "\n"
                            "Type 'yes' to continue, or 'no' to cancel: "
                            % database_name.upper()
                        )
                        if confirm != "yes":
                            print(
                                "Skipping drop and create of database %s"
                                % database_name.upper()
                            )
                            continue

                    # Drop the database
                    try:
                        sql = f'drop database "{database_name}" with(force)'
                        print("Executing SQL statement:", sql)
                        cursor.execute(sql)
                    except psycopg2.ProgrammingError as e:
                        raise CommandError(str(e))

                # Create the database
                try:
                    sql = "create database \"%s\" encoding = 'UTF8'" % database_name
                    if settings.DEFAULT_TABLESPACE:
                        sql += " TABLESPACE = %s" % settings.DEFAULT_TABLESPACE
                    print("Executing SQL statement:", sql)
                    cursor.execute(sql)
                except psycopg2.ProgrammingError as e:
                    raise CommandError(str(e))
