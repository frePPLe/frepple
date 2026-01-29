#
# Copyright (C) 2020 by frePPLe bv
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

from datetime import datetime
import logging
from psycopg2.extras import execute_batch

from django.db import DEFAULT_DB_ALIAS, connections
from django.conf import settings

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
    OperationDependency,
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

map_search = {0: "PRIORITY", 1: "MINCOST", 2: "MINPENALTY", 3: "MINCOSTPENALTY"}


def SQL4attributes(attrs, with_on_conflict=True):
    """Snippet is used many times in this file"""
    res0 = []
    res1 = []
    res2 = []
    for a in attrs:
        res0.append(",%s" % a[0])
        res1.append(",%s * '1 second'::interval" if a[2] == "duration" else ",%s")
        res2.append(",\n%s=excluded.%s" % (a[0], a[0]))
    if with_on_conflict:
        return ("".join(res0), "".join(res1), "".join(res2))
    else:
        return ("".join(res0), "".join(res1))


@PlanTaskRegistry.register
class cleanStatic(PlanTask):
    description = "Clean static data"
    sequence = 107.18

    @classmethod
    def getWeight(cls, database=DEFAULT_DB_ALIAS, **kwargs):
        if kwargs.get("exportstatic", False) and kwargs.get("source", None):
            return 1
        else:
            return -1

    @classmethod
    def updateNames(cls, model, database, source):
        cursor = connections[database].cursor()
        db_table = model._meta.db_table
        # detect if we have a name change
        cursor.execute(
            """
            select old%s.name, new%s.name from %s old%s
            inner join %s new%s on old%s.name != new%s.name
            and split_part(old%s.subcategory,',',2) = split_part(new%s.subcategory,',',2)
            and new%s.lastmodified > old%s.lastmodified
            and old%s.source = %%s and new%s.source = %%s
            """
            % ((db_table,) * 14),
            (source, source),
        )

        for i in cursor:
            oldname = i[0]
            newname = i[1]
            new_obj = model.objects.using(database).get(name=newname)

            # All linked fields need updating.
            for related in new_obj._meta.get_fields():
                if (
                    (related.one_to_many or related.one_to_one)
                    and related.auto_created
                    and not related.concrete
                ):
                    try:
                        related.related_model._base_manager.using(database).filter(
                            **{related.field.name: oldname}
                        ).update(**{related.field.name: new_obj})
                    except Exception:
                        # object with new name already exists => deleting old record
                        related.related_model._base_manager.using(database).filter(
                            **{related.field.name: oldname}
                        ).delete()

    @classmethod
    def getSQLNoReferences(cls, table, field):
        sql = " and ".join(
            'not exists (select 1 from "%s" as someunusedalias where someunusedalias."%s" = "%s"."%s")'
            % (x[0], x[1], table, field)
            for x in cls.fk_relations.get("%s.%s" % (table, field), [])
        )
        return sql if sql else "true"

    @classmethod
    def run(cls, database=DEFAULT_DB_ALIAS, **kwargs):
        # TODO since this is run BEFORE the export, the lastmodified field will
        # always be different from the timestamp of the current export.
        source = kwargs.get("source", None)

        with connections[database].cursor() as cursor:
            # detect if we have an item/location/customer name change
            cls.fk_relations = {}
            if source:
                cls.updateNames(Item, database, source)
                cls.updateNames(Location, database, source)
                cls.updateNames(Customer, database, source)

                # Build a dictionary of all foreign key relations in our database
                cursor.execute(
                    """
                    select
                    u.table_name || '.' || u.column_name, r.table_name, r.column_name
                    from information_schema.constraint_column_usage u
                    inner join information_schema.referential_constraints fk
                    on u.constraint_catalog = fk.unique_constraint_catalog
                    and u.constraint_schema = fk.unique_constraint_schema
                    and u.constraint_name = fk.unique_constraint_name
                    and u.table_schema = 'public'
                    inner join information_schema.key_column_usage r
                    on r.constraint_catalog = fk.constraint_catalog
                    and r.constraint_schema = fk.constraint_schema
                    and r.constraint_name = fk.constraint_name
                    and r.table_schema = 'public'
                    order by u.table_name
                    """
                )
                for fk in cursor.fetchall():
                    if fk[0] in cls.fk_relations:
                        cls.fk_relations[fk[0]].append((fk[1], fk[2]))
                    else:
                        cls.fk_relations[fk[0]] = [(fk[1], fk[2])]

            cursor.execute(
                """
                delete from operation_dependency
                where source = %%s and lastmodified <> %%s and %s
                """
                % cls.getSQLNoReferences("operation_dependency", "id"),
                (source, cls.timestamp),
            )
            cursor.execute(
                """
                with cte as (
                    select name from operation
                    where operation.source = %%s and operation.lastmodified <> %%s
                    )
                delete from operation_dependency
                where exists
                (select 1 from cte where name = any(select operation_id union all select blockedby_id))
                and %s
                """
                % cls.getSQLNoReferences("operation_dependency", "id"),
                (source, cls.timestamp),
            )

            cursor.execute(
                """
                delete from operationmaterial
                where source = %%s and lastmodified <> %%s and %s
                """
                % cls.getSQLNoReferences("operationmaterial", "id"),
                (source, cls.timestamp),
            )
            cursor.execute(
                """
                delete from operationmaterial
                where exists (
                    select 1 from operation
                    where operation.name = operationmaterial.operation_id
                    and operation.source = %%s
                    and operation.lastmodified <> %%s
                    )
                and %s
                """
                % cls.getSQLNoReferences("operationmaterial", "id"),
                (source, cls.timestamp),
            )
            cursor.execute(
                "delete from buffer where source = %%s and lastmodified <> %%s and %s"
                % cls.getSQLNoReferences("operationmaterial", "id"),
                (source, cls.timestamp),
            )
            cursor.execute(
                """
                delete from operationplan
                where exists (select 1 from demand
                where demand.name = operationplan.demand_id
                and demand.source = %s
                and demand.lastmodified <> %s)
                """,
                (source, cls.timestamp),
            )

            cursor.execute(
                "delete from demand where source = %%s and lastmodified <> %%s and %s"
                % cls.getSQLNoReferences("demand", "name"),
                (source, cls.timestamp),
            )
            cursor.execute(
                "delete from itemsupplier where source = %%s and lastmodified <> %%s and %s"
                % cls.getSQLNoReferences("itemsupplier", "id"),
                (source, cls.timestamp),
            )
            cursor.execute(
                "delete from itemdistribution where source = %%s and lastmodified <> %%s and %s"
                % cls.getSQLNoReferences("itemdistribution", "id"),
                (source, cls.timestamp),
            )
            cursor.execute(
                """
                delete from operationplan
                where owner_id is not null and (
                 (source = %s and lastmodified <> %s)
                  or exists (
                    select 1 from operation
                    where operation.name = operationplan.operation_id and operation.source = %s and operation.lastmodified <> %s
                    )
                  or exists (
                    select 1 from supplier
                    where supplier.name = operationplan.supplier_id and supplier.source = %s and supplier.lastmodified <> %s
                   )
                )
                """,
                (source, cls.timestamp, source, cls.timestamp, source, cls.timestamp),
            )

            # before deleting an operationplan, we must ensure that operationplan
            # is not the owner of another one
            cursor.execute(
                """
                delete from operationplan where exists
                (
                select 1 from operationplan opplan
                    where reference = operationplan.owner_id
                    and
                    ((source = %s and lastmodified <> %s)
                    or exists (
                        select 1 from operation op
                        where op.name = operationplan.operation_id
                          and op.source = %s and op.lastmodified <> %s
                        )
                    or exists (
                        select 1 from supplier
                        where supplier.name = supplier_id
                        and supplier.source = %s
                        and supplier.lastmodified <> %s
                    )
                    or type = 'STCK')
                )
                """,
                (source, cls.timestamp, source, cls.timestamp, source, cls.timestamp),
            )

            cursor.execute(
                """
                delete from operationplan
                where (source = %s and lastmodified <> %s)
                  or exists (
                    select 1 from operation
                    where operation.name = operationplan.operation_id
                    and operation.source = %s
                    and lastmodified <> %s
                    )
                  or exists (
                    select 1 from supplier
                    where supplier.name = operationplan.supplier_id and source = %s
                    and lastmodified <> %s
                   )
                  or type = 'STCK'
                """,
                (source, cls.timestamp, source, cls.timestamp, source, cls.timestamp),
            )
            cursor.execute(
                """
                delete from operationresource
                where ((source = %%s and lastmodified <> %%s)
                  or exists (
                     select 1 from operation
                     where operation.name = operationresource.operation_id
                     and operation.source = %%s and operation.lastmodified <> %%s
                     )
                  ) and %s
                """
                % cls.getSQLNoReferences("operationresource", "id"),
                (source, cls.timestamp, source, cls.timestamp),
            )
            cursor.execute(
                "delete from operation where source = %%s and lastmodified <> %%s and %s"
                % cls.getSQLNoReferences("operation", "name"),
                (source, cls.timestamp),
            )
            if "freppledb.forecast" in settings.INSTALLED_APPS:
                cursor.execute(
                    """
                    delete from forecast where exists
                    (select 1 from item
                    where item.name = forecast.item_id
                    and item.source = %%s
                    and item.lastmodified <> %%s)
                    and %s
                    """
                    % cls.getSQLNoReferences("forecast", "name"),
                    (source, cls.timestamp),
                )
                cursor.execute(
                    """
                    delete from forecast where exists
                    (select 1 from location
                    where location.name = forecast.location_id
                    and location.source = %%s
                    and location.lastmodified <> %%s)
                    and %s
                    """
                    % cls.getSQLNoReferences("forecast", "name"),
                    (source, cls.timestamp),
                )
                cursor.execute(
                    """
                    delete from forecast where exists
                    (select 1 from customer
                    where customer.name = forecast.customer_id
                    and source = %%s
                    and lastmodified <> %%s)
                    and %s
                    """
                    % cls.getSQLNoReferences("forecast", "name"),
                    (source, cls.timestamp),
                )
                cursor.execute(
                    """
                    delete from forecastplan where exists
                    (select 1 from item
                    where item.name = forecastplan.item_id
                    and item.source = %s
                    and item.lastmodified <> %s)
                    """,
                    (source, cls.timestamp),
                )
                cursor.execute(
                    """
                    delete from forecastplan where exists
                    (select 1 from location
                    where location.name = forecastplan.location_id
                    and location.source = %s
                    and location.lastmodified <> %s)
                    """,
                    (source, cls.timestamp),
                )
                cursor.execute(
                    """
                    delete from forecastplan where exists
                    (select 1 from customer
                    where customer.name = forecastplan.customer_id
                    and customer.source = %s
                    and customer.lastmodified <> %s)
                    """,
                    (source, cls.timestamp),
                )
            if "freppledb.inventoryplanning" in settings.INSTALLED_APPS:
                cursor.execute(
                    """
                    delete from inventoryplanning where exists
                    (select 1 from item
                    where item.name = inventoryplanning.item_id
                    and item.source = %%s
                    and item.lastmodified <> %%s)
                    and %s
                    """
                    % cls.getSQLNoReferences("inventoryplanning", "id"),
                    (source, cls.timestamp),
                )
                cursor.execute(
                    """
                    delete from out_inventoryplanning where exists
                    (select 1 from item
                    where item.name = out_inventoryplanning.item_id
                    and item.source = %s
                    and item.lastmodified <> %s)
                    """,
                    (source, cls.timestamp),
                )
                cursor.execute(
                    """
                    delete from inventoryplanning where exists
                    (select 1 from location where name = inventoryplanning.location_id and source = %%s and lastmodified <> %%s)
                    and %s
                    """
                    % cls.getSQLNoReferences("inventoryplanning", "id"),
                    (source, cls.timestamp),
                )
                cursor.execute(
                    """
                    delete from out_inventoryplanning where exists
                    (select 1 from location where name = out_inventoryplanning.location_id and source = %s and lastmodified <> %s)
                    """,
                    (source, cls.timestamp),
                )

            # item deletion
            cursor.execute(
                """
                delete from operationplanmaterial where exists
                (select 1 from item where name = operationplanmaterial.item_id and source = %s and lastmodified <> %s)
                """,
                (source, cls.timestamp),
            )

            cursor.execute(
                """
                delete from operationplan where exists
                (select 1 from item where name = operationplan.item_id and source = %s and lastmodified <> %s)
                """,
                (source, cls.timestamp),
            )

            cursor.execute(
                """
                delete from itemsupplier where exists
                (select name from item where name = itemsupplier.item_id and source = %%s and lastmodified <> %%s)
                and %s
                """
                % cls.getSQLNoReferences("itemsupplier", "id"),
                (source, cls.timestamp),
            )

            cursor.execute(
                """
                delete from itemdistribution where exists
                (select 1 from item where name = itemdistribution.item_id and source = %%s and lastmodified <> %%s)
                and %s
                """
                % cls.getSQLNoReferences("itemdistribution", "id"),
                (source, cls.timestamp),
            )

            cursor.execute(
                """
                delete from buffer where exists
                (select name from item where name = buffer.item_id and source = %%s and lastmodified <> %%s)
                and %s
                """
                % cls.getSQLNoReferences("buffer", "id"),
                (source, cls.timestamp),
            )

            cursor.execute(
                """
                update operationplan set demand_id = null where exists
                (select 1 from demand where name = operationplan.demand_id and exists
                (select 1 from item where name = demand.item_id and source = %s and lastmodified <> %s))
                """,
                (source, cls.timestamp),
            )

            cursor.execute(
                """
                delete from demand where exists
                (select 1 from item where name = demand.item_id and source = %%s and lastmodified <> %%s)
                and %s
                """
                % cls.getSQLNoReferences("demand", "name"),
                (source, cls.timestamp),
            )

            cursor.execute(
                """
                delete from operationplanmaterial where exists
                (select 1 from item where name = operationplanmaterial.item_id and source = %s
                and lastmodified <> %s)
                """,
                (source, cls.timestamp),
            )

            cursor.execute(
                """
                delete from operationplan where exists
                (select 1 from item where name = operationplan.item_id and source = %s and lastmodified <> %s)
                """,
                (source, cls.timestamp),
            )

            cursor.execute(
                """
                delete from itemsupplier where exists
                (select 1 from item where name = itemsupplier.item_id and source = %%s and lastmodified <> %%s)
                and %s
                """
                % cls.getSQLNoReferences("itemsupplier", "id"),
                (source, cls.timestamp),
            )

            cursor.execute(
                """
                delete from itemdistribution where exists
                (select 1 from item where name = itemdistribution.item_id and source = %%s
                and lastmodified <> %%s)
                and %s
                """
                % cls.getSQLNoReferences("itemdistribution", "id"),
                (source, cls.timestamp),
            )

            cursor.execute(
                """
                delete from buffer where exists
                (select 1 from item
                where item.name = buffer.item_id
                and item.source = %%s
                and item.lastmodified <> %%s)
                and %s
                """
                % cls.getSQLNoReferences("buffer", "id"),
                (source, cls.timestamp),
            )

            cursor.execute(
                """
                delete from demand where exists
                (select 1 from item
                where item.name = demand.item_id
                and item.source = %%s
                and item.lastmodified <> %%s)
                and %s
                """
                % cls.getSQLNoReferences("demand", "name"),
                (source, cls.timestamp),
            )

            cursor.execute(
                "delete from item where source = %%s and lastmodified <> %%s and %s"
                % cls.getSQLNoReferences("item", "name"),
                (source, cls.timestamp),
            )
            cursor.execute(
                "delete from resourceskill where source = %%s and lastmodified <> %%s and %s"
                % cls.getSQLNoReferences("resourceskill", "id"),
                (source, cls.timestamp),
            )
            cursor.execute(
                "delete from operation where source = %%s and lastmodified <> %%s and %s"
                % cls.getSQLNoReferences("operation", "name"),
                (source, cls.timestamp),
            )

            cursor.execute(
                """
                delete from operationplanresource where exists
                (select 1 from resource
                where resource.name = operationplanresource.resource_id
                and resource.source = %s and resource.lastmodified <> %s)
                """,
                (source, cls.timestamp),
            )

            cursor.execute(
                "delete from resource where source = %%s and lastmodified <> %%s and %s"
                % cls.getSQLNoReferences("resource", "name"),
                (source, cls.timestamp),
            )

            # location deletion
            cursor.execute(
                """
                delete from operationplanmaterial where exists
                (select 1 from location where name = operationplanmaterial.location_id
                and location.source = %s and location.lastmodified <> %s)
                """,
                (source, cls.timestamp),
            )
            cursor.execute(
                """
                delete from operationplan where exists
                (select 1 from location where location.name =
                any(select operationplan.location_id union all
                    select operationplan.origin_id union all
                    select operationplan.destination_id)
                and location.source = %s and location.lastmodified <> %s)
                """,
                (source, cls.timestamp),
            )

            cursor.execute(
                """
                delete from itemsupplier where exists
                (select 1 from location where location.name = itemsupplier.location_id
                and source = %%s and lastmodified <> %%s)
                and %s
                """
                % cls.getSQLNoReferences("itemsupplier", "id"),
                (source, cls.timestamp),
            )

            cursor.execute(
                """
                delete from itemdistribution where exists(
                  (select 1 from location where name =
                  any(select itemdistribution.location_id union all select itemdistribution.origin_id)
                  and source = %%s and lastmodified <> %%s)
                ) and %s
                """
                % cls.getSQLNoReferences("itemdistribution", "id"),
                (source, cls.timestamp),
            )

            cursor.execute(
                """
                delete from buffer where exists
                (select 1 from location where name = buffer.location_id and source = %%s and lastmodified <> %%s)
                and %s
                """
                % cls.getSQLNoReferences("buffer", "id"),
                (source, cls.timestamp),
            )

            cursor.execute(
                """
                update operationplan set demand_id = null
                where demand_id is not null
                and exists
                (select 1 from demand where demand.name = operationplan.demand_id and exists
                (select 1 from location where location.name = demand.location_id and source = %s and lastmodified <> %s))
                """,
                (source, cls.timestamp),
            )

            cursor.execute(
                """
                delete from demand where exists
                (select 1 from location where location.name = demand.location_id and source = %%s and lastmodified <> %%s)
                and %s
                """
                % cls.getSQLNoReferences("demand", "name"),
                (source, cls.timestamp),
            )
            cursor.execute(
                """
                delete from resource where exists
                (select 1 from location where location.name = resource.location_id and source = %%s and lastmodified <> %%s)
                and %s
                """
                % cls.getSQLNoReferences("resource", "name"),
                (source, cls.timestamp),
            )

            cursor.execute(
                """
                delete from operation where exists
                (select 1 from location where location.name = operation.location_id and source = %%s
                and lastmodified <> %%s)
                and %s
                """
                % cls.getSQLNoReferences("operation", "name"),
                (source, cls.timestamp),
            )

            cursor.execute(
                "delete from location where source = %%s and lastmodified <> %%s and %s"
                % cls.getSQLNoReferences("location", "name"),
                (source, cls.timestamp),
            )

            # calendar deletion
            cursor.execute(
                "delete from calendarbucket where source = %%s and lastmodified <> %%s and %s"
                % cls.getSQLNoReferences("calendarbucket", "id"),
                (source, cls.timestamp),
            )
            cursor.execute(
                "delete from calendar where source = %%s and lastmodified <> %%s and %s"
                % cls.getSQLNoReferences("calendar", "name"),
                (source, cls.timestamp),
            )
            cursor.execute(
                "delete from skill where source = %%s and lastmodified <> %%s and %s"
                % cls.getSQLNoReferences("skill", "name"),
                (source, cls.timestamp),
            )
            cursor.execute(
                "delete from setuprule where source = %%s and lastmodified <> %%s and %s"
                % cls.getSQLNoReferences("setuprule", "id"),
                (source, cls.timestamp),
            )
            cursor.execute(
                "delete from setupmatrix where source = %%s and lastmodified <> %%s and %s"
                % cls.getSQLNoReferences("setupmatrix", "name"),
                (source, cls.timestamp),
            )

            cursor.execute(
                """
                update operationplan set demand_id = null where exists
                (select 1 from demand where name = operationplan.demand_id and exists
                (select 1 from customer where name = demand.customer_id and source = %s and lastmodified <> %s))
                """,
                (source, cls.timestamp),
            )

            # customer deletion
            cursor.execute(
                """
                delete from demand where exists
                (select 1 from customer
                where customer.name = demand.customer_id
                and customer.source = %%s and
                customer.lastmodified <> %%s)
                and %s
                """
                % cls.getSQLNoReferences("demand", "name"),
                (source, cls.timestamp),
            )
            cursor.execute(
                "delete from customer where source = %%s and lastmodified <> %%s and %s"
                % cls.getSQLNoReferences("customer", "name"),
                (source, cls.timestamp),
            )

            # supplier deletion
            cursor.execute(
                """
                delete from itemsupplier where exists
                (select 1 from supplier
                where supplier.name = itemsupplier.supplier_id
                and supplier.source = %%s
                and supplier.lastmodified <> %%s)
                and %s
                """
                % cls.getSQLNoReferences("itemsupplier", "id"),
                (source, cls.timestamp),
            )
            cursor.execute(
                """
                delete from operationplan where exists
                (select 1 from supplier where name = operationplan.supplier_id and source = %s and lastmodified <> %s)
                """,
                (source, cls.timestamp),
            )
            cursor.execute(
                "delete from supplier where source = %%s and lastmodified <> %%s and %s"
                % cls.getSQLNoReferences("supplier", "name"),
                (source, cls.timestamp),
            )


@PlanTaskRegistry.register
class exportParameters(PlanTask):
    description = ("Export static data", "Export parameters")
    sequence = (107.11, "exportstatic1", 1)

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
    sequence = (107.11, "exportstatic2", 1)

    @classmethod
    def getWeight(cls, database=DEFAULT_DB_ALIAS, **kwargs):
        return 1 if kwargs.get("exportstatic", False) else -1

    @classmethod
    def run(cls, database=DEFAULT_DB_ALIAS, **kwargs):
        import frepple

        source = kwargs.get("source", None)
        attrs = list(getAttributes(Calendar))

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
                    r.append(getattr(i, a[0], None))
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
    sequence = (107.12, "exportstatic1", 1)

    @classmethod
    def getWeight(cls, database=DEFAULT_DB_ALIAS, **kwargs):
        return 1 if kwargs.get("exportstatic", False) else -1

    @classmethod
    def run(cls, database=DEFAULT_DB_ALIAS, **kwargs):
        import frepple

        source = kwargs.get("source", None)
        attrs = list(getAttributes(Location))

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
                    r.append(getattr(i, a[0], None))
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
                  owner_id=excluded.owner_id,
                  lft=null
                  %s
                """
                % SQL4attributes(attrs),
                getData(),
            )
            execute_batch(
                cursor,
                "update location set owner_id=%s, lft=null where name=%s",
                getOwners(),
            )


@PlanTaskRegistry.register
class exportItems(PlanTask):
    description = ("Export static data", "Export items")
    sequence = (107.12, "exportstatic2", 1)

    @classmethod
    def getWeight(cls, database=DEFAULT_DB_ALIAS, **kwargs):
        return 1 if kwargs.get("exportstatic", False) else -1

    @classmethod
    def run(cls, database=DEFAULT_DB_ALIAS, **kwargs):
        import frepple

        source = kwargs.get("source", None)
        attrs = list(getAttributes(Item))

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
                    (
                        "make to order"
                        if isinstance(i, frepple.item_mto)
                        else "make to stock"
                    ),
                    i.source,
                    i.uom,
                    i.volume,
                    i.weight,
                    cls.timestamp,
                ]
                for a in attrs:
                    r.append(getattr(i, a[0], None))
                yield r

        def getOwners():
            for i in frepple.items():
                if i.owner and (not source or source == i.source):
                    yield (i.owner.name, i.name)

        with connections[database].cursor() as cursor:
            execute_batch(
                cursor,
                """insert into item
                (name,description,cost,category,subcategory,type,source,uom,volume,weight,lastmodified,owner_id%s)
                values (%%s,%%s,%%s,%%s,%%s,%%s,%%s,%%s,%%s,%%s,%%s,null%s)
                on conflict (name)
                do update set
                  description=excluded.description,
                  cost=excluded.cost,
                  category=excluded.category,
                  subcategory=excluded.subcategory,
                  type=excluded.type,
                  source=excluded.source,
                  uom=excluded.uom,
                  volume=excluded.volume,
                  weight=excluded.weight,
                  lastmodified=excluded.lastmodified,
                  owner_id=excluded.owner_id,
                  lft=null
                  %s
                """
                % SQL4attributes(attrs),
                getData(),
            )
            execute_batch(
                cursor,
                "update item set owner_id=%s, lft=null where name=%s",
                getOwners(),
            )


@PlanTaskRegistry.register
class exportOperations(PlanTask):
    description = ("Export static data", "Export operations")
    sequence = (107.13, "exportstatic1", 1)

    @classmethod
    def getWeight(cls, database=DEFAULT_DB_ALIAS, **kwargs):
        return 1 if kwargs.get("exportstatic", False) else -1

    @classmethod
    def run(cls, database=DEFAULT_DB_ALIAS, **kwargs):
        import frepple

        source = kwargs.get("source", None)
        attrs = list(getAttributes(Operation))

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
                    (
                        i.duration
                        if isinstance(
                            i,
                            (frepple.operation_fixed_time, frepple.operation_time_per),
                        )
                        else None
                    ),
                    (
                        i.duration_per
                        if isinstance(i, frepple.operation_time_per)
                        else None
                    ),
                    i.location and i.location.name or None,
                    round(i.cost, 8),
                    map_search[i.search],
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
                    r.append(getattr(i, a[0], None))
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
    sequence = (107.13, "exportstatic2", 1)

    @classmethod
    def getWeight(cls, database=DEFAULT_DB_ALIAS, **kwargs):
        return 1 if kwargs.get("exportstatic", False) else -1

    @classmethod
    def run(cls, database=DEFAULT_DB_ALIAS, **kwargs):
        import frepple

        source = kwargs.get("source", None)
        attrs = list(getAttributes(SetupMatrix))

        def getData():
            for i in frepple.setupmatrices():
                if source and source != i.source:
                    continue
                r = [i.name, i.source, cls.timestamp]
                for a in attrs:
                    r.append(getattr(i, a[0], None))
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
    sequence = 107.14

    @classmethod
    def getWeight(cls, database=DEFAULT_DB_ALIAS, **kwargs):
        return 1 if kwargs.get("exportstatic", False) else -1

    @classmethod
    def run(cls, database=DEFAULT_DB_ALIAS, **kwargs):
        import frepple

        source = kwargs.get("source", None)
        attrs = list(getAttributes(Resource))

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
                    r.append(getattr(i, a[0], None))
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
                  owner_id=excluded.owner_id,
                  lft=null
                  %s
                """
                % SQL4attributes(attrs),
                getData(),
            )
            execute_batch(
                cursor,
                "update resource set owner_id=%s, lft=null where name=%s",
                getOwners(),
            )


@PlanTaskRegistry.register
class exportSetupRules(PlanTask):
    description = ("Export static data", "Export setup matrix rules")
    sequence = (107.15, "exportstatic1", 1)

    @classmethod
    def getWeight(cls, database=DEFAULT_DB_ALIAS, **kwargs):
        return 1 if kwargs.get("exportstatic", False) else -1

    @classmethod
    def run(cls, database=DEFAULT_DB_ALIAS, **kwargs):
        import frepple

        source = kwargs.get("source", None)
        attrs = list(getAttributes(SetupRule))

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
                        r.append(getattr(i, a[0], None))
                    yield r

        with connections[database].cursor() as cursor:
            execute_batch(
                cursor,
                """insert into setuprule
                (setupmatrix_id,priority,fromsetup,tosetup,duration,cost,resource_id,source,lastmodified%s)
                values(%%s,%%s,%%s,%%s,%%s * interval '1 second',%%s,%%s,%%s,%%s%s)
                on conflict (setupmatrix_id, priority)
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
    sequence = (107.15, "exportstatic1", 2)

    @classmethod
    def getWeight(cls, database=DEFAULT_DB_ALIAS, **kwargs):
        return 1 if kwargs.get("exportstatic", False) else -1

    @classmethod
    def run(cls, database=DEFAULT_DB_ALIAS, **kwargs):
        import frepple

        source = kwargs.get("source", None)
        attrs = list(getAttributes(Skill))

        def getData():
            for i in frepple.skills():
                if source and source != i.source:
                    continue
                r = [i.name, i.source, cls.timestamp]
                for a in attrs:
                    r.append(getattr(i, a[0], None))
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
    sequence = (107.15, "exportstatic1", 3)

    @classmethod
    def getWeight(cls, database=DEFAULT_DB_ALIAS, **kwargs):
        return 1 if kwargs.get("exportstatic", False) else -1

    @classmethod
    def run(cls, database=DEFAULT_DB_ALIAS, **kwargs):
        import frepple

        source = kwargs.get("source", None)
        attrs = list(getAttributes(ResourceSkill))

        def getData():
            for s in frepple.skills():
                for i in s.resourceskills:
                    if source and source != i.source:
                        continue
                    r = [
                        (
                            i.effective_start
                            if i.effective_start != default_start
                            else None
                        ),
                        i.effective_end if i.effective_end != default_end else None,
                        i.priority,
                        i.source,
                        cls.timestamp,
                        i.resource.name,
                        s.name,
                    ]
                    for a in attrs:
                        r.append(getattr(i, a[0], None))
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
    sequence = (107.15, "exportstatic1", 4)

    @classmethod
    def getWeight(cls, database=DEFAULT_DB_ALIAS, **kwargs):
        return 1 if kwargs.get("exportstatic", False) else -1

    @classmethod
    def run(cls, database=DEFAULT_DB_ALIAS, **kwargs):
        import frepple

        source = kwargs.get("source", None)
        attrs = list(getAttributes(OperationResource))

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
                        i.effective_start,
                        i.effective_end if i.effective_end != default_end else None,
                        round(i.quantity, 8),
                        round(i.quantity_fixed, 8),
                        i.setup,
                        i.name,
                        i.priority,
                        (
                            map_search[i.search]
                            if map_search[i.search] != "PRIORITY"
                            else None
                        ),
                        i.source,
                        i.skill.name if i.skill else None,
                        cls.timestamp,
                    ]
                    for a in attrs:
                        r.append(getattr(i, a[0], None))
                    yield r

        with connections[database].cursor() as cursor:
            execute_batch(
                cursor,
                """
                insert into operationresource
                (operation_id,resource_id,effective_start,effective_end,
                quantity,quantity_fixed,setup,name,priority,search,source,skill_id,lastmodified%s)
                values(%%s,%%s,%%s,%%s,%%s,%%s,%%s,%%s,%%s,%%s,%%s,%%s,%%s%s)
                on conflict (operation_id, resource_id, effective_start)
                do update set
                  effective_end=excluded.effective_end,
                  quantity=excluded.quantity,
                  quantity_fixed=excluded.quantity_fixed,
                  setup=excluded.setup,
                  name=excluded.name,
                  priority=excluded.priority,
                  search=excluded.search,
                  skill_id=excluded.skill_id,
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
    sequence = (107.15, "exportstatic2", 1)

    @classmethod
    def getWeight(cls, database=DEFAULT_DB_ALIAS, **kwargs):
        return 1 if kwargs.get("exportstatic", False) else -1

    @classmethod
    def run(cls, database=DEFAULT_DB_ALIAS, **kwargs):
        import frepple

        source = kwargs.get("source", None)
        attrs = list(getAttributes(Customer))

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
                    r.append(getattr(i, a[0], None))
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
                  owner_id=excluded.owner_id,
                  lft=null
                  %s
                """
                % SQL4attributes(attrs),
                getData(),
            )
            execute_batch(
                cursor,
                "update customer set owner_id=%s, lft=null where name=%s",
                getOwners(),
            )


@PlanTaskRegistry.register
class exportDemands(PlanTask):
    description = ("Export static data", "Export sales orders")
    sequence = (107.15, "exportstatic2", 2)

    @classmethod
    def getWeight(cls, database=DEFAULT_DB_ALIAS, **kwargs):
        return 1 if kwargs.get("exportstatic", False) else -1

    @classmethod
    def run(cls, database=DEFAULT_DB_ALIAS, **kwargs):
        import frepple

        source = kwargs.get("source", None)
        attrs = list(getAttributes(Demand))

        def getData():
            for i in frepple.demands():
                if (
                    not isinstance(i, frepple.demand_default)
                    or i.hidden
                    or (source and source != i.source)
                ):
                    continue
                has_parent = (
                    i.owner
                    and isinstance(i.owner, frepple.demand_group)
                    and not i.owner.hidden
                    and (not source or source == i.owner.source)
                )
                r = [
                    i.name,
                    i.batch if i.batch else None,
                    i.due,
                    round(i.quantity, 8),
                    i.priority,
                    i.item.name,
                    i.location.name if i.location else None,
                    (
                        i.operation.name
                        if i.operation and not i.operation.hidden
                        else None
                    ),
                    i.customer.name if i.customer else None,
                    round(i.minshipment, 8),
                    i.maxlateness,
                    i.category,
                    i.subcategory,
                    i.source,
                    i.description,
                    cls.timestamp,
                    i.status,
                    i.owner.name if has_parent else None,
                    i.owner.policy if has_parent else None,
                ]
                for a in attrs:
                    r.append(getattr(i, a[0], None))
                yield r

        with connections[database].cursor() as cursor:
            execute_batch(
                cursor,
                """
                insert into demand
                (name,batch,due,quantity,priority,item_id,location_id,operation_id,customer_id,
                 minshipment,maxlateness,category,subcategory,source,description,lastmodified,
                 status,owner,policy%s)
                values(%%s,%%s,%%s,%%s,%%s,%%s,%%s,%%s,%%s,%%s,%%s * interval '1 second',%%s,%%s,%%s,%%s,%%s,%%s,%%s,%%s%s)
                on conflict (name)
                do update set
                  batch=excluded.batch,
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
                  owner=excluded.owner,
                  policy=excluded.policy
                  %s
                """
                % SQL4attributes(attrs),
                getData(),
            )


@PlanTaskRegistry.register
class exportCalendarBuckets(PlanTask):
    description = ("Export static data", "Export calendar buckets")
    sequence = (107.15, "exportstatic3", 1)

    @classmethod
    def getWeight(cls, database=DEFAULT_DB_ALIAS, **kwargs):
        return 1 if kwargs.get("exportstatic", False) else -1

    @classmethod
    def run(cls, database=DEFAULT_DB_ALIAS, **kwargs):
        import frepple

        source = kwargs.get("source", None)
        attrs = list(getAttributes(CalendarBucket))

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
            for c in frepple.calendars():
                if (
                    c.hidden
                    or c.source == "common_bucket"
                    or (source and source != c.source)
                ):
                    continue
                for i in c.buckets:
                    r = [
                        c.name,
                        i.start if i.start != default_start else None,
                        i.end if i.end != default_end else None,
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
                        r.append(getattr(i, a[0], None))
                    yield r

        with connections[database].cursor() as cursor:
            execute_batch(
                cursor,
                """
                insert into calendarbucket
                (calendar_id,startdate,enddate,priority,value,
                sunday,monday,tuesday,wednesday,thursday,friday,saturday,
                starttime,endtime,source,lastmodified%s)
                values(%%s,%%s,%%s,%%s,%%s,%%s,%%s,%%s,%%s,%%s,%%s,%%s,%%s,%%s,%%s,%%s%s)
                on conflict (calendar_id,startdate,enddate,priority)
                do update set
                  value=excluded.value,
                  sunday=excluded.sunday,
                  monday=excluded.monday,
                  tuesday=excluded.tuesday,
                  wednesday=excluded.wednesday,
                  thursday=excluded.thursday,
                  friday=excluded.friday,
                  saturday=excluded.saturday,
                  starttime=excluded.starttime,
                  endtime=excluded.endtime,
                  source=excluded.source,
                  lastmodified=excluded.lastmodified
                  %s
                """
                % SQL4attributes(attrs),
                getData(cursor),
            )


@PlanTaskRegistry.register
class exportBuffers(PlanTask):
    description = ("Export static data", "Export buffers")
    sequence = (107.15, "exportstatic4", 1)

    @classmethod
    def getWeight(cls, database=DEFAULT_DB_ALIAS, **kwargs):
        return 1 if kwargs.get("exportstatic", False) else -1

    @classmethod
    def run(cls, database=DEFAULT_DB_ALIAS, **kwargs):
        import frepple

        source = kwargs.get("source", None)
        attrs = list(getAttributes(Buffer))

        def getData():
            for i in frepple.buffers():
                if i.hidden or (source and source != i.source):
                    continue
                r = [
                    i.item.name,
                    i.location.name,
                    i.batch or "",
                    i.description,
                    round(i.onhand, 8),
                    round(i.minimum, 8),
                    i.minimum_calendar.name if i.minimum_calendar else None,
                    round(i.maximum, 8),
                    i.maximum_calendar.name if i.maximum_calendar else None,
                    i.__class__.__name__[7:],
                    i.category,
                    i.subcategory,
                    i.source,
                    cls.timestamp,
                ]
                for a in attrs:
                    r.append(getattr(i, a[0], None))
                yield r

        with connections[database].cursor() as cursor:
            execute_batch(
                cursor,
                """
                insert into buffer
                (item_id,location_id,batch,description,onhand,
                minimum,minimum_calendar_id,
                maximum,maximum_calendar_id,
                type,category,subcategory,source,lastmodified%s)
                values(%%s,%%s,%%s,%%s,%%s,%%s,%%s,%%s,%%s,%%s,%%s,%%s,%%s,%%s%s)
                on conflict (location_id, item_id, batch)
                do update set
                  description=excluded.description,
                  onhand=excluded.onhand,
                  minimum=excluded.minimum,
                  minimum_calendar_id=excluded.minimum_calendar_id,
                  maximum=excluded.maximum,
                  maximum_calendar_id=excluded.maximum_calendar_id,
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
    sequence = (107.15, "exportstatic4", 2)

    @classmethod
    def getWeight(cls, database=DEFAULT_DB_ALIAS, **kwargs):
        return 1 if kwargs.get("exportstatic", False) else -1

    @classmethod
    def run(cls, database=DEFAULT_DB_ALIAS, **kwargs):
        import frepple

        source = kwargs.get("source", None)
        attrs = list(getAttributes(OperationMaterial))

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
                        i.effective_start,
                        round(i.quantity, 8),
                        round(i.quantity_fixed, 8),
                        i.type[5:],
                        i.effective_end if i.effective_end != default_end else None,
                        i.name,
                        i.priority,
                        (
                            map_search[i.search]
                            if map_search[i.search] != "PRIORITY"
                            else None
                        ),
                        i.source,
                        (
                            round(i.transferbatch, 8)
                            if isinstance(i, frepple.flow_transfer_batch)
                            else None
                        ),
                        i.offset,
                        (
                            i.location.name
                            if i.location and i.location != i.operation.location
                            else None
                        ),
                        cls.timestamp,
                    ]
                    for a in attrs:
                        r.append(getattr(i, a[0], None))
                    yield r

        with connections[database].cursor() as cursor:
            execute_batch(
                cursor,
                """
                insert into operationmaterial
                (operation_id,item_id,effective_start,quantity,quantity_fixed,type,effective_end,
                name,priority,search,source,transferbatch,"offset",location_id,lastmodified%s)
                values(%%s,%%s,%%s,%%s,%%s,%%s,%%s,%%s,%%s,%%s,%%s,%%s,%%s * interval '1 second',%%s,%%s%s)
                on conflict (operation_id, item_id, effective_start)
                do update set
                  quantity=excluded.quantity,
                  quantity_fixed=excluded.quantity_fixed,
                  type=excluded.type,
                  effective_end=excluded.effective_end,
                  name=excluded.name,
                  priority=excluded.priority,
                  search=excluded.search,
                  source=excluded.source,
                  transferbatch=excluded.transferbatch,
                  "offset"=excluded."offset",
                  location_id=excluded.location_id,
                  lastmodified=excluded.lastmodified
                  %s
                """
                % SQL4attributes(attrs),
                getData(),
            )


@PlanTaskRegistry.register
class exportOperationDependencies(PlanTask):
    description = ("Export static data", "Export operation dependency")
    sequence = (107.15, "exportstatic4", 2.5)

    @classmethod
    def getWeight(cls, database=DEFAULT_DB_ALIAS, **kwargs):
        return 1 if kwargs.get("exportstatic", False) else -1

    @classmethod
    def run(cls, database=DEFAULT_DB_ALIAS, **kwargs):
        import frepple

        source = kwargs.get("source", None)
        attrs = list(getAttributes(OperationDependency))

        def getData():
            for o in frepple.operations():
                if o.hidden:
                    continue
                for i in o.dependencies:
                    if (
                        (source and source != i.source)
                        or not i.operation
                        or not i.blockedby
                    ):
                        continue
                    r = [
                        i.operation.name,
                        i.blockedby.name,
                        round(i.quantity, 8),
                        i.safety_leadtime,
                        i.hard_safety_leadtime,
                        cls.timestamp,
                    ]
                    for a in attrs:
                        r.append(getattr(i, a[0], None))
                    yield r

        with connections[database].cursor() as cursor:
            execute_batch(
                cursor,
                """
                insert into operation_dependency
                (operation_id,blockedby_id,quantity,safety_leadtime,hard_safety_leadtime,lastmodified%s)
                values(%%s,%%s,%%s,%%s * interval '1 second',%%s * interval '1 second',%%s%s)
                on conflict (operation_id, blockedby_id)
                do update set
                  quantity=excluded.quantity,
                  safety_leadtime=excluded.safety_leadtime,
                  hard_safety_leadtime=excluded.hard_safety_leadtime,
                  lastmodified=excluded.lastmodified
                  %s
                """
                % SQL4attributes(attrs),
                getData(),
            )


@PlanTaskRegistry.register
class exportSuppliers(PlanTask):
    description = ("Export static data", "Export suppliers")
    sequence = (107.15, "exportstatic4", 3)

    @classmethod
    def getWeight(cls, database=DEFAULT_DB_ALIAS, **kwargs):
        return 1 if kwargs.get("exportstatic", False) else -1

    @classmethod
    def run(cls, database=DEFAULT_DB_ALIAS, **kwargs):
        import frepple

        source = kwargs.get("source", None)
        attrs = list(getAttributes(Supplier))

        def getData():
            for i in frepple.suppliers():
                if source and source != i.source:
                    continue
                try:
                    available = frepple.location(name=i.name, action="C").available
                except Exception:
                    available = None
                r = [
                    i.name,
                    i.description,
                    i.category,
                    i.subcategory,
                    available.name if available else None,
                    i.source,
                    cls.timestamp,
                ]
                for a in attrs:
                    r.append(getattr(i, a[0], None))
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
                (name,description,category,subcategory,available_id,source,lastmodified,owner_id%s)
                values(%%s,%%s,%%s,%%s,%%s,%%s,%%s,null%s)
                on conflict (name)
                do update set
                  description=excluded.description,
                  category=excluded.category,
                  subcategory=excluded.subcategory,
                  available_id=excluded.available_id,
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
    sequence = (107.15, "exportstatic4", 4)

    @classmethod
    def getWeight(cls, database=DEFAULT_DB_ALIAS, **kwargs):
        return 1 if kwargs.get("exportstatic", False) else -1

    @classmethod
    def run(cls, database=DEFAULT_DB_ALIAS, **kwargs):
        import frepple

        source = kwargs.get("source", None)
        attrs = list(getAttributes(ItemSupplier))

        def getData(null_location):
            for s in frepple.suppliers():
                for i in s.itemsuppliers:
                    if i.hidden or (source and source != i.source):
                        continue
                    if null_location != (i.location is None):
                        continue
                    r = [
                        i.item.name,
                        i.location.name if i.location else None,
                        i.supplier.name,
                        i.effective_start,
                        i.leadtime,
                        i.size_minimum,
                        i.size_multiple,
                        i.size_maximum if i.size_maximum < 10**12 else None,
                        i.batchwindow,
                        i.hard_safety_leadtime,
                        i.extra_safety_leadtime,
                        i.fence,
                        i.cost,
                        i.priority,
                        i.effective_end if i.effective_end != default_end else None,
                        i.resource.name if i.resource else None,
                        i.resource_qty,
                        i.source,
                        cls.timestamp,
                    ]
                    for a in attrs:
                        r.append(getattr(i, a[0], None))
                    yield r

        with connections[database].cursor() as cursor:
            execute_batch(
                cursor,
                """
                insert into itemsupplier
                (item_id,location_id,supplier_id,effective_start,leadtime,sizeminimum,
                 sizemultiple,sizemaximum,batchwindow,hard_safety_leadtime,extra_safety_leadtime,
                 fence,cost,priority,effective_end,
                 resource_id,resource_qty,source,lastmodified%s)
                values(%%s,%%s,%%s,%%s,%%s * interval '1 second',%%s,%%s,%%s,
                %%s * interval '1 second',%%s * interval '1 second',%%s * interval '1 second',
                %%s * interval '1 second',%%s,%%s,%%s,%%s,%%s,%%s,%%s%s)
                on conflict (item_id, location_id, supplier_id, effective_start)
                do update set
                  leadtime=excluded.leadtime,
                  sizeminimum=excluded.sizeminimum,
                  sizemultiple=excluded.sizemultiple,
                  sizemaximum=excluded.sizemaximum,
                  batchwindow=excluded.batchwindow,
                  hard_safety_leadtime=excluded.hard_safety_leadtime,
                  extra_safety_leadtime=excluded.extra_safety_leadtime,
                  fence=excluded.fence,
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
                getData(null_location=False),
            )
            execute_batch(
                cursor,
                """
                insert into itemsupplier
                (item_id,location_id,supplier_id,effective_start,leadtime,sizeminimum,
                 sizemultiple,sizemaximum,batchwindow,hard_safety_leadtime,extra_safety_leadtime,
                 fence,cost,priority,effective_end,
                 resource_id,resource_qty,source,lastmodified%s)
                values(%%s,%%s,%%s,%%s,%%s * interval '1 second',%%s,%%s,%%s,
                %%s * interval '1 second',%%s * interval '1 second',%%s * interval '1 second',
                %%s * interval '1 second',%%s,%%s,%%s,%%s,%%s,%%s,%%s%s)
                on conflict (item_id, supplier_id, effective_start)
                   where location_id is null
                do update set
                  leadtime=excluded.leadtime,
                  sizeminimum=excluded.sizeminimum,
                  sizemultiple=excluded.sizemultiple,
                  sizemaximum=excluded.sizemaximum,
                  batchwindow=excluded.batchwindow,
                  hard_safety_leadtime=excluded.hard_safety_leadtime,
                  extra_safety_leadtime=excluded.extra_safety_leadtime,
                  fence=excluded.fence,
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
                getData(null_location=True),
            )


@PlanTaskRegistry.register
class exportItemDistributions(PlanTask):
    description = ("Export static data", "Export item distributions")
    sequence = (107.15, "exportstatic4", 5)

    @classmethod
    def getWeight(cls, database=DEFAULT_DB_ALIAS, **kwargs):
        return 1 if kwargs.get("exportstatic", False) else -1

    @classmethod
    def run(cls, database=DEFAULT_DB_ALIAS, **kwargs):
        import frepple

        source = kwargs.get("source", None)
        attrs = list(getAttributes(ItemDistribution))

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
                        i.effective_start,
                        i.leadtime,
                        i.size_minimum,
                        i.size_multiple,
                        i.batchwindow,
                        i.cost,
                        i.priority,
                        i.effective_end if i.effective_end != default_end else None,
                        i.source,
                        cls.timestamp,
                    ]
                    for a in attrs:
                        r.append(getattr(i, a[0], None))
                    yield r

        with connections[database].cursor() as cursor:
            execute_batch(
                cursor,
                """
                insert into itemdistribution
                (item_id,location_id,origin_id,effective_start,leadtime,sizeminimum,
                 sizemultiple,batchwindow,cost,priority,effective_end,source,lastmodified%s)
                values(%%s,%%s,%%s,%%s,%%s * interval '1 second',%%s,%%s,%%s * interval '1 second',%%s,%%s,%%s,%%s,%%s%s)
                on conflict (item_id, location_id, origin_id, effective_start)
                do update set
                  leadtime=excluded.leadtime,
                  sizeminimum=excluded.sizeminimum,
                  sizemultiple=excluded.sizemultiple,
                  batchwindow=excluded.batchwindow,
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
