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


import django.db
from django.db.utils import InterfaceError as djangoInterfaceError
from django.db.backends.postgresql.base import (
    DatabaseWrapper as BuiltinPostgresDatabaseWrapper,
)

from psycopg2 import InterfaceError
import psycopg2.extensions


class DatabaseWrapper(BuiltinPostgresDatabaseWrapper):

    # Default psycopg2 casting functions
    DATE_PARSER = psycopg2.extensions.string_types.get(1082)
    TIMESTAMP_PARSER = psycopg2.extensions.string_types.get(1114)
    TIMESTAMPTZ_PARSER = psycopg2.extensions.string_types.get(1184)

    @classmethod
    def cast_date_safely(cls, value, cur):
        try:
            return cls.DATE_PARSER(value, cur)
        except ValueError:
            # Postgres supports a wider range of dates than Python
            return None

    @classmethod
    def cast_timestamp_safely(cls, value, cur):
        try:
            return cls.TIMESTAMP_PARSER(value, cur)
        except ValueError:
            # Postgres supports a wider range of timestamps than Python
            return None

    @classmethod
    def cast_timestamptz_safely(cls, value, cur):
        try:
            return cls.TIMESTAMPTZ_PARSER(value, cur)
        except ValueError:
            # Postgres supports a wider range of timestamptz than Python
            return None

    def get_new_connection(self, conn_params):
        connection = super().get_new_connection(conn_params)
        psycopg2.extensions.register_type(
            psycopg2.extensions.new_type((1082,), "SAFE_DATE", self.cast_date_safely),
            connection,
        )
        psycopg2.extensions.register_type(
            psycopg2.extensions.new_type(
                (1114,), "SAFE_TIMESTAMP", self.cast_timestamp_safely
            ),
            connection,
        )
        psycopg2.extensions.register_type(
            psycopg2.extensions.new_type(
                (1184,), "SAFE_TIMESTAMPTZ", self.cast_timestamptz_safely
            ),
            connection,
        )
        return connection

    def create_cursor(self, name=None):
        try:
            return super().create_cursor(name=name)
        except (InterfaceError, djangoInterfaceError):
            django.db.close_old_connections()
            django.db.connection.connect()
            return super().create_cursor(name=name)
