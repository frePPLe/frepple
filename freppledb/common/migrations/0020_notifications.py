#
# Copyright (C) 2020 by frePPLe bv
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
import django.core.validators
import django.utils.timezone
from django.db import migrations, connections, models
import django.db.models.deletion


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
            for table in ["common_follower", "common_notification"]:
                cursor.execute("grant select on table %s to %s" % (table, role))


class Migration(migrations.Migration):
    dependencies = [
        ("contenttypes", "0002_remove_content_type_name"),
        ("common", "0019_scenario_url"),
    ]

    operations = [
        migrations.AddField(
            model_name="comment",
            name="attachment",
            field=models.FileField(
                blank=True,
                null=True,
                upload_to="",
                validators=[
                    django.core.validators.FileExtensionValidator(
                        allowed_extensions=[
                            "gif",
                            "jpeg",
                            "jpg",
                            "png",
                            "docx",
                            "gz",
                            "log",
                            "pdf",
                            "pptx",
                            "txt",
                            "xlsx",
                            "zip",
                        ]
                    )
                ],
            ),
        ),
        migrations.AddField(
            model_name="comment",
            name="object_repr",
            field=models.CharField(
                default="tmp", max_length=200, verbose_name="object repr"
            ),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name="comment",
            name="processed",
            field=models.BooleanField(
                db_index=True, default=False, verbose_name="processed"
            ),
        ),
        migrations.AddField(
            model_name="comment",
            name="type",
            field=models.CharField(
                choices=[
                    ("add", "add"),
                    ("change", "change"),
                    ("delete", "delete"),
                    ("comment", "comment"),
                ],
                default="add",
                max_length=10,
                verbose_name="type",
            ),
        ),
        migrations.AddField(
            model_name="user",
            name="avatar",
            field=models.ImageField(blank=True, null=True, upload_to=""),
        ),
        migrations.AlterField(
            model_name="comment",
            name="comment",
            field=models.TextField(max_length=3000, verbose_name="message"),
        ),
        migrations.AlterField(
            model_name="comment",
            name="lastmodified",
            field=models.DateTimeField(
                db_index=True,
                default=django.utils.timezone.now,
                editable=False,
                verbose_name="last modified",
            ),
        ),
        migrations.CreateModel(
            name="Notification",
            fields=[
                (
                    "id",
                    models.AutoField(
                        primary_key=True, serialize=False, verbose_name="identifier"
                    ),
                ),
                (
                    "status",
                    models.CharField(
                        choices=[("U", "unread"), ("R", "read")],
                        default="U",
                        max_length=5,
                        verbose_name="status",
                    ),
                ),
                (
                    "type",
                    models.CharField(
                        choices=[("M", "email"), ("O", "online")],
                        default="O",
                        max_length=5,
                        verbose_name="type",
                    ),
                ),
                (
                    "comment",
                    models.ForeignKey(
                        null=True,
                        on_delete=django.db.models.deletion.CASCADE,
                        to="common.Comment",
                        verbose_name="comment",
                    ),
                ),
                (
                    "user",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        to=settings.AUTH_USER_MODEL,
                        verbose_name="user",
                    ),
                ),
            ],
            options={
                "verbose_name": "notification",
                "verbose_name_plural": "notifications",
                "db_table": "common_notification",
            },
        ),
        migrations.CreateModel(
            name="Follower",
            fields=[
                (
                    "id",
                    models.AutoField(
                        primary_key=True, serialize=False, verbose_name="identifier"
                    ),
                ),
                ("object_pk", models.TextField(null=True, verbose_name="object id")),
                (
                    "type",
                    models.CharField(
                        choices=[("M", "email"), ("O", "online")],
                        default="O",
                        max_length=10,
                        verbose_name="type",
                    ),
                ),
                (
                    "content_type",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="content_type_set_for_follower",
                        to="contenttypes.ContentType",
                        verbose_name="content type",
                    ),
                ),
                (
                    "user",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        to=settings.AUTH_USER_MODEL,
                        verbose_name="user",
                    ),
                ),
            ],
            options={
                "verbose_name": "follower",
                "verbose_name_plural": "followers",
                "db_table": "common_follower",
            },
        ),
        migrations.RunPython(grant_read_access),
    ]
