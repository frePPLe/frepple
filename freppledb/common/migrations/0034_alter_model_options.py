#
# Copyright (C) 2024 by frePPLe bv
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
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):
    dependencies = [
        ("contenttypes", "0002_remove_content_type_name"),
        ("common", "0033_squash_70_post"),
    ]

    operations = [
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
    ]
