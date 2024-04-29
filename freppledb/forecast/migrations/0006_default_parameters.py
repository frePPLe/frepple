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
from freppledb.forecast.commands import default_forecast_parameters


def setDefaultParameters(apps, schema_editor):

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
