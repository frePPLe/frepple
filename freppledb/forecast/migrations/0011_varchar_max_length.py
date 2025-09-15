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

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("forecast", "0010_forecastplan"),
    ]

    operations = [
        migrations.RunSQL(
            sql="drop materialized view if exists forecastreport_view",
            reverse_sql=migrations.RunSQL.noop,
        ),
        migrations.AlterModelOptions(
            name="forecastplan",
            options={
                "managed": False,
                "ordering": ["id"],
                "verbose_name": "forecast plan",
                "verbose_name_plural": "forecast plans",
            },
        ),
        migrations.AlterField(
            model_name="forecast",
            name="batch",
            field=models.CharField(
                blank=True, help_text="MTO batch name", null=True, verbose_name="batch"
            ),
        ),
        migrations.AlterField(
            model_name="forecast",
            name="category",
            field=models.CharField(
                blank=True, db_index=True, null=True, verbose_name="category"
            ),
        ),
        migrations.AlterField(
            model_name="forecast",
            name="description",
            field=models.CharField(blank=True, null=True, verbose_name="description"),
        ),
        migrations.AlterField(
            model_name="forecast",
            name="method",
            field=models.CharField(
                blank=True,
                default="automatic",
                help_text="Method used to generate a base forecast",
                null=True,
                verbose_name="Forecast method",
            ),
        ),
        migrations.AlterField(
            model_name="forecast",
            name="name",
            field=models.CharField(
                primary_key=True, serialize=False, verbose_name="name"
            ),
        ),
        migrations.AlterField(
            model_name="forecast",
            name="out_method",
            field=models.CharField(
                blank=True, null=True, verbose_name="calculated forecast method"
            ),
        ),
        migrations.AlterField(
            model_name="forecast",
            name="source",
            field=models.CharField(
                blank=True, db_index=True, null=True, verbose_name="source"
            ),
        ),
        migrations.AlterField(
            model_name="forecast",
            name="subcategory",
            field=models.CharField(
                blank=True, db_index=True, null=True, verbose_name="subcategory"
            ),
        ),
        migrations.AlterField(
            model_name="measure",
            name="compute_expression",
            field=models.CharField(
                blank=True,
                help_text="Formula to compute values",
                null=True,
                verbose_name="compute expression",
            ),
        ),
        migrations.AlterField(
            model_name="measure",
            name="description",
            field=models.CharField(blank=True, null=True, verbose_name="description"),
        ),
        migrations.AlterField(
            model_name="measure",
            name="formatter",
            field=models.CharField(
                blank=True,
                choices=[("number", "number"), ("currency", "currency")],
                default="number",
                null=True,
                verbose_name="format",
            ),
        ),
        migrations.AlterField(
            model_name="measure",
            name="label",
            field=models.CharField(
                blank=True,
                help_text="Label to be displayed in the user interface",
                null=True,
                verbose_name="label",
            ),
        ),
        migrations.AlterField(
            model_name="measure",
            name="mode_future",
            field=models.CharField(
                blank=True,
                choices=[("edit", "edit"), ("view", "view"), ("hide", "hide")],
                default="edit",
                null=True,
                verbose_name="mode in future periods",
            ),
        ),
        migrations.AlterField(
            model_name="measure",
            name="mode_past",
            field=models.CharField(
                blank=True,
                choices=[("edit", "edit"), ("view", "view"), ("hide", "hide")],
                default="edit",
                null=True,
                verbose_name="mode in past periods",
            ),
        ),
        migrations.AlterField(
            model_name="measure",
            name="name",
            field=models.CharField(
                help_text="Unique identifier",
                primary_key=True,
                serialize=False,
                verbose_name="name",
            ),
        ),
        migrations.AlterField(
            model_name="measure",
            name="overrides",
            field=models.CharField(
                blank=True, null=True, verbose_name="override measure"
            ),
        ),
        migrations.AlterField(
            model_name="measure",
            name="source",
            field=models.CharField(
                blank=True, db_index=True, null=True, verbose_name="source"
            ),
        ),
        migrations.AlterField(
            model_name="measure",
            name="type",
            field=models.CharField(
                blank=True,
                choices=[
                    ("aggregate", "aggregate"),
                    ("local", "local"),
                    ("computed", "computed"),
                ],
                default="default",
                null=True,
                verbose_name="type",
            ),
        ),
        migrations.AlterField(
            model_name="measure",
            name="update_expression",
            field=models.CharField(
                blank=True,
                help_text="Formula executed when updating this field",
                null=True,
                verbose_name="update expression",
            ),
        ),
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
            reverse_sql=migrations.RunSQL.noop,
        ),
    ]
