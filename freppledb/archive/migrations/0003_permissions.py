#
# Copyright (C) 2021 by frePPLe bv
#
# This library is free software; you can redistribute it and/or modify it
# under the terms of the GNU Affero General Public License as published
# by the Free Software Foundation; either version 3 of the License, or
#
# This library is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU Affero
# General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public
# License along with this program.  If not, see <http://www.gnu.org/licenses/>.
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
