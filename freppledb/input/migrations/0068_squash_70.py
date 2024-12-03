#
# Copyright (C) 2022 by frePPLe bv
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

import datetime

from django.conf import settings
from django.db import migrations, models, connections
import django.db.models.deletion
import django.utils.timezone


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
        cursor.execute(
            """
            alter table operationplanresource
            ADD FOREIGN KEY (operationplan_id)
            REFERENCES public.operationplan (reference) MATCH SIMPLE
            ON UPDATE NO ACTION
            ON DELETE CASCADE
            DEFERRABLE INITIALLY DEFERRED
            """
        )
        cursor.execute(
            """
            alter table operationplanmaterial
                ADD FOREIGN KEY (operationplan_id)
                REFERENCES public.operationplan (reference) MATCH SIMPLE
                ON UPDATE NO ACTION
                ON DELETE CASCADE
                DEFERRABLE INITIALLY DEFERRED
            """
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
            for table in [
                "calendar",
                "calendarbucket",
                "item",
                "location",
                "customer",
                "item",
                "operation",
                "suboperation",
                "buffer",
                "setupmatrix",
                "setuprule",
                "resource",
                "skill",
                "resourceskill",
                "operationmaterial",
                "operationresource",
                "supplier",
                "itemsupplier",
                "itemdistribution",
                "demand",
                "operationplan",
                "operationplanmaterial",
                "operationplanresource",
            ]:
                cursor.execute("grant select on table %s to %s" % (table, role))


def dropIndexLike(apps, schema_editor):
    db = schema_editor.connection.alias
    output = []
    with connections[db].cursor() as cursor:
        cursor.execute(
            """
            with cte as (
            select
            t.relname as table_name,
            i.relname as index_name,
            array_to_string(array_agg(a.attname), ', ') as column_names
            from
            pg_class t,
            pg_class i,
            pg_index ix,
            pg_attribute a
            where
            t.oid = ix.indrelid
            and i.oid = ix.indexrelid
            and a.attrelid = t.oid
            and a.attnum = ANY(ix.indkey)
            and t.relkind = 'r'
            and i.relname like '%like'
            group by
            t.relname,
            i.relname
            )
            select cte.index_name
            from information_schema.table_constraints tco
            inner join information_schema.key_column_usage kcu
              on tco.constraint_schema = kcu.constraint_schema
              and tco.constraint_name = kcu.constraint_name
            inner join cte
              on cte.table_name = kcu.table_name
              and cte.column_names = kcu.column_name
            inner join information_schema.referential_constraints rco
              on tco.constraint_schema = rco.constraint_schema
              and tco.constraint_name = rco.constraint_name
            inner join information_schema.table_constraints rel_tco
              on tco.constraint_schema = rel_tco.constraint_schema
              and tco.constraint_name = rel_tco.constraint_name
            where tco.constraint_type = 'FOREIGN KEY'
            and kcu.table_name in ('buffer', 'calendarbucket', 'customer', 'demand', 'item',
                                'itemdistribution', 'itemsupplier', 'location', 'operation',
                                'operationmaterial', 'operationplan', 'operationplanmaterial',
                                'operationplanresource', 'operationresource', 'resource', 'resourceskill',
                                'setuprule', 'suboperation', 'supplier' )
            group by
            kcu.table_name,
            kcu.column_name,
            cte.index_name
            """
        )
        for i in cursor:
            output.append(i[0])

        cursor.execute("drop index %s" % ",".join(output))


class Migration(migrations.Migration):
    replaces = [
        ("input", "0045_opplan_cascade_delete"),
        ("input", "0046_sql_role"),
        ("input", "0047_mto"),
        ("input", "0048_setuprule_resource"),
        ("input", "0049_parameter_completed"),
        ("input", "0050_operationmaterial_offset"),
        ("input", "0051_item_weight_volume"),
        ("input", "0052_item_periodofcover"),
        ("input", "0053_operationplan_quantitycompleted"),
        ("input", "0054_itemsupplier_batchwindow"),
        ("input", "0055_itemdistribution_batchwindow"),
        ("input", "0056_parameter_wipproducefullquantity"),
        ("input", "0057_itemsupplier_extra_safety_lt"),
        ("input", "0058_nullable_unique_fields"),
        ("input", "0059_item_uom"),
        ("input", "0060_remove_like_indexes"),
        ("input", "0061_itemsupplier_uniqueness"),
        ("input", "0062_parameter_fix_supply_path"),
        ("input", "0063_itemsupplier_hard_safety_leadtime"),
        ("input", "0064_opm_opr_sequence_cycle"),
        ("input", "0065_demand_owner"),
        ("input", "0066_demand_index"),
        ("input", "0067_itemdistribution_location"),
    ]

    dependencies = [
        ("input", "0044_squashed_60"),
    ]

    operations = [
        migrations.RunPython(
            code=recreateConstraintsCascade,
        ),
        migrations.RunPython(
            code=grant_read_access,
        ),
        migrations.AlterModelOptions(
            name="buffer",
            options={
                "ordering": ["item", "location", "batch"],
                "verbose_name": "buffer",
                "verbose_name_plural": "buffers",
            },
        ),
        migrations.AddField(
            model_name="buffer",
            name="batch",
            field=models.CharField(
                blank=True, max_length=300, null=True, verbose_name="batch"
            ),
        ),
        migrations.AlterUniqueTogether(
            name="buffer",
            unique_together={("item", "location", "batch")},
        ),
        migrations.AddField(
            model_name="demand",
            name="batch",
            field=models.CharField(
                blank=True,
                db_index=True,
                help_text="MTO batch name",
                max_length=300,
                null=True,
                verbose_name="batch",
            ),
        ),
        migrations.AddField(
            model_name="item",
            name="type",
            field=models.CharField(
                blank=True,
                choices=[
                    ("make to stock", "make to stock"),
                    ("make to order", "make to order"),
                ],
                max_length=20,
                null=True,
                verbose_name="type",
            ),
        ),
        migrations.AddField(
            model_name="operationplan",
            name="batch",
            field=models.CharField(
                blank=True,
                db_index=True,
                help_text="MTO batch name",
                max_length=300,
                null=True,
                verbose_name="batch",
            ),
        ),
        migrations.AddField(
            model_name="setuprule",
            name="resource",
            field=models.ForeignKey(
                blank=True,
                help_text="Extra resource used during this changeover",
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name="setuprules",
                to="input.resource",
                verbose_name="resource",
            ),
        ),
        migrations.AddField(
            model_name="operationmaterial",
            name="offset",
            field=models.DurationField(
                blank=True,
                help_text="Time offset from the start or end to consume or produce material",
                null=True,
                verbose_name="offset",
            ),
        ),
        migrations.AddField(
            model_name="item",
            name="volume",
            field=models.DecimalField(
                blank=True,
                decimal_places=8,
                help_text="Volume of the item",
                max_digits=20,
                null=True,
                verbose_name="volume",
            ),
        ),
        migrations.AddField(
            model_name="item",
            name="weight",
            field=models.DecimalField(
                blank=True,
                decimal_places=8,
                help_text="Weight of the item",
                max_digits=20,
                null=True,
                verbose_name="weight",
            ),
        ),
        migrations.AddField(
            model_name="item",
            name="periodofcover",
            field=models.IntegerField(
                blank=True,
                help_text="period of cover of the item (in days)",
                null=True,
                verbose_name="periodofcover",
            ),
        ),
        migrations.AddField(
            model_name="operationplan",
            name="quantity_completed",
            field=models.DecimalField(
                blank=True,
                decimal_places=8,
                default="0.00",
                max_digits=20,
                null=True,
                verbose_name="completed quantity",
            ),
        ),
        migrations.AddField(
            model_name="itemsupplier",
            name="batchwindow",
            field=models.DurationField(
                blank=True,
                default=datetime.timedelta(days=7),
                help_text="Proposed purchase orders within this window will be grouped together",
                null=True,
                verbose_name="batching window",
            ),
        ),
        migrations.AddField(
            model_name="itemdistribution",
            name="batchwindow",
            field=models.DurationField(
                blank=True,
                default=datetime.timedelta(days=7),
                help_text="Proposed distribution orders within this window will be grouped together",
                null=True,
                verbose_name="batching window",
            ),
        ),
        migrations.AddField(
            model_name="itemsupplier",
            name="extra_safety_leadtime",
            field=models.DurationField(
                blank=True,
                help_text="Extra safety lead time on top of standard lead time",
                null=True,
                verbose_name="extra safety leadtime",
            ),
        ),
        migrations.RunSQL(
            sql="ALTER TABLE buffer ALTER COLUMN batch SET DEFAULT ''",
        ),
        migrations.RunSQL(
            sql="ALTER TABLE calendarbucket ALTER COLUMN startdate SET DEFAULT '1971-01-01'::timestamp",
        ),
        migrations.RunSQL(
            sql="ALTER TABLE calendarbucket ALTER COLUMN enddate SET DEFAULT '2030-12-31'::timestamp",
        ),
        migrations.RunSQL(
            sql="ALTER TABLE calendarbucket ALTER COLUMN priority SET DEFAULT 0",
        ),
        migrations.RunSQL(
            sql="ALTER TABLE suboperation ALTER COLUMN effective_start SET DEFAULT '1971-01-01'::timestamp",
        ),
        migrations.RunSQL(
            sql="ALTER TABLE operationmaterial ALTER COLUMN effective_start SET DEFAULT '1971-01-01'::timestamp",
        ),
        migrations.RunSQL(
            sql="ALTER TABLE operationresource ALTER COLUMN effective_start SET DEFAULT '1971-01-01'::timestamp",
        ),
        migrations.RunSQL(
            sql="ALTER TABLE itemsupplier ALTER COLUMN effective_start SET DEFAULT '1971-01-01'::timestamp",
        ),
        migrations.RunSQL(
            sql="ALTER TABLE itemdistribution ALTER COLUMN effective_start SET DEFAULT '1971-01-01'::timestamp",
        ),
        migrations.AddField(
            model_name="item",
            name="uom",
            field=models.CharField(
                blank=True, max_length=20, null=True, verbose_name="unit of measure"
            ),
        ),
        migrations.RunPython(
            code=dropIndexLike,
        ),
        migrations.AddConstraint(
            model_name="itemsupplier",
            constraint=models.UniqueConstraint(
                condition=models.Q(("location__isnull", True)),
                fields=("item", "supplier", "effective_start"),
                name="itemsupplier_partial2",
            ),
        ),
        migrations.AddField(
            model_name="itemsupplier",
            name="hard_safety_leadtime",
            field=models.DurationField(
                blank=True,
                help_text="hard safety lead time",
                null=True,
                verbose_name="hard safety lead time",
            ),
        ),
        migrations.RunSQL(
            sql="\n            alter sequence operationplanmaterial_id_seq cycle;\n            alter sequence operationplanresource_id_seq cycle;\n            ",
        ),
        migrations.RemoveField(
            model_name="demand",
            name="lft",
        ),
        migrations.RemoveField(
            model_name="demand",
            name="lvl",
        ),
        migrations.RemoveField(
            model_name="demand",
            name="rght",
        ),
        migrations.AddField(
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
                max_length=15,
                null=True,
                verbose_name="policy",
            ),
        ),
        migrations.AlterField(
            model_name="demand",
            name="owner",
            field=models.CharField(
                blank=True,
                db_index=True,
                max_length=300,
                null=True,
                verbose_name="owner",
            ),
        ),
        migrations.AlterField(
            model_name="demand",
            name="item",
            field=models.ForeignKey(
                db_index=False,
                on_delete=django.db.models.deletion.CASCADE,
                to="input.item",
                verbose_name="item",
            ),
        ),
        migrations.AddIndex(
            model_name="demand",
            index=models.Index(
                fields=["item", "location", "customer", "due"], name="demand_sorted"
            ),
        ),
        migrations.AlterField(
            model_name="itemdistribution",
            name="location",
            field=models.ForeignKey(
                help_text="Destination location to be replenished",
                on_delete=django.db.models.deletion.CASCADE,
                related_name="itemdistributions_destination",
                to="input.location",
                verbose_name="location",
            ),
        ),
    ]
