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

from django.db import migrations, models

from freppledb.common.migrate import AttributeMigration


class Migration(AttributeMigration):
    extends_app_label = "input"

    dependencies = [("input", "0044_squashed_60")]

    operations = [
        migrations.AddField(
            model_name="item",
            name="latedemandcount",
            field=models.IntegerField(
                blank=True,
                db_index=True,
                null=True,
                verbose_name="count of late demands",
            ),
        ),
        migrations.AddField(
            model_name="item",
            name="latedemandquantity",
            field=models.DecimalField(
                blank=True,
                db_index=True,
                decimal_places=8,
                max_digits=20,
                null=True,
                verbose_name="quantity of late demands",
            ),
        ),
        migrations.AddField(
            model_name="item",
            name="latedemandvalue",
            field=models.DecimalField(
                blank=True,
                db_index=True,
                decimal_places=8,
                max_digits=20,
                null=True,
                verbose_name="value of late demand",
            ),
        ),
        migrations.AddField(
            model_name="item",
            name="unplanneddemandcount",
            field=models.DecimalField(
                blank=True,
                db_index=True,
                decimal_places=8,
                max_digits=20,
                null=True,
                verbose_name="count of unplanned demands",
            ),
        ),
        migrations.AddField(
            model_name="item",
            name="unplanneddemandquantity",
            field=models.DecimalField(
                blank=True,
                db_index=True,
                decimal_places=8,
                max_digits=20,
                null=True,
                verbose_name="quantity of unplanned demands",
            ),
        ),
        migrations.AddField(
            model_name="item",
            name="unplanneddemandvalue",
            field=models.DecimalField(
                blank=True,
                db_index=True,
                decimal_places=8,
                max_digits=20,
                null=True,
                verbose_name="value of unplanned demands",
            ),
        ),
        migrations.AddField(
            model_name="resource",
            name="overloadcount",
            field=models.IntegerField(
                blank=True,
                db_index=True,
                null=True,
                verbose_name="count of capacity overload problems",
            ),
        ),
    ]
