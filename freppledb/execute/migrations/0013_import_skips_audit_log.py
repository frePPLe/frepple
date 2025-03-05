#
# Copyright (C) 2025 by frePPLe bv
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


class Migration(migrations.Migration):
    """
    Addition of a parameter to enable/disable log auditing on import from folder command
    """

    dependencies = [("execute", "0012_scheduledtask_tz")]
    operations = [
        migrations.RunSQL(
            sql="""
            insert into common_parameter
            (name, value, description, lastmodified)
            values
            ('import_skips_audit_log','true','When set to true, the import data files command doesn''t create any audit log message. Default:true', now())
            on conflict (name) do nothing
            """,
            reverse_sql="""
            delete from common_parameter where name = 'import_skips_audit_log';
            """,
        )
    ]
