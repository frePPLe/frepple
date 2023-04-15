#
# Copyright (C) 2021 by frePPLe bv
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

from django.apps import AppConfig
from django.conf import settings
from django.core import checks


@checks.register(checks.Tags.database)
def check_python_packages(app_configs, **kwargs):
    errors = []
    for db, dbparams in settings.DATABASES.items():
        if "SQL_ROLE" not in dbparams:
            errors.append(db)
    return (
        [
            checks.Error(
                "No SQL_ROLE setting configured in djangosettings.py for databases: %s"
                % ", ".join(errors),
                id="reportmanager.E001",
            )
        ]
        if errors
        else []
    )


class ReportManagerConfig(AppConfig):
    name = "freppledb.reportmanager"
    verbose_name = "reportmanager"
