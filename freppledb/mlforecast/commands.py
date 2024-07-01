#
# Copyright (C) 2015 by frePPLe bv
#
# All information contained herein is, and remains the property of frePPLe.
# You are allowed to use and modify the source code, as long as the software is used
# within your company.
# You are not allowed to distribute the software, either in the form of source code
# or in the form of compiled binaries.
#

import os
from datetime import timedelta

import logging


from orbit.models import ETS, DLT, KTR, LGT
import pandas as pd

from django.db import DEFAULT_DB_ALIAS
from django.utils.translation import gettext_lazy as _


from freppledb.common.commands import PlanTaskRegistry, PlanTask
from freppledb.common.models import Parameter
from freppledb.common.report import getCurrentDate


logger = logging.getLogger(__name__)


@PlanTaskRegistry.register
class ExportForecast(PlanTask):
    description = "Generate machine learning forecast data"
    sequence = 172

    @classmethod
    def getWeight(cls, database=DEFAULT_DB_ALIAS, **kwargs):
        if "fcst" in os.environ and Parameter.getValue(
            "forecast.calendar", database, None
        ):
            return 1
        else:
            return -1

    @classmethod
    def run(cls, database=DEFAULT_DB_ALIAS, **kwargs):
        import frepple

        calendar = Parameter.getValue("forecast.calendar", database, None)
        currentdate = getCurrentDate(database)
        horizon_future = int(
            Parameter.getValue("forecast.Horizon_future", database, 365)
        )
        test = {
            "date": [
                i.start
                for i in frepple.calendar(name=calendar).buckets
                if i.end >= currentdate
                and i.start <= currentdate + timedelta(days=horizon_future)
            ],
        }
        test["quantity"] = [None] * len(test["date"])
        test_pd = pd.DataFrame(test)

        for i in frepple.demands():
            if isinstance(i, frepple.demand_forecast) and i.methods == "automatic":
                train = {"date": [], "quantity": []}
                found = False

                for b in i.buckets:
                    if b.end >= currentdate:
                        break
                    if b.orderstotal + b.ordersadjustment > 0 or found:
                        if not found:
                            found = True
                        train["date"].append(b.start)
                        train["quantity"].append(b.orderstotal + b.ordersadjustment)
                    if not found:
                        continue

                if len(train["date"]) < 2:
                    # too small to forecast, will be forecasted with statistical methods
                    continue

                try:
                    orbit_model = KTR(
                        response_col="quantity",
                        date_col="date",
                        seasonality=(52 if calendar == "week" else 12),
                    )

                    train_pd = pd.DataFrame(train)
                    orbit_model.fit(train_pd)
                    predicted_df = orbit_model.predict(df=test_pd, decompose=True)
                    index = 0
                    for j in frepple.demands():
                        if j.owner == i and (j.start in test["date"]):
                            j.forecastbaseline = max(
                                0, predicted_df.iloc[index]["prediction"]
                            )
                            index += 1
                except Exception as e:
                    # silently move on and use the statistical forecast
                    print(
                        "skipping machine learning forecast calculation for %s: %s"
                        % (i.name, e)
                    )
                    pass
