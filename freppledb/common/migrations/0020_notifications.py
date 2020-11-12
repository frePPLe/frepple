#
# Copyright (C) 2020 by frePPLe bv
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
import django.core.validators
import django.utils.timezone
from django.db import migrations, connections, models
import django.db.models.deletion


def grant_read_access(apps, schema_editor):
    db = schema_editor.connection.alias
    role = settings.DATABASES[db].get("SQL_ROLE", "report_role")
    if role:
        with connections[db].cursor() as cursor:
            cursor.execute("select count(*) from pg_roles where rolname = %s", (role,))
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
        migrations.RunSQL(
            "update common_comment set object_repr = object_pk, type='comment', processed=true"
        ),
        migrations.RunSQL(
            """
            insert into common_comment
            (object_pk, comment, lastmodified, content_type_id, user_id, object_repr, processed, type)
            select
               object_id, change_message, action_time, content_type_id, user_id, object_repr, true,
               case when action_flag = 1 then 'add'
                 when action_flag = 2 then 'change'
                 else 'deletion'
                 end
            from django_admin_log
            order by id
            """
        ),
        migrations.RunSQL("drop table django_admin_log"),
    ]
