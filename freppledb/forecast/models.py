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

from datetime import date, datetime
from itertools import chain
import json
from logging import INFO, ERROR, WARNING, DEBUG
from openpyxl.worksheet.cell_range import CellRange
from openpyxl.worksheet.worksheet import Worksheet
import os
import random
import requests
from requests import ConnectionError
from threading import Thread

from django.core import management
from django.core.exceptions import ValidationError
from django.db import models, DEFAULT_DB_ALIAS, connections
from django.utils import translation
from django.utils.encoding import force_str
from django.utils.translation import pgettext, gettext_lazy as _

from freppledb.common.auth import getWebserviceAuthorization
from freppledb.common.localization import parseLocalizedDateTime
from freppledb.common.models import AuditModel, BucketDetail, Parameter, Scenario
from freppledb.common.utils import forceWsgiReload, get_databases
from freppledb.input.models import Customer, Item, Location, Operation
from freppledb.webservice.utils import useWebService


class Forecast(AuditModel):
    # Forecasting methods
    methods = (
        ("automatic", _("Automatic")),
        ("constant", pgettext("forecast method", "Constant")),
        ("trend", pgettext("forecast method", "Trend")),
        ("seasonal", pgettext("forecast method", "Seasonal")),
        ("intermittent", pgettext("forecast method", "Intermittent")),
        ("moving average", pgettext("forecast method", "Moving average")),
        ("manual", _("Manual")),
        ("aggregate", _("Aggregate")),
    )

    # Database fields
    name = models.CharField(_("name"), primary_key=True)
    description = models.CharField(_("description"), null=True, blank=True)
    category = models.CharField(_("category"), null=True, blank=True, db_index=True)
    subcategory = models.CharField(
        _("subcategory"), null=True, blank=True, db_index=True
    )
    customer = models.ForeignKey(
        Customer, verbose_name=_("customer"), db_index=True, on_delete=models.CASCADE
    )
    item = models.ForeignKey(
        Item, verbose_name=_("item"), db_index=True, on_delete=models.CASCADE
    )
    location = models.ForeignKey(
        Location, verbose_name=_("location"), db_index=True, on_delete=models.CASCADE
    )
    batch = models.CharField(
        _("batch"),
        null=True,
        blank=True,
        help_text=_("MTO batch name"),
    )
    method = models.CharField(
        _("Forecast method"),
        null=True,
        blank=True,
        choices=methods,
        default="automatic",
        help_text=_("Method used to generate a base forecast"),
    )
    priority = models.IntegerField(
        _("priority"),
        default=10,
        help_text=_(
            "Priority of the demand (lower numbers indicate more important demands)"
        ),
    )
    minshipment = models.DecimalField(
        _("minimum shipment"),
        null=True,
        blank=True,
        max_digits=20,
        decimal_places=8,
        help_text=_("Minimum shipment quantity when planning this demand"),
    )
    maxlateness = models.DurationField(
        _("maximum lateness"),
        null=True,
        blank=True,
        help_text=_("Maximum lateness allowed when planning this demand"),
    )
    discrete = models.BooleanField(
        _("discrete"), default=True, help_text=_("Round forecast numbers to integers")
    )
    out_smape = models.DecimalField(
        _("estimated forecast error"),
        null=True,
        blank=True,
        max_digits=20,
        decimal_places=8,
    )
    out_method = models.CharField(
        _("calculated forecast method"), null=True, blank=True
    )
    out_deviation = models.DecimalField(
        _("calculated standard deviation"),
        null=True,
        blank=True,
        max_digits=20,
        decimal_places=8,
    )
    planned = models.BooleanField(
        _("planned"),
        default=True,
        null=False,
        help_text=_("Specifies whether this forecast record should be planned"),
    )
    operation = models.ForeignKey(
        Operation,
        verbose_name=_("delivery operation"),
        null=True,
        blank=True,
        related_name="used_forecast",
        on_delete=models.SET_NULL,
        help_text=_("Operation used to satisfy this demand"),
    )

    class Meta(AuditModel.Meta):
        db_table = "forecast"
        verbose_name = _("forecast")
        verbose_name_plural = _("forecasts")
        ordering = ["name"]
        unique_together = (("item", "location", "customer"),)

    def __str__(self):
        return self.name

    @classmethod
    def beforeUpload(cls, database=DEFAULT_DB_ALIAS):
        # Assure the hierarchies are up to date and have only single root
        # This also creates the dummy parent root if required
        Item.createRootObject(database=database)
        Location.createRootObject(database=database)
        Customer.createRootObject(database=database)

    @staticmethod
    def flush(session, mode, database=DEFAULT_DB_ALIAS, token=None):
        if "FREPPLE_TEST" in os.environ:
            server = get_databases()[database]["TEST"]["FREPPLE_PORT"].replace(
                "0.0.0.0:", "localhost:"
            )
        else:
            server = get_databases()[database]["FREPPLE_PORT"].replace(
                "0.0.0.0:", "localhost:"
            )
        response = session.post(
            "http://%s/flush/%s/" % (server, mode),
            headers={
                "Authorization": "Bearer %s"
                % (token or getWebserviceAuthorization(user="admin", exp=3600)),
                "Content-Type": "application/json",
                "content-length": "0",
            },
        )
        if response.status_code != 200:
            raise Exception(response.text)

    @staticmethod
    def updatePlan(
        startdate=None,
        enddate=None,
        database=DEFAULT_DB_ALIAS,
        forecast=None,
        item=None,
        customer=None,
        location=None,
        request=None,
        session=None,
        token=None,
        **kwargs,
    ):
        if not kwargs:
            return
        data = {}
        if item:
            data["item"] = item
        if location:
            data["location"] = location
        if customer:
            data["customer"] = customer
        if forecast:
            data["forecast"] = forecast
        if "FREPPLE_TEST" in os.environ:
            server = get_databases()[database]["TEST"]["FREPPLE_PORT"].replace(
                "0.0.0.0:", "localhost:"
            )
        else:
            server = get_databases()[database]["FREPPLE_PORT"].replace(
                "0.0.0.0:", "localhost:"
            )
        if startdate:
            if isinstance(startdate, (date, datetime)):
                data["startdate"] = startdate.strftime("%Y-%m-%dT%H:%M:%S")
            else:
                data["startdate"] = parseLocalizedDateTime(startdate).strftime(
                    "%Y-%m-%dT%H:%M:%S"
                )
        if enddate:
            if isinstance(enddate, (date, datetime)):
                data["enddate"] = enddate.strftime("%Y-%m-%dT%H:%M:%S")
            else:
                data["enddate"] = parseLocalizedDateTime(enddate).strftime(
                    "%Y-%m-%dT%H:%M:%S"
                )
        for m, val in kwargs.items():
            if val is not None:
                data[m] = float(val)
        my_session = session or requests.Session()
        my_token = token or getWebserviceAuthorization(
            user=request.user.username if request else "admin",
            sid=request.user.id if request else 1,
            exp=3600,
        )
        try:
            payload = json.dumps([data]).encode("utf-8")
            response = my_session.post(
                "http://%s/forecast/detail/" % server,
                data=payload,
                headers={
                    "Authorization": "Bearer %s" % my_token,
                    "Content-Type": "application/json",
                    "content-length": str(len(payload)),
                },
            )
            if response.status_code != 200:
                raise Exception(response.text)
        finally:
            if not session:
                my_session.close()


class PropertyField:
    """
    A class to define a computed field on a Django model.
    The model is exposed a property on model instances, and the get
    and set methods are used to store and retrieve the values.
    """

    type = "number"
    editable = False
    name = None
    verbose_name = None
    export = True
    choices = None

    def __init__(self, **kwargs):
        for key, value in kwargs.items():
            if key == "type" and value not in (
                "string",
                "boolean",
                "number",
                "integer",
                "date",
                "datetime",
                "duration",
                "time",
            ):
                raise Exception("Invalid property type '%s'." % value)
            else:
                setattr(self, key, value)
        if not self.name:
            raise Exception("Missing property name.")
        if not self.verbose_name:
            self.verbose_name = self.name


class ForecastPlan(models.Model):
    allow_report_manager_access = True

    # Model managers
    objects = models.Manager()  # The default model manager

    @classmethod
    def export_objects(cls, query, request):
        return query.extra(
            select={
                m.name: f"value.{m.name}"
                for m in chain(
                    Measure.standard_measures(), Measure.objects.using(request.database)
                )
            },
            where=[
                """
                exists (
                select 1
                from forecast
                where forecastplan.item_id = forecast.item_id
                and forecastplan.customer_id = forecast.customer_id
                and forecastplan.location_id = forecast.location_id)
                """
            ],
        ).order_by("item", "location", "customer", "startdate")

    # The forecast plan model also depends on the bucket detail table.
    # The database constraints don't reflect that, so we need to define it explicitly.
    extra_dependencies = [BucketDetail, Forecast]

    # Database fields
    id = models.AutoField(_("identifier"), primary_key=True)
    item = models.ForeignKey(
        Item,
        verbose_name=_("item"),
        null=False,
        db_index=True,
        on_delete=models.DO_NOTHING,
        db_constraint=False,
    )
    location = models.ForeignKey(
        Location,
        verbose_name=_("location"),
        null=False,
        db_index=True,
        on_delete=models.DO_NOTHING,
        db_constraint=False,
    )
    customer = models.ForeignKey(
        Customer,
        verbose_name=_("customer"),
        null=False,
        db_index=True,
        on_delete=models.DO_NOTHING,
        db_constraint=False,
    )
    startdate = models.DateTimeField(_("start date"), null=False, db_index=True)
    enddate = models.DateTimeField(_("end date"), null=False)
    value = models.JSONField(default=dict, blank=False, null=False)

    # Property fields
    # TODO this syntax for defining properties isn't as slick and clean as it could be.
    # Ideally we want some form of syntax as the above for Django fields.
    @staticmethod
    def propertyFields(request):
        return [
            PropertyField(
                name=m.name,
                verbose_name=m.description,
                editable=m.editable,
                type="number",
            )
            for m in chain(
                Measure.standard_measures(),
                Measure.objects.all().using(request.database),
            )
        ] + [
            # Used during import
            PropertyField(
                name="forecast",
                verbose_name=_("forecast"),
                editable=True,
                type="string",
                export=False,
            ),
            PropertyField(
                name="bucket",
                verbose_name=_("bucket"),
                editable=True,
                type="string",
                export=False,
            ),
            PropertyField(
                name="datafield",
                verbose_name=_("data field"),
                editable=True,
                type="string",
                export=False,
            ),
        ]

    def __str__(self):
        return "%s - %s - %s - %s" % (
            self.item,
            self.location,
            self.customer,
            str(self.startdate),
        )

    class Meta:
        db_table = "forecastplan"
        ordering = ["id"]
        verbose_name = _("forecast plan")
        verbose_name_plural = _("forecast plans")
        constraints = [
            models.UniqueConstraint(
                fields=["item", "location", "customer", "startdate"],
                name="forecastplan_uidx",
            )
        ]
        managed = False

    @staticmethod
    def parseData(
        data,
        rowmapper,
        user,
        database,
        ping,
        excel_duration_in_days=False,
        skip_audit_log=False,
    ):
        """
        This method is called when importing forecast data through a CSV
        or Excel file.
        """
        warnings = 0
        changed = 0
        errors = 0
        rownumber = 0
        processed_header = False
        rowWrapper = rowmapper()
        headers = []
        measures = []
        pivotbuckets = None
        session = None
        token = None

        # Need to assure that the web service is up and running
        if useWebService(database):
            exc = None

            def StartServiceThread():
                nonlocal exc
                try:
                    management.call_command(
                        "runwebservice", database=database, wait=True
                    )
                except Exception as e:
                    exc = e

            # We need a trick to enforce using a new database connection and transaction
            t = Thread(target=StartServiceThread)
            t.start()
            t.join()
            if exc:
                yield (ERROR, None, None, None, "Web service didn't start")
                raise StopIteration
        else:
            yield (ERROR, None, None, None, "Web service not activated")
            raise StopIteration

        # Detect excel autofilter data tables
        if isinstance(data, Worksheet) and data.auto_filter.ref:
            bounds = CellRange(data.auto_filter.ref).bounds
        else:
            bounds = None
        svcdata = []

        # keep a list of all forecast combinations visited
        # This is used to add missing forecast records.
        populateForecastTable = (
            Parameter.getValue(
                "forecast.populateForecastTable", database, "true"
            ).lower()
            == "true"
        )
        forecast_combinations = set()

        for row in data:
            rownumber += 1
            if bounds:
                # Only process data in the excel auto-filter range
                if rownumber < bounds[1]:
                    continue
                elif rownumber > bounds[3]:
                    break
                else:
                    rowWrapper.setData(row)
            else:
                rowWrapper.setData(row)

            # Case 1: Process the header row
            if not processed_header:
                processed_header = True
                colnum = 1
                for col in rowWrapper.values():
                    if isinstance(col, datetime):
                        col = col.strftime("%Y-%m-%dT%H:%M:%S")
                    else:
                        col = str(col).strip().strip("#").lower() if col else ""

                    ok = False
                    if pivotbuckets is not None:
                        headers.append(
                            PropertyField(name=col, editable=True, type="string")
                        )
                        pivotbuckets.append(col)
                        continue
                    for i in chain(
                        ForecastPlan._meta.fields,
                        Measure.standard_measures(),
                        Measure.objects.all().using(database),
                        [
                            # Dummy fields used during import
                            PropertyField(
                                name="forecast",
                                verbose_name=_("forecast"),
                                editable=True,
                                type="string",
                                export=False,
                            ),
                            PropertyField(
                                name="bucket",
                                verbose_name=_("bucket"),
                                editable=True,
                                type="string",
                                export=False,
                            ),
                            PropertyField(
                                name="datafield",
                                verbose_name=_("data field"),
                                editable=True,
                                type="string",
                                export=False,
                            ),
                            PropertyField(
                                name="multiplier",
                                verbose_name=_("multiplier"),
                                editable=True,
                                type="number",
                                export=False,
                            ),
                        ],
                    ):
                        # Try with translated field names
                        if (
                            col == i.name.lower()
                            or col == i.verbose_name.lower()
                            or col
                            == (
                                "%s - %s" % (ForecastPlan.__name__, i.verbose_name)
                            ).lower()
                        ):
                            if i.name == "datafield":
                                pivotbuckets = []
                                headers.append(i)
                            elif i.editable is True:
                                headers.append(i)
                                if isinstance(i, Measure):
                                    measures.append(i)
                            else:
                                headers.append(None)
                            ok = True
                            break
                        if translation.get_language() != "en":
                            # Try with English field names
                            with translation.override("en"):
                                if (
                                    col == i.name.lower()
                                    or col == i.verbose_name.lower()
                                    or col
                                    == (
                                        "%s - %s"
                                        % (ForecastPlan.__name__, i.verbose_name)
                                    ).lower()
                                ):
                                    if i.name == "datafield":
                                        pivotbuckets = []
                                        headers.append(i)
                                    elif i.editable is True:
                                        headers.append(i)
                                        if isinstance(i, Measure):
                                            measures.append(i)
                                    else:
                                        headers.append(None)
                                    ok = True
                                    break
                    if not ok:
                        headers.append(None)
                        warnings += 1
                        yield (
                            WARNING,
                            None,
                            None,
                            None,
                            force_str(
                                _(
                                    "Skipping unknown field %(column)s"
                                    % {"column": '"%s"' % col}
                                )
                            ),
                        )
                    colnum += 1
                rowWrapper = rowmapper(headers)

                # Check required fields
                fields = [i.name for i in headers if i]
                hasforecastfield = "forecast" in fields
                missing = []
                if not hasforecastfield:
                    for k in ["item", "customer", "location"]:
                        if k not in fields:
                            missing.append(k)
                if (
                    "startdate" not in fields
                    and "enddate" not in fields
                    and "bucket" not in fields
                    and pivotbuckets is None
                ):
                    missing.append("startdate")
                if missing:
                    errors += 1
                    e = "Some keys were missing: %(keys)s" % {
                        "keys": ", ".join(missing)
                    }
                    yield (
                        ERROR,
                        None,
                        None,
                        None,
                        _(e),
                    )
                    raise Exception(e)
                if pivotbuckets:
                    measures = [
                        m
                        for m in chain(
                            Measure.standard_measures(),
                            Measure.objects.all().using(database),
                        )
                        if m.editable
                    ]
                elif not measures:
                    # Check the presence of editable fields
                    warnings += 1
                    yield (WARNING, None, None, None, _("No editable fields found"))
                    raise StopIteration

                # Initialize http connection
                session = requests.Session()
                token = getWebserviceAuthorization(
                    user=user.username if user else "admin",
                    sid=user.id if user else 1,
                    exp=3600,
                )
                if "FREPPLE_TEST" in os.environ:
                    server = get_databases()[database]["TEST"].get("FREPPLE_PORT", None)
                else:
                    server = get_databases()[database].get("FREPPLE_PORT", None)
                if server:
                    server = server.replace("0.0.0.0:", "localhost:")

                def sendToService(d):
                    response = session.post(
                        "http://%s/forecast/detail/" % server,
                        headers={
                            "Authorization": "Bearer %s" % token,
                            "Content-Type": "application/json",
                        },
                        json=d,
                    )
                    return response.json().get("errors", []) or []

                Forecast.flush(session, mode="manual", database=database, token=token)

            # Case 2: Skip empty rows
            elif rowWrapper.empty():
                continue

            # Case 3: Process a data row
            else:
                # Send a ping-alive message to make the upload interruptable
                if ping:
                    if rownumber % 50 == 0:
                        yield (DEBUG, rownumber, None, None, None)

                multiplier = rowWrapper.get("multiplier") or 1
                if populateForecastTable:
                    forecast_combinations.add(
                        (
                            rowWrapper.get("item", None),
                            rowWrapper.get("location", None),
                            rowWrapper.get("customer", None),
                        )
                    )

                # Call the update method
                if pivotbuckets:
                    # Upload in pivot layout
                    fieldname = rowWrapper.get("datafield", "").lower()
                    field = None
                    for m in measures:
                        if (
                            fieldname == m.verbose_name.lower()
                            or fieldname == m.name.lower()
                        ):
                            field = m
                            break
                    if not field:
                        # Irrelevant data field
                        continue
                    for col in pivotbuckets:
                        try:
                            val = rowWrapper.get(col, None)
                            if val is not None and val != "":
                                svcdata.append(
                                    {
                                        "bucket": col,
                                        "forecast": rowWrapper.get("forecast", None),
                                        "item": rowWrapper.get("item", None),
                                        "location": rowWrapper.get("location", None),
                                        "customer": rowWrapper.get("customer", None),
                                        field.name: val * multiplier,
                                    }
                                )
                                if len(svcdata) >= 1000:
                                    for e in sendToService(svcdata):
                                        yield (ERROR, None, None, None, e)
                                    svcdata = []
                                changed += 1
                        except ConnectionError:
                            yield (
                                ERROR,
                                None,
                                None,
                                None,
                                "The connection with the web service was lost",
                            )
                            raise StopIteration
                        except Exception as e:
                            errors += 1
                            yield (ERROR, rownumber, field, val, str(e))
                else:
                    # Upload in list layout
                    try:
                        r = {
                            m.name: (
                                rowWrapper.get(m.name) * multiplier
                                if rowWrapper.get(m.name) is not None
                                and rowWrapper.get(m.name) != ""
                                else None
                            )
                            for m in measures
                        }
                        for f in (
                            "forecast",
                            "item",
                            "customer",
                            "location",
                            "startdate",
                            "enddate",
                            "bucket",
                        ):
                            t = rowWrapper.get(f, None)
                            if isinstance(t, datetime):
                                t = t.strftime("%Y-%m-%dT%H:%M:%S")
                            if t:
                                r[f] = t
                        svcdata.append(r)
                        if len(svcdata) >= 1000:
                            for e in sendToService(svcdata):
                                yield (ERROR, None, None, None, e)
                            svcdata = []
                        changed += 1
                    except ConnectionError:
                        yield (
                            ERROR,
                            None,
                            None,
                            None,
                            "The connection with the web service was lost",
                        )
                        raise StopIteration
                    except Exception as e:
                        errors += 1
                        yield (ERROR, rownumber, None, None, str(e))

        if svcdata:
            for e in sendToService(svcdata):
                yield (ERROR, None, None, None, e)

        # Add any missing forecast record
        if populateForecastTable:
            with connections[database].cursor() as cursor:
                # create a temp table to process a possible new forecast combination
                cursor.execute(
                    """
                            create temporary table forecast_combinations as
                            select item_id, location_id, customer_id from forecast where false;
                            create unique index on forecast_combinations (item_id, location_id, customer_id);
                            """
                )
                # insert all combinations found in the file
                cursor.executemany(
                    "insert into forecast_combinations values (%s,%s,%s)",
                    forecast_combinations,
                )
                # delete invalid combinations
                cursor.execute(
                    """
                            delete from forecast_combinations
                            where item_id is null
                            or location_id is null
                            or customer_id is null;
                            """
                )
                # delete combinations where the forecast record exists
                cursor.execute(
                    """
                            delete from forecast_combinations
                            where exists (select 1 from forecasthierarchy
                                                where item_id = forecast_combinations.item_id
                                                and location_id = forecast_combinations.location_id
                                                and customer_id = forecast_combinations.customer_id);
                            """
                )
                # delete any non-leaf combinations
                cursor.execute(
                    """
                    delete from forecast_combinations where
                    item_id not in (select name from item where lft = rght-1)
                    or location_id not in (select name from location where lft = rght-1)
                    or customer_id not in (select name from customer where lft = rght-1);
                    """
                )

                # insert the new forecast records
                cursor.execute(
                    """
                        insert into forecast (name, item_id, location_id, customer_id, discrete, priority, method, planned)
                        select item_id||' @ '||location_id||' @ '||customer_id,
                        item_id, location_id, customer_id, true, 20, 'automatic', true from forecast_combinations
                        on conflict (name) do nothing;
                                    """
                )
                # update the forecasthierarchy table
                cursor.execute(
                    """
                with cte as (
                    select item_parent.name as item_id,
                        location_parent.name as location_id,
                        customer_parent.name as customer_id from forecast_combinations
                    inner join item on item.name = forecast_combinations.item_id
                    inner join location on location.name = forecast_combinations.location_id
                    inner join customer on customer.name = forecast_combinations.customer_id
                    inner join item item_parent on item.lft between item_parent.lft and item_parent.rght
                    inner join location location_parent on location.lft between location_parent.lft and location_parent.rght
                    inner join customer customer_parent on customer.lft between customer_parent.lft and customer_parent.rght
                    )
                    insert into forecasthierarchy
                    select * from cte on conflict (item_id, location_id, customer_id) do nothing;
                    """
                )

        if session:
            Forecast.flush(session, mode="auto", database=database, token=token)
            session.close()
        yield (
            INFO,
            None,
            None,
            None,
            _(
                "%(rows)d data rows, changed %(changed)d and added %(added)d records, %(errors)d errors, %(warnings)d warnings"
            )
            % {
                "rows": rownumber - 1,
                "changed": changed,
                "added": 0,
                "errors": errors,
                "warnings": warnings,
            },
        )

        # refresh materialized view in case new combinations have been added
        with connections[database].cursor() as cursor:
            cursor.execute("REFRESH MATERIALIZED VIEW forecastreport_view")
            cursor.execute("analyze forecastreport_view")

    @staticmethod
    def refreshTableColumns(database=DEFAULT_DB_ALIAS):
        """
        Adjust the forecastplan table to have a columnn for every measure.

        This method is opening a database connection to all active scenarios,
        and can have an impact on scalability. Call with care!
        """
        # Get a list with all expected columns
        expected_columns = [
            m.name for m in Measure.standard_measures() if not m.computed
        ]
        for m in Measure.objects.using(database).only("name"):
            expected_columns.append(m.name)

        # Check the forecastplan table
        modified = False
        with connections[database].cursor() as cursor:
            cursor.execute(
                """
                select column_name
                from information_schema.columns
                where table_name = 'forecastplan'
                and column_name not in (
                    'item_id', 'location_id', 'customer_id', 'startdate', 'enddate'
                    )
                """
            )
            columns = [c[0] for c in cursor.fetchall()]
            for m in expected_columns:
                if m not in columns:
                    cursor.execute(
                        "alter table forecastplan add column if not exists %s decimal(20,8)"
                        % m
                    )
                    modified = True
            for c in columns:
                if c not in expected_columns:
                    cursor.execute(
                        "alter table forecastplan drop column if exists %s" % c
                    )
                    modified = True

        if modified:
            # Trigger wsgi reload by importing from freppledb.common.utils.force
            forceWsgiReload()


class Measure(AuditModel):
    obfuscate = False

    @classmethod
    def standard_measures(cls):
        if not hasattr(cls, "_standardmeasures"):
            cls._standardmeasures = (
                # Measures computed in the backend
                # TODO the past, future and outlier measures need to be defined
                # first: that's unfortunately hardcoded in the forecast report grid
                Measure(
                    name="past",
                    mode_past="hide",
                    mode_future="hide",
                    computed="backend",
                    initially_hidden=True,
                ),
                Measure(
                    name="future",
                    mode_past="hide",
                    mode_future="hide",
                    computed="backend",
                    initially_hidden=True,
                ),
                Measure(
                    name="outlier",
                    mode_past="hide",
                    mode_future="hide",
                    computed="backend",
                    initially_hidden=True,
                ),
                # Measures computed in the frontend
                Measure(
                    name="orderstotal3ago",
                    type="aggregate",
                    label=_("total orders 3 years ago"),
                    mode_future="view",
                    mode_past="hide",
                    formatter="number",
                    computed="frontend",
                ),
                Measure(
                    name="ordersadjustment3ago",
                    type="aggregate",
                    label=_("orders adjustment 3 years ago"),
                    mode_future="edit",
                    mode_past="hide",
                    formatter="number",
                    computed="frontend",
                    initially_hidden=True,
                ),
                Measure(
                    name="orderstotalvalue3ago",
                    type="aggregate",
                    label=_("total orders value 3 years ago"),
                    mode_future="view",
                    mode_past="hide",
                    formatter="currency",
                    computed="frontend",
                    initially_hidden=True,
                ),
                Measure(
                    name="ordersadjustmentvalue3ago",
                    type="aggregate",
                    label=_("orders adjustment value 3 years ago"),
                    mode_future="edit",
                    mode_past="hide",
                    formatter="currency",
                    computed="frontend",
                    initially_hidden=True,
                ),
                Measure(
                    name="orderstotal2ago",
                    type="aggregate",
                    label=_("total orders 2 years ago"),
                    mode_future="view",
                    mode_past="hide",
                    formatter="number",
                    computed="frontend",
                ),
                Measure(
                    name="ordersadjustment2ago",
                    type="aggregate",
                    label=_("orders adjustment 2 years ago"),
                    mode_future="edit",
                    mode_past="hide",
                    formatter="number",
                    computed="frontend",
                    initially_hidden=True,
                ),
                Measure(
                    name="orderstotalvalue2ago",
                    type="aggregate",
                    label=_("total orders value 2 years ago"),
                    mode_future="view",
                    mode_past="hide",
                    formatter="currency",
                    computed="frontend",
                    initially_hidden=True,
                ),
                Measure(
                    name="ordersadjustmentvalue2ago",
                    type="aggregate",
                    label=_("orders adjustment value 2 years ago"),
                    mode_future="edit",
                    mode_past="hide",
                    formatter="currency",
                    computed="frontend",
                    initially_hidden=True,
                ),
                Measure(
                    name="orderstotal1ago",
                    type="aggregate",
                    label=_("total orders 1 years ago"),
                    mode_future="view",
                    mode_past="hide",
                    formatter="number",
                    computed="frontend",
                ),
                Measure(
                    name="ordersadjustment1ago",
                    type="aggregate",
                    label=_("orders adjustment 1 years ago"),
                    mode_future="edit",
                    mode_past="hide",
                    formatter="number",
                    computed="frontend",
                ),
                Measure(
                    name="orderstotalvalue1ago",
                    type="aggregate",
                    label=_("total orders value 1 years ago"),
                    mode_future="view",
                    mode_past="hide",
                    formatter="currency",
                    computed="frontend",
                    initially_hidden=True,
                ),
                Measure(
                    name="ordersadjustmentvalue1ago",
                    type="aggregate",
                    label=_("orders adjustment value 1 years ago"),
                    mode_future="edit",
                    mode_past="hide",
                    formatter="currency",
                    computed="frontend",
                    initially_hidden=True,
                ),
                # Unit measures
                Measure(
                    name="orderstotal",
                    type="aggregate",
                    label=_("total orders"),
                    mode_future="view",
                    mode_past="view",
                    formatter="number",
                ),
                Measure(
                    name="ordersopen",
                    type="aggregate",
                    label=_("open orders"),
                    mode_future="view",
                    mode_past="view",
                    formatter="number",
                    initially_hidden=True,
                ),
                Measure(
                    name="ordersadjustment",
                    type="aggregate",
                    label=_("orders adjustment"),
                    mode_future="hide",
                    mode_past="edit",
                    formatter="number",
                ),
                Measure(
                    name="forecastbaseline",
                    type="aggregate",
                    label=_("forecast baseline"),
                    mode_future="view",
                    mode_past="hide",
                    formatter="number",
                ),
                Measure(
                    name="forecastoverride",
                    type="aggregate",
                    label=_("forecast override"),
                    mode_future="edit",
                    mode_past="view",
                    defaultvalue=-1,
                    formatter="number",
                ),
                Measure(
                    name="forecastnet",
                    type="aggregate",
                    label=_("forecast net"),
                    mode_future="view",
                    mode_past="hide",
                    formatter="number",
                    initially_hidden=True,
                ),
                Measure(
                    name="forecastconsumed",
                    type="aggregate",
                    label=_("forecast consumed"),
                    mode_future="view",
                    mode_past="hide",
                    formatter="number",
                    initially_hidden=True,
                ),
                Measure(
                    name="ordersplanned",
                    type="aggregate",
                    label=_("planned orders"),
                    mode_future="view",
                    mode_past="hide",
                    formatter="number",
                    initially_hidden=False,
                ),
                Measure(
                    name="forecastplanned",
                    type="aggregate",
                    label=_("planned net forecast"),
                    mode_future="view",
                    mode_past="hide",
                    formatter="number",
                    initially_hidden=False,
                ),
                # Measures computed in the backend
                Measure(
                    name="backlogorder",
                    type="aggregate",
                    label=_("order backlog"),
                    mode_past="view",
                    mode_future="view",
                    computed="backend",
                    initially_hidden=True,
                ),
                Measure(
                    name="backlogforecast",
                    type="aggregate",
                    label=_("forecast backlog"),
                    mode_past="view",
                    mode_future="view",
                    computed="backend",
                    initially_hidden=True,
                ),
                Measure(
                    name="backlog",
                    type="aggregate",
                    label=_("backlog"),
                    mode_past="view",
                    mode_future="view",
                    computed="backend",
                    initially_hidden=True,
                ),
                Measure(
                    name="totaldemand",
                    type="aggregate",
                    label=_("total demand"),
                    mode_past="view",
                    mode_future="view",
                    computed="backend",
                    initially_hidden=True,
                ),
                Measure(
                    name="totalsupply",
                    type="aggregate",
                    label=_("total supply"),
                    mode_past="view",
                    mode_future="view",
                    computed="backend",
                    initially_hidden=True,
                ),
                Measure(
                    name="backlogordervalue",
                    type="aggregate",
                    label=_("order backlog value"),
                    mode_past="view",
                    mode_future="view",
                    formatter="currency",
                    initially_hidden=True,
                    computed="backend",
                ),
                Measure(
                    name="backlogforecastvalue",
                    type="aggregate",
                    label=_("forecast backlog value"),
                    mode_past="view",
                    mode_future="view",
                    formatter="currency",
                    initially_hidden=True,
                    computed="backend",
                ),
                Measure(
                    name="backlogvalue",
                    type="aggregate",
                    label=_("backlog value"),
                    mode_past="view",
                    mode_future="view",
                    formatter="currency",
                    initially_hidden=True,
                    computed="backend",
                ),
                Measure(
                    name="totaldemandvalue",
                    type="aggregate",
                    label=_("total demand value"),
                    mode_past="view",
                    mode_future="view",
                    formatter="currency",
                    initially_hidden=True,
                    computed="backend",
                ),
                Measure(
                    name="totalsupplyvalue",
                    type="aggregate",
                    label=_("total supply value"),
                    mode_past="view",
                    mode_future="view",
                    formatter="currency",
                    initially_hidden=True,
                    computed="backend",
                ),
            )
        return cls._standardmeasures

    # Types of measures.
    types = (
        ("aggregate", _("aggregate")),
        ("local", _("local")),
        ("computed", _("computed")),
    )
    modes = (("edit", _("edit")), ("view", _("view")), ("hide", _("hide")))
    formatters = (("number", _("number")), ("currency", _("currency")))

    # Database fields
    name = models.CharField(
        _("name"), primary_key=True, help_text=_("Unique identifier")
    )
    label = models.CharField(
        _("label"),
        null=True,
        blank=True,
        help_text=_("Label to be displayed in the user interface"),
    )
    description = models.CharField(_("description"), null=True, blank=True)
    type = models.CharField(
        _("type"),
        null=True,
        blank=True,
        choices=types,
        default="default",
    )
    mode_future = models.CharField(
        _("mode in future periods"),
        null=True,
        blank=True,
        choices=modes,
        default="edit",
    )
    mode_past = models.CharField(
        _("mode in past periods"),
        null=True,
        blank=True,
        choices=modes,
        default="edit",
    )
    compute_expression = models.CharField(
        _("compute expression"),
        null=True,
        blank=True,
        help_text=_("Formula to compute values"),
    )
    update_expression = models.CharField(
        _("update expression"),
        null=True,
        blank=True,
        help_text=_("Formula executed when updating this field"),
    )
    initially_hidden = models.BooleanField(
        _("initially hidden"),
        null=True,
        blank=True,
        help_text=_("controls whether or not this measure is visible by default"),
    )
    formatter = models.CharField(
        _("format"),
        null=True,
        blank=True,
        choices=formatters,
        default="number",
    )
    discrete = models.BooleanField(_("discrete"), null=True, blank=True)
    defaultvalue = models.DecimalField(
        _("default value"),
        max_digits=20,
        decimal_places=8,
        default=0,
        null=True,
        blank=True,
    )
    overrides = models.CharField(_("override measure"), null=True, blank=True)

    @property
    def editable(self):
        return self.mode_future == "edit" or self.mode_past == "edit"

    @property
    def verbose_name(self):
        return self.label or self.name

    @property
    def computed(self):
        """
        A measure can be computed, either in frontend javascript or in backend python.
        TODO Make this a database field rather than hidden logic.
        """
        return getattr(self, "_computed", False)

    @computed.setter
    def computed(self, value):
        self._computed = value

    def clean(self):
        if self.name and not (
            self.name.isalnum() and self.name.islower() and self.name[0].isalpha()
        ):
            raise ValidationError(
                _("Name can only be lowercase alphanumeric starting with a letter")
            )

    def save(self, *args, **kwargs):
        # Call the real save() method
        super().save(*args, **kwargs)

        # Add or update the database schema
        ForecastPlan.refreshTableColumns(database=self._state.db)

    def delete(self, *args, **kwargs):
        # Call the real save() method
        super().delete(*args, **kwargs)

        # Add or update the database schema
        ForecastPlan.refreshTableColumns(database=self._state.db)

    class Meta(AuditModel.Meta):
        db_table = "measure"
        verbose_name = _("measure")
        verbose_name_plural = _("measures")
        ordering = ["name"]

    def __str__(self):
        return self.name


class ForecastPlanView(models.Model):
    # Model managers
    objects = models.Manager()  # The default model manager

    # Database fields
    name = models.CharField("name", null=False, blank=False, primary_key=True)
    item_id = models.CharField("item", null=False, blank=False)
    location_id = models.CharField("location", null=False, blank=False)
    customer_id = models.CharField("customer", null=False, blank=False)

    class Meta(AuditModel.Meta):
        db_table = "forecastreport_view"
        verbose_name = "forecastreport_view"
        verbose_name_plural = "forecastreports_view"
        unique_together = (("item_id", "location_id", "customer_id"),)
        managed = False


def Benchmark():
    """
    Code used for testing the throughput of the forecast engine. It posts
    a continuous series of random forecast updates.

    To test, you will need to launch multiple Python processes executing this
    function because the forecast engine can handle more messages per second
    than a single test process can generate. The test script is the bottleneck.
    """
    session = requests.Session()
    items = [i.name for i in Item.objects.all().only("name")]
    customers = [i.name for i in Customer.objects.all().only("name")]
    locations = [i.name for i in Location.objects.all().only("name")]
    buckets = [
        (date(2019, 12, 2), date(2019, 12, 9)),
        (date(2019, 12, 9), date(2019, 12, 16)),
        (date(2019, 12, 16), date(2019, 12, 23)),
        (date(2019, 12, 23), date(2019, 12, 30)),
    ]
    print("items:", items)
    print("customers:", customers)
    print("locations:", locations)
    print("buckets:", buckets)

    count = 0
    start = datetime.now()
    while True:
        count += 1
        bckt = random.choice(buckets)
        Forecast.updatePlan(
            startdate=bckt[0],
            enddate=bckt[1],
            forecastoverride=random.randint(0, 1000),
            ordersadjustment=None,
            units=False,
            forecast=None,
            item=random.choice(items),
            location=random.choice(locations),
            customer=random.choice(customers),
            session=session,
        )
        if count % 1000 == 0:
            delta = datetime.now() - start
            print(
                count,
                " messages ",
                delta,
                round(count / delta.total_seconds()),
                "per second",
            )
