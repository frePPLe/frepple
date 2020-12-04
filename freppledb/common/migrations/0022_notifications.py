#
# Copyright (C) 2020 by frePPLe bv
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

from django.db import migrations, transaction
from django.contrib.admin.models import LogEntry


def migrateAdminLog(apps, schema_editor):
    Comment = apps.get_model("common", "Comment")

    db = schema_editor.connection.alias
    with transaction.atomic(using=db):
        for rec in LogEntry.objects.all().using(db):
            if rec.action_flag == 1:
                rectype = "add"
            elif rec.action_flag == 2:
                rectype = "change"
            elif rec.action_flag == 3:
                rectype = "deletion"
            else:
                rectype = "comment"
            Comment(
                object_pk=rec.object_id,
                comment=rec.get_change_message(),
                lastmodified=rec.action_time,
                content_type_id=rec.content_type_id,
                user_id=rec.user_id,
                object_repr=rec.object_repr,
                processed=True,
                type=rectype,
            ).save(using=db)


class Migration(migrations.Migration):

    dependencies = [("common", "0021_notifications")]

    operations = [
        migrations.RunSQL(
            "update common_comment set object_repr = object_pk, type='comment', processed=true"
        ),
        migrations.RunPython(migrateAdminLog),
        migrations.RunSQL("truncate table django_admin_log"),
    ]
