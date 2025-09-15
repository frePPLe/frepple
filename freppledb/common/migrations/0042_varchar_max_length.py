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

from django.conf import settings
import django.contrib.postgres.fields
from django.db import migrations, models
import django.db.models.deletion
import freppledb.common.models


class Migration(migrations.Migration):
    dependencies = [
        ("contenttypes", "0002_remove_content_type_name"),
        ("common", "0041_sqlrole_setlogin"),
    ]

    operations = [
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
            field=models.CharField(
                default="en",
                verbose_name="language",
            ),
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
            field=models.CharField(
                default="earth",
                verbose_name="theme",
            ),
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
    ]
