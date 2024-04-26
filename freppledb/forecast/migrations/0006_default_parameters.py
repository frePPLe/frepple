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

from django.db import migrations, models
from django.db.models import Case, When, Value, IntegerField, Q
from django.db.models.deletion import CASCADE

from freppledb.common.models import Parameter


def setDefaultParameters(apps, schema_editor):

    default_forecast_parameters = {
        "day": {
            "forecast.Croston_initialAlfa": "0.1",
            "forecast.Croston_maxAlfa": "0.3",
            "forecast.Croston_minAlfa": "0.03",
            "forecast.Croston_minIntermittence": "0.33",
            "forecast.DoubleExponential_dampenTrend": "0.95",
            "forecast.DoubleExponential_initialAlfa": "0.2",
            "forecast.DoubleExponential_initialGamma": "0.2",
            "forecast.DoubleExponential_maxAlfa": "0.3",
            "forecast.DoubleExponential_maxGamma": "0.3",
            "forecast.DoubleExponential_minAlfa": "0.02",
            "forecast.DoubleExponential_minGamma": "0.05",
            "forecast.Iterations": "15",
            "forecast.MovingAverage_order": "21",
            "forecast.Seasonal_dampenTrend": "0.9",
            "forecast.Seasonal_initialAlfa": "0.2",
            "forecast.Seasonal_initialBeta": "0.2",
            "forecast.Seasonal_maxAlfa": "0.3",
            "forecast.Seasonal_maxBeta": "0.3",
            "forecast.Seasonal_maxPeriod": "65",
            "forecast.Seasonal_minAlfa": "0.02",
            "forecast.Seasonal_minBeta": "0.2",
            "forecast.Seasonal_gamma": "0.05",
            "forecast.Seasonal_minPeriod": "3",
            "forecast.Seasonal_minAutocorrelation": "0.45",
            "forecast.Seasonal_maxAutocorrelation": "0.55",
            "forecast.Skip": "0",
            "forecast.SingleExponential_initialAlfa": "0.2",
            "forecast.SingleExponential_maxAlfa": "0.3",
            "forecast.SingleExponential_minAlfa": "0.03",
            "forecast.SmapeAlfa": "0.95",
            "forecast.Outlier_maxDeviation": "2",
            "forecast.DeadAfterInactivity": "365",
        },
        "week": {
            "forecast.Croston_initialAlfa": "0.1",
            "forecast.Croston_maxAlfa": "0.3",
            "forecast.Croston_minAlfa": "0.03",
            "forecast.Croston_minIntermittence": "0.33",
            "forecast.DoubleExponential_dampenTrend": "0.95",
            "forecast.DoubleExponential_initialAlfa": "0.2",
            "forecast.DoubleExponential_initialGamma": "0.2",
            "forecast.DoubleExponential_maxAlfa": "0.3",
            "forecast.DoubleExponential_maxGamma": "0.3",
            "forecast.DoubleExponential_minAlfa": "0.02",
            "forecast.DoubleExponential_minGamma": "0.05",
            "forecast.Iterations": "15",
            "forecast.MovingAverage_order": "5",
            "forecast.Seasonal_dampenTrend": "0.9",
            "forecast.Seasonal_initialAlfa": "0.2",
            "forecast.Seasonal_initialBeta": "0.2",
            "forecast.Seasonal_maxAlfa": "0.3",
            "forecast.Seasonal_maxBeta": "0.3",
            "forecast.Seasonal_maxPeriod": "65",
            "forecast.Seasonal_minAlfa": "0.02",
            "forecast.Seasonal_minBeta": "0.2",
            "forecast.Seasonal_gamma": "0.05",
            "forecast.Seasonal_minPeriod": "3",
            "forecast.Seasonal_minAutocorrelation": "0.45",
            "forecast.Seasonal_maxAutocorrelation": "0.55",
            "forecast.Skip": "0",
            "forecast.SingleExponential_initialAlfa": "0.2",
            "forecast.SingleExponential_maxAlfa": "0.3",
            "forecast.SingleExponential_minAlfa": "0.03",
            "forecast.SmapeAlfa": "0.95",
            "forecast.Outlier_maxDeviation": "2",
            "forecast.DeadAfterInactivity": "365",
        },
        "month": {
            "forecast.Croston_initialAlfa": "0.1",
            "forecast.Croston_maxAlfa": "0.8",
            "forecast.Croston_minAlfa": "0.03",
            "forecast.Croston_minIntermittence": "0.33",
            "forecast.DoubleExponential_dampenTrend": "0.8",
            "forecast.DoubleExponential_initialAlfa": "0.2",
            "forecast.DoubleExponential_initialGamma": "0.2",
            "forecast.DoubleExponential_maxAlfa": "0.6",
            "forecast.DoubleExponential_maxGamma": "0.6",
            "forecast.DoubleExponential_minAlfa": "0.02",
            "forecast.DoubleExponential_minGamma": "0.05",
            "forecast.Iterations": "15",
            "forecast.MovingAverage_order": "5",
            "forecast.Seasonal_dampenTrend": "0.8",
            "forecast.Seasonal_initialAlfa": "0.2",
            "forecast.Seasonal_initialBeta": "0.2",
            "forecast.Seasonal_maxAlfa": "0.5",
            "forecast.Seasonal_maxBeta": "0.5",
            "forecast.Seasonal_maxPeriod": "14",
            "forecast.Seasonal_minAlfa": "0.02",
            "forecast.Seasonal_minBeta": "0.2",
            "forecast.Seasonal_gamma": "0.05",
            "forecast.Seasonal_minPeriod": "2",
            "forecast.Seasonal_minAutocorrelation": "0.5",
            "forecast.Seasonal_maxAutocorrelation": "0.8",
            "forecast.Skip": "0",
            "forecast.SingleExponential_initialAlfa": "0.2",
            "forecast.SingleExponential_maxAlfa": "0.6",
            "forecast.SingleExponential_minAlfa": "0.03",
            "forecast.SmapeAlfa": "0.95",
            "forecast.Outlier_maxDeviation": "2",
            "forecast.DeadAfterInactivity": "365",
        },
    }

    db = schema_editor.connection.alias
    calendar = Parameter.getValue("forecast.calendar", db)
    if calendar not in default_forecast_parameters:
        calendar = "month"

    for param in (
        Parameter.objects.annotate(
            custom_order=Case(
                When(name="forecast.calendar", then=Value(1)),
                When(
                    ~Q(name="forecast.calendar"),
                    then=Value(2),
                ),
                output_field=IntegerField(),
            )
        )
        .all()
        .using(db)
        .filter(name__startswith="forecast.")
        .exclude(name="forecast.populateForecastTable")
        .exclude(name="forecast.runnetting")
        .order_by("custom_order")
    ):
        if param.name in default_forecast_parameters.get(calendar):
            if param.value == default_forecast_parameters.get(calendar).get(param.name):
                param.value = "default"
                param.save()


class Migration(migrations.Migration):
    dependencies = [("forecast", "0005_batch")]

    operations = [
        migrations.RunPython(
            setDefaultParameters,
            migrations.RunPython.noop,
        ),
    ]
