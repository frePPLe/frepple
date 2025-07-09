#
# Copyright (C) 2025 by frePPLe bv
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
from django.db import connections, DEFAULT_DB_ALIAS


def countItemLocations(db=DEFAULT_DB_ALIAS):
    """
    Return the number of active item locations in a database.
    This count is a key metric for understanding the value a planning tool brings.

    It's used for the pricing of the Enterprise and Cloud Editions.
    """
    try:
        with connections[db].cursor() as cursor:
            cursor.execute(
                """
                select greatest(
                   (select count(*) from
                    (
                      %s
                      select distinct item_id, location_id from operationplanmaterial
                    ) t
                   ),
                   (select count(*) from 
                     (select distinct operation_id from operationplan) t
                   )
                )
                """
                % (
                    "select distinct item_id, location_id from forecastplan union "
                    if "freppledb.forecast" in settings.INSTALLED_APPS
                    else ""
                )
            )
            return cursor.fetchone()[0]
    except Exception:
        return 0
