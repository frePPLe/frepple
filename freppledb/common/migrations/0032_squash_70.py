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
#

from datetime import datetime

from django.conf import settings
from django.contrib.admin.models import LogEntry
from django.contrib.auth.hashers import make_password
import django.contrib.auth.models
import django.contrib.auth.validators
import django.core.validators
from django.db import migrations, models, connections, transaction
import django.db.models.deletion
import django.utils.timezone


import freppledb.common.fields


def createAdminUser(apps, schema_editor):
    if not schema_editor.connection.alias == "default":
        return
    User = apps.get_model("common", "User")
    usr = User(
        username="admin",
        email="your@company.com",
        first_name="admin",
        last_name="admin",
        date_joined=datetime(2000, 1, 1),
        horizontype=True,
        horizonlength=6,
        horizonunit="month",
        language="auto",
        is_superuser=True,
        is_staff=True,
        is_active=True,
    )
    usr._password = "admin"
    usr.password = make_password("admin")
    usr.save()


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
                "common_parameter",
                "common_bucket",
                "common_bucketdetail",
                "common_comment",
            ]:
                cursor.execute("grant select on table %s to %s" % (table, role))


def grant_read_access_notification(apps, schema_editor):
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


def migrateAdminLog(apps, schema_editor):
    Comment = apps.get_model("common", "Comment")

    db = schema_editor.connection.alias
    with transaction.atomic(using=db):
        for rec in LogEntry.objects.all().using(db):
            if rec.action_flag == 1:
                rectype = "add"
            elif rec.action_flag == 2:
                rectype = "change"
            elif rec.action_flag == 3:
                rectype = "deletion"
            else:
                rectype = "comment"
            Comment(
                object_pk=rec.object_id,
                comment=rec.get_change_message(),
                lastmodified=rec.action_time,
                content_type_id=rec.content_type_id,
                user_id=rec.user_id,
                object_repr=rec.object_repr,
                processed=True,
                type=rectype,
            ).save(using=db)


def remove_permissions(apps, _unused):
    Permission = apps.get_model("auth.Permission")
    Permission.objects.filter(
        codename__in=(
            "add_follower",
            "change_follower",
            "view_follower",
            "delete_follower",
            "add_scenario",
            "change_scenario",
            "delete_scenario",
            "view_scenario",
        )
    ).delete()


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
            and kcu.table_name in ('common_bucketdetail')
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
        ("common", "0016_meta"),
        ("common", "0017_sql_role"),
        ("common", "0018_promote_scenario"),
        ("common", "0019_scenario_url"),
        ("common", "0020_notifications"),
        ("common", "0021_notifications"),
        ("common", "0022_notifications"),
        ("common", "0023_notifications"),
        ("common", "0024_follower"),
        ("common", "0025_user_horizonbefore"),
        ("common", "0026_permissions"),
        ("common", "0027_last_currentdate"),
        ("common", "0028_comment_permission"),
        ("common", "0029_attributes"),
        ("common", "0030_remove_like_indexes"),
        ("common", "0031_user_default_scenario"),
    ]

    dependencies = [
        ("common", "0014_squashed_60"),
        ("contenttypes", "0002_remove_content_type_name"),
    ]

    operations = [
        migrations.AlterModelOptions(
            name="comment",
            options={
                "default_permissions": [],
                "ordering": ("id",),
                "verbose_name": "comment",
                "verbose_name_plural": "comments",
            },
        ),
        migrations.AlterModelOptions(
            name="scenario",
            options={
                "default_permissions": ("copy", "release"),
                "ordering": ["name"],
                "verbose_name": "scenario",
                "verbose_name_plural": "scenarios",
            },
        ),
        migrations.AlterModelOptions(
            name="userpreference",
            options={
                "default_permissions": [],
                "verbose_name": "preference",
                "verbose_name_plural": "preferences",
            },
        ),
        migrations.RunPython(
            code=grant_read_access,
        ),
        migrations.AlterModelOptions(
            name="Scenario",
            options={
                "db_table": "common_scenario",
                "ordering": ["name"],
                "permissions": (
                    ("copy_scenario", "Can copy a scenario"),
                    ("release_scenario", "Can release a scenario"),
                    ("promote_scenario", "Can promote a scenario"),
                ),
                "verbose_name": "scenario",
                "verbose_name_plural": "scenarios",
            },
        ),
        migrations.AddField(
            model_name="scenario",
            name="help_url",
            field=models.URLField(editable=False, null=True, verbose_name="help"),
        ),
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
                        to="common.comment",
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
                        to="contenttypes.contenttype",
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
        migrations.RunPython(
            code=grant_read_access_notification,
        ),
        migrations.RunPython(
            code=migrateAdminLog,
        ),
        migrations.RunSQL(
            sql="truncate table django_admin_log",
        ),
        migrations.AddField(
            model_name="notification",
            name="follower",
            field=models.ForeignKey(
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                to="common.follower",
                verbose_name="follower",
            ),
        ),
        migrations.AddField(
            model_name="follower",
            name="args",
            field=freppledb.common.fields.JSONBField(blank=True, null=True),
        ),
        migrations.CreateModel(
            name="SystemMessage",
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
            ],
            options={
                "managed": False,
                "default_permissions": (),
            },
        ),
        migrations.AddField(
            model_name="user",
            name="horizonbefore",
            field=models.IntegerField(blank=True, default=0, null=True),
        ),
        migrations.RunPython(
            code=remove_permissions,
        ),
        migrations.RunSQL(
            sql="\n            insert into common_parameter (name, value, description, lastmodified)\n            select\n            'last_currentdate',value,'This parameter is automatically populated. It stores the date of the last plan execution', now()\n            from common_parameter\n            where name = 'currentdate'\n            ON CONFLICT (name) DO NOTHING\n            ",
        ),
        migrations.AlterModelOptions(
            name="comment",
            options={"default_permissions": ("add",), "ordering": ("id",)},
        ),
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
                    models.CharField(choices=[], max_length=300, verbose_name="model"),
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
        migrations.RunPython(
            code=dropIndexLike,
        ),
        migrations.AddField(
            model_name="user",
            name="default_scenario",
            field=models.CharField(
                blank=True, max_length=300, null=True, verbose_name="default scenario"
            ),
        ),
    ]
