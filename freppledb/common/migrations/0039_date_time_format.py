#
# Copyright (C) 2024 by frePPLe bv
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

from django.conf import settings
from django.db import migrations


class Migration(migrations.Migration):
    dependencies = [("common", "0038_scenario")]

    operations = [
        migrations.RunSQL(
            f"""
            insert into common_parameter (name, value, description, lastmodified)
            select
            'display_time','{str(
                    settings.DATE_STYLE_WITH_HOURS
                    if hasattr(settings, "DATE_STYLE_WITH_HOURS")
                    else False
                ).lower()}','This parameter applies to ALL scenarios and controls if date time fields should display the time. Accepted values: true or false', now()
            from common_parameter
            ON CONFLICT (name) DO NOTHING;
            insert into common_parameter (name, value, description, lastmodified)
            select
            'date_format','{str(
                    settings.DATE_STYLE
                    if hasattr(settings, "DATE_STYLE")
                    else "year-month-day"
                ).lower()}','This parameter applies to ALL scenarios. Accepted values: month-day-year, day-month-year, year-month-day.', now()
            from common_parameter
            ON CONFLICT (name) DO NOTHING;
            """,
            "delete from common_parameter where name in ('display_time','date_format')",
        )
    ]
