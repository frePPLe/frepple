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
from django.core.management import call_command
from django.db import connections, migrations, models
import django.db.models.deletion


def loadParameters(apps, schema_editor):
    from django.core.management.commands.loaddata import Command

    call_command(
        Command(),
        "parameters.json",
        app_label="archive",
        verbosity=0,
        database=schema_editor.connection.alias,
    )


def removeParameters(apps, schema_editor):
    db = schema_editor.connection.alias
    with connections[db].cursor() as cursor:
        cursor.execute("delete from common_parameter where name like 'archive.%'")


def remove_permissions(apps, _unused):
    Permission = apps.get_model("auth.Permission")
    Permission.objects.filter(codename__contains="archive").delete()


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
            for table in ["ax_demand", "ax_buffer", "ax_operationplan"]:
                cursor.execute("grant select on table %s to %s" % (table, role))


class Migration(migrations.Migration):

    replaces = [
        ("archive", "0001_initial"),
        ("archive", "0002_cascade_delete"),
        ("archive", "0003_permissions"),
        ("archive", "0004_truncate_archive"),
        ("archive", "0005_grant_read"),
        ("archive", "0006_archive_duration"),
        ("archive", "0007_varchar_max_length"),
        ("archive", "0008_alter_indexes"),
    ]

    dependencies = [("common", "0045_squash_100"), ("input", "0087_squash_100")]

    operations = [
        migrations.RunPython(
            code=loadParameters,
            reverse_code=removeParameters,
        ),
        migrations.CreateModel(
            name="ArchiveManager",
            fields=[
                (
                    "snapshot_date",
                    models.DateTimeField(
                        db_index=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="snapshot date",
                    ),
                ),
                ("total_records", models.IntegerField(verbose_name="total_records")),
                ("buffer_records", models.IntegerField(verbose_name="buffer_records")),
                ("demand_records", models.IntegerField(verbose_name="demand_records")),
                (
                    "operationplan_records",
                    models.IntegerField(verbose_name="operationplan_records"),
                ),
            ],
            options={
                "verbose_name": "archive manager",
                "verbose_name_plural": "archive managers",
                "db_table": "ax_manager",
                "ordering": ["snapshot_date"],
            },
        ),
        migrations.CreateModel(
            name="ArchivedBuffer",
            fields=[
                (
                    "id",
                    models.AutoField(
                        primary_key=True, serialize=False, verbose_name="identifier"
                    ),
                ),
                (
                    "snapshot_date",
                    models.ForeignKey(
                        db_constraint=False,
                        on_delete=django.db.models.deletion.CASCADE,
                        to="archive.archivemanager",
                        verbose_name="snapshot date",
                    ),
                ),
                (
                    "item",
                    models.CharField(verbose_name="item"),
                ),
                (
                    "location",
                    models.CharField(verbose_name="location"),
                ),
                (
                    "batch",
                    models.CharField(blank=True, null=True, verbose_name="batch"),
                ),
                (
                    "cost",
                    models.DecimalField(
                        blank=True,
                        decimal_places=8,
                        max_digits=20,
                        null=True,
                        verbose_name="cost",
                    ),
                ),
                (
                    "onhand",
                    models.DecimalField(
                        blank=True,
                        decimal_places=8,
                        max_digits=20,
                        null=True,
                        verbose_name="onhand",
                    ),
                ),
                (
                    "safetystock",
                    models.DecimalField(
                        blank=True,
                        decimal_places=8,
                        max_digits=20,
                        null=True,
                        verbose_name="safety stock",
                    ),
                ),
            ],
            options={
                "verbose_name": "archived buffer",
                "verbose_name_plural": "archived buffers",
                "db_table": "ax_buffer",
                "ordering": ["item", "location", "batch"],
            },
        ),
        migrations.CreateModel(
            name="ArchivedDemand",
            fields=[
                (
                    "id",
                    models.AutoField(
                        primary_key=True, serialize=False, verbose_name="identifier"
                    ),
                ),
                (
                    "snapshot_date",
                    models.ForeignKey(
                        db_constraint=False,
                        on_delete=django.db.models.deletion.CASCADE,
                        to="archive.archivemanager",
                        verbose_name="snapshot date",
                    ),
                ),
                ("name", models.CharField(verbose_name="name")),
                (
                    "item",
                    models.CharField(verbose_name="item"),
                ),
                (
                    "cost",
                    models.DecimalField(
                        blank=True,
                        decimal_places=8,
                        max_digits=20,
                        null=True,
                        verbose_name="cost",
                    ),
                ),
                (
                    "location",
                    models.CharField(verbose_name="location"),
                ),
                (
                    "customer",
                    models.CharField(verbose_name="customer"),
                ),
                ("due", models.DateTimeField(verbose_name="due")),
                (
                    "status",
                    models.CharField(blank=True, null=True, verbose_name="status"),
                ),
                ("priority", models.IntegerField(verbose_name="priority")),
                (
                    "quantity",
                    models.DecimalField(
                        decimal_places=8, max_digits=20, verbose_name="quantity"
                    ),
                ),
                (
                    "deliverydate",
                    models.DateTimeField(
                        blank=True, null=True, verbose_name="delivery date"
                    ),
                ),
                (
                    "quantityplanned",
                    models.DecimalField(
                        blank=True,
                        decimal_places=8,
                        max_digits=20,
                        null=True,
                        verbose_name="planned quantity",
                    ),
                ),
            ],
            options={
                "verbose_name": "archived sales order",
                "verbose_name_plural": "archived sales orders",
                "db_table": "ax_demand",
                "ordering": ["priority", "due"],
            },
        ),
        migrations.CreateModel(
            name="ArchivedOperationPlan",
            fields=[
                (
                    "id",
                    models.AutoField(
                        primary_key=True, serialize=False, verbose_name="identifier"
                    ),
                ),
                (
                    "snapshot_date",
                    models.ForeignKey(
                        db_constraint=False,
                        on_delete=django.db.models.deletion.CASCADE,
                        to="archive.archivemanager",
                        verbose_name="snapshot date",
                    ),
                ),
                (
                    "reference",
                    models.CharField(verbose_name="reference"),
                ),
                (
                    "status",
                    models.CharField(blank=True, null=True, verbose_name="status"),
                ),
                (
                    "type",
                    models.CharField(verbose_name="type"),
                ),
                (
                    "quantity",
                    models.DecimalField(
                        decimal_places=8, max_digits=20, verbose_name="quantity"
                    ),
                ),
                (
                    "startdate",
                    models.DateTimeField(
                        blank=True,
                        help_text="start date",
                        null=True,
                        verbose_name="start date",
                    ),
                ),
                (
                    "enddate",
                    models.DateTimeField(
                        blank=True,
                        help_text="end date",
                        null=True,
                        verbose_name="end date",
                    ),
                ),
                (
                    "operation",
                    models.CharField(blank=True, null=True, verbose_name="operation"),
                ),
                (
                    "owner",
                    models.CharField(blank=True, null=True, verbose_name="owner"),
                ),
                (
                    "batch",
                    models.CharField(blank=True, null=True, verbose_name="batch"),
                ),
                (
                    "item",
                    models.CharField(verbose_name="item"),
                ),
                (
                    "item_cost",
                    models.DecimalField(
                        blank=True,
                        decimal_places=8,
                        max_digits=20,
                        null=True,
                        verbose_name="item cost",
                    ),
                ),
                (
                    "itemsupplier_cost",
                    models.DecimalField(
                        blank=True,
                        decimal_places=8,
                        max_digits=20,
                        null=True,
                        verbose_name="itemsupplier cost",
                    ),
                ),
                (
                    "origin",
                    models.CharField(blank=True, null=True, verbose_name="origin"),
                ),
                (
                    "destination",
                    models.CharField(
                        blank=True,
                        null=True,
                        verbose_name="destination",
                    ),
                ),
                (
                    "supplier",
                    models.CharField(blank=True, null=True, verbose_name="supplier"),
                ),
                (
                    "location",
                    models.CharField(blank=True, null=True, verbose_name="location"),
                ),
                (
                    "demand",
                    models.CharField(blank=True, null=True, verbose_name="demand"),
                ),
                (
                    "due",
                    models.DateTimeField(blank=True, null=True, verbose_name="due"),
                ),
                (
                    "name",
                    models.CharField(blank=True, null=True, verbose_name="name"),
                ),
            ],
            options={
                "verbose_name": "operationplan",
                "verbose_name_plural": "operationplans",
                "db_table": "ax_operationplan",
                "ordering": ["reference"],
            },
        ),
        migrations.AlterModelOptions(
            name="archivedbuffer",
            options={
                "default_permissions": (),
                "ordering": ["item", "location", "batch"],
                "verbose_name": "archived buffer",
                "verbose_name_plural": "archived buffers",
            },
        ),
        migrations.AlterModelOptions(
            name="archiveddemand",
            options={
                "default_permissions": (),
                "ordering": ["priority", "due"],
                "verbose_name": "archived sales order",
                "verbose_name_plural": "archived sales orders",
            },
        ),
        migrations.AlterModelOptions(
            name="archivedoperationplan",
            options={
                "default_permissions": (),
                "ordering": ["reference"],
                "verbose_name": "operationplan",
                "verbose_name_plural": "operationplans",
            },
        ),
        migrations.AlterModelOptions(
            name="archivemanager",
            options={
                "default_permissions": (),
                "ordering": ["snapshot_date"],
                "verbose_name": "archive manager",
                "verbose_name_plural": "archive managers",
            },
        ),
        migrations.RunPython(code=remove_permissions),
        migrations.RunPython(code=grant_read_access),
        migrations.RunSQL(sql="""
            alter table ax_demand
            add constraint ax_demand_snapshot_date_id_fkey
            foreign key (snapshot_date_id) references ax_manager (snapshot_date)
            on delete cascade deferrable initially deferred;

            alter table ax_buffer
            add constraint ax_buffer_snapshot_date_id_fkey
            foreign key (snapshot_date_id) references ax_manager (snapshot_date)
            on delete cascade deferrable initially deferred;

            alter table ax_operationplan
            add constraint ax_operationplan_snapshot_date_id_fkey
            foreign key (snapshot_date_id) references ax_manager (snapshot_date)
            on delete cascade deferrable initially deferred;
            """),
        migrations.AddIndex(
            model_name="archivedbuffer",
            index=models.Index(fields=["item"], name="ax_buffer_item_idx"),
        ),
        migrations.AddIndex(
            model_name="archivedbuffer",
            index=models.Index(fields=["location"], name="ax_buffer_location_idx"),
        ),
        migrations.AddIndex(
            model_name="archiveddemand",
            index=models.Index(fields=["customer"], name="ax_demand_customer_idx"),
        ),
        migrations.AddIndex(
            model_name="archiveddemand",
            index=models.Index(fields=["item"], name="ax_demand_item_idx"),
        ),
        migrations.AddIndex(
            model_name="archiveddemand",
            index=models.Index(fields=["location"], name="ax_demand_location_idx"),
        ),
        migrations.AddIndex(
            model_name="archivedoperationplan",
            index=models.Index(
                fields=["destination"], name="ax_opplan_destination_idx"
            ),
        ),
        migrations.AddIndex(
            model_name="archivedoperationplan",
            index=models.Index(fields=["item"], name="ax_opplan_item_idx"),
        ),
        migrations.AddIndex(
            model_name="archivedoperationplan",
            index=models.Index(fields=["type"], name="ax_opplan_type_idx"),
        ),
        migrations.AddIndex(
            model_name="archivedoperationplan",
            index=models.Index(fields=["name"], name="ax_opplan_name_idx"),
        ),
    ]
