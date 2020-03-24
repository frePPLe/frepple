#
# Copyright (C) 2020 by frePPLe bvba
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
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [("input", "0047_mto")]

    operations = [
        migrations.AddField(
            model_name="setuprule",
            name="resource",
            field=models.ForeignKey(
                blank=True,
                help_text="Extra resource used during this changeover",
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name="setuprules",
                to="input.Resource",
                verbose_name="resource",
            ),
        )
    ]
