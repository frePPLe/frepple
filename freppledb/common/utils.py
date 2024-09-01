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

import os

from django.conf import settings
from django.db import connections, DEFAULT_DB_ALIAS

from freppledb.common.models import Scenario


def getStorageUsage():
    """
    The storage counts:
    - All files in the LOGDIR folder.
      This includes input data files, engine log files, database dump files, plan export files.
    - Postgres database storage.
    """
    total_size = 0

    # Add the size of all log files and data files
    for dirpath, dirnames, filenames in os.walk(settings.FREPPLE_LOGDIR):
        for f in filenames:
            fp = os.path.join(dirpath, f)
            if not os.path.islink(fp):
                total_size += os.path.getsize(fp)

    # Add the size of all scenarios in use
    dblist = [
        settings.DATABASES[sc.name]["NAME"]
        for sc in Scenario.objects.using(DEFAULT_DB_ALIAS)
        .filter(status="In use")
        .only("name")
    ]
    with connections[DEFAULT_DB_ALIAS].cursor() as cursor:
        cursor.execute(
            "select %s" % " + ".join(["pg_database_size(%s)"] * len(dblist)), dblist
        )
        dbsizevalue = cursor.fetchone()
        if len(dbsizevalue) > 0:
            total_size += dbsizevalue[0]
    return total_size
