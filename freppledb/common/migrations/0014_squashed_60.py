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

from datetime import datetime

from django.conf import settings
import django.contrib.auth.models
from django.contrib.auth.hashers import make_password
from django.contrib.auth.validators import UnicodeUsernameValidator
from django.db import migrations, models
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


class Migration(migrations.Migration):
    replaces = [
        ("common", "0001_initial"),
        ("common", "0008_squashed_41"),
        ("common", "0009_jsonb"),
        ("common", "0010_remove_wizard"),
        ("common", "0011_username"),
        ("common", "0012_adminLT_param"),
        ("common", "0013_currency_param"),
    ]

    initial = True

    dependencies = [
        ("auth", "0006_require_contenttypes_0002"),
        ("contenttypes", "0002_remove_content_type_name"),
    ]

    operations = [
        migrations.CreateModel(
            name="User",
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
                ("password", models.CharField(max_length=128, verbose_name="password")),
                (
                    "last_login",
                    models.DateTimeField(
                        blank=True, null=True, verbose_name="last login"
                    ),
                ),
                (
                    "is_superuser",
                    models.BooleanField(
                        default=False,
                        help_text="Designates that this user has all permissions without explicitly assigning them.",
                        verbose_name="superuser status",
                    ),
                ),
                (
                    "username",
                    models.CharField(
                        error_messages={
                            "unique": "A user with that username already exists."
                        },
                        help_text="Required. 150 characters or fewer. Letters, digits and @/./+/-/_ only.",
                        max_length=150,
                        unique=True,
                        validators=[UnicodeUsernameValidator()],
                        verbose_name="username",
                    ),
                ),
                (
                    "first_name",
                    models.CharField(
                        blank=True, max_length=30, verbose_name="first name"
                    ),
                ),
                (
                    "last_name",
                    models.CharField(
                        blank=True, max_length=30, verbose_name="last name"
                    ),
                ),
                (
                    "email",
                    models.EmailField(
                        blank=True, max_length=254, verbose_name="email address"
                    ),
                ),
                (
                    "is_staff",
                    models.BooleanField(
                        default=False,
                        help_text="Designates whether the user can log into this admin site.",
                        verbose_name="staff status",
                    ),
                ),
                (
                    "is_active",
                    models.BooleanField(
                        default=True,
                        help_text="Designates whether this user should be treated as active. Unselect this instead of deleting accounts.",
                        verbose_name="active",
                    ),
                ),
                (
                    "date_joined",
                    models.DateTimeField(
                        default=django.utils.timezone.now, verbose_name="date joined"
                    ),
                ),
                (
                    "language",
                    models.CharField(
                        choices=[
                            ("auto", "Detect automatically"),
                            ("en", "English"),
                            ("fr", "French"),
                            ("de", "German"),
                            ("he", "Hebrew"),
                            ("it", "Italian"),
                            ("ja", "Japanese"),
                            ("nl", "Dutch"),
                            ("pt", "Portuguese"),
                            ("pt-br", "Brazilian Portuguese"),
                            ("ru", "Russian"),
                            ("es", "Spanish"),
                            ("zh-cn", "Simplified Chinese"),
                            ("zh-tw", "Traditional Chinese"),
                        ],
                        default="auto",
                        max_length=10,
                        verbose_name="language",
                    ),
                ),
                (
                    "theme",
                    models.CharField(
                        choices=[
                            ("earth", "Earth"),
                            ("grass", "Grass"),
                            ("lemon", "Lemon"),
                            ("odoo", "Odoo"),
                            ("openbravo", "Openbravo"),
                            ("orange", "Orange"),
                            ("snow", "Snow"),
                            ("strawberry", "Strawberry"),
                            ("water", "Water"),
                        ],
                        default="earth",
                        max_length=20,
                        verbose_name="theme",
                    ),
                ),
                (
                    "pagesize",
                    models.PositiveIntegerField(default=100, verbose_name="page size"),
                ),
                (
                    "horizonbuckets",
                    models.CharField(blank=True, max_length=300, null=True),
                ),
                ("horizonstart", models.DateTimeField(blank=True, null=True)),
                ("horizonend", models.DateTimeField(blank=True, null=True)),
                ("horizontype", models.BooleanField(default=True)),
                (
                    "horizonlength",
                    models.IntegerField(blank=True, default=6, null=True),
                ),
                (
                    "horizonunit",
                    models.CharField(
                        blank=True,
                        choices=[("day", "day"), ("week", "week"), ("month", "month")],
                        default="month",
                        max_length=5,
                        null=True,
                    ),
                ),
                (
                    "lastmodified",
                    models.DateTimeField(
                        auto_now=True,
                        db_index=True,
                        null=True,
                        verbose_name="last modified",
                    ),
                ),
                (
                    "groups",
                    models.ManyToManyField(
                        blank=True,
                        help_text="The groups this user belongs to. A user will get all permissions granted to each of their groups.",
                        related_name="user_set",
                        related_query_name="user",
                        to="auth.Group",
                        verbose_name="groups",
                    ),
                ),
                (
                    "user_permissions",
                    models.ManyToManyField(
                        blank=True,
                        help_text="Specific permissions for this user.",
                        related_name="user_set",
                        related_query_name="user",
                        to="auth.Permission",
                        verbose_name="user permissions",
                    ),
                ),
            ],
            options={
                "db_table": "common_user",
                "verbose_name": "user",
                "verbose_name_plural": "users",
            },
            managers=[("objects", django.contrib.auth.models.UserManager())],
        ),
        migrations.CreateModel(
            name="Bucket",
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
                    "name",
                    models.CharField(
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
                    "level",
                    models.IntegerField(
                        help_text="Higher values indicate more granular time buckets",
                        verbose_name="level",
                    ),
                ),
            ],
            options={
                "db_table": "common_bucket",
                "verbose_name": "bucket",
                "verbose_name_plural": "buckets",
            },
        ),
        migrations.CreateModel(
            name="Comment",
            fields=[
                (
                    "id",
                    models.AutoField(
                        primary_key=True, serialize=False, verbose_name="identifier"
                    ),
                ),
                ("object_pk", models.TextField(verbose_name="object id")),
                ("comment", models.TextField(max_length=3000, verbose_name="comment")),
                (
                    "lastmodified",
                    models.DateTimeField(
                        default=django.utils.timezone.now,
                        editable=False,
                        verbose_name="last modified",
                    ),
                ),
                (
                    "content_type",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="content_type_set_for_comment",
                        to="contenttypes.ContentType",
                        verbose_name="content type",
                    ),
                ),
                (
                    "user",
                    models.ForeignKey(
                        blank=True,
                        editable=False,
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        to=settings.AUTH_USER_MODEL,
                        verbose_name="user",
                    ),
                ),
            ],
            options={
                "db_table": "common_comment",
                "ordering": ("id",),
                "verbose_name_plural": "comments",
                "verbose_name": "comment",
            },
        ),
        migrations.CreateModel(
            name="Parameter",
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
                    "name",
                    models.CharField(
                        max_length=60,
                        primary_key=True,
                        serialize=False,
                        verbose_name="name",
                    ),
                ),
                (
                    "value",
                    models.CharField(
                        blank=True, max_length=1000, null=True, verbose_name="value"
                    ),
                ),
                (
                    "description",
                    models.CharField(
                        blank=True,
                        max_length=1000,
                        null=True,
                        verbose_name="description",
                    ),
                ),
            ],
            options={
                "db_table": "common_parameter",
                "verbose_name": "parameter",
                "verbose_name_plural": "parameters",
                "abstract": False,
            },
        ),
        migrations.CreateModel(
            name="Scenario",
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
                    "description",
                    models.CharField(
                        blank=True,
                        max_length=500,
                        null=True,
                        verbose_name="description",
                    ),
                ),
                (
                    "status",
                    models.CharField(
                        choices=[
                            ("free", "free"),
                            ("in use", "in use"),
                            ("busy", "busy"),
                        ],
                        max_length=10,
                        verbose_name="status",
                    ),
                ),
                (
                    "lastrefresh",
                    models.DateTimeField(
                        editable=False, null=True, verbose_name="last refreshed"
                    ),
                ),
            ],
            options={
                "db_table": "common_scenario",
                "ordering": ["name"],
                "verbose_name_plural": "scenarios",
                "verbose_name": "scenario",
                "permissions": (
                    ("copy_scenario", "Can copy a scenario"),
                    ("release_scenario", "Can release a scenario"),
                ),
            },
        ),
        migrations.CreateModel(
            name="BucketDetail",
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
                ("startdate", models.DateTimeField(verbose_name="start date")),
                ("enddate", models.DateTimeField(verbose_name="end date")),
                (
                    "bucket",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        to="common.Bucket",
                        verbose_name="bucket",
                    ),
                ),
            ],
            options={
                "db_table": "common_bucketdetail",
                "ordering": ["bucket", "startdate"],
                "verbose_name_plural": "bucket dates",
                "verbose_name": "bucket date",
                "unique_together": {("bucket", "startdate")},
            },
        ),
        migrations.CreateModel(
            name="UserPreference",
            fields=[
                (
                    "id",
                    models.AutoField(
                        primary_key=True, serialize=False, verbose_name="identifier"
                    ),
                ),
                ("property", models.CharField(max_length=100)),
                ("value", freppledb.common.fields.JSONBField(max_length=1000)),
                (
                    "user",
                    models.ForeignKey(
                        editable=False,
                        null=True,
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="preferences",
                        to=settings.AUTH_USER_MODEL,
                        verbose_name="user",
                    ),
                ),
            ],
            options={
                "verbose_name_plural": "preferences",
                "verbose_name": "preference",
                "db_table": "common_preference",
                "unique_together": {("user", "property")},
            },
        ),
        migrations.RunPython(code=createAdminUser),
    ]
