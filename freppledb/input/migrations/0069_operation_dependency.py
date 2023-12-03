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

from django.db import migrations, models
import django.db.models.deletion
import django.utils.timezone


class Migration(migrations.Migration):
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
                "verbose_name": "operation dependency",
                "verbose_name_plural": "operation dependencies",
                "db_table": "operation_dependency",
                "ordering": ["operation", "blockedby"],
                "abstract": False,
                "unique_together": {("operation", "blockedby")},
            },
        ),
    ]
