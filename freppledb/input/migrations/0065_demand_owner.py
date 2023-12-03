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

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("input", "0064_opm_opr_sequence_cycle"),
    ]

    operations = [
        migrations.RemoveField(
            model_name="demand",
            name="lft",
        ),
        migrations.RemoveField(
            model_name="demand",
            name="lvl",
        ),
        migrations.RemoveField(
            model_name="demand",
            name="rght",
        ),
        migrations.AddField(
            model_name="demand",
            name="policy",
            field=models.CharField(
                blank=True,
                choices=[
                    ("independent", "independent"),
                    ("alltogether", "all together"),
                    ("inratio", "in ratio"),
                ],
                default="independent",
                help_text="Defines how sales orders are shipped together",
                max_length=15,
                null=True,
                verbose_name="policy",
            ),
        ),
        migrations.AlterField(
            model_name="demand",
            name="owner",
            field=models.CharField(
                blank=True,
                db_index=True,
                max_length=300,
                null=True,
                verbose_name="owner",
            ),
        ),
    ]
