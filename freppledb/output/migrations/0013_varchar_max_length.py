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

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("output", "0012_resourcesummary_load_confirmed"),
    ]

    operations = [
        migrations.AlterField(
            model_name="constraint",
            name="demand",
            field=models.CharField(db_index=True, null=True, verbose_name="demand"),
        ),
        migrations.AlterField(
            model_name="constraint",
            name="description",
            field=models.CharField(verbose_name="description"),
        ),
        migrations.AlterField(
            model_name="constraint",
            name="entity",
            field=models.CharField(db_index=True, verbose_name="entity"),
        ),
        migrations.AlterField(
            model_name="constraint",
            name="forecast",
            field=models.CharField(db_index=True, null=True, verbose_name="forecast"),
        ),
        migrations.AlterField(
            model_name="constraint",
            name="item",
            field=models.CharField(db_index=True, null=True, verbose_name="item"),
        ),
        migrations.AlterField(
            model_name="constraint",
            name="name",
            field=models.CharField(db_index=True, verbose_name="name"),
        ),
        migrations.AlterField(
            model_name="constraint",
            name="owner",
            field=models.CharField(db_index=True, verbose_name="owner"),
        ),
        migrations.AlterField(
            model_name="problem",
            name="description",
            field=models.CharField(verbose_name="description"),
        ),
        migrations.AlterField(
            model_name="problem",
            name="entity",
            field=models.CharField(db_index=True, verbose_name="entity"),
        ),
        migrations.AlterField(
            model_name="problem",
            name="name",
            field=models.CharField(db_index=True, verbose_name="name"),
        ),
        migrations.AlterField(
            model_name="problem",
            name="owner",
            field=models.CharField(db_index=True, verbose_name="owner"),
        ),
        migrations.AlterField(
            model_name="resourcesummary",
            name="resource",
            field=models.CharField(verbose_name="resource"),
        ),
    ]
