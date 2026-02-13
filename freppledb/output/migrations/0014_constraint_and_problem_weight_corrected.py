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

from django.conf import settings
from django.db import migrations


class Migration(migrations.Migration):
    dependencies = [
        ("output", "0014_constraint_and_problem_weight"),
    ]

    DATE_FORMAT = (
        settings.DATE_FORMAT_JS if hasattr(settings, "DATE_FORMAT_JS") else "YYYY-MM-DD"
    )
    operations = [
        migrations.RunSQL(
            """
            update execute_export
               set sql = 'select
                       entity, owner, name, description,
                       to_char(startdate,''%s HH24:MI:SS'') as startdate,
                       to_char(enddate,''%s HH24:MI:SS'') as enddate
                     from out_problem
                     where name <> ''material excess''
                     order by entity, name, startdate
                    '
            where name = 'problems.csv.gz'
            and regexp_replace(sql, '\\s', '', 'g') =
               regexp_replace('select
                       entity, owner, name, description,
                       to_char(startdate,''%s HH24:MI:SS'') as startdate,
                       to_char(enddate,''%s HH24:MI:SS'') as enddate,
                       weight
                     from out_problem
                     where name <> ''material excess''
                     order by entity, name, startdate
                     ', '\\s', '', 'g')
            """
            % ((DATE_FORMAT,) * 4),
            """
            update execute_export
               set sql = 'select
                       entity, owner, name, description,
                       to_char(startdate,''%s HH24:MI:SS'') as startdate,
                       to_char(enddate,''%s HH24:MI:SS'') as enddate,
                       weight
                     from out_problem
                     where name <> ''material excess''
                     order by entity, name, startdate
                    '
            where name = 'problems.csv.gz'
            and regexp_replace(sql, '\\s', '', 'g') =
               regexp_replace('select
                       entity, owner, name, description,
                       to_char(startdate,''%s HH24:MI:SS'') as startdate,
                       to_char(enddate,''%s HH24:MI:SS'') as enddate
                     from out_problem
                     where name <> ''material excess''
                     order by entity, name, startdate
                    ', '\\s', '', 'g')
            """
            % ((DATE_FORMAT,) * 4),
        ),
    ]
