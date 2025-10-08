#
# Copyright (C) 2007-2020 by frePPLe bv
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
import logging
import uuid
from time import time
from datetime import datetime, date, timedelta
from dateutil.parser import parse

from django.conf import settings
from django.db import connections, transaction, DEFAULT_DB_ALIAS
from django.db.utils import OperationalError

from freppledb.boot import getAttributes
from freppledb.common.models import Parameter
from freppledb.common.commands import PlanTaskRegistry, PlanTask
from freppledb.common.report import getCurrentDate
from freppledb.input.models import (
    Resource,
    Item,
    Location,
    OperationPlan,
    Demand,
    Operation,
)

logger = logging.getLogger(__name__)


class CheckTask(PlanTask):
    """
    Planning task to be used for data validation tasks.

    Specific are:
      - low weight by default, ie fast execution assumed
    """

    @staticmethod
    def getWeight(database=DEFAULT_DB_ALIAS, **kwargs):
        return 0.1


class LoadTask(PlanTask):
    """
    Planning task to be used for data loading tasks.

    Specific are:
    - low weight by default, ie fast execution assumed
    - filter attribute to load only a subset of the data
    - subclass is used by the odoo connector to recognize data loading tasks
    """

    @staticmethod
    def getWeight(database=DEFAULT_DB_ALIAS, **kwargs):
        return 0.1

    filter = None


@PlanTaskRegistry.register
class checkBuckets(CheckTask):
    # check for no buckets available
    # check for gaps between buckets (enddate bucket <> startdate next bucket)
    # check for overlaps (more than 1 bucket have the same startdate or the same enddate)
    # make sure partial indexes are created
    description = "Checking Buckets"
    sequence = 79

    @classmethod
    def run(cls, database=DEFAULT_DB_ALIAS, **kwargs):
        import frepple

        with connections[database].cursor() as cursor:
            cursor.execute(
                """
                WITH problems AS (
                  (
                    SELECT bucket_id, enddate AS date, 'enddate not matching next bucket startdate' AS message FROM common_bucketdetail
                    EXCEPT
                    SELECT bucket_id, startdate, 'enddate not matching next bucket startdate' AS message FROM common_bucketdetail
                  )
                  UNION ALL
                    SELECT bucket_id, startdate AS date, 'startdate not unique for this bucket_id' AS message FROM common_bucketdetail GROUP BY bucket_id, startdate HAVING COUNT(*)>1
                  UNION ALL
                    SELECT bucket_id, enddate AS date, 'enddate not unique for this bucket_id' AS message FROM common_bucketdetail GROUP BY bucket_id, enddate HAVING COUNT(*)>1
                ),
                maxenddate AS (
                      SELECT bucket_id, MAX(enddate) AS theend FROM common_bucketdetail GROUP BY bucket_id
                )
                SELECT problems.bucket_id, common_bucketdetail.name, problems.date, problems.date = maxenddate.theend, problems.message
                FROM common_bucketdetail
                RIGHT OUTER JOIN problems ON problems.bucket_id = common_bucketdetail.bucket_id AND (common_bucketdetail.startdate = problems.date OR common_bucketdetail.enddate = problems.date)
                INNER JOIN maxenddate ON maxenddate.bucket_id = common_bucketdetail.bucket_id
                """
            )
            errors = 0
            empty = True
            for rec in cursor:
                empty = False
                if rec[3] is False:
                    if not errors:
                        logger.error("Your reporting time buckets are invalid.")
                        logger.error(
                            "Time buckets cannot leave time gaps: the end date of one bucket "
                            "must be equal to the start date of the next one."
                        )
                    errors += 1
                    logger.error("%s %s %s %s" % (rec[0], rec[1], rec[2], rec[4]))
            if empty:
                logger.error("No reporting time buckets have been defined.")
                logger.error("You can define such buckets in different ways:")
                logger.error(
                    ' 1) Load the standard reporting buckets in the "admin/execute" screen.'
                )
                logger.error(
                    '    Use the "load a dataset" option and choose the "dates" dataset.'
                )
                logger.error(
                    ' 2) Use the "generate buckets" task in the "admin/execute" screen.'
                )
                logger.error(
                    "    You can choose the start and end date, and the name for each bucket."
                )
                logger.error(
                    " 3) For ultimate flexibility you can upload your own bucket definitions"
                )
                logger.error(
                    '    in the "admin/buckets" and "admin/bucket dates" tables.'
                )
                raise ValueError("No reporting time buckets have been defined")
            if errors > 0:
                raise ValueError("Invalid reporting time buckets")

            # Check if partial indexes exist
            cursor.execute(
                """
                select name from common_bucket
                except
                select description from pg_description
                inner join pg_class on pg_class.oid = pg_description.objoid
                inner join pg_indexes on pg_indexes.indexname = pg_class.relname and pg_indexes.tablename = 'common_bucketdetail'
                """
            )
            queries = []
            for rec in cursor:
                indexName = "common_bucketdetail_" + str(uuid.uuid4())[:8]
                queries.append((indexName, rec[0]))

            for q in queries:
                cursor.execute(
                    "create index %s on common_bucketdetail (startdate, enddate, name) where bucket_id  = %%s"
                    % q[0],
                    (q[1],),
                )
                cursor.execute("comment on index %s is %%s" % q[0], (q[1],))


@PlanTaskRegistry.register
class checkDatabaseHealth(CheckTask):
    description = "Sanity check on the database"
    sequence = 76

    @classmethod
    def getWeight(cls, **kwargs):
        return -1 if kwargs.get("skipLoad", False) or "loadplan" in os.environ else 1

    @classmethod
    def run(cls, database=DEFAULT_DB_ALIAS, **kwargs):
        with connections[database].cursor() as cursor:

            # check 1: make sure the max(id) is less than the sequence value
            cursor.execute(
                """
                select
                    s.relname as sequencename,
                    t.relname as tablename,
                    a.attname as columnname,
                    pg_sequences.last_value
                from pg_class s
                inner join pg_depend d on d.objid=s.oid and d.classid='pg_class'::regclass and d.refclassid='pg_class'::regclass
                inner join pg_class t on t.oid=d.refobjid
                inner join pg_namespace n on n.oid=t.relnamespace
                inner join pg_attribute a on a.attrelid=t.oid and a.attnum=d.refobjsubid
                inner join pg_sequences on pg_sequences.sequencename = s.relname
                where s.relkind='S'
                  and n.nspname = 'public'
                  and has_table_privilege(current_user, format('%I.%I', n.nspname, t.relname), 'select')
                  and has_sequence_privilege(current_user, format('%I.%I', n.nspname, s.relname), 'update')
                """
            )
            sequences = [i for i in cursor]
            for sequencename, tablename, columnname, last_value in sequences:
                cursor.execute(f"select max({columnname}) from {tablename}")
                max_id = cursor.fetchone()[0]
                if max_id and max_id > (last_value or 0):
                    cursor.execute(
                        f"""
                        SELECT setval('{sequencename}', (SELECT max({columnname}) FROM {tablename}));
                        """
                    )
                    logger.info(
                        f"updated sequence {sequencename} for table {tablename}: nexval too low"
                    )

            # check 2: make sure the sequence has not reached 90% of the max value

            # identify all the foreign keys
            cursor.execute(
                """
                select rel_kcu.table_name as primary_table,
                rel_kcu.column_name as primary_column
                from information_schema.table_constraints tco
                join information_schema.key_column_usage kcu
                    on tco.constraint_schema = kcu.constraint_schema
                    and tco.constraint_name = kcu.constraint_name
                join information_schema.referential_constraints rco
                    on tco.constraint_schema = rco.constraint_schema
                    and tco.constraint_name = rco.constraint_name
                join information_schema.key_column_usage rel_kcu
                    on rco.unique_constraint_schema = rel_kcu.constraint_schema
                    and rco.unique_constraint_name = rel_kcu.constraint_name
                    and kcu.ordinal_position = rel_kcu.ordinal_position
                where tco.constraint_type = 'FOREIGN KEY'
                """
            )
            foreign_key_exists = [i for i in cursor]

            cursor.execute(
                """
                with cte as (
                select sequencename from pg_sequences
                where schemaname='public'
                and last_value > 0.9 * max_value)
                select s.relname as sequencename,
                t.relname as tablename,
                a.attname as columnname
                from pg_class s
                inner join pg_depend d on d.objid=s.oid and d.classid='pg_class'::regclass and d.refclassid='pg_class'::regclass
                inner join pg_class t on t.oid=d.refobjid
                inner join pg_namespace n on n.oid=t.relnamespace
                inner join pg_attribute a on a.attrelid=t.oid and a.attnum=d.refobjsubid
                inner join cte on cte.sequencename = s.relname
                where s.relkind='S'
                  and n.nspname = 'public'
                  and has_table_privilege(current_user, format('%I.%I', n.nspname, t.relname), 'select')
                  and has_sequence_privilege(current_user, format('%I.%I', n.nspname, sequencename), 'update')
                """
            )
            sequences = [i for i in cursor]
            for sequencename, tablename, columnname in sequences:

                # we can't update the ids if this is a foreign key
                if (tablename, columnname) in foreign_key_exists:
                    logger.warning(
                        f"sequence {sequencename} is almost at its maximum but can't be updated as it's a foreign key"
                    )
                    continue

                cursor.execute(
                    f"""
                    WITH numbered_rows AS (
                    SELECT {columnname}, ROW_NUMBER() OVER (ORDER BY {columnname}) AS new_id
                    FROM {tablename}
                    )
                    UPDATE {tablename}
                    SET {columnname} = numbered_rows.new_id
                    FROM numbered_rows
                    WHERE {tablename}.{columnname} = numbered_rows.{columnname};
                    SELECT setval('{sequencename}', (SELECT max({columnname}) FROM {tablename}));
                    """
                )
                logger.info(
                    f"updated sequence {sequencename} for table {tablename}: reaching max value"
                )

            # check 3: Make sure table common_comment remains below 5M records
            cursor.execute("select count(*) from common_comment")
            to_delete = cursor.fetchone()[0] - 5000000
            if to_delete > 0:
                cursor.execute(
                    """
                    with recs_to_delete as (
                        select id from (
                            select
                              id,
                              row_number() over (order by lastmodified ASC) AS row_num
                            from common_comment
                            where content_type_id  in (
                                -- delete only from the entities with most comments
                                select top5.content_type_id
                                from common_comment top5
                                group by top5.content_type_id
                                order by count(*) desc
                                limit 5
                            )
                            and common_comment.type != 'comment'
                        ) subquery
                        where row_num <= %s
                    )
                    delete from common_comment
                    using recs_to_delete
                    where common_comment.id = recs_to_delete.id
                    """,
                    (to_delete,),
                )
                logger.info(f"Deleted {cursor.rowcount} old comments")


@PlanTaskRegistry.register
class checkBrokenSupplyPath(CheckTask):
    # check for item location combinations in the demand
    # check for item location that are consumed in operation materials
    # check for item location at origin of item distribution
    # and make sure they can be either manufactured, transported and purchased
    description = "Check broken supply paths"
    sequence = 78

    @classmethod
    def getWeight(cls, **kwargs):
        return -1 if kwargs.get("skipLoad", False) or "loadplan" in os.environ else 1

    @classmethod
    def run(cls, database=DEFAULT_DB_ALIAS, **kwargs):
        Item.rebuildHierarchy(database)
        Location.rebuildHierarchy(database)
        with_fcst_module = "freppledb.forecast" in settings.INSTALLED_APPS
        currentdate = getCurrentDate(database=database)
        param = (
            Parameter.getValue(
                "plan.fixBrokenSupplyPath", database=database, default="true"
            )
            .strip()
            .lower()
            == "true"
        )

        try:
            with transaction.atomic(using=database, savepoint=False):
                with connections[database].cursor() as cursor:
                    if not param:
                        logger.info("skipping search of broken supply")
                        cursor.execute(
                            """
                            delete from itemsupplier where supplier_id = 'Unknown supplier';
                            delete from operationplan where supplier_id = 'Unknown supplier';
                            delete from supplier where name = 'Unknown supplier';
                            """
                        )
                        return

                    # Setting a max run time to protect against bad data
                    cursor.execute("set local statement_timeout = '300s'")

                    # cleaning previous records
                    cursor.execute(
                        """
                        delete from itemsupplier where supplier_id = 'Unknown supplier';
                        insert into supplier (name, description)
                        values
                        ('Unknown supplier', 'automatically created to resolve broken supply paths')
                        on conflict (name)
                        do nothing;
                        """
                    )

                    # inserting combinations with no replenishment
                    cursor.execute(
                        """
                        with cte as (
                        select 'Unknown supplier' as supplier_id, item_id, location_id from demand where status in ('open','quote')
                        union
                        select 'Unknown supplier', operationmaterial.item_id,
                        coalesce(operationmaterial.location_id, operation.location_id) from operationmaterial
                        inner join operation on operation.name = operationmaterial.operation_id
                        where operationmaterial.quantity < 0
                        %s
                        )
                        insert into itemsupplier (supplier_id, item_id, location_id)
                        (
                        select * from cte
                        union
                        select 'Unknown supplier', item.name, itemdistribution.origin_id from itemdistribution
                        inner join item parentitem on itemdistribution.item_id = parentitem.name
                        inner join item on item.lft between parentitem.lft and parentitem.rght
                            and item.lft = item.rght-1
                        inner join cte on cte.item_id = itemdistribution.item_id
                            and cte.location_id = itemdistribution.location_id
                        where coalesce(itemdistribution.effective_end, %%s) >= %%s
                        and itemdistribution.priority is distinct from 0
                        )
                        except
                        (select 'Unknown supplier', item.name, itemdistribution.location_id from itemdistribution
                        inner join item parentitem on itemdistribution.item_id = parentitem.name
                        inner join item on item.lft between parentitem.lft and parentitem.rght
                        where coalesce(itemdistribution.effective_end, %%s) >= %%s
                        and itemdistribution.priority is distinct from 0
                        union
                        select 'Unknown supplier', item.name, location_id from itemsupplier
                        inner join item parentitem on itemsupplier.item_id = parentitem.name
                        inner join item on item.lft between parentitem.lft and parentitem.rght
                        inner join location on itemsupplier.location_id = location.name
                        where coalesce(itemsupplier.effective_end, %%s) >= %%s
                        and itemsupplier.priority is distinct from 0
                        union
                        select 'Unknown supplier', item.name, location.name from itemsupplier
                        inner join item parentitem on itemsupplier.item_id = parentitem.name
                        inner join item on item.lft between parentitem.lft and parentitem.rght
                        cross join location
                        where itemsupplier.location_id is null and coalesce(itemsupplier.effective_end, %%s) >= %%s
                        and itemsupplier.priority is distinct from 0
                        union
                        select 'Unknown supplier', operationmaterial.item_id,
                        coalesce(operationmaterial.location_id, operation.location_id) from operationmaterial
                        inner join operation on operation.name = operationmaterial.operation_id
                        where operationmaterial.quantity > 0 and coalesce(operation.effective_end, %%s) >= %%s
                        and operation.priority is distinct from 0
                        union
                        select 'Unknown supplier', item_id, location_id from operation
                        where coalesce(operation.effective_end, %%s) >= %%s
                        and operation.priority is distinct from 0
                        )
                        """
                        % (
                            (
                                """
                            union
                            select 'Unknown supplier', item_id, location_id from forecast where planned
                            """
                                if with_fcst_module
                                else ""
                            ),
                        ),
                        ((currentdate,) * 12),
                    )

                    if cursor.rowcount == 0:
                        # removing unknown supplier if no invalid record has been found
                        cursor.execute(
                            """
                            update operationplan set supplier_id = null where supplier_id = 'Unknown supplier';
                            delete from supplier where name = 'Unknown supplier';
                            """
                        )
                        logger.info("No broken supply path detected")
                    else:
                        logger.info(
                            "Created %d item suppliers records" % (cursor.rowcount,)
                        )
        except OperationalError:
            logger.error("Aborted creation of item supplier records after 5 minutes.")


@PlanTaskRegistry.register
class loadParameter(LoadTask):
    description = "Importing parameters"
    sequence = 90

    @classmethod
    def run(cls, database=DEFAULT_DB_ALIAS, **kwargs):
        import frepple

        if settings.TIME_ZONE:
            frepple.settings.timezone = settings.TIME_ZONE
        with transaction.atomic(using=database):
            with connections[database].chunked_cursor() as cursor:
                cursor.execute(
                    """
                    SELECT name, trim(value)
                    FROM common_parameter
                    where name in (
                       'currentdate', 'last_currentdate',
                       'COMPLETED.allow_future', 'WIP.produce_full_quantity',
                       'plan.individualPoolResources', 'plan.minimalBeforeCurrentConstraints',
                       'plan.autoFenceOperations', 'plan.deliveryDuration'
                       )
                    """
                )
                current_date = None
                last_current_date = None
                for rec in cursor:
                    if rec[0] == "currentdate":
                        current_date = rec[1]
                    elif rec[0] == "last_currentdate":
                        last_current_date = rec[1]
                    elif rec[0] == "COMPLETED.allow_future":
                        frepple.settings.completed_allow_future = (
                            str(rec[1]).lower() == "true"
                        )
                    elif rec[0] == "WIP.produce_full_quantity":
                        frepple.settings.wip_produce_full_quantity = (
                            str(rec[1]).lower() == "true"
                        )
                    elif rec[0] == "plan.individualPoolResources":
                        frepple.settings.individualPoolResources = (
                            str(rec[1]).lower() == "true"
                        )
                    elif rec[0] == "plan.minimalBeforeCurrentConstraints":
                        frepple.settings.minimalBeforeCurrentConstraints = (
                            str(rec[1]).lower() == "true"
                        )
                    elif rec[0] == "plan.autoFenceOperations":
                        frepple.settings.autofence = float(rec[1]) * 86400
                    elif rec[0] == "plan.deliveryDuration":
                        frepple.settings.deliveryduration = float(rec[1]) * 3600
                current_set = False
                if "loadplan" in os.environ and last_current_date:
                    try:
                        frepple.settings.current = parse(last_current_date)
                        current_set = True
                    except Exception:
                        if last_current_date and last_current_date.lower() == "today":
                            n = datetime.now()
                            frepple.settings.current = datetime(n.year, n.month, n.day)
                            current_set = True
                if not current_set and current_date:
                    try:
                        frepple.settings.current = parse(current_date)
                        current_set = True
                    except Exception:
                        if current_date and current_date.lower() == "today":
                            n = datetime.now()
                            frepple.settings.current = datetime(n.year, n.month, n.day)
                            current_set = True
                if not current_set:
                    frepple.settings.current = datetime.now().replace(microsecond=0)
                logger.info("Current date: %s" % frepple.settings.current)


@PlanTaskRegistry.register
class loadLocations(LoadTask):
    description = "Importing locations"
    sequence = 91

    @classmethod
    def getWeight(cls, **kwargs):
        return -1 if kwargs.get("skipLoad", False) else 1

    @classmethod
    def run(cls, database=DEFAULT_DB_ALIAS, **kwargs):
        import frepple

        if cls.filter:
            filter_where = "where %s " % cls.filter
        else:
            filter_where = ""

        with transaction.atomic(using=database):
            with connections[database].chunked_cursor() as cursor:
                cnt = 0
                starttime = time()

                attrs = [
                    f[0]
                    for f in getAttributes(Location)
                    if not f[2].startswith("foreignkey:")
                ]
                if attrs:
                    attrsql = ", %s" % ", ".join(attrs)
                else:
                    attrsql = ""

                cursor.execute(
                    """
                    SELECT
                    name, description, owner_id, available_id, category, subcategory, source %s
                    FROM location %s
                    """
                    % (attrsql, filter_where)
                )

                for i in cursor:
                    cnt += 1
                    try:
                        x = frepple.location(
                            name=i[0],
                            description=i[1],
                            category=i[4],
                            subcategory=i[5],
                            source=i[6],
                        )
                        if i[2]:
                            x.owner = frepple.location(name=i[2])
                        if i[3]:
                            x.available = frepple.calendar(name=i[3])
                        idx = 7
                        for a in attrs:
                            setattr(x, a, i[idx])
                            idx += 1
                    except Exception as e:
                        logger.error("**** %s ****" % e)
                logger.info(
                    "Loaded %d locations in %.2f seconds" % (cnt, time() - starttime)
                )


@PlanTaskRegistry.register
class loadCalendars(LoadTask):
    description = "Importing calendars"
    sequence = 92

    @classmethod
    def getWeight(cls, **kwargs):
        return 1

    @classmethod
    def run(cls, database=DEFAULT_DB_ALIAS, **kwargs):
        import frepple

        if cls.filter:
            filter_where = "where %s " % cls.filter
        else:
            filter_where = ""

        with transaction.atomic(using=database):
            with connections[database].chunked_cursor() as cursor:
                cnt = 0
                starttime = time()
                if kwargs.get("skipLoad", False):
                    cursor.execute(
                        """
                        select
                        name, 0, 'common_bucket', 1 hidden
                        FROM common_bucket
                        order by name asc
                        """
                    )
                else:
                    cursor.execute(
                        """
                        select
                        name, defaultvalue, source, 0 hidden
                        FROM calendar %s
                        union
                        SELECT
                        name, 0, 'common_bucket', 1 hidden
                        FROM common_bucket
                        order by name asc
                        """
                        % filter_where
                    )
                for i in cursor:
                    cnt += 1
                    try:
                        frepple.calendar(
                            name=i[0], default=i[1], source=i[2], hidden=i[3]
                        )
                    except Exception as e:
                        logger.error("**** %s ****" % e)
                logger.info(
                    "Loaded %d calendars in %.2f seconds" % (cnt, time() - starttime)
                )


@PlanTaskRegistry.register
class loadCalendarBuckets(LoadTask):
    description = "Importing calendar buckets"
    sequence = 93

    @classmethod
    def getWeight(cls, **kwargs):
        return 1

    @classmethod
    def run(cls, database=DEFAULT_DB_ALIAS, **kwargs):
        import frepple

        if cls.filter:
            filter_where = "and %s " % cls.filter
        else:
            filter_where = ""

        with transaction.atomic(using=database):
            with connections[database].chunked_cursor() as cursor:
                cnt = 0
                starttime = time()
                if kwargs.get("skipLoad", False):
                    cursor.execute(
                        """
                        SELECT
                        bucket_id calendar_id, startdate, enddate, 10 priority , 0 as value,
                        't' sunday,'t' monday,'t' tuesday,'t' wednesday,'t' thurday,'t' friday,'t' saturday,
                        time '00:00:00' starttime, time '23:59:59' endtime, 'common_bucketdetail' source, lower(name)
                        FROM common_bucketdetail
                        ORDER BY calendar_id, startdate desc
                        """
                    )
                else:
                    cursor.execute(
                        """
                        SELECT
                        calendar_id, startdate, enddate, priority, value,
                        sunday, monday, tuesday, wednesday, thursday, friday, saturday,
                        starttime, endtime, source, null
                        FROM calendarbucket
                        WHERE (startdate < enddate or startdate is null or enddate is null) %s
                        UNION
                        SELECT
                        bucket_id calendar_id, startdate, enddate, 10 priority , 0 as value,
                        't' sunday,'t' monday,'t' tuesday,'t' wednesday,'t' thurday,'t' friday,'t' saturday,
                        time '00:00:00' starttime, time '23:59:59' endtime, 'common_bucketdetail' source, lower(name)
                        FROM common_bucketdetail
                        ORDER BY calendar_id, startdate desc
                        """
                        % filter_where
                    )
                prevcal = None
                for i in cursor:
                    cnt += 1
                    try:
                        days = 0
                        if i[5]:
                            days += 1
                        if i[6]:
                            days += 2
                        if i[7]:
                            days += 4
                        if i[8]:
                            days += 8
                        if i[9]:
                            days += 16
                        if i[10]:
                            days += 32
                        if i[11]:
                            days += 64
                        if i[0] != prevcal:
                            cal = frepple.calendar(name=i[0])
                            prevcal = i[0]
                        b = frepple.bucket(
                            calendar=cal,
                            start=i[1],
                            end=i[2] if i[2] else datetime(2030, 12, 31),
                            priority=i[3],
                            source=i[14],
                            value=i[4],
                            days=days,
                        )
                        if i[12]:
                            b.starttime = (
                                i[12].hour * 3600 + i[12].minute * 60 + i[12].second
                            )
                        if i[13]:
                            b.endtime = (
                                i[13].hour * 3600 + i[13].minute * 60 + i[13].second + 1
                            )
                        if i[15]:
                            b.name = i[15]
                    except Exception as e:
                        logger.error("**** %s ****" % e)
                logger.info(
                    "Loaded %d calendar buckets in %.2f seconds"
                    % (cnt, time() - starttime)
                )


@PlanTaskRegistry.register
class loadCustomers(LoadTask):
    description = "Importing customers"
    sequence = 94

    @classmethod
    def getWeight(cls, **kwargs):
        return -1 if kwargs.get("skipLoad", False) else 1

    @classmethod
    def run(cls, database=DEFAULT_DB_ALIAS, **kwargs):
        import frepple

        if cls.filter:
            filter_where = "where %s " % cls.filter
        else:
            filter_where = ""

        with transaction.atomic(using=database):
            with connections[database].chunked_cursor() as cursor:
                cnt = 0
                starttime = time()
                cursor.execute(
                    """
                SELECT
                  name, description, owner_id, category, subcategory, source
                FROM customer %s
                """
                    % filter_where
                )
                for i in cursor:
                    cnt += 1
                    try:
                        x = frepple.customer(
                            name=i[0],
                            description=i[1],
                            category=i[3],
                            subcategory=i[4],
                            source=i[5],
                        )
                        if i[2]:
                            x.owner = frepple.customer(name=i[2])
                    except Exception as e:
                        logger.error("**** %s ****" % e)
                logger.info(
                    "Loaded %d customers in %.2f seconds" % (cnt, time() - starttime)
                )


@PlanTaskRegistry.register
class loadSuppliers(LoadTask):
    description = "Importing suppliers"
    sequence = 95

    @classmethod
    def getWeight(cls, **kwargs):
        return -1 if kwargs.get("skipLoad", False) else 1

    @classmethod
    def run(cls, database=DEFAULT_DB_ALIAS, **kwargs):
        import frepple

        if cls.filter:
            filter_where = "where %s " % cls.filter
        else:
            filter_where = ""

        with transaction.atomic(using=database):
            with connections[database].chunked_cursor() as cursor:
                cnt = 0
                starttime = time()
                cursor.execute(
                    """
                SELECT
                  name, description, owner_id, category, subcategory, source, available_id
                FROM supplier %s
                """
                    % filter_where
                )
                for i in cursor:
                    cnt += 1
                    try:
                        x = frepple.supplier(
                            name=i[0],
                            description=i[1],
                            category=i[3],
                            subcategory=i[4],
                            source=i[5],
                        )
                        if i[2]:
                            x.owner = frepple.supplier(name=i[2])
                        if i[6]:
                            frepple.location(name=i[0]).available = frepple.calendar(
                                name=i[6]
                            )
                    except Exception as e:
                        logger.error("**** %s ****" % e)
                logger.info(
                    "Loaded %d suppliers in %.2f seconds" % (cnt, time() - starttime)
                )


@PlanTaskRegistry.register
class loadOperations(LoadTask):
    description = "Importing operations"
    sequence = 96

    @classmethod
    def getWeight(cls, **kwargs):
        return -1 if kwargs.get("skipLoad", False) else 1

    @classmethod
    def run(cls, database=DEFAULT_DB_ALIAS, **kwargs):
        import frepple

        if cls.filter:
            filter_where = "where %s " % cls.filter
        else:
            filter_where = ""

        attrs = [
            f[0] for f in getAttributes(Operation) if not f[2].startswith("foreignkey:")
        ]
        if attrs:
            attrsql = ", %s" % ", ".join(attrs)
        else:
            attrsql = ""

        with connections[database].cursor() as cursor:
            cnt = 0
            starttime = time()

            # Preprocessing step
            # Make sure any routing has the produced item of its last step populated in the operation table
            # Old style
            cursor.execute(
                """
                update operation
                set item_id = t.item_id
                from (
                      select operation.name operation_id, min(operationmaterial.item_id) item_id
                       from operation
                       inner join suboperation s1 on s1.operation_id = operation.name
                       inner join operationmaterial
                         on operationmaterial.operation_id = s1.suboperation_id and quantity > 0
                       where operation.type = 'routing'
                       and not exists
                          (select 1 from suboperation s2 where s1.operation_id = s2.operation_id and s1.priority < s2.priority)
                       group by operation.name
                       having count(operationmaterial.item_id) = 1
                     ) t
                where operation.type = 'routing'
                  and operation.name = t.operation_id
                """
            )
            # New style
            cursor.execute(
                """
                update operation
                set item_id = t.item_id
                from (
                      select operation.name operation_id, min(operationmaterial.item_id) item_id
                       from operation
                       inner join operation s1 on s1.owner_id = operation.name
                       inner join operationmaterial
                         on operationmaterial.operation_id = s1.name and quantity > 0
                       where operation.type = 'routing'
                       and not exists
                          (select 1 from operation s2 where s1.owner_id = s2.owner_id and s1.priority < s2.priority)
                       group by operation.name
                       having count(operationmaterial.item_id) = 1
                     ) t
                where operation.type = 'routing'
                  and operation.name = t.operation_id
                """
            )

            # Preprocessing step
            # Make sure any regular operation (i.e. that has no suboperation and is not a suboperation)
            # has its item_id field populated
            # That should cover 90% of the cases
            # Old style
            cursor.execute(
                """
                update operation
                set item_id = t.item_id
                from (
                      select operation.name operation_id, min(operationmaterial.item_id) item_id
                      from operation
                      inner join operationmaterial
                        on operationmaterial.operation_id = operation.name and quantity > 0
                      where not exists
                            (select 1 from suboperation
                            where suboperation.operation_id = operation.name
                                  or suboperation.suboperation_id = operation.name)
                        and not exists
                            (select 1 from operation subop
                            where subop.owner_id = operation.name)
                        and operation.type not in ('routing', 'alternate', 'split')
                        and operation.owner_id is null
                      group by operation.name
                      having count(operationmaterial.item_id) = 1
                     ) t
                where operation.type not in ('routing', 'alternate', 'split')
                  and t.operation_id = operation.name
                """
            )

            # Preprocessing step
            # Operations that are suboperation of a parent operation shouldn't have
            # the item field set. It is the parent operation that should have it set.
            cursor.execute(
                """
                update operation
                set item_id = null
                from suboperation
                where operation.name = suboperation.suboperation_id
                and operation.item_id is not null
                """
            )
            cursor.execute(
                """
                update operation
                set item_id = null
                where owner_id is not null
                and operation.item_id is not null
                """
            )

        with transaction.atomic(using=database):
            with connections[database].chunked_cursor() as cursor:
                cursor.execute(
                    """
                    SELECT
                    name, fence, posttime, sizeminimum, sizemultiple, sizemaximum,
                    type, duration, duration_per, location_id, cost, search, description,
                    category, subcategory, source, item_id, priority, effective_start,
                    effective_end, available_id,
                    (select type from item where item.name = operation.item_id)
                    %s
                    FROM operation %s
                    """
                    % (attrsql, filter_where)
                )
                for i in cursor:
                    cnt += 1
                    try:
                        if not i[6] or i[6] == "fixed_time":
                            x = frepple.operation_fixed_time(
                                name=i[0],
                                description=i[12],
                                category=i[13],
                                subcategory=i[14],
                                source=i[15],
                            )
                            if i[7]:
                                # Convert to second to support microseconds
                                x.duration = i[7].total_seconds()
                        elif i[6] == "time_per":
                            x = frepple.operation_time_per(
                                name=i[0],
                                description=i[12],
                                category=i[13],
                                subcategory=i[14],
                                source=i[15],
                            )
                            if i[7]:
                                # Convert to second to support microseconds
                                x.duration = i[7].total_seconds()
                            if i[8]:
                                # Convert to second to support microseconds
                                x.duration_per = i[8].total_seconds()
                        elif i[6] == "alternate":
                            x = frepple.operation_alternate(
                                name=i[0],
                                description=i[12],
                                category=i[13],
                                subcategory=i[14],
                                source=i[15],
                            )
                        elif i[6] == "split":
                            x = frepple.operation_split(
                                name=i[0],
                                description=i[12],
                                category=i[13],
                                subcategory=i[14],
                                source=i[15],
                            )
                        elif i[6] == "routing":
                            x = frepple.operation_routing(
                                name=i[0],
                                description=i[12],
                                category=i[13],
                                subcategory=i[14],
                                source=i[15],
                                # Uncomment the next line if you want to treat post-operation times
                                # between routing steps as a hard constraint.
                                # By default they are a soft constraint only, meaning that we can
                                # compress them to deliver sales orders faster.
                                # hard_posttime=True,
                            )
                        else:
                            raise ValueError(
                                "Operation type '%s' not recognized" % i[6]
                            )
                        if i[1]:
                            x.fence = i[1]
                        if i[2]:
                            x.posttime = i[2]
                        if i[3] is not None:
                            x.size_minimum = i[3]
                        if i[4]:
                            x.size_multiple = i[4]
                        if i[5]:
                            x.size_maximum = i[5]
                        if i[9]:
                            x.location = frepple.location(name=i[9])
                        if i[10]:
                            x.cost = i[10]
                        if i[11]:
                            x.search = i[11]
                        if i[16]:
                            if i[21] == "make to order":
                                x.item = frepple.item_mto(name=i[16])
                            else:
                                x.item = frepple.item_mts(name=i[16])
                        if i[17] is not None:
                            x.priority = i[17]
                        if i[18] and i[18] > datetime(1971, 1, 3):
                            x.effective_start = i[18]
                        if i[19] and i[19] < datetime(2030, 12, 29):
                            x.effective_end = i[19]
                        if i[20]:
                            x.available = frepple.calendar(name=i[20])
                        if i[13] == "subcontractor":
                            x.nolocationcalendar = True
                        idx = 22
                        for a in attrs:
                            setattr(x, a, i[idx])
                            idx += 1
                    except Exception as e:
                        logger.error("**** %s ****" % e)
                logger.info(
                    "Loaded %d operations in %.2f seconds" % (cnt, time() - starttime)
                )


@PlanTaskRegistry.register
class loadSuboperations(LoadTask):
    description = "Importing suboperations"
    sequence = 97

    @classmethod
    def getWeight(cls, **kwargs):
        return -1 if kwargs.get("skipLoad", False) else 1

    @classmethod
    def run(cls, database=DEFAULT_DB_ALIAS, **kwargs):
        import frepple

        if cls.filter:
            filter_and = "and %s " % cls.filter
        else:
            filter_and = ""

        with transaction.atomic(using=database):
            with connections[database].chunked_cursor() as cursor:
                cnt = 0
                starttime = time()
                cursor.execute(
                    """
                select
                  operation_id, suboperation_id, priority, effective_start, effective_end
                from (
                    SELECT operation_id, suboperation_id, priority, effective_start, effective_end,
                      (SELECT type
                       from operation
                       where suboperation.operation_id = operation.name) as type
                    FROM suboperation
                    WHERE priority >= 0 %s
                    union
                    select owner_id, name, priority, effective_start, effective_end,
                      (SELECT type
                       from operation as parent
                       where operation.owner_id = parent.name) as type
                    from operation
                    where owner_id is not null and priority >= 0 %s
                    ) suboperations
                order by operation_id, priority, suboperation_id
                """
                    % (filter_and, filter_and)
                )
                curopername = None
                for i in cursor:
                    cnt += 1
                    try:
                        if i[0] != curopername:
                            curopername = i[0]
                            curoper = frepple.operation(name=curopername)
                        sub = frepple.suboperation(
                            owner=curoper,
                            operation=frepple.operation(name=i[1]),
                            priority=i[2],
                        )
                        if i[3] and i[3] > datetime(1971, 1, 3):
                            sub.effective_start = i[3]
                        if i[4] and i[4] < datetime(2030, 12, 29):
                            sub.effective_end = i[4]
                    except Exception as e:
                        logger.error("**** %s ****" % e)
                logger.info(
                    "Loaded %d suboperations in %.2f seconds"
                    % (cnt, time() - starttime)
                )


@PlanTaskRegistry.register
class loadOperationDependencies(LoadTask):
    description = "Importing operation dependencies"
    sequence = 97.5

    @classmethod
    def getWeight(cls, **kwargs):
        return -1 if kwargs.get("skipLoad", False) else 1

    @classmethod
    def run(cls, database=DEFAULT_DB_ALIAS, **kwargs):
        import frepple

        if cls.filter:
            filter_where = "where %s " % cls.filter
        else:
            filter_where = ""

        with transaction.atomic(using=database):
            with connections[database].chunked_cursor() as cursor:
                cnt = 0
                starttime = time()
                cursor.execute(
                    """
                    select
                      operation_id, blockedby_id, quantity, safety_leadtime, hard_safety_leadtime
                    from operation_dependency
                    %s
                    order by operation_id, blockedby_id
                    """
                    % filter_where
                )
                for i in cursor:
                    cnt += 1
                    try:
                        op1 = frepple.operation(name=i[0], action="C")
                        op2 = frepple.operation(name=i[1], action="C")
                        if op1 and op2:
                            frepple.operationdependency(
                                operation=op1,
                                blockedby=op2,
                                quantity=i[2] if i[2] is not None else 1,
                                safety_leadtime=i[3] or 0,
                                hard_safety_leadtime=i[4] or 0,
                            )
                    except Exception as e:
                        logger.error("**** %s ****" % e)
                logger.info(
                    "Loaded %d operation dependencies in %.2f seconds"
                    % (cnt, time() - starttime)
                )


@PlanTaskRegistry.register
class loadItems(LoadTask):
    description = "Importing items"
    sequence = 98

    @classmethod
    def getWeight(cls, **kwargs):
        return -1 if kwargs.get("skipLoad", False) else 1

    @classmethod
    def run(cls, database=DEFAULT_DB_ALIAS, **kwargs):
        import frepple

        if cls.filter:
            filter_where = "where %s " % cls.filter
        else:
            filter_where = ""

        with transaction.atomic(using=database):
            with connections[database].chunked_cursor() as cursor:
                cnt = 0
                starttime = time()
                attrs = [
                    f[0]
                    for f in getAttributes(Item)
                    if not f[2].startswith("foreignkey:")
                ]
                if attrs:
                    attrsql = ", %s" % ", ".join(attrs)
                else:
                    attrsql = ""
                cursor.execute(
                    """
                select
                  name, description, owner_id,
                  cost, category, subcategory, source, type,
                  (select type from item p_item where item.owner_id = p_item.name) %s
                from item %s
                """
                    % (attrsql, filter_where)
                )
                for i in cursor:
                    cnt += 1
                    try:
                        if i[7] == "make to order":
                            x = frepple.item_mto(
                                name=i[0],
                                description=i[1],
                                category=i[4],
                                subcategory=i[5],
                                source=i[6],
                            )
                        else:
                            x = frepple.item_mts(
                                name=i[0],
                                description=i[1],
                                category=i[4],
                                subcategory=i[5],
                                source=i[6],
                            )
                        if i[2]:
                            if i[8] == "make to order":
                                x.owner = frepple.item_mto(name=i[2])
                            else:
                                x.owner = frepple.item_mts(name=i[2])
                        if i[3]:
                            x.cost = i[3]
                        idx = 9
                        for a in attrs:
                            setattr(x, a, i[idx])
                            idx += 1
                    except Exception as e:
                        logger.error("**** %s ****" % e)
                logger.info(
                    "Loaded %d items in %.2f seconds" % (cnt, time() - starttime)
                )


@PlanTaskRegistry.register
class loadItemSuppliers(LoadTask):
    description = "Importing item suppliers"
    sequence = 99

    @classmethod
    def getWeight(cls, **kwargs):
        return -1 if kwargs.get("skipLoad", False) else 1

    @classmethod
    def run(cls, database=DEFAULT_DB_ALIAS, **kwargs):
        import frepple

        if cls.filter:
            filter_where = "where %s " % cls.filter
        else:
            filter_where = ""

        with transaction.atomic(using=database):
            with connections[database].chunked_cursor() as cursor:
                cnt = 0
                starttime = time()
                cursor.execute(
                    """
                    SELECT
                    supplier_id, item_id, location_id, sizeminimum, sizemultiple, sizemaximum,
                    cost, priority, effective_start, effective_end, source, leadtime,
                    resource_id, resource_qty, fence, batchwindow, extra_safety_leadtime,
                    hard_safety_leadtime
                    FROM itemsupplier %s
                    ORDER BY supplier_id, item_id, location_id, priority desc
                    """
                    % filter_where
                )
                cursuppliername = None
                curitemname = None
                for i in cursor:
                    cnt += 1
                    try:
                        if i[0] != cursuppliername:
                            cursuppliername = i[0]
                            cursupplier = frepple.supplier(name=cursuppliername)
                        if i[1] != curitemname:
                            curitemname = i[1]
                            curitem = frepple.item(name=curitemname)
                        curitemsupplier = frepple.itemsupplier(
                            supplier=cursupplier,
                            item=curitem,
                            source=i[9],
                            leadtime=i[11] if i[11] else 0,
                            fence=i[14] if i[14] else 0,
                            resource_qty=i[13],
                            batchwindow=i[15] if i[15] is not None else 7 * 86400,
                            extra_safety_leadtime=i[16] if i[16] else 0,
                            hard_safety_leadtime=i[17] if i[17] else 0,
                        )
                        if i[2]:
                            curitemsupplier.location = frepple.location(name=i[2])
                        if i[3] is not None:
                            curitemsupplier.size_minimum = i[3]
                        if i[4] is not None:
                            curitemsupplier.size_multiple = i[4]
                        if i[5]:
                            curitemsupplier.size_maximum = i[5]
                        if i[6]:
                            curitemsupplier.cost = i[6]
                        if i[7] is not None:
                            curitemsupplier.priority = i[7]
                        if i[8] and i[8] > datetime(1971, 1, 3):
                            curitemsupplier.effective_start = i[8]
                        if i[9] and i[9] < datetime(2030, 12, 29):
                            curitemsupplier.effective_end = i[9]
                        if i[12]:
                            curitemsupplier.resource = frepple.resource(name=i[12])
                    except Exception as e:
                        logger.error("**** %s ****" % e)
                logger.info(
                    "Loaded %d item suppliers in %.2f seconds"
                    % (cnt, time() - starttime)
                )


@PlanTaskRegistry.register
class loadItemDistributions(LoadTask):
    description = "Importing item distributions"
    sequence = 100

    @classmethod
    def getWeight(cls, **kwargs):
        return -1 if kwargs.get("skipLoad", False) else 1

    @classmethod
    def run(cls, database=DEFAULT_DB_ALIAS, **kwargs):
        import frepple

        if cls.filter:
            filter_where = "where %s " % cls.filter
        else:
            filter_where = ""

        with transaction.atomic(using=database):
            with connections[database].chunked_cursor() as cursor:
                cnt = 0
                starttime = time()
                cursor.execute(
                    """
                SELECT
                  origin_id, item_id, location_id, sizeminimum, sizemultiple, sizemaximum,
                  cost, priority, effective_start, effective_end, source,
                  leadtime, resource_id, resource_qty, fence, batchwindow
                FROM itemdistribution %s
                ORDER BY origin_id, item_id, location_id, priority desc
                """
                    % filter_where
                )
                curoriginname = None
                curitemname = None
                for i in cursor:
                    if not i[0] or not i[2]:
                        logger.error(
                            "Origin and location must be defined, skipping one record"
                        )
                        continue
                    if i[0] == i[2]:
                        logger.error(
                            "Origin and location must be different, skipping one record"
                        )
                        continue
                    cnt += 1
                    try:
                        if i[0] != curoriginname:
                            curoriginname = i[0]
                            curorigin = frepple.location(name=curoriginname)
                        if i[1] != curitemname:
                            curitemname = i[1]
                            curitem = frepple.item(name=curitemname)
                        curitemdistribution = frepple.itemdistribution(
                            origin=curorigin,
                            item=curitem,
                            source=i[10],
                            leadtime=i[11] if i[11] else 0,
                            fence=i[14] if i[14] else 0,
                            resource_qty=i[13],
                            batchwindow=i[15] if i[15] is not None else 7 * 86400,
                        )
                        if i[2]:
                            curitemdistribution.destination = frepple.location(
                                name=i[2]
                            )
                        if i[3] is not None:
                            curitemdistribution.size_minimum = i[3]
                        if i[4] is not None:
                            curitemdistribution.size_multiple = i[4]
                        if i[5]:
                            curitemdistribution.size_maximum = i[5]
                        if i[6]:
                            curitemdistribution.cost = i[6]
                        if i[7] is not None:
                            curitemdistribution.priority = i[7]
                        if i[8] and i[8] > datetime(1971, 1, 3):
                            curitemdistribution.effective_start = i[8]
                        if i[9] and i[9] < datetime(2030, 12, 29):
                            curitemdistribution.effective_end = i[9]
                        if i[12]:
                            curitemdistribution.resource = frepple.resource(name=i[12])
                    except Exception as e:
                        logger.error("**** %s ****" % e)
                logger.info(
                    "Loaded %d item distributions in %.2f seconds"
                    % (cnt, time() - starttime)
                )


@PlanTaskRegistry.register
class loadBuffers(LoadTask):
    description = "Importing buffers"
    sequence = 101

    @classmethod
    def getWeight(cls, **kwargs):
        return -1 if kwargs.get("skipLoad", False) else 1

    @classmethod
    def run(cls, database=DEFAULT_DB_ALIAS, **kwargs):
        import frepple

        if cls.filter:
            filter_where = "where %s " % cls.filter
        else:
            filter_where = ""

        with transaction.atomic(using=database):
            with connections[database].chunked_cursor() as cursor:
                cnt = 0
                starttime = time()
                cursor.execute(
                    """
                select
                  case
                  when batch is not null
                    and batch is distinct from ''
                    and exists (select 1 from item where item.name = buffer.item_id and item.type = 'make to order')
                    then item_id || ' @ ' || batch || ' @ '||location_id
                  else
                    item_id ||' @ '||location_id
                  end as name,
                  min (description),
                  min(location_id), min(item_id),
                  sum(onhand),
                  min(minimum),
                  min(minimum_calendar_id),
                  min(type),
                  min(min_interval),
                  min(category),
                  min(subcategory),
                  min(source),
                  min(batch),
                  min(maximum),
                  min(maximum_calendar_id)
                from buffer
                %s
                group by case
                  when batch is not null
                    and batch is distinct from ''
                    and exists (select 1 from item where item.name = buffer.item_id and item.type = 'make to order')
                    then item_id || ' @ ' || batch || ' @ '||location_id
                  else
                    item_id ||' @ '||location_id
                  end
                """
                    % filter_where
                )
                for i in cursor:
                    cnt += 1
                    if i[7] == "infinite":
                        b = frepple.buffer_infinite(
                            name=i[0],
                            description=i[1],
                            location=frepple.location(name=i[2]),
                            item=frepple.item(name=i[3]),
                            batch=i[12] if i[12] else None,
                            onhand=max(i[4] or 0, 0),
                            category=i[9],
                            subcategory=i[10],
                            source=i[11],
                        )
                    elif not i[7] or i[7] == "default":
                        b = frepple.buffer(
                            name=i[0],
                            description=i[1],
                            location=frepple.location(name=i[2]),
                            item=frepple.item(name=i[3]),
                            batch=i[12] if i[12] else None,
                            onhand=max(i[4] or 0, 0),
                            category=i[9],
                            subcategory=i[10],
                            source=i[11],
                        )
                        if i[8]:
                            b.mininterval = i[8]
                    else:
                        raise ValueError("Buffer type '%s' not recognized" % i[7])
                    if i[10] == "tool":
                        b.tool = True
                    if i[5]:
                        b.minimum = i[5]
                    if i[6]:
                        b.minimum_calendar = frepple.calendar(name=i[6])
                    if i[13]:
                        b.maximum = i[13]
                    if i[14]:
                        b.maximum_calendar = frepple.calendar(name=i[14])

                logger.info(
                    "Loaded %d buffers in %.2f seconds" % (cnt, time() - starttime)
                )


@PlanTaskRegistry.register
class LinkCalendarsToBuffers(LoadTask):
    description = "Associate calendars to the buffers"
    sequence = 105.5

    @classmethod
    def getWeight(cls, **kwargs):
        return -1 if kwargs.get("skipLoad", False) else 1

    @staticmethod
    def run(database=DEFAULT_DB_ALIAS, **kwargs):
        import frepple

        def findOrCreateBuffer(name):
            try:
                # Found existing buffer
                return frepple.buffer(name=name, action="C")
            except Exception:
                try:
                    # Create new buffer
                    p = name.rsplit(" @ ", 2)
                    if len(p) == 2:
                        return frepple.buffer(
                            name=name,
                            item=frepple.item(name=p[0], action="C"),
                            location=frepple.location(name=p[1], action="C"),
                        )
                    elif len(p) == 3:
                        return frepple.buffer(
                            name=name,
                            item=frepple.item(name=p[0], action="C"),
                            location=frepple.location(name=p[1], action="C"),
                            batch=p[2],
                        )
                except Exception:
                    return None

        for cal in frepple.calendars():
            # Try linking safety stock calendar to a buffer
            if cal.name.startswith("SS for "):
                b = findOrCreateBuffer(cal.name[7:])
                if b:
                    b.minimum_calendar = cal

            # Try linking safety stock calendar with a replenishment quantity calendar
            if cal.name.startswith("ROQ for "):
                try:
                    b = findOrCreateBuffer(cal.name[8:])
                    if not b:
                        continue
                    if isinstance(
                        b.producing,
                        (
                            frepple.operation_routing,
                            frepple.operation_alternate,
                        ),
                    ):
                        for o in b.producing.suboperations:
                            o.operation.size_minimum_calendar = cal
                            if isinstance(o.operation, frepple.operation_routing):
                                for o2 in o.operation.suboperations:
                                    o2.operation.size_minimum_calendar = cal
                    elif b.producing:
                        b.producing.size_minimum_calendar = cal
                except Exception:
                    pass


@PlanTaskRegistry.register
class loadSetupMatrices(LoadTask):
    description = "Importing setup matrix rules"
    sequence = 102

    @classmethod
    def getWeight(cls, **kwargs):
        return -1 if kwargs.get("skipLoad", False) else 1

    @classmethod
    def run(cls, database=DEFAULT_DB_ALIAS, **kwargs):
        import frepple

        if cls.filter:
            filter_where = "where %s " % cls.filter
        else:
            filter_where = ""

        with transaction.atomic(using=database):
            with connections[database].chunked_cursor() as cursor:
                cnt = 0
                starttime = time()
                cursor.execute(
                    """
                SELECT name, source
                FROM setupmatrix %s
                ORDER BY name
                """
                    % filter_where
                )
                for i in cursor:
                    cnt += 1
                    try:
                        frepple.setupmatrix(name=i[0], source=i[1])
                    except Exception as e:
                        logger.error("**** %s ****" % e)
                logger.info(
                    "Loaded %d setup matrices in %.2f seconds"
                    % (cnt, time() - starttime)
                )

        with transaction.atomic(using=database):
            with connections[database].chunked_cursor() as cursor:
                cnt = 0
                starttime = time()
                cursor.execute(
                    """
                SELECT
                  setupmatrix_id, priority, fromsetup, tosetup, duration,
                  cost, source, resource_id
                FROM setuprule %s
                ORDER BY setupmatrix_id, priority DESC
                """
                    % filter_where
                )
                for i in cursor:
                    cnt += 1
                    try:
                        r = frepple.setupmatrixrule(
                            setupmatrix=frepple.setupmatrix(name=i[0]),
                            priority=i[1],
                            fromsetup=i[2],
                            tosetup=i[3],
                            duration=i[4] if i[4] else 0,
                            cost=i[5],
                            source=i[6],
                        )
                        if i[7]:
                            r.resource = frepple.resource(name=i[7])
                    except Exception as e:
                        logger.error("**** %s ****" % e)
                logger.info(
                    "Loaded %d setup matrix rules in %.2f seconds"
                    % (cnt, time() - starttime)
                )


@PlanTaskRegistry.register
class loadResources(LoadTask):
    description = "Importing resources"
    sequence = 94.5

    @classmethod
    def getWeight(cls, **kwargs):
        return -1 if kwargs.get("skipLoad", False) else 1

    @classmethod
    def run(cls, database=DEFAULT_DB_ALIAS, **kwargs):
        # NOTE: setup matrices aren't assigned here, but in the loadOperationPlans method
        import frepple

        if cls.filter:
            filter_where = "where %s " % cls.filter
        else:
            filter_where = ""

        attrs = [
            f[0] for f in getAttributes(Resource) if not f[2].startswith("foreignkey:")
        ]
        if attrs:
            attrsql = ", %s" % ", ".join(attrs)
        else:
            attrsql = ""

        with transaction.atomic(using=database):
            with connections[database].chunked_cursor() as cursor:
                cnt = 0
                starttime = time()
                Resource.rebuildHierarchy(database=database)
                cursor.execute(
                    """
                SELECT
                  name, description, maximum, maximum_calendar_id, location_id, type,
                  cost, maxearly, setup, setupmatrix_id, category, subcategory,
                  owner_id, source, available_id, efficiency, efficiency_calendar_id,
                  coalesce(constrained, true) %s
                FROM resource %s
                ORDER BY lvl ASC, name
                """
                    % (attrsql, filter_where)
                )
                for i in cursor:
                    cnt += 1
                    try:
                        if i[5] == "infinite":
                            x = frepple.resource_infinite(
                                name=i[0],
                                description=i[1],
                                category=i[10],
                                subcategory=i[11],
                                source=i[13],
                                constrained=i[17],
                            )
                            convert2cal = None
                        elif not i[5] or i[5] == "default":
                            x = frepple.resource_default(
                                name=i[0],
                                description=i[1],
                                category=i[10],
                                subcategory=i[11],
                                source=i[13],
                                constrained=i[17],
                            )
                            convert2cal = None
                        elif i[5].startswith("buckets"):
                            x = frepple.resource_buckets(
                                name=i[0],
                                description=i[1],
                                category=i[10],
                                subcategory=i[11],
                                source=i[13],
                                constrained=i[17],
                            )
                            convert2cal = i[5][8:]
                        else:
                            raise ValueError("Resource type '%s' not recognized" % i[5])
                        if i[11] == "tool":
                            x.tool = True
                        elif i[11] == "tool per piece":
                            x.toolperpiece = True
                        if i[7] is not None:
                            x.maxearly = i[7]
                        if i[2] is not None:
                            x.maximum = i[2]
                        if i[3]:
                            x.maximum_calendar = frepple.calendar(name=i[3])
                        if i[4]:
                            x.location = frepple.location(name=i[4])
                        if i[6]:
                            x.cost = i[6]
                        if i[8]:
                            x.setup = i[8]
                        if i[12]:
                            x.owner = frepple.resource(name=i[12])
                        if i[14]:
                            x.available = frepple.calendar(name=i[14])
                        if i[15] is not None:
                            x.efficiency = i[15]
                        if i[16]:
                            x.efficiency_calendar = frepple.calendar(name=i[16])
                        if convert2cal:
                            x.computeAvailability(
                                frepple.calendar(name=convert2cal, action="C"),
                                False,  # Debug flag
                            )
                        idx = 18
                        for a in attrs:
                            setattr(x, a, i[idx])
                            idx += 1
                    except Exception as e:
                        logger.error("**** %s ****" % e)
                logger.info(
                    "Loaded %d resources in %.2f seconds" % (cnt, time() - starttime)
                )


@PlanTaskRegistry.register
class loadResourceSkills(LoadTask):
    description = "Importing resources skills"
    sequence = 104

    @classmethod
    def getWeight(cls, **kwargs):
        return -1 if kwargs.get("skipLoad", False) else 1

    @classmethod
    def run(cls, database=DEFAULT_DB_ALIAS, **kwargs):
        import frepple

        if cls.filter:
            filter_where = "where %s " % cls.filter
        else:
            filter_where = ""

        with transaction.atomic(using=database):
            with connections[database].chunked_cursor() as cursor:
                cnt = 0
                starttime = time()
                cursor.execute(
                    """
                SELECT
                  resource_id, skill_id, effective_start, effective_end, priority, source
                FROM resourceskill %s
                ORDER BY skill_id, priority, resource_id
                """
                    % filter_where
                )
                for i in cursor:
                    cnt += 1
                    try:
                        cur = frepple.resourceskill(
                            resource=frepple.resource(name=i[0]),
                            skill=frepple.skill(name=i[1]),
                            priority=i[4] if i[4] is not None else 1,
                            source=i[5],
                        )
                        if i[2] and i[2] > datetime(1971, 1, 3):
                            cur.effective_start = i[2]
                        if i[3] and i[3] < datetime(2030, 12, 29):
                            cur.effective_end = i[3]
                    except Exception as e:
                        logger.error("**** %s ****" % e)
                logger.info(
                    "Loaded %d resource skills in %.2f seconds"
                    % (cnt, time() - starttime)
                )


@PlanTaskRegistry.register
class loadOperationMaterials(LoadTask):
    description = "Importing operation materials"
    sequence = 105

    @classmethod
    def getWeight(cls, **kwargs):
        return -1 if kwargs.get("skipLoad", False) else 1

    @classmethod
    def run(cls, database=DEFAULT_DB_ALIAS, **kwargs):
        import frepple

        if cls.filter:
            filter_where = "where %s " % cls.filter
        else:
            filter_where = ""

        with transaction.atomic(using=database):
            with connections[database].chunked_cursor() as cursor:
                cnt = 0
                starttime = time()
                # Note: The sorting of the flows is not really necessary, but helps to make
                # the planning progress consistent across runs and database engines.
                cursor.execute(
                    """
                SELECT
                  operation_id, item_id, quantity, type, effective_start, effective_end,
                  name, priority, search, source, transferbatch, quantity_fixed, "offset", location_id
                FROM operationmaterial %s
                ORDER BY operation_id, priority, item_id
                """
                    % filter_where
                )
                for i in cursor:
                    cnt += 1
                    try:
                        curflow = frepple.flow(
                            operation=frepple.operation(name=i[0]),
                            item=frepple.item(name=i[1]),
                            location=frepple.location(name=i[13]) if i[13] else None,
                            quantity=i[2],
                            quantity_fixed=i[11],
                            type="flow_%s" % i[3],
                            source=i[9],
                        )
                        if i[4] and i[4] > datetime(1971, 1, 3):
                            curflow.effective_start = i[4]
                        if i[5] and i[5] < datetime(2030, 12, 29):
                            curflow.effective_end = i[5]
                        if i[6] and i[6] != "":
                            curflow.name = i[6]
                        if i[7] is not None:
                            curflow.priority = i[7]
                        if i[8]:
                            curflow.search = i[8]
                        if i[3] == "transfer_batch":
                            if i[10]:
                                curflow.transferbatch = i[10]
                        else:
                            if i[12]:
                                curflow.offset = i[12]
                    except Exception as e:
                        logger.error("**** %s ****" % e)
                logger.info(
                    "Loaded %d operation materials in %.2f seconds"
                    % (cnt, time() - starttime)
                )

                # Check for operations where:
                #  - operation.item is still blank
                #  - they have a single operationmaterial item with quantity > 0
                # If found we update
                starttime = time()
                cnt = 0
                logger.info("Auto-update operation items...")
                for oper in frepple.operations():
                    if oper.hidden or oper.item or oper.owner:
                        continue
                    item = None
                    for fl in oper.flows:
                        if fl.quantity < 0 or fl.hidden:
                            continue
                        if item and item != fl.item:
                            item = None
                            break
                        else:
                            item = fl.item
                    if item:
                        cnt += 1
                        oper.item = item
                logger.info(
                    "Auto-update of %s operation items in %.2f seconds"
                    % (cnt, time() - starttime)
                )


@PlanTaskRegistry.register
class loadOperationResources(LoadTask):
    description = "Importing operation resources"
    sequence = 106

    @classmethod
    def getWeight(cls, **kwargs):
        return -1 if kwargs.get("skipLoad", False) else 1

    @classmethod
    def run(cls, database=DEFAULT_DB_ALIAS, **kwargs):
        import frepple

        if cls.filter:
            filter_where = "where %s " % cls.filter
        else:
            filter_where = ""

        with transaction.atomic(using=database):
            with connections[database].chunked_cursor() as cursor:
                cnt = 0
                starttime = time()
                # Note: The sorting of the loads is not really necessary, but helps to make
                # the planning progress consistent across runs and database engines.
                cursor.execute(
                    """
                SELECT
                  operation_id, resource_id, quantity, effective_start, effective_end, name,
                  priority, setup, search, skill_id, source, quantity_fixed
                FROM operationresource %s
                ORDER BY operation_id, priority, resource_id
                """
                    % filter_where
                )
                for i in cursor:
                    cnt += 1
                    try:
                        curload = frepple.load(
                            operation=frepple.operation(name=i[0]),
                            resource=frepple.resource(name=i[1]),
                            source=i[10],
                        )
                        if i[2] is not None:
                            curload.quantity = i[2]
                        if i[3] and i[3] > datetime(1971, 1, 3):
                            curload.effective_start = i[3]
                        if i[4] and i[4] < datetime(2030, 12, 29):
                            curload.effective_end = i[4]
                        if i[5]:
                            curload.name = i[5]
                        if i[6] is not None:
                            curload.priority = i[6]
                        if i[7]:
                            curload.setup = i[7]
                        if i[8]:
                            curload.search = i[8]
                        if i[9]:
                            curload.skill = frepple.skill(name=i[9])
                        if i[11]:
                            curload.quantity_fixed = i[11]
                    except Exception as e:
                        logger.error("**** %s ****" % e)
                logger.info(
                    "Loaded %d resource loads in %.2f seconds"
                    % (cnt, time() - starttime)
                )


@PlanTaskRegistry.register
class loadDemand(LoadTask):
    description = "Importing demands"
    sequence = 107

    @classmethod
    def getWeight(cls, **kwargs):
        return -1 if kwargs.get("skipLoad", False) else 1

    @classmethod
    def run(cls, database=DEFAULT_DB_ALIAS, **kwargs):
        import frepple

        if cls.filter:
            # Note: extra escaping of % is needed to avoid colliding with query argument
            filter_and = "and %s " % cls.filter.replace("%", "%%")
        else:
            filter_and = ""

        attrs = [
            f[0] for f in getAttributes(Demand) if not f[2].startswith("foreignkey:")
        ]
        if attrs:
            attrsql = ", %s" % ", ".join(attrs)
        else:
            attrsql = ""

        # Find the start date of the current forecasting bucket
        calendar = Parameter.getValue("forecast.calendar", database, None)
        threshold = frepple.settings.current
        if (
            Parameter.getValue("forecast.Net_PastDemand", database, "false").lower()
            == "true"
        ):
            try:
                threshold -= timedelta(
                    days=float(Parameter.getValue("forecast.Net_NetLate", database, 0))
                )
            except Exception:
                pass
        fcst_start_date = None
        if calendar:
            for i in frepple.calendar(name=calendar).events():
                if i[0] > threshold:
                    break
                fcst_start_date = i[0]
        if not fcst_start_date:
            fcst_start_date = date(2030, 1, 1)

        with transaction.atomic(using=database):
            with connections[database].chunked_cursor() as cursor:
                cnt = 0
                starttime = time()
                cursor.execute(
                    """
                    SELECT
                    name, due, quantity, priority, item_id,
                    operation_id, customer_id, owner, minshipment, maxlateness,
                    category, subcategory, source, location_id, status,
                    batch, description, policy %s
                    FROM demand
                    WHERE (status IS NULL OR status in ('open', 'quote', 'inquiry') or (status = 'closed' and due >= %%s)) %s
                    """
                    % (attrsql, filter_and),
                    (fcst_start_date,),
                )
                for i in cursor:
                    cnt += 1
                    try:
                        x = frepple.demand(
                            name=i[0],
                            due=i[1],
                            quantity=i[2],
                            priority=i[3],
                            status=i[14],
                            item=frepple.item(name=i[4]),
                            category=i[10],
                            subcategory=i[11],
                            source=i[12],
                            batch=i[15],
                            description=i[16],
                        )
                        if i[5]:
                            x.operation = frepple.operation(name=i[5])
                        if i[6]:
                            x.customer = frepple.customer(name=i[6])
                        if i[7]:
                            x.owner = frepple.demand_group(name=i[7])
                            if i[17]:
                                x.owner.policy = i[17]
                        if i[8] is not None:
                            x.minshipment = i[8]
                        if i[9] is not None:
                            x.maxlateness = i[9]
                        if i[13]:
                            x.location = frepple.location(name=i[13])
                        idx = 18
                        for a in attrs:
                            setattr(x, a, i[idx])
                            idx += 1
                    except Exception as e:
                        logger.error("**** %s ****" % e)
                logger.info(
                    "Loaded %d demands in %.2f seconds" % (cnt, time() - starttime)
                )


@PlanTaskRegistry.register
class loadOperationPlans(LoadTask):
    description = "Importing operationplans"
    sequence = 108

    @classmethod
    def getWeight(cls, **kwargs):
        return -1 if kwargs.get("skipLoad", False) else 1

    @classmethod
    def run(cls, database=DEFAULT_DB_ALIAS, **kwargs):
        import frepple

        if cls.filter:
            filter_and = "and %s " % cls.filter
        else:
            filter_and = ""

        # Disable the automatic creation of inventory consumption & production until we have
        # read also operationplanmaterial. When operationplanmaterial data is available we
        # don't create extra ones but take that data as input.
        frepple.settings.suppressFlowplanCreation = True

        with transaction.atomic(using=database):
            with connections[database].chunked_cursor() as cursor:
                with_fcst = "freppledb.forecast" in settings.INSTALLED_APPS
                consume_material = (
                    Parameter.getValue("WIP.consume_material", database, "true").lower()
                    == "true"
                )
                consume_capacity = (
                    Parameter.getValue("WIP.consume_capacity", database, "true").lower()
                    == "true"
                )
                consume_material_completed = (
                    Parameter.getValue(
                        "COMPLETED.consume_material", database, "true"
                    ).lower()
                    == "true"
                )
                if "supply" in os.environ:
                    confirmed_filter = """ and (
                      operationplan.status in ('confirmed', 'approved', 'completed')
                      or exists (
                        select 1 from operationplan as child_opplans
                        where child_opplans.owner_id = operationplan.reference
                        and child_opplans.status in ('approved', 'confirmed', 'completed')
                        )
                      )
                      """
                    parent_filter = (
                        " where status in ('confirmed', 'approved', 'completed') "
                    )
                    create_flag = True
                else:
                    confirmed_filter = " and operationplan.status <> 'closed'"
                    parent_filter = " where status <> 'closed' "
                    create_flag = False
                cnt_mo = 0
                cnt_po = 0
                cnt_do = 0
                cnt_dlvr = 0

                attrs = [
                    "operationplan.%s" % f[0]
                    for f in getAttributes(OperationPlan)
                    if not f[2].startswith("foreignkey:")
                ]
                if attrs:
                    attrsql = ", %s" % ", ".join(attrs)
                else:
                    attrsql = ""

                starttime = time()
                if with_fcst:
                    cursor.execute(
                        """
                        SELECT
                        operationplan.operation_id, operationplan.reference, operationplan.quantity,
                        case when operationplan.plan ? 'setupend'
                           then (operationplan.plan->>'setupend')::timestamp
                           else operationplan.startdate
                           end, operationplan.enddate, operationplan.status, operationplan.source,
                        operationplan.type, operationplan.origin_id, operationplan.destination_id, operationplan.supplier_id,
                        operationplan.item_id, operationplan.location_id, operationplan.batch, operationplan.quantity_completed,
                        array(
                            select resource_id
                            from operationplanresource
                            where operationplan_id = operationplan.reference
                            order by resource_id
                        ),
                        case when operationplan.plan ? 'setupoverride'
                          then (operationplan.plan->>'setupoverride')::integer
                        end,
                        coalesce(dmd.name, null),
                        remark,
                        coalesce(forecast.name, null), operationplan.due
                        %s
                        FROM operationplan
                        LEFT OUTER JOIN (select name from demand
                        where demand.status is null or demand.status in ('open', 'quote')
                        ) dmd
                        on dmd.name = operationplan.demand_id
                        LEFT OUTER JOIN (select name from forecast) forecast
                        on forecast.name = operationplan.forecast
                        WHERE operationplan.owner_id IS NULL
                        and operationplan.quantity >= 0 and operationplan.status <> 'closed'
                        %s%s and operationplan.type in ('PO', 'MO', 'DO', 'DLVR')
                        and (operationplan.startdate is null or operationplan.startdate < '2030-12-31')
                        and (operationplan.enddate is null or operationplan.enddate < '2030-12-31')
                        ORDER BY operationplan.reference ASC
                        """
                        % (attrsql, filter_and, confirmed_filter)
                    )
                else:
                    cursor.execute(
                        """
                        SELECT
                        operationplan.operation_id, operationplan.reference, operationplan.quantity,
                        case when operationplan.plan ? 'setupend'
                           then (operationplan.plan->>'setupend')::timestamp
                           else operationplan.startdate
                           end, operationplan.enddate, operationplan.status, operationplan.source,
                        operationplan.type, operationplan.origin_id, operationplan.destination_id, operationplan.supplier_id,
                        operationplan.item_id, operationplan.location_id, operationplan.batch, operationplan.quantity_completed,
                        array(
                            select resource_id
                            from operationplanresource
                            where operationplan_id = operationplan.reference
                            order by resource_id
                        ),
                        case when operationplan.plan ? 'setupoverride'
                          then (operationplan.plan->>'setupoverride')::integer
                        end,
                        coalesce(dmd.name, null),
                        remark
                        %s
                        FROM operationplan
                        LEFT OUTER JOIN (select name from demand
                        where demand.status is null or demand.status in ('open', 'quote')
                        ) dmd
                        on dmd.name = operationplan.demand_id
                        WHERE operationplan.owner_id IS NULL
                        and operationplan.quantity >= 0 and operationplan.status <> 'closed'
                        %s%s and operationplan.type in ('PO', 'MO', 'DO', 'DLVR')
                        and (operationplan.startdate is null or operationplan.startdate < '2030-12-31')
                        and (operationplan.enddate is null or operationplan.enddate < '2030-12-31')
                        ORDER BY operationplan.reference ASC
                        """
                        % (attrsql, filter_and, confirmed_filter)
                    )
                for i in cursor:
                    try:
                        if i[17]:
                            dmd = frepple.demand(name=i[17])
                        elif with_fcst and i[19] and i[20]:
                            dmd = frepple.demand_forecastbucket(
                                forecast=frepple.demand_forecast(name=i[19]),
                                start=i[20],
                            )
                        else:
                            dmd = None
                        if i[7] == "MO":
                            cnt_mo += 1
                            opplan = frepple.operationplan(
                                operation=frepple.operation(name=i[0]),
                                reference=i[1],
                                quantity=i[2],
                                source=i[6],
                                start=i[3],
                                end=i[4],
                                statusNoPropagation=i[5],
                                create=create_flag,
                                batch=i[13],
                                quantity_completed=i[14],
                                resources=i[15],
                                remark=i[18],
                            )
                            if opplan:
                                if i[5] == "confirmed":
                                    if not consume_material:
                                        opplan.consume_material = False
                                    if not consume_capacity:
                                        opplan.consume_capacity = False
                                elif i[5] == "completed":
                                    if not consume_material_completed:
                                        opplan.consume_material = False
                                if i[16] is not None:
                                    opplan.setupoverride = i[16]
                        elif i[7] == "PO":
                            cnt_po += 1
                            opplan = frepple.operationplan(
                                location=frepple.location(name=i[12]),
                                ordertype=i[7],
                                reference=i[1],
                                item=frepple.item(name=i[11]) if i[11] else None,
                                supplier=(
                                    frepple.supplier(name=i[10]) if i[10] else None
                                ),
                                quantity=i[2],
                                start=i[3],
                                end=i[4],
                                statusNoPropagation=i[5],
                                source=i[6],
                                create=create_flag,
                                batch=i[13],
                                remark=i[18],
                            )
                            if opplan and i[5] == "confirmed":
                                if not consume_capacity:
                                    opplan.consume_capacity = False
                        elif i[7] == "DO":
                            cnt_do += 1
                            opplan = frepple.operationplan(
                                location=frepple.location(name=i[9]) if i[9] else None,
                                reference=i[1],
                                ordertype=i[7],
                                item=frepple.item(name=i[11]) if i[11] else None,
                                origin=frepple.location(name=i[8]) if i[8] else None,
                                quantity=i[2],
                                start=i[3],
                                end=i[4],
                                statusNoPropagation=i[5],
                                source=i[6],
                                create=create_flag,
                                batch=i[13],
                                remark=i[18],
                            )
                            if opplan:
                                if i[5] == "confirmed":
                                    if not consume_capacity:
                                        opplan.consume_capacity = False
                                elif i[5] == "completed":
                                    if not consume_material_completed:
                                        opplan.consume_material = False
                        elif i[7] == "DLVR":
                            cnt_dlvr += 1
                            opplan = frepple.operationplan(
                                location=(
                                    frepple.location(name=i[12]) if i[12] else None
                                ),
                                reference=i[1],
                                ordertype=i[7],
                                item=frepple.item(name=i[11]) if i[11] else None,
                                origin=frepple.location(name=i[8]) if i[8] else None,
                                demand=dmd,
                                quantity=i[2],
                                start=i[3],
                                end=i[4],
                                statusNoPropagation=i[5],
                                source=i[6],
                                create=create_flag,
                                batch=i[13],
                                remark=i[18],
                            )
                            if opplan:
                                if i[5] == "confirmed":
                                    if not consume_capacity:
                                        opplan.consume_capacity = False
                                elif i[5] == "completed":
                                    if not consume_material_completed:
                                        opplan.consume_material = False
                            opplan = None
                        else:
                            logger.warning(
                                "Warning: unhandled operationplan type '%s'" % i[7]
                            )
                            continue

                        if opplan:
                            idx = 21 if with_fcst else 19
                            for a in getAttributes(OperationPlan):
                                setattr(opplan, a[0], i[idx])
                                idx += 1

                        if dmd and opplan:
                            opplan.demand = dmd
                    except Exception as e:
                        logger.error("**** %s ****" % e)
        with transaction.atomic(using=database):
            with connections[database].chunked_cursor() as cursor:
                if with_fcst:
                    cursor.execute(
                        """
                        SELECT
                        operationplan.operation_id, operationplan.reference, operationplan.quantity,
                        case when operationplan.plan ? 'setupend'
                           then (operationplan.plan->>'setupend')::timestamp
                           else operationplan.startdate
                           end, operationplan.enddate, operationplan.status,
                        operationplan.owner_id, operationplan.source, operationplan.batch,
                        array(
                            select resource_id
                            from operationplanresource
                            where operationplan_id = operationplan.reference
                            order by resource_id
                        ),
                        coalesce(dmd.name, null), remark, coalesce(forecast.name, null), operationplan.due %s
                        FROM operationplan
                        INNER JOIN (select reference
                        from operationplan %s
                        ) opplan_parent
                        on operationplan.owner_id = opplan_parent.reference
                        LEFT OUTER JOIN (select name from demand
                        where demand.status is null or demand.status in ('open', 'quote')
                        ) dmd
                        on dmd.name = operationplan.demand_id
                        LEFT OUTER JOIN (select name from forecast) forecast
                        on forecast.name = operationplan.forecast
                        WHERE operationplan.quantity >= 0
                        and (
                          operationplan.status <> 'closed'
                          or exists (
                            select 1 from operationplan as parent_opplan
                            where parent_opplan.reference = operationplan.owner_id
                            and parent_opplan.status <> 'closed'
                            )
                        )
                        %s and operationplan.type = 'MO'
                        and (operationplan.startdate is null or operationplan.startdate < '2030-12-31')
                        and (operationplan.enddate is null or operationplan.enddate < '2030-12-31')
                        ORDER BY operationplan.reference ASC
                        """
                        % (attrsql, parent_filter, filter_and)
                    )
                else:
                    cursor.execute(
                        """
                        SELECT
                        operationplan.operation_id, operationplan.reference, operationplan.quantity,
                        case when operationplan.plan ? 'setupend'
                           then (operationplan.plan->>'setupend')::timestamp
                           else operationplan.startdate
                           end, operationplan.enddate, operationplan.status,
                        operationplan.owner_id, operationplan.source, operationplan.batch,
                        array(
                            select resource_id
                            from operationplanresource
                            where operationplan_id = operationplan.reference
                            order by resource_id
                        ),
                        coalesce(dmd.name, null),
                        remark %s
                        FROM operationplan
                        INNER JOIN (select reference
                        from operationplan %s
                        ) opplan_parent
                        on operationplan.owner_id = opplan_parent.reference
                        LEFT OUTER JOIN (select name from demand
                        where demand.status is null or demand.status in ('open', 'quote')
                        ) dmd
                        on dmd.name = operationplan.demand_id
                        WHERE operationplan.quantity >= 0
                        and (
                          operationplan.status <> 'closed'
                          or exists (
                            select 1 from operationplan as parent_opplan
                            where parent_opplan.reference = operationplan.owner_id
                            and parent_opplan.status <> 'closed'
                            )
                        )
                        %s and operationplan.type = 'MO'
                        and (operationplan.startdate is null or operationplan.startdate < '2030-12-31')
                        and (operationplan.enddate is null or operationplan.enddate < '2030-12-31')
                        ORDER BY operationplan.reference ASC
                        """
                        % (attrsql, parent_filter, filter_and)
                    )
                for i in cursor:
                    try:
                        cnt_mo += 1
                        opplan = frepple.operationplan(
                            operation=frepple.operation(name=i[0]),
                            reference=i[1],
                            quantity=i[2],
                            source=i[7],
                            start=i[3],
                            end=i[4],
                            statusNoPropagation=i[5],
                            batch=i[8],
                            resources=i[9],
                            remark=i[11],
                        )
                        if opplan:
                            if i[5] == "confirmed":
                                if not consume_material:
                                    opplan.consume_material = False
                                if not consume_capacity:
                                    opplan.consume_capacity = False
                            elif i[5] == "completed":
                                if not consume_material_completed:
                                    opplan.consume_material = False
                            if i[6]:
                                try:
                                    opplan.owner = frepple.operationplan(reference=i[6])
                                except Exception:
                                    logger.error(
                                        "Reference %s: Can't set owner field to %s"
                                        % (i[1], i[6])
                                    )
                            if i[10]:
                                opplan.demand = frepple.demand(name=i[10])
                            elif with_fcst and i[12] and i[13]:
                                opplan.demand = frepple.forecastbucket(
                                    forecast=frepple.demand_forecast(name=i[12]),
                                    start=i[13],
                                )
                            idx = 14 if with_fcst else 12
                            for a in getAttributes(OperationPlan):
                                setattr(opplan, a[0], i[idx])
                                idx += 1
                    except Exception as e:
                        logger.error("**** %s ****" % e)
                logger.info(
                    "Loaded %d manufacturing orders, %d purchase orders, %d distribution orders and %s deliveries in %.2f seconds"
                    % (cnt_mo, cnt_po, cnt_do, cnt_dlvr, time() - starttime)
                )

        with connections[database].cursor() as cursor:
            # Assure the operationplan ids will be unique.
            # We call this method only at the end, as calling it earlier gives a slower
            # performance to load operationplans
            # By limiting the number of digits in the query we enforce reusing numbers at some point.
            if "supply" in os.environ:
                # Allow reusing references of proposed operationplans
                cursor.execute(
                    """
                    select coalesce(max(reference::bigint), 0) as max_reference
                    from operationplan
                    where status <> 'proposed'
                    and reference ~ '^[0-9]*$'
                    and char_length(reference) <= 9
                    """
                )
            else:
                # Don't reuse any references
                cursor.execute(
                    """
                    select coalesce(max(reference::bigint), 0) as max_reference
                    from operationplan
                    where reference ~ '^[0-9]*$'
                    and char_length(reference) <= 9
                    """
                )
            d = cursor.fetchone()
            frepple.settings.id = d[0] + 1

        # We only assign resource setup matrices here.
        # If we do it before the operationplans are read in, then a) the setup
        # calculations take extra calculations and b) the results depend on the
        # order we read in the operationplans.
        with transaction.atomic(using=database):
            with connections[database].chunked_cursor() as cursor:
                cursor.execute(
                    """
                    select name, setupmatrix_id
                    from resource
                    where setupmatrix_id is not null %s
                    order by name
                    """
                    % filter_and
                )
                for i in cursor:
                    frepple.resource(name=i[0]).setupmatrix = frepple.setupmatrix(
                        name=i[1]
                    )


@PlanTaskRegistry.register
class loadOperationPlanMaterials(LoadTask):
    description = "Importing operationplanmaterials"
    sequence = 109

    @classmethod
    def getWeight(cls, **kwargs):
        return -1 if kwargs.get("skipLoad", False) else 1

    @classmethod
    def run(cls, database=DEFAULT_DB_ALIAS, **kwargs):
        import frepple

        with transaction.atomic(using=database):
            with connections[database].chunked_cursor() as cursor:
                cnt = 0
                starttime = time()
                cursor.execute(
                    """
                    select
                    operationplan_id, opplanmat.item_id,
                    coalesce(opplanmat.status, 'confirmed'), opplanmat.quantity,
                    opplanmat.flowdate
                    from (select * from operationplanmaterial %s) as opplanmat
                    inner join operationplan
                    on operationplan.reference = opplanmat.operationplan_id
                    where operationplan.type = 'MO'
                    %s
                    order by operationplan_id
                    """
                    % (
                        "where %s" % cls.filter if cls.filter else "",
                        (
                            "and operationplan.status in ('approved', 'confirmed', 'completed')"
                            if "supply" in os.environ
                            else ""
                        ),
                    )
                )
                for i in cursor:
                    cnt += 1
                    try:
                        frepple.flowplan(
                            operationplan=frepple.operationplan(id=i[0]),
                            item=frepple.item(name=i[1]),
                            status=i[2],
                            quantity=i[3],
                        )
                    except Exception as e:
                        logger.error("**** %s ****" % e)
                logger.info(
                    "Loaded %d operationplanmaterials in %.2f seconds"
                    % (cnt, time() - starttime)
                )

                # All predefined inventory detail records are now loaded.
                # We now create any missing ones.
                frepple.settings.suppressFlowplanCreation = False


@PlanTaskRegistry.register
class PlanSize(CheckTask):
    description = "Plan Size"
    sequence = 120

    @classmethod
    def getWeight(cls, **kwargs):
        return -1 if kwargs.get("skipLoad", False) else 1

    @staticmethod
    def run(database=DEFAULT_DB_ALIAS, **kwargs):
        """
        It is important that all data is loaded at this point. We build out
        all buffers and their supply paths at this point.
        If new replenishment methods are added later on, they will not be used.
        """
        import frepple

        frepple.printsize()
