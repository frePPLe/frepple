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

from django.core.management import call_command
from django.conf import settings
from django.db import migrations, connections, DEFAULT_DB_ALIAS
import django.contrib.postgres.fields
import django.db.models.deletion
import django.utils.timezone
import freppledb.common.models
from django.db.models import Q
from django.db import migrations, models, transaction, DatabaseError

from freppledb.common.utils import get_databases


def recreateConstraintsCascade(apps, schema_editor):
    with connections[schema_editor.connection.alias].cursor() as cursor:
        cursor.execute("""
            select conname from pg_constraint
            inner join pg_class opplan on opplan.oid = pg_constraint.confrelid and opplan.relname = 'common_comment'
            inner join pg_class opm on opm.oid = pg_constraint.conrelid and opm.relname = 'common_notification'
            inner join pg_attribute on attname = 'comment_id' and attrelid = opm.oid and pg_attribute.attnum = any(conkey)
            """)
        cursor.execute(
            "alter table common_notification drop constraint %s" % cursor.fetchone()[0]
        )
        cursor.execute("""
            alter table common_notification
            add foreign key (comment_id)
            references public.common_comment(id) match simple
            on update no action
            on delete cascade
            deferrable initially deferred
            """)


def populateDatabaseField(apps, schema_editor):
    db = schema_editor.connection.alias
    if db == DEFAULT_DB_ALIAS:
        scenario_model = apps.get_model("common", "Scenario")
        user_model = apps.get_model("common", "User")
        user_scenarios = {}
        for sc in scenario_model.objects.using(db).filter(
            Q(status="In use") & ~Q(name=DEFAULT_DB_ALIAS)
        ):
            for u in (
                user_model.objects.using(sc.name)
                .filter(is_active=True)
                .only("is_active")
            ):
                if u.pk in user_scenarios:
                    user_scenarios[u.pk].append(sc.name)
                else:
                    user_scenarios[u.pk] = [sc.name]
        for u in user_model.objects.using(DEFAULT_DB_ALIAS).filter(is_active=True):
            if u.pk in user_scenarios:
                user_scenarios[u.pk].append(DEFAULT_DB_ALIAS)
            else:
                user_scenarios[u.pk] = [DEFAULT_DB_ALIAS]
            u.databases = user_scenarios[u.pk]
            u.save(update_fields=["databases"], using=DEFAULT_DB_ALIAS)


def updateScenarioInfo(apps, schema_editor):
    from ...execute.models import ScheduledTask

    try:
        if not schema_editor.connection.settings_dict.get(
            "TEST"
        ) or schema_editor.connection.settings_dict.get("TEST").get(
            "NAME"
        ) != schema_editor.connection.settings_dict.get(
            "NAME"
        ):
            with transaction.atomic(using=schema_editor.connection.alias):
                ScheduledTask.updateScenario(schema_editor.connection.alias)
    except Exception as e:
        # On a new schema, the execute app may not be installed yet.
        # This is not a problem as it won't have any scheduled tasks then.
        pass


def alterRoleSetLogin(apps, schema_editor):
    db = schema_editor.connection.alias
    if get_databases()[db].get("SQL_ROLE"):
        try:
            with transaction.atomic(using=db):
                with connections[db].cursor() as cursor:
                    cursor.execute(
                        f"alter role {get_databases()[db].get('SQL_ROLE')} with login password '{get_databases()[db].get('PASSWORD')}'"
                    )
        except DatabaseError:
            pass


def alterRoleSetNoLogin(apps, schema_editor):
    db = schema_editor.connection.alias
    if get_databases()[db].get("SQL_ROLE"):
        try:
            with transaction.atomic(using=db):
                with connections[db].cursor() as cursor:
                    cursor.execute(
                        f"alter role {get_databases()[db].get('SQL_ROLE')} with nologin"
                    )
        except DatabaseError:
            pass


def loadParameters(apps, schema_editor):
    from django.core.management.commands.loaddata import Command

    call_command(
        Command(),
        "parameters.json",
        app_label="common",
        verbosity=0,
        database=schema_editor.connection.alias,
    )


def removeParameters(apps, schema_editor):
    db = schema_editor.connection.alias
    with connections[db].cursor() as cursor:
        cursor.execute(
            "delete from common_parameter where name in ('scenarios', 'optional_apps')"
        )


class Migration(migrations.Migration):

    replaces = [
        ("common", "0033_squash_70_post"),
        ("common", "0034_alter_model_options"),
        ("common", "0035_user_scenario_themes"),
        ("common", "0036_user_databases"),
        ("common", "0037_user_databases"),
        ("common", "0038_scenario"),
        ("common", "0039_date_time_format"),
        ("common", "0040_add_delete_scenario_permissions"),
        ("common", "0041_sqlrole_setlogin"),
        ("common", "0042_varchar_max_length"),
        ("common", "0043_apikey"),
        ("common", "0044_parameters"),
    ]

    dependencies = [
        ("common", "0032_squash_70"),
        ("contenttypes", "0002_remove_content_type_name"),
    ]

    operations = [
        migrations.RunPython(
            code=recreateConstraintsCascade,
        ),
        migrations.RunSQL(
            sql="update common_comment set object_repr = object_pk, type='comment', processed=true",
        ),
        migrations.AlterModelOptions(
            name="comment",
            options={
                "default_permissions": ("add",),
                "ordering": ("id",),
                "verbose_name": "comment",
                "verbose_name_plural": "comments",
            },
        ),
        migrations.AlterModelOptions(
            name="follower",
            options={
                "default_permissions": (),
                "verbose_name": "follower",
                "verbose_name_plural": "followers",
            },
        ),
        migrations.AlterModelOptions(
            name="notification",
            options={
                "default_permissions": [],
                "verbose_name": "notification",
                "verbose_name_plural": "notifications",
            },
        ),
        migrations.AlterModelOptions(
            name="scenario",
            options={
                "default_permissions": ("copy", "release", "promote"),
                "ordering": ["name"],
                "verbose_name": "scenario",
                "verbose_name_plural": "scenarios",
            },
        ),
        migrations.AddField(
            model_name="user",
            name="scenario_themes",
            field=models.JSONField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name="user",
            name="databases",
            field=django.contrib.postgres.fields.ArrayField(
                base_field=models.CharField(max_length=300, verbose_name="databases"),
                null=True,
                size=None,
            ),
        ),
        migrations.RunPython(
            code=populateDatabaseField,
            reverse_code=migrations.RunPython.noop,
        ),
        migrations.RemoveField(
            model_name="scenario",
            name="lastrefresh",
        ),
        migrations.AddField(
            model_name="scenario",
            name="info",
            field=models.JSONField(blank=True, null=True),
        ),
        migrations.AlterField(
            model_name="user",
            name="databases",
            field=django.contrib.postgres.fields.ArrayField(
                base_field=models.CharField(max_length=300, verbose_name="databases"),
                default=freppledb.common.models.defaultdatabase,
                null=True,
                size=None,
            ),
        ),
        migrations.RunPython(
            code=updateScenarioInfo,
            reverse_code=migrations.RunPython.noop,
            hints={"allow_atomic": False},
        ),
        migrations.RunSQL(
            sql="\n            insert into common_parameter (name, value, description, lastmodified)\n            select\n            'display_time','true','This parameter applies to ALL scenarios and controls if date time fields should display the time. Accepted values: true or false', now()\n            from common_parameter\n            ON CONFLICT (name) DO NOTHING;\n            insert into common_parameter (name, value, description, lastmodified)\n            select\n            'date_format','year-month-day','This parameter applies to ALL scenarios. Accepted values: month-day-year, day-month-year, year-month-day.', now()\n            from common_parameter\n            ON CONFLICT (name) DO NOTHING;\n            ",
            reverse_sql="delete from common_parameter where name in ('display_time','date_format')",
        ),
        migrations.AlterModelOptions(
            name="scenario",
            options={
                "default_permissions": ("copy", "release", "promote", "add", "delete"),
                "ordering": ["name"],
                "verbose_name": "scenario",
                "verbose_name_plural": "scenarios",
            },
        ),
        migrations.RunPython(code=alterRoleSetLogin, reverse_code=alterRoleSetNoLogin),
        migrations.AlterField(
            model_name="attribute",
            name="label",
            field=models.CharField(db_index=True, verbose_name="label"),
        ),
        migrations.AlterField(
            model_name="attribute",
            name="model",
            field=models.CharField(verbose_name="model"),
        ),
        migrations.AlterField(
            model_name="attribute",
            name="name",
            field=models.CharField(db_index=True, verbose_name="name"),
        ),
        migrations.AlterField(
            model_name="attribute",
            name="source",
            field=models.CharField(
                blank=True, db_index=True, null=True, verbose_name="source"
            ),
        ),
        migrations.AlterField(
            model_name="attribute",
            name="type",
            field=models.CharField(verbose_name="type"),
        ),
        migrations.AlterField(
            model_name="bucket",
            name="description",
            field=models.CharField(blank=True, null=True, verbose_name="description"),
        ),
        migrations.AlterField(
            model_name="bucket",
            name="name",
            field=models.CharField(
                primary_key=True, serialize=False, verbose_name="name"
            ),
        ),
        migrations.AlterField(
            model_name="bucket",
            name="source",
            field=models.CharField(
                blank=True, db_index=True, null=True, verbose_name="source"
            ),
        ),
        migrations.AlterField(
            model_name="bucketdetail",
            name="name",
            field=models.CharField(db_index=True, verbose_name="name"),
        ),
        migrations.AlterField(
            model_name="bucketdetail",
            name="source",
            field=models.CharField(
                blank=True, db_index=True, null=True, verbose_name="source"
            ),
        ),
        migrations.AlterField(
            model_name="comment",
            name="comment",
            field=models.TextField(verbose_name="message"),
        ),
        migrations.AlterField(
            model_name="comment",
            name="content_type",
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.CASCADE,
                related_name="content_type_set_for_%(class)s",
                to="contenttypes.contenttype",
                verbose_name="content type",
            ),
        ),
        migrations.AlterField(
            model_name="comment",
            name="object_repr",
            field=models.CharField(verbose_name="object repr"),
        ),
        migrations.AlterField(
            model_name="comment",
            name="type",
            field=models.CharField(default="add", verbose_name="type"),
        ),
        migrations.AlterField(
            model_name="follower",
            name="args",
            field=models.JSONField(blank=True, null=True),
        ),
        migrations.AlterField(
            model_name="follower",
            name="content_type",
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.CASCADE,
                to="contenttypes.contenttype",
                verbose_name="model name",
            ),
        ),
        migrations.AlterField(
            model_name="follower",
            name="object_pk",
            field=models.TextField(null=True, verbose_name="object name"),
        ),
        migrations.AlterField(
            model_name="follower",
            name="type",
            field=models.CharField(
                choices=[("M", "email"), ("O", "online")],
                default="O",
                verbose_name="type",
            ),
        ),
        migrations.AlterField(
            model_name="follower",
            name="user",
            field=models.ForeignKey(
                blank=True,
                on_delete=django.db.models.deletion.CASCADE,
                to=settings.AUTH_USER_MODEL,
                verbose_name="user",
            ),
        ),
        migrations.AlterField(
            model_name="notification",
            name="status",
            field=models.CharField(
                choices=[("U", "unread"), ("R", "read")],
                default="U",
                verbose_name="status",
            ),
        ),
        migrations.AlterField(
            model_name="notification",
            name="type",
            field=models.CharField(
                choices=[("M", "email"), ("O", "online")],
                default="O",
                verbose_name="type",
            ),
        ),
        migrations.AlterField(
            model_name="parameter",
            name="description",
            field=models.CharField(blank=True, null=True, verbose_name="description"),
        ),
        migrations.AlterField(
            model_name="parameter",
            name="name",
            field=models.CharField(
                primary_key=True, serialize=False, verbose_name="name"
            ),
        ),
        migrations.AlterField(
            model_name="parameter",
            name="source",
            field=models.CharField(
                blank=True, db_index=True, null=True, verbose_name="source"
            ),
        ),
        migrations.AlterField(
            model_name="parameter",
            name="value",
            field=models.CharField(blank=True, null=True, verbose_name="value"),
        ),
        migrations.AlterField(
            model_name="scenario",
            name="description",
            field=models.CharField(blank=True, null=True, verbose_name="description"),
        ),
        migrations.AlterField(
            model_name="scenario",
            name="name",
            field=models.CharField(
                primary_key=True, serialize=False, verbose_name="name"
            ),
        ),
        migrations.AlterField(
            model_name="scenario",
            name="status",
            field=models.CharField(
                choices=[("free", "free"), ("in use", "in use"), ("busy", "busy")],
                verbose_name="status",
            ),
        ),
        migrations.AlterField(
            model_name="user",
            name="databases",
            field=django.contrib.postgres.fields.ArrayField(
                base_field=models.CharField(verbose_name="databases"),
                default=freppledb.common.models.defaultdatabase,
                null=True,
                size=None,
            ),
        ),
        migrations.AlterField(
            model_name="user",
            name="default_scenario",
            field=models.CharField(
                blank=True, null=True, verbose_name="default scenario"
            ),
        ),
        migrations.AlterField(
            model_name="user",
            name="first_name",
            field=models.CharField(
                blank=True, max_length=150, verbose_name="first name"
            ),
        ),
        migrations.AlterField(
            model_name="user",
            name="horizonbuckets",
            field=models.CharField(blank=True, null=True),
        ),
        migrations.AlterField(
            model_name="user",
            name="horizontype",
            field=models.BooleanField(blank=True, default=True),
        ),
        migrations.AlterField(
            model_name="user",
            name="horizonunit",
            field=models.CharField(
                blank=True,
                choices=[("day", "day"), ("week", "week"), ("month", "month")],
                default="month",
                null=True,
            ),
        ),
        migrations.AlterField(
            model_name="user",
            name="language",
            field=models.CharField(default="en", verbose_name="language"),
        ),
        migrations.AlterField(
            model_name="user",
            name="last_name",
            field=models.CharField(
                blank=True, max_length=150, verbose_name="last name"
            ),
        ),
        migrations.AlterField(
            model_name="user",
            name="theme",
            field=models.CharField(default="earth", verbose_name="theme"),
        ),
        migrations.AlterField(
            model_name="userpreference",
            name="property",
            field=models.CharField(),
        ),
        migrations.AlterField(
            model_name="userpreference",
            name="value",
            field=models.JSONField(),
        ),
        migrations.CreateModel(
            name="APIKey",
            fields=[
                (
                    "id",
                    models.AutoField(
                        primary_key=True, serialize=False, verbose_name="identifier"
                    ),
                ),
                ("name", models.CharField()),
                ("expiry_date", models.DateTimeField(verbose_name="expiry date")),
                (
                    "created",
                    models.DateTimeField(
                        default=django.utils.timezone.now, editable=False
                    ),
                ),
                (
                    "hashed_key",
                    models.CharField(editable=False, max_length=150, unique=True),
                ),
                (
                    "user",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="api_keys",
                        to=settings.AUTH_USER_MODEL,
                        verbose_name="user",
                    ),
                ),
            ],
            options={
                "verbose_name": "API key",
                "verbose_name_plural": "API keys",
                "db_table": "common_apikey",
            },
        ),
        migrations.RunPython(
            code=loadParameters,
            reverse_code=removeParameters,
        ),
    ]
