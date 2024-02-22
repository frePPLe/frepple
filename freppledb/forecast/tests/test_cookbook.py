#
# Copyright (C) 2023 by frePPLe bv
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

import unittest

from django.conf import settings
from django.core import management

from freppledb.execute.tests import cookbooktest


class cookbook_forecast(cookbooktest):
    @unittest.skipUnless(
        "freppledb.forecast" in settings.INSTALLED_APPS, "App not activated"
    )
    def test_forecast_netting(self):
        self.loadExcel(
            settings.FREPPLE_HOME,
            "..",
            "doc",
            "examples",
            "forecasting",
            "forecast-netting.xlsx",
            webservice=True,
        )
        management.call_command(
            "runplan",
            plantype=1,
            constraint="capa,mfg_lt,po_lt",
            env="fcst,supply,nowebservice",
        )
        self.assertOperationplans(
            settings.FREPPLE_HOME,
            "..",
            "doc",
            "examples",
            "forecasting",
            "forecast-netting.expect",
        )

    @unittest.skipUnless(
        "freppledb.forecast" in settings.INSTALLED_APPS, "App not activated"
    )
    def test_middle_out_forecast(self):
        self.loadExcel(
            settings.FREPPLE_HOME,
            "..",
            "doc",
            "examples",
            "forecasting",
            "middle-out-forecast.xlsx",
            webservice=True,
        )
        management.call_command(
            "runplan",
            plantype=1,
            constraint="capa,mfg_lt,po_lt",
            env="fcst,supply,nowebservice",
        )
        self.assertOperationplans(
            settings.FREPPLE_HOME,
            "..",
            "doc",
            "examples",
            "forecasting",
            "middle-out-forecast.expect",
        )

    @unittest.skipUnless(
        "freppledb.forecast" in settings.INSTALLED_APPS, "App not activated"
    )
    def test_forecast_method(self):
        self.loadExcel(
            settings.FREPPLE_HOME,
            "..",
            "doc",
            "examples",
            "forecasting",
            "forecast-method.xlsx",
            webservice=True,
        )
        management.call_command(
            "runplan",
            plantype=1,
            constraint="capa,mfg_lt,po_lt",
            env="fcst,supply,nowebservice",
        )
        self.assertOperationplans(
            settings.FREPPLE_HOME,
            "..",
            "doc",
            "examples",
            "forecasting",
            "forecast-method.expect",
        )

    @unittest.skip("Temporarily disabled - intermittent failures")
    def test_forecast_with_missing_data(self):
        self.loadExcel(
            settings.FREPPLE_HOME,
            "..",
            "doc",
            "examples",
            "forecasting",
            "forecast-with-missing-data.xlsx",
            webservice=True,
        )
        management.call_command(
            "runplan",
            plantype=1,
            constraint="capa,mfg_lt,po_lt",
            env="fcst,supply,nowebservice",
        )
        self.assertOperationplans(
            settings.FREPPLE_HOME,
            "..",
            "doc",
            "examples",
            "forecasting",
            "forecast-with-missing-data.expect",
        )
