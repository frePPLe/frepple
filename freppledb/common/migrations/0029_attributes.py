#
# Copyright (C) 2021 by frePPLe bv
#
# This library is free software; you can redistribute it and/or modify it
# under the terms of the GNU Affero General Public License as published
# by the Free Software Foundation; either version 3 of the License, or
# (at your option) any later version.
#
# This library is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU Affero
# General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public
# License along with this program.  If not, see <http://www.gnu.org/licenses/>.
#

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion
import django.utils.timezone


class Migration(migrations.Migration):

    dependencies = [
        ("contenttypes", "0002_remove_content_type_name"),
        ("common", "0028_comment_permission"),
    ]

    operations = [
        migrations.CreateModel(
            name="Attribute",
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
                    "id",
                    models.AutoField(
                        primary_key=True, serialize=False, verbose_name="identifier"
                    ),
                ),
                (
                    "name",
                    models.CharField(
                        db_index=True, max_length=300, verbose_name="name"
                    ),
                ),
                (
                    "label",
                    models.CharField(
                        db_index=True, max_length=300, verbose_name="label"
                    ),
                ),
                (
                    "type",
                    models.CharField(
                        blank=True,
                        choices=[
                            ("string", "string"),
                            ("boolean", "boolean"),
                            ("number", "number"),
                            ("integer", "integer"),
                            ("date", "date"),
                            ("datetime", "datetime"),
                            ("duration", "duration"),
                            ("time", "time"),
                            ("jsonb", "JSON"),
                        ],
                        max_length=20,
                        null=True,
                        verbose_name="type",
                    ),
                ),
                (
                    "editable",
                    models.BooleanField(
                        blank=True, default=True, verbose_name="editable"
                    ),
                ),
                (
                    "initially_hidden",
                    models.BooleanField(
                        blank=True, default=False, verbose_name="initially hidden"
                    ),
                ),
                (
                    "model",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="attributes_for_attributes",
                        to="contenttypes.ContentType",
                        verbose_name="model",
                    ),
                ),
            ],
            options={
                "verbose_name": "attribute",
                "verbose_name_plural": "attributes",
                "db_table": "common_attribute",
                "ordering": ["model", "name"],
                "unique_together": {("model", "name")},
            },
        ),
    ]
