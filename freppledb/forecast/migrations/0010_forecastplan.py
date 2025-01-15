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

from django.db import migrations, connections


def getMeasures(cursor):
    measures = {
        "forecasttotal",
        "forecastconsumed",
        "forecastnet",
        "forecastbaseline",
        "forecastoverride",
        "orderstotal",
        "ordersadjustment",
        "ordersopen",
        "ordersplanned",
        "forecastplanned",
    }
    cursor.execute("select name from measure")
    for r in cursor.fetchall():
        measures.add(r[0])
    return measures


def fromJsonbToColumns(apps, schema_editor):
    with connections[schema_editor.connection.alias].cursor() as cursor:
        measures = getMeasures(cursor)

        # Add columns
        cursor.execute(
            "alter table forecastplan "
            + ",".join(f"add column {name} numeric(20,8)" for name in measures)
        )

        # Populate the columns
        cursor.execute(
            "update forecastplan set "
            + ",".join(f"{name} = (value->>'{name}')::numeric" for name in measures)
        )

        # Drop the value column
        cursor.execute("alter table forecastplan drop column value")

        # Vacuum the table
        cursor.execute("vacuum full forecastplan")


def fromColumnsToJsonb(apps, schema_editor):
    with connections[schema_editor.connection.alias].cursor() as cursor:
        measures = getMeasures(cursor)

        # Add the value column
        cursor.execute("alter table forecastplan add column value jsonb")

        # Populate the jsob column
        cursor.execute(
            "update forecastplan set value = jsonb_strip_nulls(jsonb_build_object("
            + ",".join(f"'{name}', {name}" for name in measures)
            + "))"
        )

        # Drop measure columns
        cursor.execute(
            "alter table forecastplan "
            + ",".join(f"drop column {name}" for name in measures)
        )

        # Vacuum the table
        cursor.execute("vacuum full forecastplan")


class Migration(migrations.Migration):
    dependencies = [
        ("forecast", "0009_forecastreport_view"),
    ]

    # Running without a transaction block is needed for the vacuum full command
    atomic = False

    operations = [migrations.RunPython(fromJsonbToColumns, fromColumnsToJsonb)]
