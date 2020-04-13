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
from datetime import datetime
import logging
from psycopg2.extras import execute_batch

from django.db import DEFAULT_DB_ALIAS, connections

from freppledb.boot import getAttributes
from freppledb.common.commands import PlanTaskRegistry, PlanTask
from freppledb.input.models import (
    Buffer,
    Calendar,
    CalendarBucket,
    Customer,
    Demand,
    Item,
    ItemSupplier,
    ItemDistribution,
    Location,
    Operation,
    OperationMaterial,
    OperationResource,
    Resource,
    ResourceSkill,
    SetupMatrix,
    SetupRule,
    Skill,
    Supplier,
)

logger = logging.getLogger(__name__)

# Default effectivity dates
default_start = datetime(1971, 1, 1)
default_end = datetime(2030, 12, 31)


def SQL4attributes(attrs, with_on_conflict=True):
    """ Snippet is used many times in this file"""
    if with_on_conflict:
        return (
            "".join([",%s" % i for i in attrs]),
            ",%s" * len(attrs),
            "".join([",\n%s=excluded.%s" % (i, i) for i in attrs]),
        )
    else:
        return ("".join([",%s" % i for i in attrs]), ",%s" * len(attrs))


@PlanTaskRegistry.register
class cleanStatic(PlanTask):

    description = "Clean static data"
    sequence = 300

    @classmethod
    def getWeight(cls, database=DEFAULT_DB_ALIAS, **kwargs):
        if kwargs.get("exportstatic", False) and kwargs.get("source", None):
            return 1
        else:
            return -1

    @classmethod
    def run(cls, database=DEFAULT_DB_ALIAS, **kwargs):
        source = kwargs.get("source", None)
        with connections[database].cursor() as cursor:
            cursor.execute(
                """
                delete from operationmaterial
                where (source = %s and lastmodified <> %s)
                  or operation_id in (
                    select name from operation
                    where operation.source = %s and operation.lastmodified <> %s
                    )
                """,
                (source, cls.timestamp, source, cls.timestamp),
            )
            cursor.execute(
                "delete from buffer where source = %s and lastmodified <> %s",
                (source, cls.timestamp),
            )
            cursor.execute(
                "delete from operationplan where demand_id in (select name from demand where source = %s and lastmodified <> %s)",
                (source, cls.timestamp),
            )
            cursor.execute(
                "delete from demand where source = %s and lastmodified <> %s",
                (source, cls.timestamp),
            )
            cursor.execute(
                "delete from itemsupplier where source = %s and lastmodified <> %s",
                (source, cls.timestamp),
            )
            cursor.execute(
                "delete from itemdistribution where source = %s and lastmodified <> %s",
                (source, cls.timestamp),
            )
            cursor.execute(
                """
                delete from operationplan
                where owner_id is not null and ((source = %s and lastmodified <> %s)
                  or operation_id in (
                    select name from operation
                    where operation.source = %s and operation.lastmodified <> %s
                    )
                  or supplier_id in (
                    select name from supplier where source = %s and lastmodified <> %s
                   ))
                """,
                (source, cls.timestamp, source, cls.timestamp, source, cls.timestamp),
            )
            cursor.execute(
                """
                delete from operationplan
                where (source = %s and lastmodified <> %s)
                  or operation_id in (
                    select name from operation
                    where operation.source = %s and operation.lastmodified <> %s
                    )
                  or supplier_id in (
                    select name from supplier where source = %s and lastmodified <> %s
                   )
                """,
                (source, cls.timestamp, source, cls.timestamp, source, cls.timestamp),
            )
            cursor.execute(
                """
                delete from operationresource
                where (source = %s and lastmodified <> %s)
                  or operation_id in (
                     select name from operation
                     where operation.source = %s and operation.lastmodified <> %s
                     )
                  """,
                (source, cls.timestamp, source, cls.timestamp),
            )
            cursor.execute(
                "delete from operation where source = %s and lastmodified <> %s",
                (source, cls.timestamp),
            )
            cursor.execute(
                "delete from item where source = %s and lastmodified <> %s",
                (source, cls.timestamp),
            )
            cursor.execute(
                "delete from resourceskill where source = %s and lastmodified <> %s",
                (source, cls.timestamp),
            )
            cursor.execute(
                "delete from operation where source = %s and lastmodified <> %s",
                (source, cls.timestamp),
            )
            cursor.execute(
                "delete from resource where source = %s and lastmodified <> %s",
                (source, cls.timestamp),
            )
            cursor.execute(
                "delete from location where source = %s and lastmodified <> %s",
                (source, cls.timestamp),
            )
            cursor.execute(
                "delete from calendarbucket where source = %s and lastmodified <> %s",
                (source, cls.timestamp),
            )
            cursor.execute(
                "delete from calendar where source = %s and lastmodified <> %s",
                (source, cls.timestamp),
            )
            cursor.execute(
                "delete from skill where source = %s and lastmodified <> %s",
                (source, cls.timestamp),
            )
            cursor.execute(
                "delete from setuprule where source = %s and lastmodified <> %s",
                (source, cls.timestamp),
            )
            cursor.execute(
                "delete from setupmatrix where source = %s and lastmodified <> %s",
                (source, cls.timestamp),
            )
            cursor.execute(
                "delete from customer where source = %s and lastmodified <> %s",
                (source, cls.timestamp),
            )
            cursor.execute(
                "delete from supplier where source = %s and lastmodified <> %s",
                (source, cls.timestamp),
            )


@PlanTaskRegistry.register
class exportParameters(PlanTask):

    description = ("Export static data", "Export parameters")
    sequence = (301, "exportstatic1", 1)

    @classmethod
    def getWeight(cls, database=DEFAULT_DB_ALIAS, **kwargs):
        # Only complete export should save the current date
        if kwargs.get("exportstatic", False) and not kwargs.get("source", None):
            return 1
        else:
            return -1

    @classmethod
    def run(cls, database=DEFAULT_DB_ALIAS, **kwargs):
        import frepple

        with connections[database].cursor() as cursor:
            # Update current date if the parameter already exists
            # If it doesn't exist, we want to continue using the system clock for the next run.
            cursor.execute(
                "update common_parameter set value=%s, lastmodified=%s where name='currentdate'",
                (frepple.settings.current.strftime("%Y-%m-%d %H:%M:%S"), cls.timestamp),
            )


@PlanTaskRegistry.register
class exportCalendars(PlanTask):

    description = ("Export static data", "Export calendars")
    sequence = (301, "exportstatic2", 1)

    @classmethod
    def getWeight(cls, database=DEFAULT_DB_ALIAS, **kwargs):
        return 1 if kwargs.get("exportstatic", False) else -1

    @classmethod
    def run(cls, database=DEFAULT_DB_ALIAS, **kwargs):
        import frepple

        source = kwargs.get("source", None)
        attrs = [f[0] for f in getAttributes(Calendar)]

        def getData():
            for i in frepple.calendars():
                if (
                    i.hidden
                    or i.source == "common_bucket"
                    or (source and source != i.source)
                ):
                    continue
                r = [i.name, round(i.default, 8), i.source, cls.timestamp]
                for a in attrs:
                    r.append(getattr(i, a, None))
                yield r

        with connections[database].cursor() as cursor:
            execute_batch(
                cursor,
                """insert into calendar
                (name,defaultvalue,source,lastmodified%s)
                values(%%s,%%s,%%s,%%s%s)
                on conflict (name)
                do update set
                  defaultvalue=excluded.defaultvalue,
                  source=excluded.source,
                  lastmodified=excluded.lastmodified
                  %s
                """
                % SQL4attributes(attrs),
                getData(),
            )


@PlanTaskRegistry.register
class exportLocations(PlanTask):

    description = ("Export static data", "Export locations")
    sequence = (302, "exportstatic1", 1)

    @classmethod
    def getWeight(cls, database=DEFAULT_DB_ALIAS, **kwargs):
        return 1 if kwargs.get("exportstatic", False) else -1

    @classmethod
    def run(cls, database=DEFAULT_DB_ALIAS, **kwargs):
        import frepple

        source = kwargs.get("source", None)
        attrs = [f[0] for f in getAttributes(Location)]

        def getData():
            for i in frepple.locations():
                if source and source != i.source:
                    continue
                r = [
                    i.name,
                    i.description,
                    i.available and i.available.name or None,
                    i.category,
                    i.subcategory,
                    i.source,
                    cls.timestamp,
                ]
                for a in attrs:
                    r.append(getattr(i, a, None))
                yield r

        def getOwners():
            for i in frepple.locations():
                if i.owner and (not source or source == i.source):
                    yield (i.owner.name, i.name)

        with connections[database].cursor() as cursor:
            execute_batch(
                cursor,
                """insert into location
                (name,description,available_id,category,subcategory,source,lastmodified,owner_id%s)
                values(%%s,%%s,%%s,%%s,%%s,%%s,%%s,null%s)
                on conflict (name)
                do update set
                  description=excluded.description,
                  available_id=excluded.available_id,
                  category=excluded.category,
                  subcategory=excluded.subcategory,
                  source=excluded.source,
                  lastmodified=excluded.lastmodified,
                  owner_id=excluded.owner_id
                  %s
                """
                % SQL4attributes(attrs),
                getData(),
            )
            execute_batch(
                cursor, "update location set owner_id=%s where name=%s", getOwners()
            )


@PlanTaskRegistry.register
class exportItems(PlanTask):

    description = ("Export static data", "Export items")
    sequence = (302, "exportstatic2", 1)

    @classmethod
    def getWeight(cls, database=DEFAULT_DB_ALIAS, **kwargs):
        return 1 if kwargs.get("exportstatic", False) else -1

    @classmethod
    def run(cls, database=DEFAULT_DB_ALIAS, **kwargs):
        import frepple

        source = kwargs.get("source", None)
        attrs = [f[0] for f in getAttributes(Item)]

        def getData():
            for i in frepple.items():
                if source and source != i.source:
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
                if i.owner and (not source or source == i.source):
                    yield (i.owner.name, i.name)

        with connections[database].cursor() as cursor:
            execute_batch(
                cursor,
                """insert into item
                (name,description,cost,category,subcategory,type,source,lastmodified,owner_id%s)
                values (%%s,%%s,%%s,%%s,%%s,%%s,%%s,%%s,null%s)
                on conflict (name)
                do update set
                  description=excluded.description,
                  cost=excluded.cost,
                  category=excluded.category,
                  subcategory=excluded.subcategory,
                  type=excluded.type,
                  source=excluded.source,
                  lastmodified=excluded.lastmodified,
                  owner_id=excluded.owner_id
                  %s
                """
                % SQL4attributes(attrs),
                getData(),
            )
            execute_batch(
                cursor, "update item set owner_id=%s where name=%s", getOwners()
            )


@PlanTaskRegistry.register
class exportOperations(PlanTask):

    description = ("Export static data", "Export operations")
    sequence = (303, "exportstatic1", 1)

    @classmethod
    def getWeight(cls, database=DEFAULT_DB_ALIAS, **kwargs):
        return 1 if kwargs.get("exportstatic", False) else -1

    @classmethod
    def run(cls, database=DEFAULT_DB_ALIAS, **kwargs):
        import frepple

        source = kwargs.get("source", None)
        attrs = [f[0] for f in getAttributes(Operation)]

        def getData():
            for i in frepple.operations():
                if (
                    i.hidden
                    or (source and source != i.source)
                    or isinstance(
                        i,
                        (
                            frepple.operation_itemsupplier,
                            frepple.operation_itemdistribution,
                        ),
                    )
                ):
                    continue
                r = [
                    i.name,
                    i.fence,
                    i.posttime,
                    round(i.size_minimum, 8),
                    round(i.size_multiple, 8),
                    i.size_maximum < 9999999999999 and round(i.size_maximum, 8) or None,
                    i.__class__.__name__[10:],
                    i.duration
                    if isinstance(
                        i, (frepple.operation_fixed_time, frepple.operation_time_per)
                    )
                    else None,
                    i.duration_per
                    if isinstance(i, frepple.operation_time_per)
                    else None,
                    i.location and i.location.name or None,
                    round(i.cost, 8),
                    i.search,
                    i.description,
                    i.category,
                    i.subcategory,
                    i.source,
                    i.item.name if i.item else None,
                    i.priority if i.priority != 1 else None,
                    i.effective_start if i.effective_start != default_start else None,
                    i.effective_end if i.effective_end != default_end else None,
                    cls.timestamp,
                ]
                for a in attrs:
                    r.append(getattr(i, a, None))
                yield r

        def getOwners():
            for i in frepple.operations():
                if (
                    i.owner
                    and not i.hidden
                    and not i.owner.hidden
                    and (not source or source == i.source)
                    and not isinstance(
                        i,
                        (
                            frepple.operation_itemsupplier,
                            frepple.operation_itemdistribution,
                        ),
                    )
                ):
                    yield (i.owner.name, i.name)

        with connections[database].cursor() as cursor:
            execute_batch(
                cursor,
                """
                insert into operation
                (name,fence,posttime,sizeminimum,sizemultiple,sizemaximum,type,
                duration,duration_per,location_id,cost,search,description,category,
                subcategory,source,item_id,priority,effective_start,effective_end,
                lastmodified,owner_id%s)
                values(%%s,%%s * interval '1 second',%%s * interval '1 second',%%s,%%s,
                %%s,%%s,%%s * interval '1 second',%%s * interval '1 second',%%s,%%s,%%s,
                %%s,%%s,%%s,%%s,%%s,%%s,%%s,%%s,%%s,null%s)
                on conflict (name)
                do update set
                  fence=excluded.fence,
                  posttime=excluded.posttime,
                  sizeminimum=excluded.sizeminimum,
                  sizemultiple=excluded.sizemultiple,
                  sizemaximum=excluded.sizemaximum,
                  type=excluded.type,
                  duration=excluded.duration,
                  duration_per=excluded.duration_per,
                  location_id=excluded.location_id,
                  cost=excluded.cost,
                  search=excluded.search,
                  description=excluded.description,
                  category=excluded.category,
                  subcategory=excluded.subcategory,
                  source=excluded.source,
                  item_id=excluded.item_id,
                  priority=excluded.priority,
                  effective_start=excluded.effective_start,
                  effective_end=excluded.effective_end,
                  lastmodified=excluded.lastmodified,
                  owner_id=excluded.owner_id
                  %s
                """
                % SQL4attributes(attrs),
                getData(),
            )
            execute_batch(
                cursor, "update operation set owner_id=%s where name=%s", getOwners()
            )


@PlanTaskRegistry.register
class exportSetupMatrices(PlanTask):

    description = ("Export static data", "Export setup matrices")
    sequence = (303, "exportstatic2", 1)

    @classmethod
    def getWeight(cls, database=DEFAULT_DB_ALIAS, **kwargs):
        return 1 if kwargs.get("exportstatic", False) else -1

    @classmethod
    def run(cls, database=DEFAULT_DB_ALIAS, **kwargs):
        import frepple

        attrs = [f[0] for f in getAttributes(SetupMatrix)]

        def getData():
            for i in frepple.setupmatrices():
                if source and source != i.source:
                    continue
                r = [i.name, i.source, cls.timestamp]
                for a in attrs:
                    r.append(getattr(i, a, None))
                yield r

        with connections[database].cursor() as cursor:
            execute_batch(
                cursor,
                """insert into setupmatrix
                (name,source,lastmodified%s)
                values(%%s,%%s,%%s%s)
                on conflict (name)
                do update set
                  source=excluded.source,
                  lastmodified=excluded.lastmodified
                  %s
                """
                % SQL4attributes(attrs),
                getData(),
            )


@PlanTaskRegistry.register
class exportResources(PlanTask):

    description = ("Export static data", "Export resources")
    sequence = 304

    @classmethod
    def getWeight(cls, database=DEFAULT_DB_ALIAS, **kwargs):
        return 1 if kwargs.get("exportstatic", False) else -1

    @classmethod
    def run(cls, database=DEFAULT_DB_ALIAS, **kwargs):
        import frepple

        source = kwargs.get("source", None)
        attrs = [f[0] for f in getAttributes(Resource)]

        def getData():
            for i in frepple.resources():
                if i.hidden or (source and source != i.source):
                    continue
                r = [
                    i.name,
                    i.description,
                    i.maximum,
                    i.maximum_calendar.name if i.maximum_calendar else None,
                    i.location and i.location.name or None,
                    i.__class__.__name__[9:],
                    round(i.cost, 8),
                    i.maxearly,
                    i.setup,
                    i.setupmatrix.name if i.setupmatrix else None,
                    i.category,
                    i.subcategory,
                    i.efficiency,
                    i.efficiency_calendar.name if i.efficiency_calendar else None,
                    i.available.name if i.available else None,
                    i.constrained,
                    i.source,
                    cls.timestamp,
                ]
                for a in attrs:
                    r.append(getattr(i, a, None))
                yield r

        def getOwners():
            for i in frepple.resources():
                if not i.hidden and i.owner and (not source or source == i.source):
                    yield (i.owner.name, i.name)

        with connections[database].cursor() as cursor:
            execute_batch(
                cursor,
                """insert into resource
                (name,description,maximum,maximum_calendar_id,location_id,type,cost,
                 maxearly,setup,setupmatrix_id,category,subcategory,efficiency,
                 efficiency_calendar_id,available_id,constrained,source,lastmodified,owner_id%s)
                values(
                  %%s,%%s,%%s,%%s,%%s,%%s,%%s,%%s * interval '1 second',%%s,%%s,%%s,%%s,
                  %%s,%%s,%%s,%%s,%%s,%%s,null%s)
                on conflict (name)
                do update set
                  description=excluded.description,
                  maximum=excluded.maximum,
                  maximum_calendar_id=excluded.maximum_calendar_id,
                  location_id=excluded.location_id,
                  type=excluded.type,
                  cost=excluded.cost,
                  maxearly=excluded.maxearly,
                  setup=excluded.setup,
                  setupmatrix_id=excluded.setupmatrix_id,
                  category=excluded.category,
                  subcategory=excluded.subcategory,
                  efficiency=excluded.efficiency,
                  efficiency_calendar_id=excluded.efficiency_calendar_id,
                  available_id=excluded.available_id,
                  constrained=excluded.constrained,
                  source=excluded.source,
                  lastmodified=excluded.lastmodified,
                  owner_id=excluded.owner_id
                  %s
                """
                % SQL4attributes(attrs),
                getData(),
            )
            execute_batch(
                cursor, "update resource set owner_id=%s where name=%s", getOwners()
            )


@PlanTaskRegistry.register
class exportSetupRules(PlanTask):

    description = ("Export static data", "Export setup matrix rules")
    sequence = (305, "exportstatic1", 1)

    @classmethod
    def getWeight(cls, database=DEFAULT_DB_ALIAS, **kwargs):
        return 1 if kwargs.get("exportstatic", False) else -1

    @classmethod
    def run(cls, database=DEFAULT_DB_ALIAS, **kwargs):
        import frepple

        source = kwargs.get("source", None)
        attrs = [f[0] for f in getAttributes(SetupRule)]

        def getData():
            for m in frepple.setupmatrices():
                for i in m.rules:
                    if source and source != i.source:
                        continue
                    r = [
                        m.name,
                        i.priority,
                        i.fromsetup,
                        i.tosetup,
                        i.duration,
                        round(i.cost, 8),
                        i.resource.name if i.resource else None,
                        i.source,
                        cls.timestamp,
                    ]
                    for a in attrs:
                        r.append(getattr(i, a, None))
                    yield r

        with connections[database].cursor() as cursor:
            execute_batch(
                cursor,
                """insert into setuprule
                (setupmatrix_id,priority,fromsetup,tosetup,duration,cost,resource_id,source,lastmodified%s)
                values(%%s,%%s,%%s,%%s,%%s * interval '1 second',%%s,%%s,%%s,%%s%s)
                on conflict (matrix_id, priority)
                do update set
                  fromsetup=excluded.fromsetup,
                  tosetup=excluded.tosetup,
                  duration=excluded.duration,
                  cost=excluded.cost,
                  resource_id=excluded.resource_id,
                  source=excluded.source,
                  lastmodified=excluded.lastmodified
                  %s
                """
                % SQL4attributes(attrs),
                getData(),
            )


@PlanTaskRegistry.register
class exportSkills(PlanTask):

    description = ("Export static data", "Export skills")
    sequence = (305, "exportstatic1", 2)

    @classmethod
    def getWeight(cls, database=DEFAULT_DB_ALIAS, **kwargs):
        return 1 if kwargs.get("exportstatic", False) else -1

    @classmethod
    def run(cls, database=DEFAULT_DB_ALIAS, **kwargs):
        import frepple

        source = kwargs.get("source", None)
        attrs = [f[0] for f in getAttributes(Skill)]

        def getData():
            for i in frepple.skills():
                if source and source != i.source:
                    continue
                r = [i.name, i.source, cls.timestamp]
                for a in attrs:
                    r.append(getattr(i, a, None))
                yield r

        with connections[database].cursor() as cursor:
            execute_batch(
                cursor,
                """insert into skill
                (name,source,lastmodified%s)
                values(%%s,%%s,%%s%s)
                on conflict (name)
                do update set
                  source=excluded.source,
                  lastmodified=excluded.lastmodified
                  %s
                """
                % SQL4attributes(attrs),
                getData(),
            )


@PlanTaskRegistry.register
class exportResourceSkills(PlanTask):

    description = ("Export static data", "Export resource skills")
    sequence = (305, "exportstatic1", 3)

    @classmethod
    def getWeight(cls, database=DEFAULT_DB_ALIAS, **kwargs):
        return 1 if kwargs.get("exportstatic", False) else -1

    @classmethod
    def run(cls, database=DEFAULT_DB_ALIAS, **kwargs):
        import frepple

        source = kwargs.get("source", None)
        attrs = [f[0] for f in getAttributes(ResourceSkill)]

        def getData():
            for s in frepple.skills():
                for i in s.resourceskills:
                    if source and source != i.source:
                        continue
                    r = [
                        i.effective_start
                        if i.effective_start != default_start
                        else None,
                        i.effective_end if i.effective_end != default_end else None,
                        i.priority,
                        i.source,
                        cls.timestamp,
                        i.resource.name,
                        s.name,
                    ]
                    for a in attrs:
                        r.append(getattr(i, a, None))
                    yield r

        with connections[database].cursor() as cursor:
            execute_batch(
                cursor,
                """
                insert into resourceskill
                (effective_start,effective_end,priority,source,lastmodified,resource_id,skill_id%s)
                values(%%s,%%s,%%s,%%s,%%s,%%s,%%s%s)
                on conflict (resource_id, skill_id)
                do update set
                  effective_start=excluded.effective_start,
                  effective_end=excluded.effective_end,
                  priority=excluded.priority,
                  source=excluded.source,
                  lastmodified=excluded.lastmodified
                  %s
                """
                % SQL4attributes(attrs),
                getData(),
            )


@PlanTaskRegistry.register
class exportOperationResources(PlanTask):

    description = ("Export static data", "Export operation resources")
    sequence = (305, "exportstatic1", 4)

    @classmethod
    def getWeight(cls, database=DEFAULT_DB_ALIAS, **kwargs):
        return 1 if kwargs.get("exportstatic", False) else -1

    @classmethod
    def run(cls, database=DEFAULT_DB_ALIAS, **kwargs):
        import frepple

        source = kwargs.get("source", None)
        attrs = [f[0] for f in getAttributes(OperationResource)]

        def getData():
            for o in frepple.operations():
                if o.hidden:
                    continue
                for i in o.loads:
                    if i.hidden or (source and source != i.source):
                        continue
                    r = [
                        i.operation.name,
                        i.resource.name,
                        i.effective_start
                        if i.effective_start != default_start
                        else None,
                        i.effective_end if i.effective_end != default_end else None,
                        round(i.quantity, 8),
                        i.setup,
                        i.name,
                        i.priority,
                        i.search if i.search != "PRIORITY" else None,
                        i.source,
                        cls.timestamp,
                    ]
                    for a in attrs:
                        r.append(getattr(i, a, None))
                    yield r

        with connections[database].cursor() as cursor:
            execute_batch(
                cursor,
                """
                insert into operationresource
                (operation_id,resource_id,effective_start,effective_end,
                quantity,setup,name,priority,search,source,lastmodified%s)
                values(%%s,%%s,%%s,%%s,%%s,%%s,%%s,%%s,%%s,%%s,%%s%s)
                on conflict (operation_id, resource_id, effective_start)
                do update set
                  effective_end=excluded.effective_end,
                  quantity=excluded.quantity,
                  setup=excluded.setup,
                  name=excluded.name,
                  priority=excluded.priority,
                  search=excluded.search,
                  source=excluded.source,
                  lastmodified=excluded.lastmodified
                  %s
                """
                % SQL4attributes(attrs),
                getData(),
            )


@PlanTaskRegistry.register
class exportCustomers(PlanTask):

    description = ("Export static data", "Export customers")
    sequence = (305, "exportstatic2", 1)

    @classmethod
    def getWeight(cls, database=DEFAULT_DB_ALIAS, **kwargs):
        return 1 if kwargs.get("exportstatic", False) else -1

    @classmethod
    def run(cls, database=DEFAULT_DB_ALIAS, **kwargs):
        import frepple

        source = kwargs.get("source", None)
        attrs = [f[0] for f in getAttributes(Customer)]

        def getData():
            for i in frepple.customers():
                if source and source != i.source:
                    continue
                r = [
                    i.name,
                    i.description,
                    i.category,
                    i.subcategory,
                    i.source,
                    cls.timestamp,
                ]
                for a in attrs:
                    r.append(getattr(i, a, None))
                yield r

        def getOwners():
            for i in frepple.customers():
                if i.owner and (not source or source == i.source):
                    yield (i.owner.name, i.name)

        with connections[database].cursor() as cursor:
            execute_batch(
                cursor,
                """
                insert into customer
                (name,description,category,subcategory,source,lastmodified,owner_id%s)
                values(%%s,%%s,%%s,%%s,%%s,%%s,null%s)
                on conflict (name)
                do update set
                  description=excluded.description,
                  category=excluded.category,
                  subcategory=excluded.subcategory,
                  source=excluded.source,
                  lastmodified=excluded.lastmodified,
                  owner_id=excluded.owner_id
                  %s
                """
                % SQL4attributes(attrs),
                getData(),
            )
            execute_batch(
                cursor, "update customer set owner_id=%s where name=%s", getOwners()
            )


@PlanTaskRegistry.register
class exportDemands(PlanTask):

    description = ("Export static data", "Export sales orders")
    sequence = (305, "exportstatic2", 2)

    @classmethod
    def getWeight(cls, database=DEFAULT_DB_ALIAS, **kwargs):
        return 1 if kwargs.get("exportstatic", False) else -1

    @classmethod
    def run(cls, database=DEFAULT_DB_ALIAS, **kwargs):
        import frepple

        source = kwargs.get("source", None)
        attrs = [f[0] for f in getAttributes(Demand)]

        def getData():
            for i in frepple.demands():
                if (
                    not isinstance(i, frepple.demand_default)
                    or i.hidden
                    or (source and source != i.source)
                ):
                    continue
                r = [
                    i.name,
                    i.due,
                    round(i.quantity, 8),
                    i.priority,
                    i.item.name,
                    i.location.name if i.location else None,
                    i.operation.name
                    if i.operation and not i.operation.hidden
                    else None,
                    i.customer.name if i.customer else None,
                    round(i.minshipment, 8),
                    i.maxlateness,
                    i.category,
                    i.subcategory,
                    i.source,
                    i.description,
                    cls.timestamp,
                    i.status,
                ]
                for a in attrs:
                    r.append(getattr(i, a, None))
                yield r

        def getOwners():
            for i in frepple.demands():
                if (
                    i.owner
                    and isinstance(i, frepple.demand_default)
                    and not i.hidden
                    and (not source or source == i.source)
                ):
                    yield (i.owner.name, i.name)

        with connections[database].cursor() as cursor:
            execute_batch(
                cursor,
                """
                insert into demand
                (name,due,quantity,priority,item_id,location_id,operation_id,customer_id,
                 minshipment,maxlateness,category,subcategory,source,description,lastmodified,
                 status,owner_id%s)
                values(%%s,%%s,%%s,%%s,%%s,%%s,%%s,%%s,%%s,%%s * interval '1 second',%%s,%%s,%%s,%%s,%%s,%%s,null%s)
                on conflict (name)
                do update set
                  due=excluded.due,
                  quantity=excluded.quantity,
                  priority=excluded.priority,
                  item_id=excluded.item_id,
                  location_id=excluded.location_id,
                  operation_id=excluded.operation_id,
                  customer_id=excluded.customer_id,
                  minshipment=excluded.minshipment,
                  maxlateness=excluded.maxlateness,
                  category=excluded.category,
                  description=excluded.description,
                  source=excluded.source,
                  lastmodified=excluded.lastmodified,
                  status=excluded.status,
                  owner_id=excluded.owner_id
                  %s
                """
                % SQL4attributes(attrs),
                getData(),
            )
        execute_batch(
            cursor, "update demand set owner_id=%s where name=%s", getOwners()
        )


@PlanTaskRegistry.register
class exportCalendarBuckets(PlanTask):

    description = ("Export static data", "Export calendar buckets")
    sequence = (305, "exportstatic3", 1)

    @classmethod
    def getWeight(cls, database=DEFAULT_DB_ALIAS, **kwargs):
        return 1 if kwargs.get("exportstatic", False) else -1

    @classmethod
    def run(cls, database=DEFAULT_DB_ALIAS, **kwargs):
        import frepple

        source = kwargs.get("source", None)
        attrs = [f[0] for f in getAttributes(CalendarBucket)]

        def int_to_time(i):
            hour = i // 3600
            i -= hour * 3600
            minute = i // 60
            i -= minute * 60
            second = i
            if hour >= 24:
                hour -= 24
            return "%s:%s:%s" % (hour, minute, second)

        def getData(cursor):
            cursor.execute("SELECT max(id) FROM calendarbucket")
            cnt = cursor.fetchone()[0] or 1
            for c in frepple.calendars():
                if (
                    c.hidden
                    or c.source == "common_bucket"
                    or (source and source != c.source)
                ):
                    continue
                for i in c.buckets:
                    cnt += 1
                    r = [
                        c.name,
                        i.start if i.start != default_start else None,
                        i.end if i.end != default_end else None,
                        cnt,
                        i.priority,
                        round(i.value, 8),
                        True if (i.days & 1) else False,
                        True if (i.days & 2) else False,
                        True if (i.days & 4) else False,
                        True if (i.days & 8) else False,
                        True if (i.days & 16) else False,
                        True if (i.days & 32) else False,
                        True if (i.days & 64) else False,
                        int_to_time(i.starttime),
                        int_to_time(i.endtime - 1),
                        i.source,
                        cls.timestamp,
                    ]
                    for a in attrs:
                        r.append(getattr(i, a, None))
                    yield r

        with connections[database].cursor() as cursor:
            if source:
                cursor.execute("delete from calendarbucket where source = %s", [source])
            else:
                cursor.execute("delete from calendarbucket")
            execute_batch(
                cursor,
                """
                insert into calendarbucket
                (calendar_id,startdate,enddate,id,priority,value,
                sunday,monday,tuesday,wednesday,thursday,friday,saturday,
                starttime,endtime,source,lastmodified%s)
                values(%%s,%%s,%%s,%%s,%%s,%%s,%%s,%%s,%%s,%%s,%%s,%%s,%%s,%%s,%%s,%%s,%%s%s)
                """
                % SQL4attributes(attrs, with_on_conflict=False),
                getData(cursor),
            )


@PlanTaskRegistry.register
class exportBuffers(PlanTask):

    description = ("Export static data", "Export buffers")
    sequence = (305, "exportstatic4", 1)

    @classmethod
    def getWeight(cls, database=DEFAULT_DB_ALIAS, **kwargs):
        return 1 if kwargs.get("exportstatic", False) else -1

    @classmethod
    def run(cls, database=DEFAULT_DB_ALIAS, **kwargs):
        import frepple

        source = kwargs.get("source", None)
        attrs = [f[0] for f in getAttributes(Buffer)]

        def getData():
            for i in frepple.buffers():
                if i.hidden or (source and source != i.source):
                    continue
                r = [
                    i.item.name,
                    i.location.name,
                    i.batch or None,
                    i.description,
                    round(i.onhand, 8),
                    round(i.minimum, 8),
                    i.minimum_calendar.name if i.minimum_calendar else None,
                    i.__class__.__name__[7:],
                    i.category,
                    i.subcategory,
                    i.source,
                    cls.timestamp,
                ]
                for a in attrs:
                    r.append(getattr(i, a, None))
                yield r

        with connections[database].cursor() as cursor:
            execute_batch(
                cursor,
                """
                insert into buffer
                (item_id,location_id,batch,description,onhand,minimum,minimum_calendar_id,
                type,category,subcategory,source,lastmodified%s)
                values(%%s,%%s,%%s,%%s,%%s,%%s,%%s,%%s,%%s,%%s,%%s,%%s%s)
                on conflict (location_id, item_id, batch)
                do update set
                  description=excluded.description,
                  onhand=excluded.onhand,
                  minimum=excluded.minimum,
                  minimum_calendar_id=excluded.minimum_calendar_id,
                  type=excluded.type,
                  category=excluded.category,
                  subcategory=excluded.subcategory,
                  source=excluded.source,
                  lastmodified=excluded.lastmodified
                  %s
                """
                % SQL4attributes(attrs),
                getData(),
            )


@PlanTaskRegistry.register
class exportOperationMaterials(PlanTask):

    description = ("Export static data", "Export operation material")
    sequence = (305, "exportstatic4", 2)

    @classmethod
    def getWeight(cls, database=DEFAULT_DB_ALIAS, **kwargs):
        return 1 if kwargs.get("exportstatic", False) else -1

    @classmethod
    def run(cls, database=DEFAULT_DB_ALIAS, **kwargs):
        import frepple

        source = kwargs.get("source", None)
        attrs = [f[0] for f in getAttributes(OperationMaterial)]

        def getData():
            for o in frepple.operations():
                if o.hidden:
                    continue
                for i in o.flows:
                    if i.hidden or (source and source != i.source):
                        continue
                    r = [
                        i.operation.name,
                        i.buffer.item.name,
                        i.effective_start
                        if i.effective_start != default_start
                        else None,
                        round(i.quantity, 8),
                        i.type[5:],
                        i.effective_end if i.effective_end != default_end else None,
                        i.name,
                        i.priority,
                        i.search != "PRIORITY" and i.search or None,
                        i.source,
                        round(i.transferbatch, 8)
                        if isinstance(i, frepple.flow_transfer_batch)
                        else None,
                        cls.timestamp,
                    ]
                    for a in attrs:
                        r.append(getattr(i, a, None))
                    yield r

        with connections[database].cursor() as cursor:
            execute_batch(
                cursor,
                """
                insert into operationmaterial
                (operation_id,item_id,effective_start,quantity,type,effective_end,
                name,priority,search,source,transferbatch,lastmodified%s)
                values(%%s,%%s,%%s,%%s,%%s,%%s,%%s,%%s,%%s,%%s,%%s,%%s%s)
                on conflict (operation_id, item_id, effective_start)
                do update set
                  quantity=excluded.quantity,
                  type=excluded.type,
                  effective_end=excluded.effective_end,
                  name=excluded.name,
                  priority=excluded.priority,
                  search=excluded.search,
                  source=excluded.source,
                  transferbatch=excluded.transferbatch,
                  lastmodified=excluded.lastmodified
                  %s
                """
                % SQL4attributes(attrs),
                getData(),
            )


@PlanTaskRegistry.register
class exportSuppliers(PlanTask):

    description = ("Export static data", "Export suppliers")
    sequence = (305, "exportstatic4", 3)

    @classmethod
    def getWeight(cls, database=DEFAULT_DB_ALIAS, **kwargs):
        return 1 if kwargs.get("exportstatic", False) else -1

    @classmethod
    def run(cls, database=DEFAULT_DB_ALIAS, **kwargs):
        import frepple

        source = kwargs.get("source", None)
        attrs = [f[0] for f in getAttributes(Supplier)]

        def getData():
            for i in frepple.suppliers():
                if source and source != i.source:
                    continue
                r = [
                    i.name,
                    i.description,
                    i.category,
                    i.subcategory,
                    i.source,
                    cls.timestamp,
                ]
                for a in attrs:
                    r.append(getattr(i, a, None))
                yield r

        def getOwners():
            for i in frepple.suppliers():
                if i.owner and (not source or source == i.source):
                    yield (i.owner.name, i.name)

        with connections[database].cursor() as cursor:
            execute_batch(
                cursor,
                """
                insert into supplier
                (name,description,category,subcategory,source,lastmodified,owner_id%s)
                values(%%s,%%s,%%s,%%s,%%s,%%s,null%s)
                on conflict (name)
                do update set
                  description=excluded.description,
                  category=excluded.category,
                  subcategory=excluded.subcategory,
                  source=excluded.source,
                  lastmodified=excluded.lastmodified,
                  owner_id=excluded.owner_id
                  %s
                """
                % SQL4attributes(attrs),
                getData(),
            )
            execute_batch(
                cursor, "update supplier set owner_id=%s where name=%s", getOwners()
            )


@PlanTaskRegistry.register
class exportItemSuppliers(PlanTask):

    description = ("Export static data", "Export item suppliers")
    sequence = (305, "exportstatic4", 4)

    @classmethod
    def getWeight(cls, database=DEFAULT_DB_ALIAS, **kwargs):
        return 1 if kwargs.get("exportstatic", False) else -1

    @classmethod
    def run(cls, database=DEFAULT_DB_ALIAS, **kwargs):
        import frepple

        source = kwargs.get("source", None)
        attrs = [f[0] for f in getAttributes(ItemSupplier)]

        def getData():
            for s in frepple.suppliers():
                if source and source != s.source:
                    continue
                for i in s.itemsuppliers:
                    if i.hidden or (source and source != i.source):
                        continue
                    r = [
                        i.item.name,
                        i.location.name if i.location else None,
                        i.supplier.name,
                        i.effective_start
                        if i.effective_start != default_start
                        else None,
                        i.leadtime,
                        i.size_minimum,
                        i.size_multiple,
                        i.cost,
                        i.priority,
                        i.effective_end if i.effective_end != default_end else None,
                        i.resource.name if i.resource else None,
                        i.resource_qty,
                        i.source,
                        cls.timestamp,
                    ]
                    for a in attrs:
                        r.append(getattr(i, a, None))
                    yield r

        with connections[database].cursor() as cursor:
            execute_batch(
                cursor,
                """
                insert into itemsupplier
                (item_id,location_id,supplier_id,effective_start,leadtime,sizeminimum,
                 sizemultiple,cost,priority,effective_end,resource_id,resource_qty,source,
                 lastmodified%s)
                values(%%s,%%s,%%s,%%s,%%s * interval '1 second',%%s,%%s,%%s,%%s,%%s,%%s,%%s,%%s,%%s%s)
                on conflict (item_id, location_id, supplier_id, effective_start)
                do update set
                  leadtime=excluded.leadtime,
                  sizeminimum=excluded.sizeminimum,
                  sizemultiple=excluded.sizemultiple,
                  cost=excluded.cost,
                  priority=excluded.priority,
                  effective_end=excluded.effective_end,
                  resource_id=excluded.resource_id,
                  resource_qty=excluded.resource_qty,
                  source=excluded.source,
                  lastmodified=excluded.lastmodified
                  %s
                """
                % SQL4attributes(attrs),
                getData(),
            )


@PlanTaskRegistry.register
class exportItemDistributions(PlanTask):

    description = ("Export static data", "Export item distributions")
    sequence = (305, "exportstatic4", 5)

    @classmethod
    def getWeight(cls, database=DEFAULT_DB_ALIAS, **kwargs):
        return 1 if kwargs.get("exportstatic", False) else -1

    @classmethod
    def run(cls, database=DEFAULT_DB_ALIAS, **kwargs):
        import frepple

        source = kwargs.get("source", None)
        attrs = [f[0] for f in getAttributes(ItemDistribution)]

        def getData():
            for s in frepple.items():
                if s.hidden or (source and source != s.source):
                    continue
                for i in s.itemdistributions:
                    if i.hidden or (source and source != i.source):
                        continue
                    r = [
                        i.item.name,
                        i.destination.name if i.destination else None,
                        i.origin.name,
                        i.effective_start
                        if i.effective_start != default_start
                        else None,
                        i.leadtime,
                        i.size_minimum,
                        i.size_multiple,
                        i.cost,
                        i.priority,
                        i.effective_end if i.effective_end != default_end else None,
                        i.source,
                        cls.timestamp,
                    ]
                    for a in attrs:
                        r.append(getattr(i, a, None))
                    yield r

        with connections[database].cursor() as cursor:
            execute_batch(
                cursor,
                """
                insert into itemdistribution
                (item_id,location_id,origin_id,effective_start,leadtime,sizeminimum,
                 sizemultiple,cost,priority,effective_end,source,lastmodified%s)
                values(%%s,%%s,%%s,%%s,%%s * interval '1 second',%%s,%%s,%%s,%%s,%%s,%%s,%%s%s)
                on conflict (item_id, location_id, origin_id, effective_start)
                do update set
                  leadtime=excluded.leadtime,
                  sizeminimum=excluded.sizeminimum,
                  sizemultiple=excluded.sizemultiple,
                  cost=excluded.cost,
                  priority=excluded.priority,
                  effective_end=excluded.effective_end,
                  source=excluded.source,
                  lastmodified=excluded.lastmodified
                  %s
                """
                % SQL4attributes(attrs),
                getData(),
            )
