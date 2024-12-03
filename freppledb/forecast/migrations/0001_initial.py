#
# Copyright (C) 2023 by frePPLe bv
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

from django.db import migrations, models, connections
import django.db.models.deletion
from django.conf import settings
from django.core.management import call_command
import django.utils.timezone
import freppledb.common.fields


def loadParameters(apps, schema_editor):
    from django.core.management.commands.loaddata import Command

    call_command(
        Command(),
        "parameters.json",
        app_label="forecast",
        verbosity=0,
        database=schema_editor.connection.alias,
    )


def removeParameters(apps, schema_editor):
    db = schema_editor.connection.alias
    with connections[db].cursor() as cursor:
        cursor.execute("delete from common_parameter where name like 'forecast.%'")


def loadParameters_measures(apps, schema_editor):
    from django.core.management.commands.loaddata import Command

    call_command(
        Command(),
        "measures.json",
        app_label="forecast",
        verbosity=0,
        database=schema_editor.connection.alias,
    )


def grant_read_access(apps, schema_editor):
    db = schema_editor.connection.alias
    role = settings.DATABASES[db].get("SQL_ROLE", "report_role")
    if role:
        with connections[db].cursor() as cursor:
            cursor.execute("select count(*) from pg_roles where rolname = lower(%s)", (role,))
            if not cursor.fetchone()[0]:
                cursor.execute(
                    "create role %s with nologin noinherit role current_user" % (role,)
                )
            for table in ["forecast", "forecastplan", "measure"]:
                cursor.execute("grant select on table %s to %s" % (table, role))


def createProcedure(apps, schema_editor):
    db = schema_editor.connection.alias
    with connections[db].cursor() as cursor:
        if cursor.connection.server_version < 110000:
            # Do not create the procedure when the postgres version is too old
            return

        cursor.execute(
            """
            drop procedure if exists aggregatedemand;

            drop type if exists demand_key_type;

            create type demand_key_type as (
                item_id varchar,
                location_id varchar,
                customer_id varchar,
                startdate timestamp,
                enddate timestamp,
                orderstotal numeric,
                ordersopen numeric,
                orderstotalvalue numeric,
                ordersopenvalue numeric
            );

            create or replace procedure aggregatedemand(
               buckets varchar(300),
               horizon_start timestamp,
               horizon_end timestamp
            )
            language plpgsql
            as $$
            declare
                dmd_cursor cursor
                  (buckets varchar(300), horizon_start timestamp, horizon_end timestamp)
                  for
                    select
                        item_id, location_id, customer_id,
                        common_bucketdetail.startdate,
                        common_bucketdetail.enddate,
                        quantity,
                        case when status is null or status in ('open', 'quote') then quantity end,
                        quantity * item.cost,
                        case when status is null or status in ('open', 'quote') then quantity * item.cost end
                    from demand
                    inner join item
                        on demand.item_id = item.name
                    inner join common_bucketdetail
                        on bucket_id = buckets
                        and demand.due >= common_bucketdetail.startdate
                        and demand.due < common_bucketdetail.enddate
                    where
                        demand.status is distinct from 'canceled'
                        and common_bucketdetail.startdate >= horizon_start
                        and common_bucketdetail.startdate < horizon_end
                    order by item_id, location_id, customer_id, due;

                fcstplan_cursor cursor
                    (horizon_start timestamp, horizon_end timestamp)
                    for
                    select
                        forecastplan.item_id, forecastplan.location_id, forecastplan.customer_id,
                        startdate,enddate,
                        (value->>'orderstotal')::numeric,
                        (value->>'ordersopen')::numeric,
                        (value->>'orderstotalvalue')::numeric,
                        (value->>'ordersopenvalue')::numeric
                    from forecastplan
                    where value ? 'leaf'
                      and startdate >= horizon_start
                      and startdate < horizon_end
                    order by item_id, location_id, customer_id, startdate
                    for update;

                dmd_cur demand_key_type;
                dmd_prev demand_key_type;
                fcstplan_cur demand_key_type;

                counter_inserted integer = 0;
                counter_updated integer = 0;
                counter_deleted integer = 0;
                counter_untouched integer = 0;
            begin

            open dmd_cursor(buckets, horizon_start, horizon_end);
            open fcstplan_cursor(horizon_start, horizon_end);

            fetch fcstplan_cursor into fcstplan_cur;
            fetch dmd_cursor into dmd_cur;
            if dmd_cur.item_id is not null then
                dmd_prev = dmd_cur;
                fetch dmd_cursor into dmd_cur;
            end if;

            loop
            if fcstplan_cur.item_id is null
                and dmd_cur.item_id is null
                and dmd_prev.item_id is null then
                -- processed all records
                -- raise notice 'done';
                exit;
            elsif dmd_cur.item_id is not null
                and dmd_cur.item_id is not distinct from dmd_prev.item_id
                and dmd_cur.location_id is not distinct from dmd_prev.location_id
                and dmd_cur.customer_id is not distinct from dmd_prev.customer_id
                and dmd_cur.startdate is not distinct from dmd_prev.startdate
                and dmd_cur.enddate is not distinct from dmd_prev.enddate
                then
                -- same demand key
                dmd_prev.orderstotal = dmd_prev.orderstotal + dmd_cur.orderstotal;
                dmd_prev.ordersopen = dmd_prev.ordersopen + dmd_cur.ordersopen;
                dmd_prev.orderstotalvalue = dmd_prev.orderstotalvalue + dmd_cur.orderstotalvalue;
                dmd_prev.ordersopenvalue = dmd_prev.ordersopenvalue + dmd_cur.ordersopenvalue;
                fetch dmd_cursor into dmd_cur;
                -- raise notice 'same demand key %', dmd_prev;
            elsif fcstplan_cur.item_id is not null
               and (
                dmd_cur.item_id is null
                or (fcstplan_cur.item_id, fcstplan_cur.location_id, fcstplan_cur.customer_id, fcstplan_cur.startdate)
                  < (dmd_prev.item_id, dmd_prev.location_id, dmd_prev.customer_id, dmd_prev.startdate)
                )
                then
                -- delete this forecastplan record: there are no matching demand keys
                -- raise notice 'deleting %s', fcstplan_cur;
                counter_deleted = counter_deleted + 1;
                update forecastplan
                    set value = value - array ['orderstotal', 'ordersopen', 'orderstotalvalue', 'ordersopenvalue', 'leaf']
                    where current of fcstplan_cursor;
                fetch fcstplan_cursor into fcstplan_cur;
            elsif dmd_prev.item_id is not null
                and (
                fcstplan_cur.item_id is null
                or (fcstplan_cur.item_id, fcstplan_cur.location_id, fcstplan_cur.customer_id, fcstplan_cur.startdate)
                  > (dmd_prev.item_id, dmd_prev.location_id, dmd_prev.customer_id, dmd_prev.startdate)
                )
                then
                -- insert a new forecastplan record
                -- raise notice 'inserting %', dmd_prev;
                counter_inserted = counter_inserted + 1;
                insert into forecastplan
                    (item_id, location_id, customer_id, startdate, enddate, value)
                    values(
                    dmd_prev.item_id,
                    dmd_prev.location_id,
                    dmd_prev.customer_id,
                    dmd_prev.startdate,
                    dmd_prev.enddate,
                    jsonb_build_object(
                        'orderstotal', dmd_prev.orderstotal,
                        'ordersopen', dmd_prev.ordersopen,
                        'orderstotalvalue', dmd_prev.orderstotalvalue,
                        'ordersopenvalue', dmd_prev.ordersopenvalue,
                        'leaf', 1
                        )
                    )
                    on conflict (item_id, location_id, customer_id, startdate)
                    do update set value =  forecastplan.value || excluded.value;
                dmd_prev = dmd_cur;
                fetch dmd_cursor into dmd_cur;
            elsif fcstplan_cur.item_id is not null
                and dmd_prev.item_id is not null
                and (
                dmd_prev.orderstotal is distinct from fcstplan_cur.orderstotal
                or dmd_prev.ordersopen is distinct from fcstplan_cur.ordersopen
                or dmd_prev.orderstotalvalue is distinct from fcstplan_cur.orderstotalvalue
                or dmd_prev.ordersopenvalue is distinct from fcstplan_cur.ordersopenvalue
                )
                then
                    -- update existing forecastplan record
                    -- raise notice 'updating %', dmd_prev;
                    counter_updated = counter_updated + 1;
                    update forecastplan
                    set value = value || jsonb_build_object(
                        'orderstotal', dmd_prev.orderstotal,
                        'ordersopen', dmd_prev.ordersopen,
                        'orderstotalvalue', dmd_prev.orderstotalvalue,
                        'ordersopenvalue', dmd_prev.ordersopenvalue,
                        'leaf', 1
                        )
                    where current of fcstplan_cursor;
                    fetch fcstplan_cursor into fcstplan_cur;
                    dmd_prev = dmd_cur;
                    fetch dmd_cursor into dmd_cur;
            else
                -- Excellent, nothing to do! The value hasn't changed.
                -- raise notice 'no change %', dmd_prev;
                counter_untouched = counter_untouched + 1;
                fetch fcstplan_cursor into fcstplan_cur;
                dmd_prev = dmd_cur;
                fetch dmd_cursor into dmd_cur;
            end if;
            end loop;

            close dmd_cursor;
            close fcstplan_cursor;

            raise notice 'inserted % forecastplan records', counter_inserted;
            raise notice 'updated % forecastplan records', counter_updated;
            raise notice 'deleted % forecastplan records', counter_deleted;
            raise notice 'unchanged % forecastplan records', counter_untouched;

            end $$;
            """
        )


class Migration(migrations.Migration):
    initial = True

    dependencies = [
        ("input", "0071_operation_dependency_access"),
    ]

    operations = [
        migrations.CreateModel(
            name="Forecast",
            fields=[
                (
                    "customer",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        to="input.customer",
                        verbose_name="customer",
                    ),
                ),
                (
                    "item",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        to="input.item",
                        verbose_name="item",
                    ),
                ),
                (
                    "location",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        to="input.location",
                        verbose_name="location",
                    ),
                ),
                (
                    "name",
                    models.CharField(
                        max_length=300,
                        primary_key=True,
                        serialize=False,
                        verbose_name="name",
                    ),
                ),
                (
                    "method",
                    models.CharField(
                        blank=True,
                        choices=[
                            ("automatic", "Automatic"),
                            ("constant", "Constant"),
                            ("trend", "Trend"),
                            ("seasonal", "Seasonal"),
                            ("intermittent", "Intermittent"),
                            ("moving average", "Moving average"),
                            ("manual", "Manual"),
                            ("aggregate", "Aggregate"),
                        ],
                        default="automatic",
                        help_text="Method used to generate a base forecast",
                        max_length=20,
                        null=True,
                        verbose_name="Forecast method",
                    ),
                ),
                (
                    "planned",
                    models.BooleanField(
                        default=True,
                        help_text="Specifies whether this forecast record should be planned",
                        verbose_name="planned",
                    ),
                ),
                (
                    "priority",
                    models.IntegerField(
                        default=10,
                        help_text="Priority of the demand (lower numbers indicate more important demands)",
                        verbose_name="priority",
                    ),
                ),
                (
                    "minshipment",
                    models.DecimalField(
                        blank=True,
                        decimal_places=8,
                        help_text="Minimum shipment quantity when planning this demand",
                        max_digits=20,
                        null=True,
                        verbose_name="minimum shipment",
                    ),
                ),
                (
                    "maxlateness",
                    models.DurationField(
                        blank=True,
                        help_text="Maximum lateness allowed when planning this demand",
                        null=True,
                        verbose_name="maximum lateness",
                    ),
                ),
                (
                    "discrete",
                    models.BooleanField(
                        default=True,
                        help_text="Round forecast numbers to integers",
                        verbose_name="discrete",
                    ),
                ),
                (
                    "description",
                    models.CharField(
                        blank=True,
                        max_length=500,
                        null=True,
                        verbose_name="description",
                    ),
                ),
                (
                    "category",
                    models.CharField(
                        blank=True,
                        db_index=True,
                        max_length=300,
                        null=True,
                        verbose_name="category",
                    ),
                ),
                (
                    "subcategory",
                    models.CharField(
                        blank=True,
                        db_index=True,
                        max_length=300,
                        null=True,
                        verbose_name="subcategory",
                    ),
                ),
                (
                    "operation",
                    models.ForeignKey(
                        blank=True,
                        help_text="Operation used to satisfy this demand",
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        related_name="used_forecast",
                        to="input.operation",
                        verbose_name="delivery operation",
                    ),
                ),
                (
                    "source",
                    models.CharField(
                        blank=True,
                        db_index=True,
                        max_length=300,
                        null=True,
                        verbose_name="source",
                    ),
                ),
                (
                    "lastmodified",
                    models.DateTimeField(
                        db_index=True,
                        default=django.utils.timezone.now,
                        editable=False,
                        verbose_name="last modified",
                    ),
                ),
                (
                    "out_smape",
                    models.DecimalField(
                        blank=True,
                        decimal_places=8,
                        max_digits=20,
                        null=True,
                        verbose_name="estimated forecast error",
                    ),
                ),
                (
                    "out_method",
                    models.CharField(
                        blank=True,
                        max_length=20,
                        null=True,
                        verbose_name="calculated forecast method",
                    ),
                ),
                (
                    "out_deviation",
                    models.DecimalField(
                        blank=True,
                        decimal_places=8,
                        max_digits=20,
                        null=True,
                        verbose_name="calculated standard deviation",
                    ),
                ),
            ],
            options={
                "abstract": False,
                "verbose_name": "forecast",
                "ordering": ["name"],
                "verbose_name_plural": "forecasts",
                "db_table": "forecast",
                "unique_together": {("item", "location", "customer")},
            },
        ),
        migrations.CreateModel(
            name="ForecastPlan",
            fields=[
                (
                    "id",
                    models.AutoField(
                        primary_key=True, serialize=False, verbose_name="identifier"
                    ),
                ),
                (
                    "customer",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        to="input.customer",
                        verbose_name="customer",
                    ),
                ),
                (
                    "item",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        to="input.item",
                        verbose_name="item",
                    ),
                ),
                (
                    "location",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        to="input.location",
                        verbose_name="location",
                    ),
                ),
                (
                    "startdate",
                    models.DateTimeField(db_index=True, verbose_name="start date"),
                ),
                (
                    "enddate",
                    models.DateTimeField(db_index=True, verbose_name="end date"),
                ),
                (
                    "value",
                    freppledb.common.fields.JSONBField(default="{}", max_length=2000),
                ),
            ],
            options={
                "db_table": "forecastplan",
                "verbose_name": "forecast plan",
                "ordering": ["id"],
                "verbose_name_plural": "forecast plans",
            },
        ),
        migrations.CreateModel(
            name="ForecastPlanView",
            fields=[
                (
                    "name",
                    models.CharField(
                        max_length=300,
                        primary_key=True,
                        serialize=False,
                        verbose_name="name",
                    ),
                ),
                ("item_id", models.CharField(max_length=300, verbose_name="item")),
                (
                    "location_id",
                    models.CharField(max_length=300, verbose_name="location"),
                ),
                (
                    "customer_id",
                    models.CharField(max_length=300, verbose_name="customer"),
                ),
                ("method", models.CharField(max_length=64, verbose_name="method")),
                (
                    "out_method",
                    models.CharField(max_length=64, verbose_name="out_method"),
                ),
                (
                    "out_smape",
                    models.DecimalField(
                        blank=True,
                        decimal_places=8,
                        max_digits=20,
                        null=True,
                        verbose_name="out_smape",
                    ),
                ),
            ],
            options={
                "verbose_name": "forecastreport_view",
                "verbose_name_plural": "forecastreports_view",
                "db_table": "forecastreport_view",
                "abstract": False,
                "managed": False,
            },
        ),
        migrations.CreateModel(
            name="Measure",
            fields=[
                (
                    "source",
                    models.CharField(
                        blank=True,
                        db_index=True,
                        max_length=300,
                        null=True,
                        verbose_name="source",
                    ),
                ),
                (
                    "lastmodified",
                    models.DateTimeField(
                        db_index=True,
                        default=django.utils.timezone.now,
                        editable=False,
                        verbose_name="last modified",
                    ),
                ),
                (
                    "name",
                    models.CharField(
                        help_text="Unique identifier",
                        max_length=300,
                        primary_key=True,
                        serialize=False,
                        verbose_name="name",
                    ),
                ),
                (
                    "label",
                    models.CharField(
                        blank=True,
                        help_text="Label to be displayed in the user interface",
                        max_length=300,
                        null=True,
                        verbose_name="label",
                    ),
                ),
                (
                    "description",
                    models.CharField(
                        blank=True,
                        max_length=500,
                        null=True,
                        verbose_name="description",
                    ),
                ),
                (
                    "type",
                    models.CharField(
                        blank=True,
                        choices=[
                            ("aggregate", "aggregate"),
                            ("local", "local"),
                            ("computed", "computed"),
                        ],
                        default="default",
                        max_length=20,
                        null=True,
                        verbose_name="type",
                    ),
                ),
                (
                    "mode_future",
                    models.CharField(
                        blank=True,
                        choices=[("edit", "edit"), ("view", "view"), ("hide", "hide")],
                        default="edit",
                        max_length=20,
                        null=True,
                        verbose_name="mode in future periods",
                    ),
                ),
                (
                    "mode_past",
                    models.CharField(
                        blank=True,
                        choices=[("edit", "edit"), ("view", "view"), ("hide", "hide")],
                        default="edit",
                        max_length=20,
                        null=True,
                        verbose_name="mode in past periods",
                    ),
                ),
                (
                    "compute_expression",
                    models.CharField(
                        blank=True,
                        help_text="Formula to compute values",
                        max_length=300,
                        null=True,
                        verbose_name="compute expression",
                    ),
                ),
                (
                    "update_expression",
                    models.CharField(
                        blank=True,
                        help_text="Formula executed when updating this field",
                        max_length=300,
                        null=True,
                        verbose_name="update expression",
                    ),
                ),
                (
                    "initially_hidden",
                    models.BooleanField(
                        blank=True,
                        help_text="controls whether or not this measure is visible by default",
                        null=True,
                        verbose_name="initially hidden",
                    ),
                ),
                (
                    "formatter",
                    models.CharField(
                        blank=True,
                        choices=[("number", "number"), ("currency", "currency")],
                        default="number",
                        max_length=20,
                        null=True,
                        verbose_name="format",
                    ),
                ),
                (
                    "discrete",
                    models.BooleanField(blank=True, null=True, verbose_name="discrete"),
                ),
                (
                    "defaultvalue",
                    models.DecimalField(
                        blank=True,
                        decimal_places=8,
                        default=0,
                        max_digits=20,
                        null=True,
                        verbose_name="default value",
                    ),
                ),
                (
                    "overrides",
                    models.CharField(
                        blank=True,
                        max_length=300,
                        null=True,
                        verbose_name="override measure",
                    ),
                ),
            ],
            options={
                "verbose_name": "measure",
                "verbose_name_plural": "measures",
                "db_table": "measure",
                "ordering": ["name"],
                "abstract": False,
            },
        ),
        migrations.RunSQL(
            sql="alter table measure alter column lastmodified set default now()",
            reverse_sql=migrations.RunSQL.noop,
        ),
        migrations.RunSQL(
            sql="alter table forecast alter column lastmodified set default now()",
            reverse_sql=migrations.RunSQL.noop,
        ),
        migrations.RunPython(
            code=loadParameters,
            reverse_code=removeParameters,
        ),
        migrations.RunPython(
            code=loadParameters_measures,
            reverse_code=migrations.RunPython.noop,
        ),
        migrations.RunPython(
            code=grant_read_access, reverse_code=migrations.RunPython.noop
        ),
        migrations.RunSQL(
            sql="""
              drop materialized view if exists forecastreport_view;

              create materialized view forecastreport_view as
              select distinct
                   coalesce(forecast.name, forecastplan.item_id||' @ '||
                     forecastplan.location_id||' @ '||
                     forecastplan.customer_id) as name,
                   forecastplan.item_id,
                   forecastplan.location_id,
                   forecastplan.customer_id,
                   coalesce(forecast.method,'aggregate') as method,
                   coalesce(forecast.out_method,'aggregate') as out_method,
                   forecast.out_smape as out_smape
              from forecastplan
              left outer join forecast
                on forecast.item_id = forecastplan.item_id
                and forecast.location_id = forecastplan.location_id\n
                and forecast.customer_id = forecastplan.customer_id;

            create unique index on forecastreport_view (item_id, location_id, customer_id)
            """,
            reverse_sql="""
            drop materialized view forecastreport_view
            """,
        ),
        migrations.RunSQL(
            sql="alter table forecastplan drop column id",
            reverse_sql=migrations.RunSQL.noop,
        ),
        migrations.AddConstraint(
            model_name="forecastplan",
            constraint=models.UniqueConstraint(
                fields=("item", "location", "customer", "startdate"),
                name="forecastplan_uidx",
            ),
        ),
        migrations.RunSQL(
            sql="cluster forecastplan using forecastplan_uidx",
            reverse_sql=migrations.RunSQL.noop,
        ),
        migrations.RunSQL(
            sql="""
               create temporary table item_hierarchy on commit preserve rows as
                 select parent.name parent, child.name child from item parent
                 inner join item child
                   on child.lft between parent.lft and parent.rght;
               create index item_hierarchy_idx on item_hierarchy (child);

               create temporary table location_hierarchy on commit preserve rows as
                 select parent.name parent, child.name child from location parent
                 inner join location child
                   on child.lft between parent.lft and parent.rght;
               create index location_hierarchy_idx on location_hierarchy (child);

               create temporary table customer_hierarchy on commit preserve rows as
                 select parent.name parent, child.name child from customer parent
                 inner join customer child
                 on child.lft between parent.lft and parent.rght;
               create index customer_hierarchy_idx on customer_hierarchy (child);

               drop table if exists forecasthierarchy;
               create table forecasthierarchy as
                 select distinct
                   item_hierarchy.parent item_id, location_hierarchy.parent location_id,
                   customer_hierarchy.parent customer_id
                 from forecast
                 inner join item_hierarchy on forecast.item_id = item_hierarchy.child
                 inner join customer_hierarchy on forecast.customer_id = customer_hierarchy.child
                 inner join location_hierarchy on forecast.location_id = location_hierarchy.child
                 where coalesce(method, 'automatic') != 'aggregate';

              drop table item_hierarchy, location_hierarchy, customer_hierarchy;
              """,
            reverse_sql="drop table if exists forecasthierarchy",
        ),
    ]
