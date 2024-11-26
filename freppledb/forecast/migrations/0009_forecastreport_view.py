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

from django.db import migrations


class Migration(migrations.Migration):
    dependencies = [
        ("forecast", "0008_outliers"),
    ]

    operations = [
        migrations.RunSQL(
            sql="""
              drop materialized view if exists forecastreport_view;

              create materialized view forecastreport_view as
              select distinct
                   coalesce(forecast.name, forecastplan.item_id||' @ '||
                     forecastplan.location_id||' @ '||
                     forecastplan.customer_id) as name,
                   forecastplan.item_id,
                   forecastplan.location_id,
                   forecastplan.customer_id
              from forecastplan
              left outer join forecast
                on forecast.item_id = forecastplan.item_id
                and forecast.location_id = forecastplan.location_id
                and forecast.customer_id = forecastplan.customer_id;

            create unique index on forecastreport_view (item_id, location_id, customer_id);

            refresh materialized view forecastreport_view;
            """,
            reverse_sql="""
            drop materialized view if exists forecastreport_view;

              create materialized view forecastreport_view as
              select distinct
                   coalesce(forecast.name, forecastplan.item_id||' @ '||
                     forecastplan.location_id||' @ '||
                     forecastplan.customer_id) as name,
                   forecastplan.item_id,
                   forecastplan.location_id,
                   forecastplan.customer_id,
                   coalesce(forecast.method,'aggregate') as method,
                   coalesce(forecast.out_method,'aggregate') as out_method,
                   forecast.out_smape as out_smape
              from forecastplan
              left outer join forecast
                on forecast.item_id = forecastplan.item_id
                and forecast.location_id = forecastplan.location_id
                and forecast.customer_id = forecastplan.customer_id;

            create unique index on forecastreport_view (item_id, location_id, customer_id);
            """,
        ),
    ]
