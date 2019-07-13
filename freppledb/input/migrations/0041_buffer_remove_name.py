#
# Copyright (C) 2019 by frePPLe bvba
#
# This library is free software; you can redistribute it and/or modify it
# under the terms of the GNU Affero General Public License as published
# by the Free Software Foundation; either version 3 of the License, or
# (at your option) any later version.
#
# This library is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU Affero
# General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public
# License along with this program.  If not, see <http://www.gnu.org/licenses/>.
#

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [("input", "0040_autofence_parameter")]

    operations = [
        migrations.AlterModelOptions(
            name="buffer",
            options={
                "ordering": ["item", "location"],
                "verbose_name": "buffer",
                "verbose_name_plural": "buffers",
            },
        ),
        migrations.RemoveField(model_name="buffer", name="name"),
        migrations.AddField(
            model_name="buffer",
            name="id",
            field=models.AutoField(
                primary_key=True, serialize=False, verbose_name="identifier"
            ),
            preserve_default=False,
        ),
    ]
