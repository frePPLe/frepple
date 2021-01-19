#
# Copyright (C) 2021 by frePPLe bv
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

from django.db import migrations


def remove_permissions(apps, _unused):
    Permission = apps.get_model("auth.Permission")
    Permission.objects.filter(
        codename__in=(
            "add_follower",
            "change_follower",
            "view_follower",
            "delete_follower",
            "add_scenario",
            "change_scenario",
            "delete_scenario",
            "view_scenario",
        )
    ).delete()


class Migration(migrations.Migration):

    dependencies = [("common", "0025_user_horizonbefore")]

    operations = [migrations.RunPython(remove_permissions)]
