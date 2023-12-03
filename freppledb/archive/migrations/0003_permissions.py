#
# Copyright (C) 2021 by frePPLe bv
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

from django.db import migrations


def remove_permissions(apps, _unused):
    Permission = apps.get_model("auth.Permission")
    Permission.objects.filter(codename__contains="archive").delete()


class Migration(migrations.Migration):
    dependencies = [("archive", "0002_cascade_delete")]

    operations = [
        migrations.AlterModelOptions(
            name="archivedbuffer",
            options={
                "default_permissions": (),
                "ordering": ["item", "location", "batch"],
                "verbose_name": "archived buffer",
                "verbose_name_plural": "archived buffers",
            },
        ),
        migrations.AlterModelOptions(
            name="archiveddemand",
            options={
                "default_permissions": (),
                "ordering": ["priority", "due"],
                "verbose_name": "archived sales order",
                "verbose_name_plural": "archived sales orders",
            },
        ),
        migrations.AlterModelOptions(
            name="archivedoperationplan",
            options={
                "default_permissions": (),
                "ordering": ["reference"],
                "verbose_name": "operationplan",
                "verbose_name_plural": "operationplans",
            },
        ),
        migrations.AlterModelOptions(
            name="archivemanager",
            options={
                "default_permissions": (),
                "ordering": ["snapshot_date"],
                "verbose_name": "archive manager",
                "verbose_name_plural": "archive managers",
            },
        ),
        migrations.RunPython(remove_permissions),
    ]
