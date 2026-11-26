#
# Copyright (C) 2026 by frePPLe bv
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
import django.utils.timezone
from django.db import migrations, models, connections
from django.core.management import call_command
import django.utils.timezone

from freppledb.common.migrate import AttributeAddField


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
            cursor.execute(
                "select count(*) from pg_roles where rolname = lower(%s)", (role,)
            )
            if not cursor.fetchone()[0]:
                cursor.execute(
                    "create role %s with nologin noinherit role current_user" % (role,)
                )
            for table in ["forecast", "forecastplan", "measure"]:
                cursor.execute("grant select on table %s to %s" % (table, role))


def getMeasures(cursor):
    measures = {
        "forecasttotal",
        "forecastconsumed",
        "forecastnet",
        "forecastbaseline",
        "forecastoverride",
        "orderstotal",
        "ordersadjustment",
        "ordersopen",
        "ordersplanned",
        "forecastplanned",
    }
    cursor.execute("select name from measure")
    for r in cursor.fetchall():
        measures.add(r[0])
    return measures


def fromJsonbToColumns(apps, schema_editor):
    with connections[schema_editor.connection.alias].cursor() as cursor:
        for name in getMeasures(cursor):
            try:
                cursor.execute(
                    f"alter table forecastplan add column {name} numeric(20,8)"
                )
            except Exception:
                pass


def SkipIndexLike(apps, schema_editor):
    schema_editor.deferred_sql[:] = [
        sql
        for sql in schema_editor.deferred_sql
        if not (
            (sql_text := str(sql)).startswith("CREATE INDEX")
            and "_like" in sql_text
            and (
                "forecast_item_" in sql_text
                or "forecast_location_" in sql_text
                or "forecast_customer_" in sql_text
                or "forecast_operation_" in sql_text
            )
        )
    ]


class Migration(migrations.Migration):

    replaces = [
        ("forecast", "0001_initial"),
        ("forecast", "0002_cluster"),
        ("forecast", "0003_demand_pattern"),
        ("forecast", "0004_operationplan"),
        ("forecast", "0005_batch"),
        ("forecast", "0006_default_parameters"),
        ("forecast", "0007_exports"),
        ("forecast", "0008_outliers"),
        ("forecast", "0009_forecastreport_view"),
        ("forecast", "0010_forecastplan"),
        ("forecast", "0011_varchar_max_length"),
        ("forecast", "0012_varchar_max_length"),
    ]

    dependencies = [
        ("execute", "0010_dataexport"),
        ("input", "0071_operation_dependency_access"),
        ("input", "0079_varchar_max_length"),
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
                        null=True,
                        verbose_name="description",
                    ),
                ),
                (
                    "category",
                    models.CharField(
                        blank=True,
                        db_index=True,
                        null=True,
                        verbose_name="category",
                    ),
                ),
                (
                    "subcategory",
                    models.CharField(
                        blank=True,
                        db_index=True,
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
                (
                    "batch",
                    models.CharField(
                        blank=True,
                        help_text="MTO batch name",
                        null=True,
                        verbose_name="batch",
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
                        db_constraint=False,
                        db_index=False,
                        on_delete=django.db.models.deletion.CASCADE,
                        to="input.customer",
                        verbose_name="customer",
                    ),
                ),
                (
                    "item",
                    models.ForeignKey(
                        db_constraint=False,
                        db_index=False,
                        on_delete=django.db.models.deletion.CASCADE,
                        to="input.item",
                        verbose_name="item",
                    ),
                ),
                (
                    "location",
                    models.ForeignKey(
                        db_constraint=False,
                        db_index=False,
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
            ],
            options={
                "db_table": "forecastplan",
                "verbose_name": "forecast plan",
                "ordering": ["id"],
                "verbose_name_plural": "forecast plans",
            },
        ),
        migrations.AddIndex(
            model_name="forecastplan",
            index=models.Index(fields=["item"], name="forecastplan_item_idx"),
        ),
        migrations.AddIndex(
            model_name="forecastplan",
            index=models.Index(fields=["customer"], name="forecastplan_customer_idx"),
        ),
        migrations.AddIndex(
            model_name="forecastplan",
            index=models.Index(fields=["location"], name="forecastplan_location_idx"),
        ),
        migrations.CreateModel(
            name="ForecastPlanView",
            fields=[
                (
                    "name",
                    models.CharField(
                        primary_key=True,
                        serialize=False,
                        verbose_name="name",
                    ),
                ),
                ("item_id", models.CharField(verbose_name="item")),
                (
                    "location_id",
                    models.CharField(verbose_name="location"),
                ),
                (
                    "customer_id",
                    models.CharField(verbose_name="customer"),
                ),
                ("method", models.CharField(verbose_name="method")),
                (
                    "out_method",
                    models.CharField(verbose_name="out_method"),
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
                        null=True,
                        verbose_name="label",
                    ),
                ),
                (
                    "description",
                    models.CharField(
                        blank=True,
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
                        null=True,
                        verbose_name="mode in past periods",
                    ),
                ),
                (
                    "compute_expression",
                    models.CharField(
                        blank=True,
                        help_text="Formula to compute values",
                        null=True,
                        verbose_name="compute expression",
                    ),
                ),
                (
                    "update_expression",
                    models.CharField(
                        blank=True,
                        help_text="Formula executed when updating this field",
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
            code=loadParameters_measures, reverse_code=migrations.RunPython.noop
        ),
        migrations.RunPython(
            code=grant_read_access, reverse_code=migrations.RunPython.noop
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
        AttributeAddField(
            app_name="input",
            model_name="item",
            name="adi",
            field=models.DecimalField(
                blank=True,
                decimal_places=6,
                max_digits=15,
                null=True,
                verbose_name="adi",
            ),
        ),
        AttributeAddField(
            app_name="input",
            model_name="item",
            name="cv2",
            field=models.DecimalField(
                blank=True,
                decimal_places=6,
                max_digits=15,
                null=True,
                verbose_name="cv2",
            ),
        ),
        AttributeAddField(
            app_name="input",
            model_name="item",
            name="demand_pattern",
            field=models.CharField(
                blank=True, max_length=32, null=True, verbose_name="demand_pattern"
            ),
        ),
        AttributeAddField(
            app_name="input",
            model_name="operationplan",
            name="forecast",
            field=models.CharField(
                blank=True,
                db_index=True,
                null=True,
                verbose_name="forecast",
            ),
        ),
        migrations.RunSQL(
            sql="""
              insert into execute_export
                (name, sql, report, arguments)
              values (
                    'forecastreport.csv.gz',
                    null,
                    'freppledb.forecast.views.OverviewReport',
                    '{"format": "csvlist", "buckets": "month", "horizontype": true, "horizonunit": "month", "horizonlength": 6}'
              )
              on conflict (name) do nothing
              """,
            reverse_sql="delete from execute_export where name = 'forecastreport.csv.gz'",
        ),
        AttributeAddField(
            app_name="input",
            model_name="item",
            name="outlier_1b",
            field=models.IntegerField(
                blank=True, null=True, verbose_name="outliers last bucket"
            ),
        ),
        AttributeAddField(
            app_name="input",
            model_name="item",
            name="outlier_6b",
            field=models.IntegerField(
                blank=True, null=True, verbose_name="outliers last 6 buckets"
            ),
        ),
        AttributeAddField(
            app_name="input",
            model_name="item",
            name="outlier_12b",
            field=models.IntegerField(
                blank=True, null=True, verbose_name="outliers last 12 buckets"
            ),
        ),
        migrations.RunPython(
            code=fromJsonbToColumns, reverse_code=migrations.RunPython.noop
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
                forecastplan.customer_id
                from forecastplan
                left outer join forecast
                on forecast.item_id = forecastplan.item_id
                and forecast.location_id = forecastplan.location_id
                and forecast.customer_id = forecastplan.customer_id;
                create unique index on forecastreport_view (item_id, location_id, customer_id);

                refresh materialized view forecastreport_view;
                """,
            reverse_sql="drop materialized view if exists forecastreport_view",
        ),
        migrations.RunPython(
            code=SkipIndexLike,
            reverse_code=migrations.RunPython.noop,
        ),
    ]
