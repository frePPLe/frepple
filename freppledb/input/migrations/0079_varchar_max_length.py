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

import datetime

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("input", "0078_parameter_deliveryduration"),
    ]

    operations = [
        migrations.RunSQL(
            sql="drop materialized view if exists forecastreport_view",
            reverse_sql=migrations.RunSQL.noop,
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
            name="adi",
            field=models.DecimalField(
                blank=True,
                db_index=True,
                decimal_places=6,
                editable=False,
                max_digits=15,
                null=True,
                verbose_name="adi",
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
            name="cv2",
            field=models.DecimalField(
                blank=True,
                db_index=True,
                decimal_places=6,
                editable=False,
                max_digits=15,
                null=True,
                verbose_name="cv2",
            ),
        ),
        migrations.AlterField(
            model_name="item",
            name="demand_pattern",
            field=models.CharField(
                blank=True,
                db_index=True,
                editable=False,
                null=True,
                verbose_name="demand_pattern",
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
            name="outlier_12b",
            field=models.DecimalField(
                blank=True,
                db_index=True,
                decimal_places=6,
                editable=False,
                max_digits=15,
                null=True,
                verbose_name="outliers last 12 buckets",
            ),
        ),
        migrations.AlterField(
            model_name="item",
            name="outlier_1b",
            field=models.DecimalField(
                blank=True,
                db_index=True,
                decimal_places=6,
                editable=False,
                max_digits=15,
                null=True,
                verbose_name="outliers last bucket",
            ),
        ),
        migrations.AlterField(
            model_name="item",
            name="outlier_6b",
            field=models.DecimalField(
                blank=True,
                db_index=True,
                decimal_places=6,
                editable=False,
                max_digits=15,
                null=True,
                verbose_name="outliers last 6 buckets",
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
                on_delete=models.deletion.CASCADE,
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
                on_delete=models.deletion.CASCADE,
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
                on_delete=models.deletion.SET_NULL,
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
                blank=True,
                default="fixed_time",
                null=True,
                verbose_name="type",
            ),
        ),
        migrations.AlterField(
            model_name="operationdependency",
            name="blockedby",
            field=models.ForeignKey(
                help_text="blocked by operation",
                on_delete=models.deletion.CASCADE,
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
                on_delete=models.deletion.CASCADE,
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
            name="forecast",
            field=models.CharField(
                blank=True,
                db_index=True,
                editable=False,
                null=True,
                verbose_name="forecast",
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
                db_index=True,
                default="MO",
                help_text="Order type",
                verbose_name="type",
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
                on_delete=models.deletion.CASCADE,
                related_name="operationplanmaterials",
                to="input.item",
                verbose_name="item",
            ),
        ),
        migrations.AlterField(
            model_name="operationplanmaterial",
            name="location",
            field=models.ForeignKey(
                on_delete=models.deletion.CASCADE,
                related_name="operationplanmaterials",
                to="input.location",
                verbose_name="location",
            ),
        ),
        migrations.AlterField(
            model_name="operationplanmaterial",
            name="operationplan",
            field=models.ForeignKey(
                on_delete=models.deletion.CASCADE,
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
                on_delete=models.deletion.CASCADE,
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
                on_delete=models.deletion.SET_NULL,
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
                on_delete=models.deletion.CASCADE,
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
    ]
