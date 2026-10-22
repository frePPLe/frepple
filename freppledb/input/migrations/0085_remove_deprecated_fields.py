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

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("input", "0084_parameter_plan_solver"),
    ]

    operations = [
        migrations.RemoveField(
            model_name="operationplanmaterial",
            name="status",
        ),
        migrations.RemoveField(
            model_name="operationplanresource",
            name="status",
        ),
        migrations.RemoveField(
            model_name="supplier",
            name="lft",
        ),
        migrations.RemoveField(
            model_name="supplier",
            name="lvl",
        ),
        migrations.RemoveField(
            model_name="supplier",
            name="owner",
        ),
        migrations.RemoveField(
            model_name="supplier",
            name="rght",
        ),
        migrations.RemoveField(
            model_name="operation",
            name="transferbatch",
        ),
        migrations.DeleteModel(
            name="SubOperation",
        ),
    ]
