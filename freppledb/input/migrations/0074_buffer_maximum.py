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

import datetime
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):
    dependencies = [
        ("input", "0073_operation_dependency"),
    ]

    operations = [
        migrations.AddField(
            model_name="buffer",
            name="maximum",
            field=models.DecimalField(
                blank=True,
                decimal_places=8,
                default="0.00",
                help_text="maximum stock",
                max_digits=20,
                null=True,
                verbose_name="maximum",
            ),
        ),
        migrations.AddField(
            model_name="buffer",
            name="maximum_calendar",
            field=models.ForeignKey(
                blank=True,
                help_text="Calendar storing a time-dependent maximum stock profile",
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name="buffermaxima",
                to="input.calendar",
                verbose_name="maximum calendar",
            ),
        ),
        migrations.AlterField(
            model_name="buffer",
            name="minimum_calendar",
            field=models.ForeignKey(
                blank=True,
                help_text="Calendar storing a time-dependent safety stock profile",
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name="bufferminima",
                to="input.calendar",
                verbose_name="minimum calendar",
            ),
        ),
    ]
