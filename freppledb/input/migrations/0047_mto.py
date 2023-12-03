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

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [("input", "0046_sql_role")]

    operations = [
        migrations.AlterModelOptions(
            name="buffer",
            options={
                "ordering": ["item", "location", "batch"],
                "verbose_name": "buffer",
                "verbose_name_plural": "buffers",
            },
        ),
        migrations.AddField(
            model_name="buffer",
            name="batch",
            field=models.CharField(
                blank=True, max_length=300, null=True, verbose_name="batch"
            ),
        ),
        migrations.AlterUniqueTogether(
            name="buffer", unique_together={("item", "location", "batch")}
        ),
        migrations.AddField(
            model_name="demand",
            name="batch",
            field=models.CharField(
                blank=True,
                db_index=True,
                help_text="MTO batch name",
                max_length=300,
                null=True,
                verbose_name="batch",
            ),
        ),
        migrations.AddField(
            model_name="item",
            name="type",
            field=models.CharField(
                blank=True,
                choices=[
                    ("make to stock", "make to stock"),
                    ("make to order", "make to order"),
                ],
                max_length=20,
                null=True,
                verbose_name="type",
            ),
        ),
        migrations.AddField(
            model_name="operationplan",
            name="batch",
            field=models.CharField(
                blank=True,
                db_index=True,
                help_text="MTO batch name",
                max_length=300,
                null=True,
                verbose_name="batch",
            ),
        ),
    ]
