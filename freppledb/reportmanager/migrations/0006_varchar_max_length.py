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
        ("reportmanager", "0005_alter_model_options"),
    ]

    operations = [
        migrations.AlterField(
            model_name="sqlcolumn",
            name="format",
            field=models.CharField(blank=True, null=True, verbose_name="format"),
        ),
        migrations.AlterField(
            model_name="sqlcolumn",
            name="name",
            field=models.CharField(verbose_name="name"),
        ),
        migrations.AlterField(
            model_name="sqlreport",
            name="description",
            field=models.CharField(blank=True, null=True, verbose_name="description"),
        ),
        migrations.AlterField(
            model_name="sqlreport",
            name="name",
            field=models.CharField(db_index=True, verbose_name="name"),
        ),
        migrations.AlterField(
            model_name="sqlreport",
            name="public",
            field=models.BooleanField(blank=True, default=False),
        ),
        migrations.AlterField(
            model_name="sqlreport",
            name="source",
            field=models.CharField(
                blank=True, db_index=True, null=True, verbose_name="source"
            ),
        ),
    ]
