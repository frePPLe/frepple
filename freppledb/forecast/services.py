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

import frepple

import json

from channels.db import database_sync_to_async
from channels.generic.http import AsyncHttpConsumer

from django.conf import settings
from django.contrib.contenttypes.models import ContentType


from freppledb.webservice.utils import lock
from freppledb.common.localization import parseLocalizedDateTime
from freppledb.common.models import Comment
from freppledb.forecast.models import Forecast
from freppledb.input.models import Item, Location, Customer, Buffer
from freppledb.webservice.utils import fcst_solver


class ForecastService(AsyncHttpConsumer):
    """
    Processes forecast update messages in these formats:
    - From forecast editor:
      {item, location, customer, buckets:[{startdate, endate, bucket, msr1, msr2}]}
    - From forecast report (regular jqgrid save) and excel upload:
      [{item, location, customer, bucket, startdate, endate, msr1, msr2}]
    """

    msgtemplate = """
        <!doctype html>
        <html lang="en">
            <head>
            <meta http-equiv="content-type" content="text/html; charset=utf-8">
            </head>
            <body>%s</body>
        </html>
        """

    @database_sync_to_async
    def updateForecastMethod(self, f):
        Forecast.objects.all().using(self.scope["database"]).filter(
            item=f.item.name, location=f.location.name, customer=f.customer.name
        ).update(method=f.methods)

    @database_sync_to_async
    def replan(self, item, location):
        from freppledb.forecast.commands import ExportForecastMetrics

        cluster = frepple.buffer(
            name="%s @ %s" % (item.name, location.name),
            item=item,
            location=location,
        ).cluster
        # Recompute the forecast
        fcst_solver.solve(
            cluster=cluster,
        )

        # Minimal export - full cluster replan is taking too long.
        ExportForecastMetrics().run(database=self.scope["database"], cluster=[cluster])

    @database_sync_to_async
    def updateComment(self, commenttype, comment, item, location, customer):
        if commenttype == "item" and item:
            Comment(
                content_object=Item.objects.using(self.scope["database"]).get(
                    name=item.name
                ),
                user=self.scope["user"],
                comment=comment,
                type="comment",
            ).save(using=self.scope["database"])
        elif commenttype == "location" and location:
            Comment(
                content_object=Location.objects.using(self.scope["database"]).get(
                    name=location.name
                ),
                user=self.scope["user"],
                comment=comment,
                type="comment",
            ).save(using=self.scope["database"])
        elif commenttype == "customer" and customer:
            Comment(
                content_object=Customer.objects.using(self.scope["database"]).get(
                    name=customer.name
                ),
                user=self.scope["user"],
                comment=comment,
                type="comment",
            ).save(using=self.scope["database"])
        elif commenttype == "itemlocation" and item and location:

            b = Buffer(
                id="%s %s",
            )
            b.pk = "%s @ %s" % (item.name, location.name)
            Comment(
                content_object=b,
                user=self.scope["user"],
                comment=comment,
                type="comment",
            ).save(using=self.scope["database"])
        else:
            raise Exception("Invalid comment type")

    async def handle(self, body):
        async with lock:
            errors = []
            try:
                if self.scope["method"] != "POST":
                    self.scope["response_headers"].append(
                        (b"Content-Type", b"text/html")
                    )
                    await self.send_response(
                        401,
                        (self.msgtemplate % "Only POST requests allowed").encode(),
                        headers=self.scope["response_headers"],
                    )
                    return

                # Check permissions
                if not self.scope["user"].has_perm("forecast.change_forecast"):
                    self.scope["response_headers"].append(
                        (b"Content-Type", b"text/html")
                    )
                    await self.send_response(
                        403,
                        (self.msgtemplate % "Permission denied").encode(),
                        headers=self.scope["response_headers"],
                    )
                    return

                data = json.loads(body.decode("utf-8"))

                try:
                    replan = False
                    frepple.cache.write_immediately = False
                    if isinstance(data, list):
                        # Message format #1
                        for bckt in data:
                            # Validate
                            item = None
                            location = None
                            customer = None
                            if bckt.get("item", None):
                                try:
                                    item = frepple.item(name=bckt["item"], action="C")
                                except Exception:
                                    errors.append("Item not found: %s" % bckt["item"])
                            else:
                                # Use root item
                                for i in frepple.items():
                                    item = i
                                    break
                                while item and item.owner:
                                    item = item.owner
                            if bckt.get("location", None):
                                try:
                                    location = frepple.location(
                                        name=bckt["location"], action="C"
                                    )
                                except Exception:
                                    errors.append(
                                        "Location not found: %s" % bckt["location"]
                                    )
                            else:
                                # Use root location
                                for i in frepple.locations():
                                    location = i
                                    break
                                while location and location.owner:
                                    location = location.owner
                            if bckt.get("customer", None):
                                try:
                                    customer = frepple.customer(
                                        name=bckt["customer"], action="C"
                                    )
                                except Exception:
                                    errors.append(
                                        "Customer not found: %s" % bckt["customer"]
                                    )
                            else:
                                # Use root customer
                                for i in frepple.customers():
                                    customer = i
                                    break
                                while customer and customer.owner:
                                    customer = customer.owner
                            if customer and item and location:
                                try:
                                    args = {
                                        "item": item,
                                        "location": location,
                                        "customer": customer,
                                    }
                                    bucket = bckt.get("bucket", None)
                                    if bucket:
                                        args["bucket"] = bucket.lower()
                                    startdate = bckt.get("startdate", None)
                                    if startdate:
                                        args["startdate"] = parseLocalizedDateTime(
                                            startdate
                                        )
                                    enddate = bckt.get("enddate", None)
                                    if enddate:
                                        args["enddate"] = parseLocalizedDateTime(
                                            enddate
                                        )
                                    for key, val in bckt.items():
                                        if (
                                            key
                                            not in (
                                                "id",
                                                "item",
                                                "location",
                                                "customer",
                                                "bucket",
                                                "startdate",
                                                "enddate",
                                                "forecast",
                                            )
                                            and val is not None
                                            and val != ""
                                        ):
                                            args[key] = float(val)
                                    frepple.setForecast(**args)
                                    replan = True
                                except Exception as e:
                                    errors.append("Error processing %s" % e)
                    else:
                        # Message format #2

                        # Pick up item, customer and location
                        item = None
                        location = None
                        customer = None
                        if data.get("item", None):
                            try:
                                item = frepple.item(name=data["item"], action="C")
                            except Exception:
                                errors.append("Item not found: %s" % data["item"])
                        else:
                            # Use root item
                            for i in frepple.items():
                                item = i
                                break
                            while item and item.owner:
                                item = item.owner
                        if data.get("location", None):
                            try:
                                location = frepple.location(
                                    name=data["location"], action="C"
                                )
                            except Exception:
                                errors.append(
                                    "Location not found: %s" % data["location"]
                                )
                        else:
                            # Use root location
                            for i in frepple.locations():
                                location = i
                                break
                            while location and location.owner:
                                location = location.owner
                        if data.get("customer", None):
                            try:
                                customer = frepple.customer(
                                    name=data["customer"], action="C"
                                )
                            except Exception:
                                errors.append(
                                    "Customer not found: %s" % data["customer"]
                                )
                        else:
                            # Use root customer
                            for i in frepple.customers():
                                customer = i
                                break
                            while customer and customer.owner:
                                customer = customer.owner

                        # Update forecast method
                        method = data.get("forecastmethod", None)
                        if method and self.scope["user"].has_perm(
                            "forecast.change_forecast"
                        ):
                            try:
                                if item and location and customer:
                                    for f in item.demands:
                                        if (
                                            isinstance(f, frepple.demand_forecastbucket)
                                            and f.location
                                            and f.location.name == location.name
                                            and f.customer == customer
                                            and f.owner.methods != method
                                        ):
                                            f.owner.methods = method
                                            replan = True
                                            await self.updateForecastMethod(f.owner)
                                        elif (
                                            isinstance(f, frepple.demand_forecast)
                                            and f.location
                                            and f.location.name == location.name
                                            and f.customer == customer
                                            and f.methods != method
                                        ):
                                            f.methods = method
                                            replan = True
                                            await self.updateForecastMethod(f)
                                else:
                                    if not item:
                                        errors.append(
                                            "Item not found: %s" % data["item"]
                                        )
                                    if not location:
                                        errors.append(
                                            "Location not found: %s" % data["location"]
                                        )
                                    if not customer:
                                        errors.append(
                                            "Customer not found: %s" % data["customer"]
                                        )
                            except Exception:
                                errors.append("Exception updating forecast method")

                        # Update forecast values
                        if (
                            "buckets" in data
                            and item
                            and location
                            and customer
                            and self.scope["user"].has_perm("forecast.change_forecast")
                        ):
                            for bckt in data["buckets"]:
                                try:
                                    args = {
                                        "item": item,
                                        "location": location,
                                        "customer": customer,
                                    }
                                    bucket = bckt.get("bucket", None)
                                    if bucket:
                                        args["bucket"] = bucket.lower()
                                    startdate = bckt.get("startdate", None)
                                    if startdate:
                                        args["startdate"] = parseLocalizedDateTime(
                                            startdate
                                        )
                                    enddate = bckt.get("enddate", None)
                                    if enddate:
                                        args["enddate"] = parseLocalizedDateTime(
                                            enddate
                                        )
                                    for key, val in bckt.items():
                                        if (
                                            key
                                            not in (
                                                "id",
                                                "bucket",
                                                "startdate",
                                                "enddate",
                                            )
                                            and val is not None
                                            and val != ""
                                        ):
                                            args[key] = float(val)
                                            if key != "forecastoverride":
                                                replan = True
                                    frepple.setForecast(**args)
                                except Exception as e:
                                    errors.append("Error processing %s" % e)

                        if replan:
                            try:
                                await self.replan(item, location)
                            except Exception:
                                errors.append(b"Exception during replanning")

                finally:
                    frepple.cache.flush()
                    frepple.cache.write_immediately = True

                # Save a new comment
                if (
                    "commenttype" in data
                    and "comment" in data
                    and self.scope["user"].has_perm("common.add_comment")
                ):
                    try:
                        await self.updateComment(
                            data["commenttype"],
                            data["comment"],
                            item,
                            location,
                            customer,
                        )
                    except Exception:
                        errors.append("Exception entering comment")

                # Reply
                self.scope["response_headers"].append(
                    (b"Content-Type", b"application/json")
                )
                if errors:
                    answer = {"errors": errors}
                else:
                    answer = {"OK": 1}
                await self.send_response(
                    500 if errors else 200,
                    json.dumps(answer).encode(),
                    headers=self.scope["response_headers"],
                )
            except Exception as e:
                errors.append(str(e).encode())
                await self.send_response(
                    500,
                    json.dumps({"errors": errors}).encode(),
                    headers=self.scope["response_headers"],
                )


class FlushService(AsyncHttpConsumer):
    async def handle(self, body):
        self.scope["response_headers"].append((b"Content-Type", b"text/html"))
        try:
            if self.scope["method"] != "POST":
                await self.send_response(
                    401,
                    b"Only POST requests allowed",
                    headers=self.scope["response_headers"],
                )
                return
            if self.scope["path"] == "/flush/manual/":
                async with lock:
                    frepple.cache.write_immediately = False
                    if settings.CACHE_MAXIMUM > 300:
                        frepple.cache.maximum = settings.CACHE_MAXIMUM
            elif self.scope["path"] == "/flush/auto/":
                async with lock:
                    frepple.cache.flush()
                    frepple.cache.write_immediately = True
                    if frepple.cache.maximum > 300:
                        frepple.cache.maximum = 300
            else:
                await self.send_response(
                    404,
                    b"Only supported modes are 'manual' and 'auto'",
                    headers=self.scope["response_headers"],
                )
            await self.send_response(200, b"OK", headers=self.scope["response_headers"])
        except Exception as e:
            await self.send_response(
                500, b"Error flushing forecast", headers=self.scope["response_headers"]
            )
