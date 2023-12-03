#
# Copyright (C) 2019 by frePPLe bv
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

from django.core.management import call_command
from django.db import migrations, models
import django.db.models.deletion
import django.utils.timezone
import freppledb.common.fields


def loadParameters(apps, schema_editor):
    from django.core.management.commands.loaddata import Command

    call_command(
        Command(),
        "parameters.json",
        app_label="input",
        verbosity=0,
        database=schema_editor.connection.alias,
    )


class Migration(migrations.Migration):
    initial = True

    dependencies = [("common", "0014_squashed_60"), ("admin", "0001_initial")]

    operations = [
        migrations.CreateModel(
            name="Calendar",
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
                (
                    "defaultvalue",
                    models.DecimalField(
                        blank=True,
                        decimal_places=8,
                        default="0.00",
                        help_text="Value to be used when no entry is effective",
                        max_digits=20,
                        null=True,
                        verbose_name="default value",
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
            ],
            options={
                "db_table": "calendar",
                "verbose_name_plural": "calendars",
                "verbose_name": "calendar",
                "abstract": False,
                "ordering": ["name"],
            },
        ),
        migrations.CreateModel(
            name="Supplier",
            fields=[
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
                    "available",
                    models.ForeignKey(
                        blank=True,
                        help_text="Calendar defining the working hours and holidays",
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        to="input.Calendar",
                        verbose_name="available",
                    ),
                ),
                (
                    "owner",
                    models.ForeignKey(
                        blank=True,
                        help_text="Hierarchical parent",
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        related_name="xchildren",
                        to="input.Supplier",
                        verbose_name="owner",
                    ),
                ),
                (
                    "lft",
                    models.PositiveIntegerField(
                        blank=True, db_index=True, editable=False, null=True
                    ),
                ),
                (
                    "rght",
                    models.PositiveIntegerField(blank=True, editable=False, null=True),
                ),
                (
                    "lvl",
                    models.PositiveIntegerField(blank=True, editable=False, null=True),
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
            ],
            options={
                "db_table": "supplier",
                "verbose_name_plural": "suppliers",
                "verbose_name": "supplier",
                "abstract": False,
                "ordering": ["name"],
            },
        ),
        migrations.CreateModel(
            name="Item",
            fields=[
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
                    "cost",
                    models.DecimalField(
                        blank=True,
                        decimal_places=8,
                        help_text="Cost of the item",
                        max_digits=20,
                        null=True,
                        verbose_name="cost",
                    ),
                ),
                (
                    "owner",
                    models.ForeignKey(
                        blank=True,
                        help_text="Hierarchical parent",
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        related_name="xchildren",
                        to="input.Item",
                        verbose_name="owner",
                    ),
                ),
                (
                    "lft",
                    models.PositiveIntegerField(
                        blank=True, db_index=True, editable=False, null=True
                    ),
                ),
                (
                    "rght",
                    models.PositiveIntegerField(blank=True, editable=False, null=True),
                ),
                (
                    "lvl",
                    models.PositiveIntegerField(blank=True, editable=False, null=True),
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
            ],
            options={
                "db_table": "item",
                "verbose_name_plural": "items",
                "verbose_name": "item",
                "abstract": False,
                "ordering": ["name"],
            },
        ),
        migrations.CreateModel(
            name="Location",
            fields=[
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
                    "available",
                    models.ForeignKey(
                        blank=True,
                        help_text="Calendar defining the working hours and holidays",
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        to="input.Calendar",
                        verbose_name="available",
                    ),
                ),
                (
                    "owner",
                    models.ForeignKey(
                        blank=True,
                        help_text="Hierarchical parent",
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        related_name="xchildren",
                        to="input.Location",
                        verbose_name="owner",
                    ),
                ),
                (
                    "lft",
                    models.PositiveIntegerField(
                        blank=True, db_index=True, editable=False, null=True
                    ),
                ),
                (
                    "rght",
                    models.PositiveIntegerField(blank=True, editable=False, null=True),
                ),
                (
                    "lvl",
                    models.PositiveIntegerField(blank=True, editable=False, null=True),
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
            ],
            options={
                "db_table": "location",
                "verbose_name_plural": "locations",
                "verbose_name": "location",
                "abstract": False,
                "ordering": ["name"],
            },
        ),
        migrations.CreateModel(
            name="Customer",
            fields=[
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
                    "owner",
                    models.ForeignKey(
                        blank=True,
                        help_text="Hierarchical parent",
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        related_name="xchildren",
                        to="input.Customer",
                        verbose_name="owner",
                    ),
                ),
                (
                    "lft",
                    models.PositiveIntegerField(
                        blank=True, db_index=True, editable=False, null=True
                    ),
                ),
                (
                    "rght",
                    models.PositiveIntegerField(blank=True, editable=False, null=True),
                ),
                (
                    "lvl",
                    models.PositiveIntegerField(blank=True, editable=False, null=True),
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
            ],
            options={
                "db_table": "customer",
                "verbose_name_plural": "customers",
                "verbose_name": "customer",
                "abstract": False,
                "ordering": ["name"],
            },
        ),
        migrations.CreateModel(
            name="Demand",
            fields=[
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
                    "item",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        to="input.Item",
                        verbose_name="item",
                    ),
                ),
                (
                    "location",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        to="input.Location",
                        verbose_name="location",
                    ),
                ),
                (
                    "customer",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        to="input.Customer",
                        verbose_name="customer",
                    ),
                ),
                (
                    "due",
                    models.DateTimeField(
                        db_index=True,
                        help_text="Due date of the demand",
                        verbose_name="due",
                    ),
                ),
                (
                    "status",
                    models.CharField(
                        blank=True,
                        choices=[
                            ("inquiry", "inquiry"),
                            ("quote", "quote"),
                            ("open", "open"),
                            ("closed", "closed"),
                            ("canceled", "canceled"),
                        ],
                        default="open",
                        help_text='Status of the demand. Only "open" demands are planned',
                        max_length=10,
                        null=True,
                        verbose_name="status",
                    ),
                ),
                (
                    "quantity",
                    models.DecimalField(
                        decimal_places=8,
                        default=1,
                        max_digits=20,
                        verbose_name="quantity",
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
                    "delay",
                    models.DurationField(
                        blank=True, editable=False, null=True, verbose_name="delay"
                    ),
                ),
                (
                    "plannedquantity",
                    models.DecimalField(
                        blank=True,
                        decimal_places=8,
                        editable=False,
                        help_text="Quantity planned for delivery",
                        max_digits=20,
                        null=True,
                        verbose_name="planned quantity",
                    ),
                ),
                (
                    "deliverydate",
                    models.DateTimeField(
                        blank=True,
                        editable=False,
                        help_text="Delivery date of the demand",
                        null=True,
                        verbose_name="delivery date",
                    ),
                ),
                (
                    "plan",
                    freppledb.common.fields.JSONBField(
                        blank=True, default="{}", editable=False, null=True
                    ),
                ),
                (
                    "owner",
                    models.ForeignKey(
                        blank=True,
                        help_text="Hierarchical parent",
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        related_name="xchildren",
                        to="input.Demand",
                        verbose_name="owner",
                    ),
                ),
                (
                    "lft",
                    models.PositiveIntegerField(
                        blank=True, db_index=True, editable=False, null=True
                    ),
                ),
                (
                    "rght",
                    models.PositiveIntegerField(blank=True, editable=False, null=True),
                ),
                (
                    "lvl",
                    models.PositiveIntegerField(blank=True, editable=False, null=True),
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
            ],
            options={
                "db_table": "demand",
                "verbose_name_plural": "sales orders",
                "verbose_name": "sales order",
                "abstract": False,
                "ordering": ["name"],
            },
        ),
        migrations.CreateModel(
            name="Operation",
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
                (
                    "type",
                    models.CharField(
                        blank=True,
                        choices=[
                            ("fixed_time", "fixed_time"),
                            ("time_per", "time_per"),
                            ("routing", "routing"),
                            ("alternate", "alternate"),
                            ("split", "split"),
                        ],
                        default="fixed_time",
                        max_length=20,
                        null=True,
                        verbose_name="type",
                    ),
                ),
                (
                    "owner",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        related_name="childoperations",
                        to="input.Operation",
                        verbose_name="owner",
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
                    "priority",
                    models.IntegerField(
                        blank=True,
                        default=1,
                        help_text="Priority among all alternates",
                        null=True,
                        verbose_name="priority",
                    ),
                ),
                (
                    "effective_start",
                    models.DateTimeField(
                        blank=True,
                        help_text="Validity start date",
                        null=True,
                        verbose_name="effective start",
                    ),
                ),
                (
                    "effective_end",
                    models.DateTimeField(
                        blank=True,
                        help_text="Validity end date",
                        null=True,
                        verbose_name="effective end",
                    ),
                ),
                (
                    "fence",
                    models.DurationField(
                        blank=True,
                        help_text="Operationplans within this time window from the current day are expected to be released to production ERP",
                        null=True,
                        verbose_name="release fence",
                    ),
                ),
                (
                    "posttime",
                    models.DurationField(
                        blank=True,
                        help_text="A delay time to be respected as a soft constraint after ending the operation",
                        null=True,
                        verbose_name="post-op time",
                    ),
                ),
                (
                    "sizeminimum",
                    models.DecimalField(
                        blank=True,
                        decimal_places=8,
                        default="1.0",
                        help_text="A minimum quantity for operationplans",
                        max_digits=20,
                        null=True,
                        verbose_name="size minimum",
                    ),
                ),
                (
                    "sizemultiple",
                    models.DecimalField(
                        blank=True,
                        decimal_places=8,
                        help_text="A multiple quantity for operationplans",
                        max_digits=20,
                        null=True,
                        verbose_name="size multiple",
                    ),
                ),
                (
                    "sizemaximum",
                    models.DecimalField(
                        blank=True,
                        decimal_places=8,
                        help_text="A maximum quantity for operationplans",
                        max_digits=20,
                        null=True,
                        verbose_name="size maximum",
                    ),
                ),
                (
                    "cost",
                    models.DecimalField(
                        blank=True,
                        decimal_places=8,
                        help_text="Cost per operationplan unit",
                        max_digits=20,
                        null=True,
                        verbose_name="cost",
                    ),
                ),
                (
                    "available",
                    models.ForeignKey(
                        blank=True,
                        help_text="Calendar defining the working hours and holidays",
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        to="input.Calendar",
                        verbose_name="available",
                    ),
                ),
                (
                    "duration",
                    models.DurationField(
                        blank=True,
                        help_text="A fixed duration for the operation",
                        null=True,
                        verbose_name="duration",
                    ),
                ),
                (
                    "duration_per",
                    models.DurationField(
                        blank=True,
                        help_text="A variable duration for the operation",
                        null=True,
                        verbose_name="duration per unit",
                    ),
                ),
                (
                    "search",
                    models.CharField(
                        blank=True,
                        choices=[
                            ("PRIORITY", "priority"),
                            ("MINCOST", "minimum cost"),
                            ("MINPENALTY", "minimum penalty"),
                            ("MINCOSTPENALTY", "minimum cost plus penalty"),
                        ],
                        help_text="Method to select preferred alternate",
                        max_length=20,
                        null=True,
                        verbose_name="search mode",
                    ),
                ),
                (
                    "item",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="operations",
                        to="input.Item",
                        verbose_name="item",
                    ),
                ),
                (
                    "location",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        to="input.Location",
                        verbose_name="location",
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
            ],
            options={
                "db_table": "operation",
                "verbose_name_plural": "operations",
                "verbose_name": "operation",
                "abstract": False,
                "ordering": ["name"],
            },
        ),
        migrations.CreateModel(
            name="OperationPlan",
            fields=[
                (
                    "reference",
                    models.CharField(
                        help_text="Unique identifier",
                        max_length=300,
                        primary_key=True,
                        serialize=False,
                        verbose_name="reference",
                    ),
                ),
                (
                    "owner",
                    models.ForeignKey(
                        blank=True,
                        help_text="Hierarchical parent",
                        null=True,
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="xchildren",
                        to="input.OperationPlan",
                        verbose_name="owner",
                    ),
                ),
                (
                    "status",
                    models.CharField(
                        blank=True,
                        choices=[
                            ("proposed", "proposed"),
                            ("approved", "approved"),
                            ("confirmed", "confirmed"),
                            ("closed", "closed"),
                        ],
                        help_text="Status of the order",
                        max_length=20,
                        null=True,
                        verbose_name="status",
                    ),
                ),
                (
                    "type",
                    models.CharField(
                        choices=[
                            ("STCK", "inventory"),
                            ("MO", "manufacturing order"),
                            ("PO", "purchase order"),
                            ("DO", "distribution order"),
                            ("DLVR", "delivery order"),
                        ],
                        db_index=True,
                        default="MO",
                        help_text="Order type",
                        max_length=5,
                        verbose_name="type",
                    ),
                ),
                (
                    "quantity",
                    models.DecimalField(
                        decimal_places=8,
                        default="1.00",
                        max_digits=20,
                        verbose_name="quantity",
                    ),
                ),
                (
                    "color",
                    models.DecimalField(
                        blank=True,
                        decimal_places=8,
                        default="0.00",
                        max_digits=20,
                        null=True,
                        verbose_name="color",
                    ),
                ),
                (
                    "startdate",
                    models.DateTimeField(
                        blank=True,
                        db_index=True,
                        help_text="start date",
                        null=True,
                        verbose_name="start date",
                    ),
                ),
                (
                    "enddate",
                    models.DateTimeField(
                        blank=True,
                        db_index=True,
                        help_text="end date",
                        null=True,
                        verbose_name="end date",
                    ),
                ),
                (
                    "criticality",
                    models.DecimalField(
                        blank=True,
                        decimal_places=8,
                        editable=False,
                        max_digits=20,
                        null=True,
                        verbose_name="criticality",
                    ),
                ),
                (
                    "delay",
                    models.DurationField(
                        blank=True, editable=False, null=True, verbose_name="delay"
                    ),
                ),
                (
                    "due",
                    models.DateTimeField(
                        blank=True,
                        editable=False,
                        help_text="Due date of the demand/forecast",
                        null=True,
                        verbose_name="due",
                    ),
                ),
                (
                    "name",
                    models.CharField(
                        blank=True,
                        db_index=True,
                        max_length=1000,
                        null=True,
                        verbose_name="name",
                    ),
                ),
                (
                    "demand",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.CASCADE,
                        to="input.Demand",
                        verbose_name="demand",
                    ),
                ),
                (
                    "supplier",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.CASCADE,
                        to="input.Supplier",
                        verbose_name="supplier",
                    ),
                ),
                (
                    "destination",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="destinations",
                        to="input.Location",
                        verbose_name="destination",
                    ),
                ),
                (
                    "item",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.CASCADE,
                        to="input.Item",
                        verbose_name="item",
                    ),
                ),
                (
                    "location",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.CASCADE,
                        to="input.Location",
                        verbose_name="location",
                    ),
                ),
                (
                    "operation",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.CASCADE,
                        to="input.Operation",
                        verbose_name="operation",
                    ),
                ),
                (
                    "origin",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="origins",
                        to="input.Location",
                        verbose_name="origin",
                    ),
                ),
                (
                    "plan",
                    freppledb.common.fields.JSONBField(
                        blank=True, default="{}", editable=False, null=True
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
            ],
            options={
                "db_table": "operationplan",
                "verbose_name_plural": "operationplans",
                "verbose_name": "operationplan",
                "abstract": False,
                "ordering": ["id"],
            },
        ),
        migrations.CreateModel(
            name="OperationPlanMaterial",
            fields=[
                (
                    "id",
                    models.AutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                (
                    "operationplan",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="materials",
                        to="input.OperationPlan",
                        verbose_name="operationplan",
                    ),
                ),
                (
                    "item",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="operationplanmaterials",
                        to="input.Item",
                        verbose_name="item",
                    ),
                ),
                (
                    "location",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="operationplanmaterials",
                        to="input.Location",
                        verbose_name="location",
                    ),
                ),
                ("flowdate", models.DateTimeField(db_index=True, verbose_name="date")),
                (
                    "quantity",
                    models.DecimalField(
                        decimal_places=8, max_digits=20, verbose_name="quantity"
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
                    "minimum",
                    models.DecimalField(
                        blank=True,
                        decimal_places=8,
                        max_digits=20,
                        null=True,
                        verbose_name="minimum",
                    ),
                ),
                (
                    "periodofcover",
                    models.DecimalField(
                        blank=True,
                        decimal_places=8,
                        max_digits=20,
                        null=True,
                        verbose_name="period of cover",
                    ),
                ),
                (
                    "status",
                    models.CharField(
                        blank=True,
                        choices=[
                            ("proposed", "proposed"),
                            ("confirmed", "confirmed"),
                            ("closed", "closed"),
                        ],
                        help_text="status of the material production or consumption",
                        max_length=20,
                        null=True,
                        verbose_name="status",
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
            ],
            options={
                "db_table": "operationplanmaterial",
                "verbose_name_plural": "operationplan materials",
                "verbose_name": "operationplan material",
                "ordering": ["item", "location", "flowdate"],
            },
        ),
        migrations.CreateModel(
            name="SetupMatrix",
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
            ],
            options={
                "db_table": "setupmatrix",
                "verbose_name_plural": "setup matrices",
                "verbose_name": "setup matrix",
                "abstract": False,
                "ordering": ["name"],
            },
        ),
        migrations.CreateModel(
            name="Skill",
            fields=[
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
            ],
            options={
                "db_table": "skill",
                "verbose_name_plural": "skills",
                "verbose_name": "skill",
                "abstract": False,
                "ordering": ["name"],
            },
        ),
        migrations.CreateModel(
            name="Resource",
            fields=[
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
                    "type",
                    models.CharField(
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
                        max_length=20,
                        null=True,
                        verbose_name="type",
                    ),
                ),
                (
                    "constrained",
                    models.NullBooleanField(
                        default=True,
                        help_text="controls whether or not this resource is planned in finite capacity mode",
                        verbose_name="constrained",
                    ),
                ),
                (
                    "maximum",
                    models.DecimalField(
                        blank=True,
                        decimal_places=8,
                        default="1.00",
                        help_text="Size of the resource",
                        max_digits=20,
                        null=True,
                        verbose_name="maximum",
                    ),
                ),
                (
                    "cost",
                    models.DecimalField(
                        blank=True,
                        decimal_places=8,
                        help_text="Cost for using 1 unit of the resource for 1 hour",
                        max_digits=20,
                        null=True,
                        verbose_name="cost",
                    ),
                ),
                (
                    "maxearly",
                    models.DurationField(
                        blank=True,
                        help_text="Time window before the ask date where we look for available capacity",
                        null=True,
                        verbose_name="max early",
                    ),
                ),
                (
                    "setup",
                    models.CharField(
                        blank=True,
                        help_text="Setup of the resource at the start of the plan",
                        max_length=300,
                        null=True,
                        verbose_name="setup",
                    ),
                ),
                (
                    "location",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.CASCADE,
                        to="input.Location",
                        verbose_name="location",
                    ),
                ),
                (
                    "available",
                    models.ForeignKey(
                        blank=True,
                        help_text="Calendar defining the working hours and holidays",
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        related_name="+",
                        to="input.Calendar",
                        verbose_name="available",
                    ),
                ),
                (
                    "efficiency",
                    models.DecimalField(
                        blank=True,
                        decimal_places=8,
                        help_text="Efficiency percentage of the resource",
                        max_digits=20,
                        null=True,
                        verbose_name="efficiency %",
                    ),
                ),
                (
                    "efficiency_calendar",
                    models.ForeignKey(
                        blank=True,
                        help_text="Calendar defining the efficiency percentage of the resource varying over time",
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        related_name="+",
                        to="input.Calendar",
                        verbose_name="efficiency % calendar",
                    ),
                ),
                (
                    "maximum_calendar",
                    models.ForeignKey(
                        blank=True,
                        help_text="Calendar defining the resource size varying over time",
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        related_name="+",
                        to="input.Calendar",
                        verbose_name="maximum calendar",
                    ),
                ),
                (
                    "owner",
                    models.ForeignKey(
                        blank=True,
                        help_text="Hierarchical parent",
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        related_name="xchildren",
                        to="input.Resource",
                        verbose_name="owner",
                    ),
                ),
                (
                    "setupmatrix",
                    models.ForeignKey(
                        blank=True,
                        help_text="Setup matrix defining the conversion time and cost",
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        to="input.SetupMatrix",
                        verbose_name="setup matrix",
                    ),
                ),
                (
                    "lft",
                    models.PositiveIntegerField(
                        blank=True, db_index=True, editable=False, null=True
                    ),
                ),
                (
                    "rght",
                    models.PositiveIntegerField(blank=True, editable=False, null=True),
                ),
                (
                    "lvl",
                    models.PositiveIntegerField(blank=True, editable=False, null=True),
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
            ],
            options={
                "db_table": "resource",
                "verbose_name_plural": "resources",
                "verbose_name": "resource",
                "abstract": False,
                "ordering": ["name"],
            },
        ),
        migrations.CreateModel(
            name="OperationPlanResource",
            fields=[
                (
                    "id",
                    models.AutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="identifier",
                    ),
                ),
                (
                    "operationplan",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="resources",
                        to="input.OperationPlan",
                        verbose_name="operationplan",
                    ),
                ),
                (
                    "resource",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="operationplanresources",
                        to="input.Resource",
                        verbose_name="resource",
                    ),
                ),
                (
                    "quantity",
                    models.DecimalField(
                        decimal_places=8, max_digits=20, verbose_name="quantity"
                    ),
                ),
                (
                    "startdate",
                    models.DateTimeField(db_index=True, verbose_name="startdate"),
                ),
                (
                    "enddate",
                    models.DateTimeField(db_index=True, verbose_name="enddate"),
                ),
                (
                    "setup",
                    models.CharField(max_length=300, null=True, verbose_name="setup"),
                ),
                (
                    "status",
                    models.CharField(
                        blank=True,
                        choices=[
                            ("proposed", "proposed"),
                            ("confirmed", "confirmed"),
                            ("closed", "closed"),
                        ],
                        help_text="Status of the OperationPlanResource",
                        max_length=20,
                        null=True,
                        verbose_name="status",
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
            ],
            options={
                "db_table": "operationplanresource",
                "verbose_name_plural": "operationplan resources",
                "verbose_name": "operationplan resource",
                "ordering": ["resource", "startdate"],
                "unique_together": {("resource", "operationplan")},
            },
        ),
        migrations.AddField(
            model_name="demand",
            name="operation",
            field=models.ForeignKey(
                blank=True,
                help_text="Operation used to satisfy this demand",
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name="used_demand",
                to="input.Operation",
                verbose_name="delivery operation",
            ),
        ),
        migrations.CreateModel(
            name="DeliveryOrder",
            fields=[],
            options={
                "proxy": True,
                "verbose_name": "delivery order",
                "verbose_name_plural": "delivery orders",
            },
            bases=("input.operationplan",),
        ),
        migrations.CreateModel(
            name="DistributionOrder",
            fields=[],
            options={
                "proxy": True,
                "verbose_name_plural": "distribution orders",
                "verbose_name": "distribution order",
            },
            bases=("input.operationplan",),
        ),
        migrations.CreateModel(
            name="ManufacturingOrder",
            fields=[],
            options={
                "proxy": True,
                "verbose_name_plural": "manufacturing orders",
                "verbose_name": "manufacturing order",
            },
            bases=("input.operationplan",),
        ),
        migrations.CreateModel(
            name="PurchaseOrder",
            fields=[],
            options={
                "proxy": True,
                "verbose_name_plural": "purchase orders",
                "verbose_name": "purchase order",
            },
            bases=("input.operationplan",),
        ),
        migrations.CreateModel(
            name="SubOperation",
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
                        help_text="Parent operation",
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="suboperations",
                        to="input.Operation",
                        verbose_name="operation",
                    ),
                ),
                (
                    "suboperation",
                    models.ForeignKey(
                        help_text="Child operation",
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="superoperations",
                        to="input.Operation",
                        verbose_name="suboperation",
                    ),
                ),
                (
                    "priority",
                    models.IntegerField(
                        default=1,
                        help_text="Sequence of this operation among the suboperations. Negative values are ignored.",
                        verbose_name="priority",
                    ),
                ),
                (
                    "effective_start",
                    models.DateTimeField(
                        blank=True,
                        help_text="Validity start date",
                        null=True,
                        verbose_name="effective start",
                    ),
                ),
                (
                    "effective_end",
                    models.DateTimeField(
                        blank=True,
                        help_text="Validity end date",
                        null=True,
                        verbose_name="effective end",
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
            ],
            options={
                "verbose_name_plural": "suboperations",
                "verbose_name": "suboperation",
                "abstract": False,
                "ordering": ["operation", "priority", "suboperation"],
                "db_table": "suboperation",
                "unique_together": {("operation", "suboperation", "effective_start")},
            },
        ),
        migrations.CreateModel(
            name="SetupRule",
            fields=[
                (
                    "id",
                    models.AutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="identifier",
                    ),
                ),
                (
                    "setupmatrix",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="rules",
                        to="input.SetupMatrix",
                        verbose_name="setup matrix",
                    ),
                ),
                ("priority", models.IntegerField(verbose_name="priority")),
                (
                    "fromsetup",
                    models.CharField(
                        blank=True,
                        help_text="Name of the old setup (wildcard characters are supported)",
                        max_length=300,
                        null=True,
                        verbose_name="from setup",
                    ),
                ),
                (
                    "tosetup",
                    models.CharField(
                        blank=True,
                        help_text="Name of the new setup (wildcard characters are supported)",
                        max_length=300,
                        null=True,
                        verbose_name="to setup",
                    ),
                ),
                (
                    "duration",
                    models.DurationField(
                        blank=True,
                        help_text="Duration of the changeover",
                        null=True,
                        verbose_name="duration",
                    ),
                ),
                (
                    "cost",
                    models.DecimalField(
                        blank=True,
                        decimal_places=8,
                        help_text="Cost of the conversion",
                        max_digits=20,
                        null=True,
                        verbose_name="cost",
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
            ],
            options={
                "verbose_name_plural": "setup matrix rules",
                "verbose_name": "setup matrix rule",
                "abstract": False,
                "ordering": ["priority"],
                "db_table": "setuprule",
                "unique_together": {("setupmatrix", "priority")},
            },
        ),
        migrations.CreateModel(
            name="ResourceSkill",
            fields=[
                (
                    "id",
                    models.AutoField(
                        primary_key=True, serialize=False, verbose_name="identifier"
                    ),
                ),
                (
                    "resource",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="skills",
                        to="input.Resource",
                        verbose_name="resource",
                    ),
                ),
                (
                    "skill",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="resources",
                        to="input.Skill",
                        verbose_name="skill",
                    ),
                ),
                (
                    "priority",
                    models.IntegerField(
                        blank=True,
                        default=1,
                        help_text="Priority of this skill in a group of alternates",
                        null=True,
                        verbose_name="priority",
                    ),
                ),
                (
                    "effective_start",
                    models.DateTimeField(
                        blank=True,
                        help_text="Validity start date",
                        null=True,
                        verbose_name="effective start",
                    ),
                ),
                (
                    "effective_end",
                    models.DateTimeField(
                        blank=True,
                        help_text="Validity end date",
                        null=True,
                        verbose_name="effective end",
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
            ],
            options={
                "verbose_name_plural": "resource skills",
                "verbose_name": "resource skill",
                "abstract": False,
                "ordering": ["resource", "skill"],
                "db_table": "resourceskill",
                "unique_together": {("resource", "skill")},
            },
        ),
        migrations.CreateModel(
            name="OperationResource",
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
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="operationresources",
                        to="input.Operation",
                        verbose_name="operation",
                    ),
                ),
                (
                    "resource",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="operationresources",
                        to="input.Resource",
                        verbose_name="resource",
                    ),
                ),
                (
                    "quantity",
                    models.DecimalField(
                        decimal_places=8,
                        default="1.00",
                        help_text="Required quantity of the resource",
                        max_digits=20,
                        verbose_name="quantity",
                    ),
                ),
                (
                    "quantity_fixed",
                    models.DecimalField(
                        blank=True,
                        decimal_places=8,
                        help_text="constant part of the capacity consumption (bucketized resources only)",
                        max_digits=20,
                        null=True,
                        verbose_name="quantity fixed",
                    ),
                ),
                (
                    "effective_start",
                    models.DateTimeField(
                        blank=True,
                        help_text="Validity start date",
                        null=True,
                        verbose_name="effective start",
                    ),
                ),
                (
                    "effective_end",
                    models.DateTimeField(
                        blank=True,
                        help_text="Validity end date",
                        null=True,
                        verbose_name="effective end",
                    ),
                ),
                (
                    "name",
                    models.CharField(
                        blank=True,
                        help_text="Optional name of this load",
                        max_length=300,
                        null=True,
                        verbose_name="name",
                    ),
                ),
                (
                    "priority",
                    models.IntegerField(
                        blank=True,
                        default=1,
                        help_text="Priority of this load in a group of alternates",
                        null=True,
                        verbose_name="priority",
                    ),
                ),
                (
                    "setup",
                    models.CharField(
                        blank=True,
                        help_text="Setup required on the resource for this operation",
                        max_length=300,
                        null=True,
                        verbose_name="setup",
                    ),
                ),
                (
                    "search",
                    models.CharField(
                        blank=True,
                        choices=[
                            ("PRIORITY", "priority"),
                            ("MINCOST", "minimum cost"),
                            ("MINPENALTY", "minimum penalty"),
                            ("MINCOSTPENALTY", "minimum cost plus penalty"),
                        ],
                        help_text="Method to select preferred alternate",
                        max_length=20,
                        null=True,
                        verbose_name="search mode",
                    ),
                ),
                (
                    "skill",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        related_name="operationresources",
                        to="input.Skill",
                        verbose_name="skill",
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
            ],
            options={
                "db_table": "operationresource",
                "verbose_name_plural": "operation resources",
                "verbose_name": "operation resource",
                "abstract": False,
                "unique_together": {("operation", "resource", "effective_start")},
            },
        ),
        migrations.CreateModel(
            name="OperationMaterial",
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
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="operationmaterials",
                        to="input.Operation",
                        verbose_name="operation",
                    ),
                ),
                (
                    "item",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="operationmaterials",
                        to="input.Item",
                        verbose_name="item",
                    ),
                ),
                (
                    "quantity",
                    models.DecimalField(
                        blank=True,
                        decimal_places=8,
                        default="1.00",
                        help_text="Quantity to consume or produce per operationplan unit",
                        max_digits=20,
                        null=True,
                        verbose_name="quantity",
                    ),
                ),
                (
                    "quantity_fixed",
                    models.DecimalField(
                        blank=True,
                        decimal_places=8,
                        help_text="Fixed quantity to consume or produce",
                        max_digits=20,
                        null=True,
                        verbose_name="fixed quantity",
                    ),
                ),
                (
                    "transferbatch",
                    models.DecimalField(
                        blank=True,
                        decimal_places=8,
                        help_text="Batch size by in which material is produced or consumed",
                        max_digits=20,
                        null=True,
                        verbose_name="transfer batch quantity",
                    ),
                ),
                (
                    "type",
                    models.CharField(
                        blank=True,
                        choices=[
                            ("start", "Start"),
                            ("end", "End"),
                            ("transfer_batch", "Batch transfer"),
                        ],
                        default="start",
                        help_text="Consume/produce material at the start or the end of the operationplan",
                        max_length=20,
                        null=True,
                        verbose_name="type",
                    ),
                ),
                (
                    "effective_start",
                    models.DateTimeField(
                        blank=True,
                        help_text="Validity start date",
                        null=True,
                        verbose_name="effective start",
                    ),
                ),
                (
                    "effective_end",
                    models.DateTimeField(
                        blank=True,
                        help_text="Validity end date",
                        null=True,
                        verbose_name="effective end",
                    ),
                ),
                (
                    "name",
                    models.CharField(
                        blank=True,
                        help_text="Optional name of this operation material",
                        max_length=300,
                        null=True,
                        verbose_name="name",
                    ),
                ),
                (
                    "priority",
                    models.IntegerField(
                        blank=True,
                        default=1,
                        help_text="Priority of this operation material in a group of alternates",
                        null=True,
                        verbose_name="priority",
                    ),
                ),
                (
                    "search",
                    models.CharField(
                        blank=True,
                        choices=[
                            ("PRIORITY", "priority"),
                            ("MINCOST", "minimum cost"),
                            ("MINPENALTY", "minimum penalty"),
                            ("MINCOSTPENALTY", "minimum cost plus penalty"),
                        ],
                        help_text="Method to select preferred alternate",
                        max_length=20,
                        null=True,
                        verbose_name="search mode",
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
            ],
            options={
                "db_table": "operationmaterial",
                "verbose_name_plural": "operation materials",
                "verbose_name": "operation material",
                "abstract": False,
                "unique_together": {("operation", "item", "effective_start")},
            },
        ),
        migrations.CreateModel(
            name="ItemSupplier",
            fields=[
                (
                    "id",
                    models.AutoField(
                        primary_key=True, serialize=False, verbose_name="identifier"
                    ),
                ),
                (
                    "item",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="itemsuppliers",
                        to="input.Item",
                        verbose_name="item",
                    ),
                ),
                (
                    "supplier",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="suppliers",
                        to="input.Supplier",
                        verbose_name="supplier",
                    ),
                ),
                (
                    "location",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="itemsuppliers",
                        to="input.Location",
                        verbose_name="location",
                    ),
                ),
                (
                    "leadtime",
                    models.DurationField(
                        blank=True,
                        help_text="Purchasing lead time",
                        null=True,
                        verbose_name="lead time",
                    ),
                ),
                (
                    "sizeminimum",
                    models.DecimalField(
                        blank=True,
                        decimal_places=8,
                        default="1.0",
                        help_text="A minimum purchasing quantity",
                        max_digits=20,
                        null=True,
                        verbose_name="size minimum",
                    ),
                ),
                (
                    "sizemultiple",
                    models.DecimalField(
                        blank=True,
                        decimal_places=8,
                        help_text="A multiple purchasing quantity",
                        max_digits=20,
                        null=True,
                        verbose_name="size multiple",
                    ),
                ),
                (
                    "sizemaximum",
                    models.DecimalField(
                        blank=True,
                        decimal_places=8,
                        help_text="A maximum purchasing quantity",
                        max_digits=20,
                        null=True,
                        verbose_name="size maximum",
                    ),
                ),
                (
                    "cost",
                    models.DecimalField(
                        blank=True,
                        decimal_places=8,
                        help_text="Purchasing cost per unit",
                        max_digits=20,
                        null=True,
                        verbose_name="cost",
                    ),
                ),
                (
                    "priority",
                    models.IntegerField(
                        blank=True,
                        default=1,
                        help_text="Priority among all alternates",
                        null=True,
                        verbose_name="priority",
                    ),
                ),
                (
                    "effective_start",
                    models.DateTimeField(
                        blank=True,
                        help_text="Validity start date",
                        null=True,
                        verbose_name="effective start",
                    ),
                ),
                (
                    "effective_end",
                    models.DateTimeField(
                        blank=True,
                        help_text="Validity end date",
                        null=True,
                        verbose_name="effective end",
                    ),
                ),
                (
                    "fence",
                    models.DurationField(
                        blank=True,
                        help_text="Frozen fence for creating new procurements",
                        null=True,
                        verbose_name="fence",
                    ),
                ),
                (
                    "resource",
                    models.ForeignKey(
                        blank=True,
                        help_text="Resource to model the supplier capacity",
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        related_name="itemsuppliers",
                        to="input.Resource",
                        verbose_name="resource",
                    ),
                ),
                (
                    "resource_qty",
                    models.DecimalField(
                        blank=True,
                        decimal_places=8,
                        default="1.0",
                        help_text="Resource capacity consumed per purchased unit",
                        max_digits=20,
                        null=True,
                        verbose_name="resource quantity",
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
            ],
            options={
                "db_table": "itemsupplier",
                "verbose_name_plural": "item suppliers",
                "verbose_name": "item supplier",
                "abstract": False,
                "unique_together": {
                    ("item", "location", "supplier", "effective_start")
                },
            },
        ),
        migrations.CreateModel(
            name="ItemDistribution",
            fields=[
                (
                    "id",
                    models.AutoField(
                        primary_key=True, serialize=False, verbose_name="identifier"
                    ),
                ),
                (
                    "item",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="distributions",
                        to="input.Item",
                        verbose_name="item",
                    ),
                ),
                (
                    "location",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="itemdistributions_destination",
                        to="input.Location",
                        verbose_name="location",
                    ),
                ),
                (
                    "origin",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="itemdistributions_origin",
                        to="input.Location",
                        verbose_name="origin",
                    ),
                ),
                (
                    "leadtime",
                    models.DurationField(
                        blank=True,
                        help_text="lead time",
                        null=True,
                        verbose_name="lead time",
                    ),
                ),
                (
                    "sizeminimum",
                    models.DecimalField(
                        blank=True,
                        decimal_places=8,
                        default="1.0",
                        help_text="A minimum shipping quantity",
                        max_digits=20,
                        null=True,
                        verbose_name="size minimum",
                    ),
                ),
                (
                    "sizemultiple",
                    models.DecimalField(
                        blank=True,
                        decimal_places=8,
                        help_text="A multiple shipping quantity",
                        max_digits=20,
                        null=True,
                        verbose_name="size multiple",
                    ),
                ),
                (
                    "sizemaximum",
                    models.DecimalField(
                        blank=True,
                        decimal_places=8,
                        help_text="A maximum shipping quantity",
                        max_digits=20,
                        null=True,
                        verbose_name="size maximum",
                    ),
                ),
                (
                    "cost",
                    models.DecimalField(
                        blank=True,
                        decimal_places=8,
                        help_text="Shipping cost per unit",
                        max_digits=20,
                        null=True,
                        verbose_name="cost",
                    ),
                ),
                (
                    "priority",
                    models.IntegerField(
                        blank=True,
                        default=1,
                        help_text="Priority among all alternates",
                        null=True,
                        verbose_name="priority",
                    ),
                ),
                (
                    "effective_start",
                    models.DateTimeField(
                        blank=True,
                        help_text="Validity start date",
                        null=True,
                        verbose_name="effective start",
                    ),
                ),
                (
                    "effective_end",
                    models.DateTimeField(
                        blank=True,
                        help_text="Validity end date",
                        null=True,
                        verbose_name="effective end",
                    ),
                ),
                (
                    "fence",
                    models.DurationField(
                        blank=True,
                        help_text="Frozen fence for creating new shipments",
                        null=True,
                        verbose_name="fence",
                    ),
                ),
                (
                    "resource",
                    models.ForeignKey(
                        blank=True,
                        help_text="Resource to model the distribution capacity",
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        related_name="itemdistributions",
                        to="input.Resource",
                        verbose_name="resource",
                    ),
                ),
                (
                    "resource_qty",
                    models.DecimalField(
                        blank=True,
                        decimal_places=8,
                        default="1.0",
                        help_text="Resource capacity consumed per distributed unit",
                        max_digits=20,
                        null=True,
                        verbose_name="resource quantity",
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
            ],
            options={
                "db_table": "itemdistribution",
                "verbose_name_plural": "item distributions",
                "verbose_name": "item distribution",
                "abstract": False,
                "unique_together": {("item", "location", "origin", "effective_start")},
            },
        ),
        migrations.CreateModel(
            name="CalendarBucket",
            fields=[
                (
                    "id",
                    models.AutoField(
                        primary_key=True, serialize=False, verbose_name="identifier"
                    ),
                ),
                (
                    "calendar",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="buckets",
                        to="input.Calendar",
                        verbose_name="calendar",
                    ),
                ),
                (
                    "priority",
                    models.IntegerField(
                        blank=True, default=0, null=True, verbose_name="priority"
                    ),
                ),
                (
                    "value",
                    models.DecimalField(
                        blank=True,
                        decimal_places=8,
                        default="0.00",
                        max_digits=20,
                        verbose_name="value",
                    ),
                ),
                (
                    "startdate",
                    models.DateTimeField(
                        blank=True, null=True, verbose_name="start date"
                    ),
                ),
                (
                    "enddate",
                    models.DateTimeField(
                        blank=True,
                        default=datetime.datetime(2030, 12, 31, 0, 0),
                        null=True,
                        verbose_name="end date",
                    ),
                ),
                ("monday", models.BooleanField(default=True, verbose_name="Monday")),
                ("tuesday", models.BooleanField(default=True, verbose_name="Tuesday")),
                (
                    "wednesday",
                    models.BooleanField(default=True, verbose_name="Wednesday"),
                ),
                (
                    "thursday",
                    models.BooleanField(default=True, verbose_name="Thursday"),
                ),
                ("friday", models.BooleanField(default=True, verbose_name="Friday")),
                (
                    "saturday",
                    models.BooleanField(default=True, verbose_name="Saturday"),
                ),
                ("sunday", models.BooleanField(default=True, verbose_name="Sunday")),
                (
                    "starttime",
                    models.TimeField(
                        blank=True,
                        default=datetime.time(0, 0),
                        null=True,
                        verbose_name="start time",
                    ),
                ),
                (
                    "endtime",
                    models.TimeField(
                        blank=True,
                        default=datetime.time(23, 59, 59),
                        null=True,
                        verbose_name="end time",
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
            ],
            options={
                "verbose_name_plural": "calendar buckets",
                "verbose_name": "calendar bucket",
                "abstract": False,
                "ordering": ["calendar", "id"],
                "db_table": "calendarbucket",
                "unique_together": {("calendar", "startdate", "enddate", "priority")},
            },
        ),
        migrations.CreateModel(
            name="Buffer",
            fields=[
                (
                    "id",
                    models.AutoField(
                        primary_key=True, serialize=False, verbose_name="identifier"
                    ),
                ),
                (
                    "item",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        to="input.Item",
                        verbose_name="item",
                    ),
                ),
                (
                    "location",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        to="input.Location",
                        verbose_name="location",
                    ),
                ),
                (
                    "onhand",
                    models.DecimalField(
                        blank=True,
                        decimal_places=8,
                        default="0.00",
                        help_text="current inventory",
                        max_digits=20,
                        null=True,
                        verbose_name="onhand",
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
                    "type",
                    models.CharField(
                        blank=True,
                        choices=[("default", "default"), ("infinite", "infinite")],
                        default="default",
                        max_length=20,
                        null=True,
                        verbose_name="type",
                    ),
                ),
                (
                    "minimum",
                    models.DecimalField(
                        blank=True,
                        decimal_places=8,
                        default="0.00",
                        help_text="safety stock",
                        max_digits=20,
                        null=True,
                        verbose_name="minimum",
                    ),
                ),
                (
                    "minimum_calendar",
                    models.ForeignKey(
                        blank=True,
                        help_text="Calendar storing a time-dependent safety stock profile",
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        to="input.Calendar",
                        verbose_name="minimum calendar",
                    ),
                ),
                (
                    "min_interval",
                    models.DurationField(
                        blank=True,
                        help_text="Batching window for grouping replenishments in batches",
                        null=True,
                        verbose_name="min_interval",
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
            ],
            options={
                "verbose_name_plural": "buffers",
                "verbose_name": "buffer",
                "abstract": False,
                "ordering": ["item", "location"],
                "db_table": "buffer",
                "unique_together": {("item", "location")},
            },
        ),
        migrations.AddIndex(
            model_name="operationplanmaterial",
            index=models.Index(fields=["item", "location"], name="opplanmat_itemloc"),
        ),
        migrations.RunSQL(
            sql="alter table buffer alter column lastmodified set default now()"
        ),
        migrations.RunSQL(
            sql="alter table calendar alter column lastmodified set default now()"
        ),
        migrations.RunSQL(
            sql="alter table calendarbucket alter column lastmodified set default now()"
        ),
        migrations.RunSQL(
            sql="alter table common_bucket alter column lastmodified set default now()"
        ),
        migrations.RunSQL(
            sql="alter table common_bucketdetail alter column lastmodified set default now()"
        ),
        migrations.RunSQL(
            sql="alter table common_comment alter column lastmodified set default now()"
        ),
        migrations.RunSQL(
            sql="alter table common_parameter alter column lastmodified set default now()"
        ),
        migrations.RunSQL(
            sql="alter table common_user alter column lastmodified set default now()"
        ),
        migrations.RunSQL(
            sql="alter table customer alter column lastmodified set default now()"
        ),
        migrations.RunSQL(
            sql="alter table demand alter column lastmodified set default now()"
        ),
        migrations.RunSQL(
            sql="alter table item alter column lastmodified set default now()"
        ),
        migrations.RunSQL(
            sql="alter table itemdistribution alter column lastmodified set default now()"
        ),
        migrations.RunSQL(
            sql="alter table itemsupplier alter column lastmodified set default now()"
        ),
        migrations.RunSQL(
            sql="alter table location alter column lastmodified set default now()"
        ),
        migrations.RunSQL(
            sql="alter table operation alter column lastmodified set default now()"
        ),
        migrations.RunSQL(
            sql="alter table operationmaterial alter column lastmodified set default now()"
        ),
        migrations.RunSQL(
            sql="alter table operationplan alter column lastmodified set default now()"
        ),
        migrations.RunSQL(
            sql="alter table operationplanmaterial alter column lastmodified set default now()"
        ),
        migrations.RunSQL(
            sql="alter table operationplanresource alter column lastmodified set default now()"
        ),
        migrations.RunSQL(
            sql="alter table operationresource alter column lastmodified set default now()"
        ),
        migrations.RunSQL(
            sql="alter table resource alter column lastmodified set default now()"
        ),
        migrations.RunSQL(
            sql="alter table resourceskill alter column lastmodified set default now()"
        ),
        migrations.RunSQL(
            sql="alter table setupmatrix alter column lastmodified set default now()"
        ),
        migrations.RunSQL(
            sql="alter table setuprule alter column lastmodified set default now()"
        ),
        migrations.RunSQL(
            sql="alter table skill alter column lastmodified set default now()"
        ),
        migrations.RunSQL(
            sql="alter table suboperation alter column lastmodified set default now()"
        ),
        migrations.RunSQL(
            sql="alter table supplier alter column lastmodified set default now()"
        ),
        migrations.RunPython(code=loadParameters),
    ]
