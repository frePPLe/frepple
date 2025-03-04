#
# Copyright (C) 2024 by frePPLe bv
#
# All information contained herein is, and remains the property of frePPLe.
# You are allowed to use and modify the source code, as long as the software is used
# within your company.
# You are not allowed to distribute the software, either in the form of source code
# or in the form of compiled binaries.
#

import django.db
from django.db.utils import InterfaceError as djangoInterfaceError
from django.db.backends.postgresql.base import (
    DatabaseWrapper as BuiltinPostgresDatabaseWrapper,
)

from psycopg2 import InterfaceError


class DatabaseWrapper(BuiltinPostgresDatabaseWrapper):
    def create_cursor(self, name=None):
        try:
            return super().create_cursor(name=name)
        except (InterfaceError, djangoInterfaceError):
            django.db.close_old_connections()
            django.db.connection.connect()
            return super().create_cursor(name=name)
