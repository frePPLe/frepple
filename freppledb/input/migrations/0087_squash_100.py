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
from django.db import connections
import datetime
import django.db.models.deletion
import django.utils.timezone
from django.db import migrations, models


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
            cursor.execute("grant select on table operation_dependency to %s" % (role,))


def recreateConstraintsCascade(apps, schema_editor):
    def getConstraint(cursor, tableName):
        cursor.execute(
            """
            select conname from pg_constraint
            inner join pg_class opplan on opplan.oid = pg_constraint.confrelid and opplan.relname = 'operationplan'
            inner join pg_class opm on opm.oid = pg_constraint.conrelid and opm.relname = %s
            inner join pg_attribute on attname = 'operationplan_id' and attrelid = opm.oid and pg_attribute.attnum = any(conkey)
            """,
            (tableName,),
        )
        return cursor.fetchone()[0]

    with connections[schema_editor.connection.alias].cursor() as cursor:
        cursor.execute(
            "alter table operationplanmaterial drop constraint %s"
            % (getConstraint(cursor, "operationplanmaterial"),)
        )
        cursor.execute(
            "alter table operationplanresource drop constraint %s"
            % (getConstraint(cursor, "operationplanresource"),)
        )
        cursor.execute("""
            alter table operationplanresource
            ADD FOREIGN KEY (operationplan_id)
            REFERENCES public.operationplan (reference) MATCH SIMPLE
            ON UPDATE NO ACTION
            ON DELETE CASCADE
            DEFERRABLE INITIALLY DEFERRED
            """)
        cursor.execute("""
            alter table operationplanmaterial
                ADD FOREIGN KEY (operationplan_id)
                REFERENCES public.operationplan (reference) MATCH SIMPLE
                ON UPDATE NO ACTION
                ON DELETE CASCADE
                DEFERRABLE INITIALLY DEFERRED
            """)


class Migration(migrations.Migration):

    replaces = [
        ("input", "0069_operation_dependency"),
        ("input", "0070_operationplanresource"),
        ("input", "0071_operation_dependency_access"),
        ("input", "0073_operation_dependency"),
        ("input", "0074_buffer_maximum"),
        ("input", "0075_operationmaterial_location"),
        ("input", "0076_operationplan_remark"),
        ("input", "0077_operationresource_quantity"),
        ("input", "0078_parameter_deliveryduration"),
        ("input", "0079_varchar_max_length"),
        ("input", "0080_parameter_move_approved_early"),
        ("input", "0081_work_orders"),
        ("input", "0082_operation_batchwindow"),
        ("input", "0083_parameter_pathreport_optimization"),
        ("input", "0084_parameter_plan_solver"),
        ("input", "0085_remove_deprecated_fields"),
        ("input", "0086_infinitefuturedate"),
    ]

    dependencies = [
        ("input", "0068_squash_70"),
    ]

    operations = [
        migrations.CreateModel(
            name="OperationDependency",
            fields=[
                (
                    "id",
                    models.AutoField(
                        primary_key=True, serialize=False, verbose_name="identifier"
                    ),
                ),
                (
                    "operation",
                    models.ForeignKey(
                        help_text="Operation",
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="dependencies",
                        to="input.operation",
                        verbose_name="operation",
                    ),
                ),
                (
                    "blockedby",
                    models.ForeignKey(
                        help_text="Blocked by operation",
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="dependents",
                        to="input.operation",
                        verbose_name="blocked by operation",
                    ),
                ),
                (
                    "quantity",
                    models.DecimalField(
                        blank=True,
                        decimal_places=8,
                        default="1.0",
                        help_text="Quantity relation between the operations",
                        max_digits=20,
                        null=True,
                        verbose_name="quantity",
                    ),
                ),
                (
                    "safety_leadtime",
                    models.DurationField(
                        blank=True,
                        help_text="soft safety lead time",
                        null=True,
                        verbose_name="soft safety lead time",
                    ),
                ),
                (
                    "hard_safety_leadtime",
                    models.DurationField(
                        blank=True,
                        help_text="hard safety lead time",
                        null=True,
                        verbose_name="hard safety lead time",
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
            ],
            options={
                "verbose_name": "operation dependency",
                "verbose_name_plural": "operation dependencies",
                "db_table": "operation_dependency",
                "ordering": ["operation", "blockedby"],
                "abstract": False,
                "unique_together": {("operation", "blockedby")},
            },
        ),
        migrations.RemoveField(
            model_name="operationplanresource",
            name="enddate",
        ),
        migrations.RemoveField(
            model_name="operationplanresource",
            name="startdate",
        ),
        migrations.RunPython(code=grant_read_access),
        migrations.RunSQL(
            sql="alter table operation_dependency alter column lastmodified set default now()",
        ),
        migrations.AddField(
            model_name="buffer",
            name="maximum",
            field=models.DecimalField(
                blank=True,
                decimal_places=8,
                default="0.00",
                help_text="maximum stock",
                max_digits=20,
                null=True,
                verbose_name="maximum",
            ),
        ),
        migrations.AddField(
            model_name="buffer",
            name="maximum_calendar",
            field=models.ForeignKey(
                blank=True,
                help_text="Calendar storing a time-dependent maximum stock profile",
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name="buffermaxima",
                to="input.calendar",
                verbose_name="maximum calendar",
            ),
        ),
        migrations.AlterField(
            model_name="buffer",
            name="minimum_calendar",
            field=models.ForeignKey(
                blank=True,
                help_text="Calendar storing a time-dependent safety stock profile",
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name="bufferminima",
                to="input.calendar",
                verbose_name="minimum calendar",
            ),
        ),
        migrations.AddField(
            model_name="operationmaterial",
            name="location",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name="operationmaterials",
                to="input.location",
                verbose_name="location",
            ),
        ),
        migrations.AddField(
            model_name="operationplan",
            name="remark",
            field=models.CharField(
                blank=True,
                help_text="remark",
                null=True,
                verbose_name="remark",
            ),
        ),
        migrations.AlterField(
            model_name="operationresource",
            name="quantity",
            field=models.DecimalField(
                blank=True,
                decimal_places=8,
                default="1.00",
                help_text="Required quantity of the resource",
                max_digits=20,
                null=True,
                verbose_name="quantity",
            ),
        ),
        migrations.RunSQL(
            sql="\n            insert into common_parameter (name, value, lastmodified, description)\n            values (\n              'plan.deliveryDuration', '0', now(),\n              'The duration (in working hours) for the final shipment of a sales order to the customer. Default: 0'\n              )\n            on conflict (name) do nothing\n            ",
            reverse_sql="\n            delete from common_parameter where name = 'plan.deliveryDuration'\n            ",
        ),
        migrations.RunSQL(
            sql="drop materialized view if exists forecastreport_view",
            reverse_sql="",
        ),
        migrations.AlterModelOptions(
            name="operationplan",
            options={
                "ordering": ["reference"],
                "verbose_name": "operationplan",
                "verbose_name_plural": "operationplans",
            },
        ),
        migrations.AlterModelOptions(
            name="operationplanmaterial",
            options={
                "ordering": ["item", "location", "flowdate"],
                "verbose_name": "inventory detail",
                "verbose_name_plural": "inventory detail",
            },
        ),
        migrations.AlterModelOptions(
            name="operationplanresource",
            options={
                "ordering": ["resource", "operationplan"],
                "verbose_name": "resource detail",
                "verbose_name_plural": "resource detail",
            },
        ),
        migrations.AlterField(
            model_name="buffer",
            name="batch",
            field=models.CharField(
                blank=True, default="", null=True, verbose_name="batch"
            ),
        ),
        migrations.AlterField(
            model_name="buffer",
            name="category",
            field=models.CharField(
                blank=True, db_index=True, null=True, verbose_name="category"
            ),
        ),
        migrations.AlterField(
            model_name="buffer",
            name="description",
            field=models.CharField(blank=True, null=True, verbose_name="description"),
        ),
        migrations.AlterField(
            model_name="buffer",
            name="source",
            field=models.CharField(
                blank=True, db_index=True, null=True, verbose_name="source"
            ),
        ),
        migrations.AlterField(
            model_name="buffer",
            name="subcategory",
            field=models.CharField(
                blank=True, db_index=True, null=True, verbose_name="subcategory"
            ),
        ),
        migrations.AlterField(
            model_name="buffer",
            name="type",
            field=models.CharField(
                blank=True,
                choices=[("default", "default"), ("infinite", "infinite")],
                default="default",
                null=True,
                verbose_name="type",
            ),
        ),
        migrations.AlterField(
            model_name="calendar",
            name="category",
            field=models.CharField(
                blank=True, db_index=True, null=True, verbose_name="category"
            ),
        ),
        migrations.AlterField(
            model_name="calendar",
            name="description",
            field=models.CharField(blank=True, null=True, verbose_name="description"),
        ),
        migrations.AlterField(
            model_name="calendar",
            name="name",
            field=models.CharField(
                primary_key=True, serialize=False, verbose_name="name"
            ),
        ),
        migrations.AlterField(
            model_name="calendar",
            name="source",
            field=models.CharField(
                blank=True, db_index=True, null=True, verbose_name="source"
            ),
        ),
        migrations.AlterField(
            model_name="calendar",
            name="subcategory",
            field=models.CharField(
                blank=True, db_index=True, null=True, verbose_name="subcategory"
            ),
        ),
        migrations.AlterField(
            model_name="calendarbucket",
            name="friday",
            field=models.BooleanField(blank=True, default=True, verbose_name="Friday"),
        ),
        migrations.AlterField(
            model_name="calendarbucket",
            name="monday",
            field=models.BooleanField(blank=True, default=True, verbose_name="Monday"),
        ),
        migrations.AlterField(
            model_name="calendarbucket",
            name="saturday",
            field=models.BooleanField(
                blank=True, default=True, verbose_name="Saturday"
            ),
        ),
        migrations.AlterField(
            model_name="calendarbucket",
            name="source",
            field=models.CharField(
                blank=True, db_index=True, null=True, verbose_name="source"
            ),
        ),
        migrations.AlterField(
            model_name="calendarbucket",
            name="startdate",
            field=models.DateTimeField(
                blank=True,
                default=datetime.datetime(1971, 1, 1, 0, 0),
                null=True,
                verbose_name="start date",
            ),
        ),
        migrations.AlterField(
            model_name="calendarbucket",
            name="sunday",
            field=models.BooleanField(blank=True, default=True, verbose_name="Sunday"),
        ),
        migrations.AlterField(
            model_name="calendarbucket",
            name="thursday",
            field=models.BooleanField(
                blank=True, default=True, verbose_name="Thursday"
            ),
        ),
        migrations.AlterField(
            model_name="calendarbucket",
            name="tuesday",
            field=models.BooleanField(blank=True, default=True, verbose_name="Tuesday"),
        ),
        migrations.AlterField(
            model_name="calendarbucket",
            name="wednesday",
            field=models.BooleanField(
                blank=True, default=True, verbose_name="Wednesday"
            ),
        ),
        migrations.AlterField(
            model_name="customer",
            name="category",
            field=models.CharField(
                blank=True, db_index=True, null=True, verbose_name="category"
            ),
        ),
        migrations.AlterField(
            model_name="customer",
            name="description",
            field=models.CharField(blank=True, null=True, verbose_name="description"),
        ),
        migrations.AlterField(
            model_name="customer",
            name="name",
            field=models.CharField(
                help_text="Unique identifier",
                primary_key=True,
                serialize=False,
                verbose_name="name",
            ),
        ),
        migrations.AlterField(
            model_name="customer",
            name="source",
            field=models.CharField(
                blank=True, db_index=True, null=True, verbose_name="source"
            ),
        ),
        migrations.AlterField(
            model_name="customer",
            name="subcategory",
            field=models.CharField(
                blank=True, db_index=True, null=True, verbose_name="subcategory"
            ),
        ),
        migrations.AlterField(
            model_name="demand",
            name="batch",
            field=models.CharField(
                blank=True,
                db_index=True,
                help_text="MTO batch name",
                null=True,
                verbose_name="batch",
            ),
        ),
        migrations.AlterField(
            model_name="demand",
            name="category",
            field=models.CharField(
                blank=True, db_index=True, null=True, verbose_name="category"
            ),
        ),
        migrations.AlterField(
            model_name="demand",
            name="description",
            field=models.CharField(blank=True, null=True, verbose_name="description"),
        ),
        migrations.AlterField(
            model_name="demand",
            name="due",
            field=models.DateTimeField(
                db_index=True,
                help_text="Due date of the sales order",
                verbose_name="due",
            ),
        ),
        migrations.AlterField(
            model_name="demand",
            name="name",
            field=models.CharField(
                help_text="Unique identifier",
                primary_key=True,
                serialize=False,
                verbose_name="name",
            ),
        ),
        migrations.AlterField(
            model_name="demand",
            name="owner",
            field=models.CharField(
                blank=True, db_index=True, null=True, verbose_name="owner"
            ),
        ),
        migrations.AlterField(
            model_name="demand",
            name="plan",
            field=models.JSONField(blank=True, default=dict, editable=False, null=True),
        ),
        migrations.AlterField(
            model_name="demand",
            name="policy",
            field=models.CharField(
                blank=True,
                choices=[
                    ("independent", "independent"),
                    ("alltogether", "all together"),
                    ("inratio", "in ratio"),
                ],
                default="independent",
                help_text="Defines how sales orders are shipped together",
                null=True,
                verbose_name="policy",
            ),
        ),
        migrations.AlterField(
            model_name="demand",
            name="quantity",
            field=models.DecimalField(
                decimal_places=8, max_digits=20, verbose_name="quantity"
            ),
        ),
        migrations.AlterField(
            model_name="demand",
            name="source",
            field=models.CharField(
                blank=True, db_index=True, null=True, verbose_name="source"
            ),
        ),
        migrations.AlterField(
            model_name="demand",
            name="status",
            field=models.CharField(
                blank=True,
                choices=[
                    ("inquiry", "inquiry"),
                    ("quote", "quote"),
                    ("open", "open"),
                    ("closed", "closed"),
                    ("canceled", "canceled"),
                ],
                default="open",
                help_text='Status of the demand. Only "open" and "quote" demands are planned',
                null=True,
                verbose_name="status",
            ),
        ),
        migrations.AlterField(
            model_name="demand",
            name="subcategory",
            field=models.CharField(
                blank=True, db_index=True, null=True, verbose_name="subcategory"
            ),
        ),
        migrations.AlterField(
            model_name="item",
            name="category",
            field=models.CharField(
                blank=True, db_index=True, null=True, verbose_name="category"
            ),
        ),
        migrations.AlterField(
            model_name="item",
            name="description",
            field=models.CharField(blank=True, null=True, verbose_name="description"),
        ),
        migrations.AlterField(
            model_name="item",
            name="name",
            field=models.CharField(
                help_text="Unique identifier",
                primary_key=True,
                serialize=False,
                verbose_name="name",
            ),
        ),
        migrations.AlterField(
            model_name="item",
            name="periodofcover",
            field=models.IntegerField(
                blank=True,
                editable=False,
                help_text="Period of cover in days",
                null=True,
                verbose_name="period of cover",
            ),
        ),
        migrations.AlterField(
            model_name="item",
            name="source",
            field=models.CharField(
                blank=True, db_index=True, null=True, verbose_name="source"
            ),
        ),
        migrations.AlterField(
            model_name="item",
            name="subcategory",
            field=models.CharField(
                blank=True, db_index=True, null=True, verbose_name="subcategory"
            ),
        ),
        migrations.AlterField(
            model_name="item",
            name="type",
            field=models.CharField(
                blank=True,
                choices=[
                    ("make to stock", "make to stock"),
                    ("make to order", "make to order"),
                ],
                null=True,
                verbose_name="type",
            ),
        ),
        migrations.AlterField(
            model_name="item",
            name="uom",
            field=models.CharField(
                blank=True, null=True, verbose_name="unit of measure"
            ),
        ),
        migrations.AlterField(
            model_name="itemdistribution",
            name="effective_end",
            field=models.DateTimeField(
                blank=True,
                default=datetime.datetime(2030, 12, 31, 0, 0),
                help_text="Validity end date",
                null=True,
                verbose_name="effective end",
            ),
        ),
        migrations.AlterField(
            model_name="itemdistribution",
            name="effective_start",
            field=models.DateTimeField(
                blank=True,
                default=datetime.datetime(1971, 1, 1, 0, 0),
                help_text="Validity start date",
                null=True,
                verbose_name="effective start",
            ),
        ),
        migrations.AlterField(
            model_name="itemdistribution",
            name="leadtime",
            field=models.DurationField(
                blank=True,
                help_text="Transport lead time",
                null=True,
                verbose_name="lead time",
            ),
        ),
        migrations.AlterField(
            model_name="itemdistribution",
            name="origin",
            field=models.ForeignKey(
                help_text="Source location shipping the item",
                on_delete=django.db.models.deletion.CASCADE,
                related_name="itemdistributions_origin",
                to="input.location",
                verbose_name="origin",
            ),
        ),
        migrations.AlterField(
            model_name="itemdistribution",
            name="source",
            field=models.CharField(
                blank=True, db_index=True, null=True, verbose_name="source"
            ),
        ),
        migrations.AlterField(
            model_name="itemsupplier",
            name="effective_end",
            field=models.DateTimeField(
                blank=True,
                default=datetime.datetime(2030, 12, 31, 0, 0),
                help_text="Validity end date",
                null=True,
                verbose_name="effective end",
            ),
        ),
        migrations.AlterField(
            model_name="itemsupplier",
            name="effective_start",
            field=models.DateTimeField(
                blank=True,
                default=datetime.datetime(1971, 1, 1, 0, 0),
                help_text="Validity start date",
                null=True,
                verbose_name="effective start",
            ),
        ),
        migrations.AlterField(
            model_name="itemsupplier",
            name="extra_safety_leadtime",
            field=models.DurationField(
                blank=True,
                help_text="soft safety lead time",
                null=True,
                verbose_name="soft safety lead time",
            ),
        ),
        migrations.AlterField(
            model_name="itemsupplier",
            name="source",
            field=models.CharField(
                blank=True, db_index=True, null=True, verbose_name="source"
            ),
        ),
        migrations.AlterField(
            model_name="location",
            name="category",
            field=models.CharField(
                blank=True, db_index=True, null=True, verbose_name="category"
            ),
        ),
        migrations.AlterField(
            model_name="location",
            name="description",
            field=models.CharField(blank=True, null=True, verbose_name="description"),
        ),
        migrations.AlterField(
            model_name="location",
            name="name",
            field=models.CharField(
                help_text="Unique identifier",
                primary_key=True,
                serialize=False,
                verbose_name="name",
            ),
        ),
        migrations.AlterField(
            model_name="location",
            name="source",
            field=models.CharField(
                blank=True, db_index=True, null=True, verbose_name="source"
            ),
        ),
        migrations.AlterField(
            model_name="location",
            name="subcategory",
            field=models.CharField(
                blank=True, db_index=True, null=True, verbose_name="subcategory"
            ),
        ),
        migrations.AlterField(
            model_name="operation",
            name="category",
            field=models.CharField(
                blank=True, db_index=True, null=True, verbose_name="category"
            ),
        ),
        migrations.AlterField(
            model_name="operation",
            name="cost",
            field=models.DecimalField(
                blank=True,
                decimal_places=8,
                help_text="Cost per produced unit",
                max_digits=20,
                null=True,
                verbose_name="cost",
            ),
        ),
        migrations.AlterField(
            model_name="operation",
            name="description",
            field=models.CharField(blank=True, null=True, verbose_name="description"),
        ),
        migrations.AlterField(
            model_name="operation",
            name="duration",
            field=models.DurationField(
                blank=True,
                help_text="Fixed production time for setup and overhead",
                null=True,
                verbose_name="duration",
            ),
        ),
        migrations.AlterField(
            model_name="operation",
            name="duration_per",
            field=models.DurationField(
                blank=True,
                help_text="Production time per produced piece",
                null=True,
                verbose_name="duration per unit",
            ),
        ),
        migrations.AlterField(
            model_name="operation",
            name="item",
            field=models.ForeignKey(
                blank=True,
                help_text="Item produced by this operation",
                null=True,
                on_delete=django.db.models.deletion.CASCADE,
                related_name="operations",
                to="input.item",
                verbose_name="item",
            ),
        ),
        migrations.AlterField(
            model_name="operation",
            name="name",
            field=models.CharField(
                primary_key=True, serialize=False, verbose_name="name"
            ),
        ),
        migrations.AlterField(
            model_name="operation",
            name="owner",
            field=models.ForeignKey(
                blank=True,
                help_text="Parent operation (which must be of type routing, alternate or split)",
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name="childoperations",
                to="input.operation",
                verbose_name="owner",
            ),
        ),
        migrations.AlterField(
            model_name="operation",
            name="search",
            field=models.CharField(
                blank=True,
                help_text="Method to select preferred alternate",
                null=True,
                verbose_name="search mode",
            ),
        ),
        migrations.AlterField(
            model_name="operation",
            name="sizemaximum",
            field=models.DecimalField(
                blank=True,
                decimal_places=8,
                help_text="Maximum production quantity",
                max_digits=20,
                null=True,
                verbose_name="size maximum",
            ),
        ),
        migrations.AlterField(
            model_name="operation",
            name="sizeminimum",
            field=models.DecimalField(
                blank=True,
                decimal_places=8,
                default="1.0",
                help_text="Minimum production quantity",
                max_digits=20,
                null=True,
                verbose_name="size minimum",
            ),
        ),
        migrations.AlterField(
            model_name="operation",
            name="sizemultiple",
            field=models.DecimalField(
                blank=True,
                decimal_places=8,
                help_text="Multiple production quantity",
                max_digits=20,
                null=True,
                verbose_name="size multiple",
            ),
        ),
        migrations.AlterField(
            model_name="operation",
            name="source",
            field=models.CharField(
                blank=True, db_index=True, null=True, verbose_name="source"
            ),
        ),
        migrations.AlterField(
            model_name="operation",
            name="subcategory",
            field=models.CharField(
                blank=True, db_index=True, null=True, verbose_name="subcategory"
            ),
        ),
        migrations.AlterField(
            model_name="operation",
            name="type",
            field=models.CharField(
                blank=True, default="fixed_time", null=True, verbose_name="type"
            ),
        ),
        migrations.AlterField(
            model_name="operationdependency",
            name="blockedby",
            field=models.ForeignKey(
                help_text="blocked by operation",
                on_delete=django.db.models.deletion.CASCADE,
                related_name="dependents",
                to="input.operation",
                verbose_name="blocked by operation",
            ),
        ),
        migrations.AlterField(
            model_name="operationdependency",
            name="operation",
            field=models.ForeignKey(
                help_text="operation",
                on_delete=django.db.models.deletion.CASCADE,
                related_name="dependencies",
                to="input.operation",
                verbose_name="operation",
            ),
        ),
        migrations.AlterField(
            model_name="operationdependency",
            name="source",
            field=models.CharField(
                blank=True, db_index=True, null=True, verbose_name="source"
            ),
        ),
        migrations.AlterField(
            model_name="operationmaterial",
            name="effective_end",
            field=models.DateTimeField(
                blank=True,
                default=datetime.datetime(2030, 12, 31, 0, 0),
                help_text="Validity end date",
                null=True,
                verbose_name="effective end",
            ),
        ),
        migrations.AlterField(
            model_name="operationmaterial",
            name="effective_start",
            field=models.DateTimeField(
                blank=True,
                default=datetime.datetime(1971, 1, 1, 0, 0),
                help_text="Validity start date",
                null=True,
                verbose_name="effective start",
            ),
        ),
        migrations.AlterField(
            model_name="operationmaterial",
            name="name",
            field=models.CharField(
                blank=True,
                help_text="Name of this operation material to identify alternates",
                null=True,
                verbose_name="name",
            ),
        ),
        migrations.AlterField(
            model_name="operationmaterial",
            name="quantity",
            field=models.DecimalField(
                blank=True,
                decimal_places=8,
                default="1.00",
                help_text="Quantity to consume or produce per piece",
                max_digits=20,
                null=True,
                verbose_name="quantity",
            ),
        ),
        migrations.AlterField(
            model_name="operationmaterial",
            name="search",
            field=models.CharField(
                blank=True,
                help_text="Method to select preferred alternate",
                null=True,
                verbose_name="search mode",
            ),
        ),
        migrations.AlterField(
            model_name="operationmaterial",
            name="source",
            field=models.CharField(
                blank=True, db_index=True, null=True, verbose_name="source"
            ),
        ),
        migrations.AlterField(
            model_name="operationmaterial",
            name="type",
            field=models.CharField(
                blank=True,
                default="start",
                help_text="Consume/produce material at the start or the end of the operationplan",
                null=True,
                verbose_name="type",
            ),
        ),
        migrations.AlterField(
            model_name="operationplan",
            name="batch",
            field=models.CharField(
                blank=True,
                db_index=True,
                help_text="MTO batch name",
                null=True,
                verbose_name="batch",
            ),
        ),
        migrations.AlterField(
            model_name="operationplan",
            name="name",
            field=models.CharField(
                blank=True, db_index=True, null=True, verbose_name="name"
            ),
        ),
        migrations.AlterField(
            model_name="operationplan",
            name="plan",
            field=models.JSONField(blank=True, default=dict, editable=False, null=True),
        ),
        migrations.AlterField(
            model_name="operationplan",
            name="quantity_completed",
            field=models.DecimalField(
                blank=True,
                decimal_places=8,
                max_digits=20,
                null=True,
                verbose_name="completed quantity",
            ),
        ),
        migrations.AlterField(
            model_name="operationplan",
            name="reference",
            field=models.CharField(
                help_text="Unique identifier",
                primary_key=True,
                serialize=False,
                verbose_name="reference",
            ),
        ),
        migrations.AlterField(
            model_name="operationplan",
            name="remark",
            field=models.CharField(
                blank=True, help_text="remark", null=True, verbose_name="remark"
            ),
        ),
        migrations.AlterField(
            model_name="operationplan",
            name="source",
            field=models.CharField(
                blank=True, db_index=True, null=True, verbose_name="source"
            ),
        ),
        migrations.AlterField(
            model_name="operationplan",
            name="status",
            field=models.CharField(
                blank=True,
                help_text="Status of the order",
                null=True,
                verbose_name="status",
            ),
        ),
        migrations.AlterField(
            model_name="operationplan",
            name="type",
            field=models.CharField(
                db_index=True, default="MO", help_text="Order type", verbose_name="type"
            ),
        ),
        migrations.AlterField(
            model_name="operationplanmaterial",
            name="id",
            field=models.AutoField(
                primary_key=True, serialize=False, verbose_name="identifier"
            ),
        ),
        migrations.AlterField(
            model_name="operationplanmaterial",
            name="item",
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.CASCADE,
                related_name="operationplanmaterials",
                to="input.item",
                verbose_name="item",
            ),
        ),
        migrations.AlterField(
            model_name="operationplanmaterial",
            name="location",
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.CASCADE,
                related_name="operationplanmaterials",
                to="input.location",
                verbose_name="location",
            ),
        ),
        migrations.AlterField(
            model_name="operationplanmaterial",
            name="operationplan",
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.CASCADE,
                related_name="materials",
                to="input.operationplan",
                verbose_name="reference",
            ),
        ),
        migrations.AlterField(
            model_name="operationplanmaterial",
            name="source",
            field=models.CharField(
                blank=True, db_index=True, null=True, verbose_name="source"
            ),
        ),
        migrations.AlterField(
            model_name="operationplanmaterial",
            name="status",
            field=models.CharField(
                blank=True,
                choices=[
                    ("proposed", "proposed"),
                    ("confirmed", "confirmed"),
                    ("closed", "closed"),
                ],
                help_text="status of the material production or consumption",
                null=True,
                verbose_name="material status",
            ),
        ),
        migrations.AlterField(
            model_name="operationplanresource",
            name="id",
            field=models.AutoField(
                primary_key=True, serialize=False, verbose_name="identifier"
            ),
        ),
        migrations.AlterField(
            model_name="operationplanresource",
            name="operationplan",
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.CASCADE,
                related_name="resources",
                to="input.operationplan",
                verbose_name="reference",
            ),
        ),
        migrations.AlterField(
            model_name="operationplanresource",
            name="quantity",
            field=models.DecimalField(
                blank=True,
                decimal_places=8,
                default=1.0,
                max_digits=20,
                null=True,
                verbose_name="quantity",
            ),
        ),
        migrations.AlterField(
            model_name="operationplanresource",
            name="setup",
            field=models.CharField(blank=True, null=True, verbose_name="setup"),
        ),
        migrations.AlterField(
            model_name="operationplanresource",
            name="source",
            field=models.CharField(
                blank=True, db_index=True, null=True, verbose_name="source"
            ),
        ),
        migrations.AlterField(
            model_name="operationplanresource",
            name="status",
            field=models.CharField(
                blank=True,
                help_text="Status of the resource assignment",
                null=True,
                verbose_name="load status",
            ),
        ),
        migrations.AlterField(
            model_name="operationresource",
            name="effective_end",
            field=models.DateTimeField(
                blank=True,
                default=datetime.datetime(2030, 12, 31, 0, 0),
                help_text="Validity end date",
                null=True,
                verbose_name="effective end",
            ),
        ),
        migrations.AlterField(
            model_name="operationresource",
            name="effective_start",
            field=models.DateTimeField(
                blank=True,
                default=datetime.datetime(1971, 1, 1, 0, 0),
                help_text="Validity start date",
                null=True,
                verbose_name="effective start",
            ),
        ),
        migrations.AlterField(
            model_name="operationresource",
            name="name",
            field=models.CharField(
                blank=True,
                help_text="Name of this operation resource to identify alternates",
                null=True,
                verbose_name="name",
            ),
        ),
        migrations.AlterField(
            model_name="operationresource",
            name="priority",
            field=models.IntegerField(
                blank=True,
                default=1,
                help_text="Priority of this operation resource in a group of alternates",
                null=True,
                verbose_name="priority",
            ),
        ),
        migrations.AlterField(
            model_name="operationresource",
            name="quantity_fixed",
            field=models.DecimalField(
                blank=True,
                decimal_places=8,
                help_text="Constant part of the capacity consumption (bucketized resources only)",
                max_digits=20,
                null=True,
                verbose_name="quantity fixed",
            ),
        ),
        migrations.AlterField(
            model_name="operationresource",
            name="search",
            field=models.CharField(
                blank=True,
                help_text="Method to select preferred alternate",
                null=True,
                verbose_name="search mode",
            ),
        ),
        migrations.AlterField(
            model_name="operationresource",
            name="setup",
            field=models.CharField(
                blank=True,
                help_text="Setup required on the resource for this operation",
                null=True,
                verbose_name="setup",
            ),
        ),
        migrations.AlterField(
            model_name="operationresource",
            name="skill",
            field=models.ForeignKey(
                blank=True,
                help_text="Required skill to perform the operation",
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name="operationresources",
                to="input.skill",
                verbose_name="skill",
            ),
        ),
        migrations.AlterField(
            model_name="operationresource",
            name="source",
            field=models.CharField(
                blank=True, db_index=True, null=True, verbose_name="source"
            ),
        ),
        migrations.AlterField(
            model_name="resource",
            name="category",
            field=models.CharField(
                blank=True, db_index=True, null=True, verbose_name="category"
            ),
        ),
        migrations.AlterField(
            model_name="resource",
            name="constrained",
            field=models.BooleanField(
                blank=True,
                help_text="controls whether or not this resource is planned in finite capacity mode",
                null=True,
                verbose_name="constrained",
            ),
        ),
        migrations.AlterField(
            model_name="resource",
            name="description",
            field=models.CharField(blank=True, null=True, verbose_name="description"),
        ),
        migrations.AlterField(
            model_name="resource",
            name="name",
            field=models.CharField(
                help_text="Unique identifier",
                primary_key=True,
                serialize=False,
                verbose_name="name",
            ),
        ),
        migrations.AlterField(
            model_name="resource",
            name="setup",
            field=models.CharField(
                blank=True,
                help_text="Setup of the resource at the start of the plan",
                null=True,
                verbose_name="setup",
            ),
        ),
        migrations.AlterField(
            model_name="resource",
            name="setupmatrix",
            field=models.ForeignKey(
                blank=True,
                help_text="Setup matrix defining the conversion time and cost",
                null=True,
                on_delete=django.db.models.deletion.CASCADE,
                to="input.setupmatrix",
                verbose_name="setup matrix",
            ),
        ),
        migrations.AlterField(
            model_name="resource",
            name="source",
            field=models.CharField(
                blank=True, db_index=True, null=True, verbose_name="source"
            ),
        ),
        migrations.AlterField(
            model_name="resource",
            name="subcategory",
            field=models.CharField(
                blank=True, db_index=True, null=True, verbose_name="subcategory"
            ),
        ),
        migrations.AlterField(
            model_name="resource",
            name="type",
            field=models.CharField(
                blank=True,
                choices=[
                    ("default", "default"),
                    ("buckets", "buckets"),
                    ("buckets_day", "buckets_day"),
                    ("buckets_week", "buckets_week"),
                    ("buckets_month", "buckets_month"),
                    ("infinite", "infinite"),
                ],
                default="default",
                null=True,
                verbose_name="type",
            ),
        ),
        migrations.AlterField(
            model_name="resourceskill",
            name="source",
            field=models.CharField(
                blank=True, db_index=True, null=True, verbose_name="source"
            ),
        ),
        migrations.AlterField(
            model_name="setupmatrix",
            name="name",
            field=models.CharField(
                primary_key=True, serialize=False, verbose_name="name"
            ),
        ),
        migrations.AlterField(
            model_name="setupmatrix",
            name="source",
            field=models.CharField(
                blank=True, db_index=True, null=True, verbose_name="source"
            ),
        ),
        migrations.AlterField(
            model_name="setuprule",
            name="fromsetup",
            field=models.CharField(
                blank=True,
                help_text="Name of the old setup (wildcard characters are supported)",
                null=True,
                verbose_name="from setup",
            ),
        ),
        migrations.AlterField(
            model_name="setuprule",
            name="id",
            field=models.AutoField(
                primary_key=True, serialize=False, verbose_name="identifier"
            ),
        ),
        migrations.AlterField(
            model_name="setuprule",
            name="source",
            field=models.CharField(
                blank=True, db_index=True, null=True, verbose_name="source"
            ),
        ),
        migrations.AlterField(
            model_name="setuprule",
            name="tosetup",
            field=models.CharField(
                blank=True,
                help_text="Name of the new setup (wildcard characters are supported)",
                null=True,
                verbose_name="to setup",
            ),
        ),
        migrations.AlterField(
            model_name="skill",
            name="name",
            field=models.CharField(
                help_text="Unique identifier",
                primary_key=True,
                serialize=False,
                verbose_name="name",
            ),
        ),
        migrations.AlterField(
            model_name="skill",
            name="source",
            field=models.CharField(
                blank=True, db_index=True, null=True, verbose_name="source"
            ),
        ),
        migrations.AlterField(
            model_name="suboperation",
            name="effective_end",
            field=models.DateTimeField(
                blank=True,
                default=datetime.datetime(2030, 12, 31, 0, 0),
                help_text="Validity end date",
                null=True,
                verbose_name="effective end",
            ),
        ),
        migrations.AlterField(
            model_name="suboperation",
            name="effective_start",
            field=models.DateTimeField(
                blank=True,
                default=datetime.datetime(1971, 1, 1, 0, 0),
                help_text="Validity start date",
                null=True,
                verbose_name="effective start",
            ),
        ),
        migrations.AlterField(
            model_name="suboperation",
            name="source",
            field=models.CharField(
                blank=True, db_index=True, null=True, verbose_name="source"
            ),
        ),
        migrations.AlterField(
            model_name="supplier",
            name="category",
            field=models.CharField(
                blank=True, db_index=True, null=True, verbose_name="category"
            ),
        ),
        migrations.AlterField(
            model_name="supplier",
            name="description",
            field=models.CharField(blank=True, null=True, verbose_name="description"),
        ),
        migrations.AlterField(
            model_name="supplier",
            name="name",
            field=models.CharField(
                help_text="Unique identifier",
                primary_key=True,
                serialize=False,
                verbose_name="name",
            ),
        ),
        migrations.AlterField(
            model_name="supplier",
            name="source",
            field=models.CharField(
                blank=True, db_index=True, null=True, verbose_name="source"
            ),
        ),
        migrations.AlterField(
            model_name="supplier",
            name="subcategory",
            field=models.CharField(
                blank=True, db_index=True, null=True, verbose_name="subcategory"
            ),
        ),
        migrations.RunPython(
            code=recreateConstraintsCascade,
            reverse_code=migrations.RunPython.noop,
        ),
        migrations.RunSQL(
            sql="\n            insert into common_parameter (name, value, lastmodified, description)\n            values (\n              'plan.move_approved_early', '0', now(),\n              'Controls rescheduling approved orders early. Values: 0 (inactive, default), 1 (active preserving existing resource assignments, 2 (active replanning resource assignments)'\n              )\n            on conflict (name) do nothing\n            ",
            reverse_sql="\n            delete from common_parameter where name = 'plan.move_approved_early'\n            ",
        ),
        migrations.RunSQL(
            sql="\n            update operationplan set type = 'WO'\n            where type = 'MO' and exists\n            (select 1 from operation inner join operationplan opplan on opplan.operation_id = operation.name where operation.type = 'routing' and opplan.reference = operationplan.owner_id)\n            ",
            reverse_sql="\n            update operationplan set type = 'MO' where type = 'WO'\n            ",
        ),
        migrations.CreateModel(
            name="WorkOrder",
            fields=[],
            options={
                "verbose_name": "work order",
                "verbose_name_plural": "work orders",
                "proxy": True,
                "indexes": [],
                "constraints": [],
            },
            bases=("input.operationplan",),
        ),
        migrations.AlterField(
            model_name="operationplan",
            name="type",
            field=models.CharField(
                choices=[
                    ("STCK", "inventory"),
                    ("MO", "manufacturing order"),
                    ("WO", "work order"),
                    ("PO", "purchase order"),
                    ("DO", "distribution order"),
                    ("DLVR", "delivery order"),
                ],
                db_index=True,
                default="MO",
                help_text="Order type",
                verbose_name="type",
            ),
        ),
        migrations.AddField(
            model_name="operation",
            name="batchwindow",
            field=models.DurationField(
                blank=True,
                help_text="The solver algorithm will scan for opportunities to create batches within this time window before and after the requirement date",
                null=True,
                verbose_name="batching window",
            ),
        ),
        migrations.RunSQL(
            sql="\n            insert into common_parameter (name, value, lastmodified, description)\n            values (\n              'pathreport_optimization', 'false', now(),\n              'Activates a fast version of the supply path report, suitable for deep bill of materials with many components. Default: false.'\n              )\n            on conflict (name) do nothing\n            ",
            reverse_sql="\n            delete from common_parameter where name = 'pathreport_optimization'\n            ",
        ),
        migrations.RunSQL(
            sql="\n            insert into common_parameter (name, value, lastmodified, description)\n            values (\n              'plan.solver', 'heuristic', now(),\n              'Selects the algorithm to use for generating the plan. Possible choices are \"heuristic\" (default), \"heuristic_2\" (an emerging evolution of the heuristic algorithm).'\n              )\n            on conflict (name) do nothing\n            ",
            reverse_sql="\n            delete from common_parameter where name = 'plan.solver'\n            ",
        ),
        migrations.RemoveField(
            model_name="operationplanmaterial",
            name="status",
        ),
        migrations.RemoveField(
            model_name="operationplanresource",
            name="status",
        ),
        migrations.RemoveField(
            model_name="supplier",
            name="lft",
        ),
        migrations.RemoveField(
            model_name="supplier",
            name="lvl",
        ),
        migrations.RemoveField(
            model_name="supplier",
            name="owner",
        ),
        migrations.RemoveField(
            model_name="supplier",
            name="rght",
        ),
        migrations.RemoveField(
            model_name="operationmaterial",
            name="transferbatch",
        ),
        migrations.DeleteModel(
            name="SubOperation",
        ),
        migrations.RunSQL(
            sql="ALTER TABLE calendarbucket ALTER COLUMN enddate SET DEFAULT '2100-12-31'::timestamp",
            reverse_sql="ALTER TABLE calendarbucket ALTER COLUMN enddate SET DEFAULT '2030-12-31'::timestamp",
        ),
    ]
