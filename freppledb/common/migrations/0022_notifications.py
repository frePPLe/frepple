#
# Copyright (C) 2020 by frePPLe bv
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
