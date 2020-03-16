#
# Copyright (C) 2020 by frePPLe bvba
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
import logging
from psycopg2.extras import execute_batch

from django.db import DEFAULT_DB_ALIAS, connections

from freppledb.boot import getAttributes
from freppledb.common.commands import PlanTaskRegistry, PlanTask
from freppledb.input.models import Item

logger = logging.getLogger(__name__)


@PlanTaskRegistry.register
class ExportItems(PlanTask):

    description = "Export items"
    sequence = 300
    export = True

    @classmethod
    def getWeight(cls, database=DEFAULT_DB_ALIAS, **kwargs):
        return -1

    @classmethod
    def run(cls, database=DEFAULT_DB_ALIAS, **kwargs):
        import frepple

        attrs = [f[0] for f in getAttributes(Item)]

        def getData():
            for i in frepple.items():
                if cls.source and cls.source != i.source:
                    continue
                r = [
                    i.name,
                    i.description,
                    round(i.cost, 8),
                    i.category,
                    i.subcategory,
                    "make to order"
                    if isinstance(i, frepple.item_mto)
                    else "make to stock",
                    i.source,
                    cls.timestamp,
                ]
                for a in attrs:
                    r.append(getattr(i, a, None))
                yield r

        def getOwners():
            for i in frepple.items():
                if not cls.source or cls.source == i.source:
                    yield (i.owner.name if i.owner else None, i.name)

        with connections[database].cursor() as cursor:
            execute_batch(
                cursor,
                """insert into item
                (name,description,cost,category,subcategory,type,source,lastmodified%s)
                values (%%s,%%s,%%s,%%s,%%s,%%s,%%s,%%s%s)
                on conflict (name)
                do update set
                  description=excluded.description,
                  cost=excluded.cost,
                  category=excluded.category,
                  subcategory=excluded.subcategory,
                  type=excluded.type,
                  source=excluded.source,
                  lastmodified=excluded.lastmodified
                  %s
                """
                % (
                    "".join([",%s" % i for i in attrs]),
                    ",%s" * len(attrs),
                    "".join([",\n%s=excluded.%s" % (i, i) for i in attrs]),
                ),
                getData(),
            )
            execute_batch(
                cursor, "update item set owner_id=%s where name=%s", getOwners()
            )
