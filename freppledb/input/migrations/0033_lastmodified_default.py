#
# Copyright (C) 2018 by frePPLe bv
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


class Migration(migrations.Migration):

    dependencies = [("input", "0032_operationresource_quantityfixed")]

    operations = [
        migrations.RunSQL(
            "alter table buffer alter column lastmodified set default now()"
        ),
        migrations.RunSQL(
            "alter table calendar alter column lastmodified set default now()"
        ),
        migrations.RunSQL(
            "alter table calendarbucket alter column lastmodified set default now()"
        ),
        migrations.RunSQL(
            "alter table common_bucket alter column lastmodified set default now()"
        ),
        migrations.RunSQL(
            "alter table common_bucketdetail alter column lastmodified set default now()"
        ),
        migrations.RunSQL(
            "alter table common_comment alter column lastmodified set default now()"
        ),
        migrations.RunSQL(
            "alter table common_parameter alter column lastmodified set default now()"
        ),
        migrations.RunSQL(
            "alter table common_user alter column lastmodified set default now()"
        ),
        migrations.RunSQL(
            "alter table customer alter column lastmodified set default now()"
        ),
        migrations.RunSQL(
            "alter table demand alter column lastmodified set default now()"
        ),
        migrations.RunSQL(
            "alter table item alter column lastmodified set default now()"
        ),
        migrations.RunSQL(
            "alter table itemdistribution alter column lastmodified set default now()"
        ),
        migrations.RunSQL(
            "alter table itemsupplier alter column lastmodified set default now()"
        ),
        migrations.RunSQL(
            "alter table location alter column lastmodified set default now()"
        ),
        migrations.RunSQL(
            "alter table operation alter column lastmodified set default now()"
        ),
        migrations.RunSQL(
            "alter table operationmaterial alter column lastmodified set default now()"
        ),
        migrations.RunSQL(
            "alter table operationplan alter column lastmodified set default now()"
        ),
        migrations.RunSQL(
            "alter table operationplanmaterial alter column lastmodified set default now()"
        ),
        migrations.RunSQL(
            "alter table operationplanresource alter column lastmodified set default now()"
        ),
        migrations.RunSQL(
            "alter table operationresource alter column lastmodified set default now()"
        ),
        migrations.RunSQL(
            "alter table resource alter column lastmodified set default now()"
        ),
        migrations.RunSQL(
            "alter table resourceskill alter column lastmodified set default now()"
        ),
        migrations.RunSQL(
            "alter table setupmatrix alter column lastmodified set default now()"
        ),
        migrations.RunSQL(
            "alter table setuprule alter column lastmodified set default now()"
        ),
        migrations.RunSQL(
            "alter table skill alter column lastmodified set default now()"
        ),
        migrations.RunSQL(
            "alter table suboperation alter column lastmodified set default now()"
        ),
        migrations.RunSQL(
            "alter table supplier alter column lastmodified set default now()"
        ),
    ]
