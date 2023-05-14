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
from dateutil.parser import parse
import json

from channels.generic.http import AsyncHttpConsumer


class ForecastService(AsyncHttpConsumer):

    msgtemplate = """
        <!doctype html>
        <html lang="en">
            <head>
            <meta http-equiv="content-type" content="text/html; charset=utf-8">
            </head>
            <body>%s</body>
        </html>
        """

    async def handle(self, body):
        import frepple

        if self.scope["method"] != "POST":
            self.scope["response_headers"].append((b"Content-Type", b"text/html"))
            await self.send_response(
                401,
                (self.msgtemplate % "Only POST requests allowed").encode("utf-8"),
                headers=self.scope["response_headers"],
            )
            return

        # Check permissions
        if not self.scope["user"].has_perm("forecast.change_forecast"):
            self.scope["response_headers"].append((b"Content-Type", b"text/html"))
            await self.send_response(
                403,
                (self.msgtemplate % "Permission denied").encode("utf-8"),
                headers=self.scope["response_headers"],
            )
            return

        data = json.loads(body.decode("utf-8"))
        errors = []

        # Validate
        try:
            item = frepple.item(name=data["item"], action="C")
        except:
            item = None
            errors.append(b"Item not found")
        try:
            location = frepple.location(name=data["location"], action="C")
        except:
            location = None
            errors.append(b"Location not found")
        try:
            customer = frepple.customer(name=data["customer"], action="C")
        except:
            customer = None
            errors.append(b"Customer not found")

        # Find forecast
        if item and location and customer:
            fcst = None
            pass
            # try:    TODO
            #     fcst = (
            #         Forecast.objects.all()
            #         .using(request.database)
            #         .get(item=item, location=location, customer=customer)
            #     )
            # except Forecast.DoesNotExist:
            #     fcst = None
        else:
            fcst = None

        # Update forecast method
        mthd = data.get("forecastmethod", None)
        if fcst and mthd and self.scope["user"].has_perm("forecast.change_forecast"):
            fcst.method = mthd
            print("updated forecast method to mthd", fcst.mthd)
            # TODO fcst.save(using=self.scope["database"])

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
                        args["bucket"] = bucket
                    startdate = bckt.get("startdate", None)
                    if startdate:
                        # Guess! the date format, using Month-Day-Year as preference
                        # to resolve ambiguity.
                        # This default style is also the default datestyle in Postgres
                        # https://www.postgresql.org/docs/9.1/runtime-config-client.html#GUC-DATESTYLE
                        args["startdate"] = parse(
                            startdate, yearfirst=False, dayfirst=False
                        )
                    enddate = bckt.get("enddate", None)
                    if enddate:
                        # Guess! the date format, using Month-Day-Year as preference
                        # to resolve ambiguity.
                        # This default style is also the default datestyle in Postgres
                        # https://www.postgresql.org/docs/9.1/runtime-config-client.html#GUC-DATESTYLE
                        args["enddate"] = parse(
                            enddate, yearfirst=False, dayfirst=False
                        )
                    for key, val in bckt.items():
                        if key not in ("bucket", "startdate", "enddate"):
                            args[key] = float(val)
                    frepple.setForecast(**args)
                except Exception as e:
                    errors.append(b"Error processing %s" % e)

        #     if not simulate:
        #         # Save a new comment
        #         if "commenttype" in data and "comment" in data:
        #             if not request.user.has_perm("common.add_comment"):
        #                 errors.append(force_str(_("Permission denied")))
        #             elif data["commenttype"] == "item" and item:
        #                 Comment(
        #                     content_object=item,
        #                     user=request.user,
        #                     comment=data["comment"],
        #                 ).save(using=request.database)
        #             elif data["commenttype"] == "location" and location:
        #                 Comment(
        #                     content_object=location,
        #                     user=request.user,
        #                     comment=data["comment"],
        #                 ).save(using=request.database)
        #             elif data["commenttype"] == "customer" and customer:
        #                 Comment(
        #                     content_object=customer,
        #                     user=request.user,
        #                     comment=data["comment"],
        #                 ).save(using=request.database)
        #             elif data["commenttype"] == "itemlocation":
        #                 try:
        #                     buf = (
        #                         Buffer.objects.all()
        #                         .using(request.database)
        #                         .get(item__name=item.name, location__name=location.name)
        #                     )
        #                     Comment(
        #                         content_object=buf,
        #                         user=request.user,
        #                         comment=data["comment"],
        #                     ).save(using=request.database)
        #                 except Buffer.DoesNotExist:
        #                     errors.append("Invalid comment data")
        #             else:
        #                 errors.append("Invalid comment data")

        self.scope["response_headers"].append((b"Content-Type", b"application/json"))
        if errors:
            answer = {b"errors": errors}
        else:
            answer = {"OK": 1}
        await self.send_response(
            500 if errors else 200,
            json.dumps(answer).encode("utf-8"),
            headers=self.scope["response_headers"],
        )
