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

from django.utils.translation import gettext_lazy as _
from freppledb.menu import menu
from freppledb.forecast.models import Forecast, ForecastPlan, Measure
from freppledb.forecast.views import (
    OverviewReport,
    ForecastList,
    MeasureList,
    ForecastWizard,
)
from freppledb.input.models import Item, Location, Customer


# Adding reports. We use an index value to keep the same order of the entries in all languages.
menu.addItem(
    "sales",
    "forecast report",
    url="/forecast/",
    report=OverviewReport,
    model=ForecastPlan,
    index=110,
    dependencies=[Forecast],
)
menu.addItem(
    "sales",
    "forecast editor",
    url="/forecast/editor/",
    label=_("Forecast editor"),
    index=111,
    permission="auth.view_forecast_report",
    dependencies=[Forecast],
)
# TODO Not ready
# menu.addItem(
#     "sales",
#     "forecast wizard",
#     url="/forecast/wizard/",
#     report=ForecastWizard,
#     index=112,
#     permission="auth.view_forecast_report",
#     dependencies=[Item, Location, Customer],
# )
menu.addItem(
    "sales",
    "forecast",
    url="/data/forecast/forecast/",
    report=ForecastList,
    index=1210,
    model=Forecast,
    dependencies=[Item, Location, Customer],
)
menu.addItem(
    "sales",
    "measure",
    url="/data/forecast/measure/",
    report=MeasureList,
    index=1220,
    model=Measure,
    dependencies=[Item, Location, Customer],
    admin=True,
)
