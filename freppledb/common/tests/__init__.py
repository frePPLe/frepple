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

from contextlib import contextmanager

from django.test import TransactionTestCase

from .tests import checkResponse
from ..utils import get_databases


class TransactionTestCaseWithReportDatabases(TransactionTestCase):

    @contextmanager
    def _allow_report_databases(self):
        # Django test suite is picky about which database connections are allowed
        cls = type(self)
        original_databases = cls.databases
        extra_databases = tuple(
            alias
            for alias in get_databases(True).keys()
            if alias.endswith("_report") and alias not in original_databases
        )
        cls.databases = tuple(original_databases) + extra_databases
        try:
            yield
        finally:
            cls.databases = original_databases
