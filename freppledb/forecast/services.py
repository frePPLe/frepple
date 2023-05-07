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
        print("pppp", self.scope)
        if self.scope["method"] != "POST":
            await self.send_response(
                401,
                (self.msgtemplate % "Only POST requests allowed").encode("utf-8"),
                headers=[(b"Content-Type", b"text/plain")],
            )
            return

        await self.send_response(
                200,
                (self.msgtemplate % "OK").encode("utf-8"),
                headers=[(b"Content-Type", b"text/plain")],
            )

        # # Check permissions
        # if not request.user.has_perm("forecast.add_forecastplan"):
        #     return HttpResponseForbidden("<h1>%s</h1>" % _("Permission denied"))

        # data = json.loads(request.body.decode(request.encoding))
        # errors = []

        # # Validate item
        # item = None
        # try:
        #     itemname = data.get("item", None)
        #     if itemname:
        #         item = Item.objects.all().using(request.database).get(pk=itemname)
        #     else:
        #         item = Item.objects.all().using(request.database).get(lvl=0)
        # except Item.DoesNotExist:
        #     errors.append("Item not found")
        # except Item.MultipleObjectsReturned:
        #     errors.append("Multiple items found")

        # # Validate location
        # location = None
        # try:
        #     locationname = data.get("location", None)
        #     if locationname:
        #         location = (
        #             Location.objects.all().using(request.database).get(pk=locationname)
        #         )
        #     else:
        #         location = Location.objects.all().using(request.database).get(lvl=0)
        # except Location.DoesNotExist:
        #     errors.append("Location not found")
        # except Location.MultipleObjectsReturned:
        #     errors.append("Multiple locations found")

        # # Validate customer
        # customer = None
        # try:
        #     customername = data.get("customer", None)
        #     if customername:
        #         customer = (
        #             Customer.objects.all().using(request.database).get(pk=customername)
        #         )
        #     else:
        #         customer = Customer.objects.all().using(request.database).get(lvl=0)
        # except Customer.DoesNotExist:
        #     errors.append("Customer not found")
        # except Customer.MultipleObjectsReturned:
        #     errors.append("Multiple customers found")

        # # Find forecast
        # try:
        #     fcst = (
        #         Forecast.objects.all()
        #         .using(request.database)
        #         .get(item=item, location=location, customer=customer)
        #     )
        # except Forecast.DoesNotExist:
        #     fcst = None

        # simulate = False  # data.get("recalculate", False) No simulations for now

        # # Save all changes to the database
        # session = requests.Session()
        # with transaction.atomic(using=request.database):

        #     if fcst:
        #         # Update forecast method
        #         mthd = data.get("forecastmethod", None)
        #         if mthd:
        #             if not request.user.has_perm("forecast.change_forecast"):
        #                 errors.append(force_str(_("Permission denied")))
        #             else:
        #                 fcst.method = mthd
        #                 fcst.save(using=request.database)

        #     # Update forecast values
        #     if "buckets" in data:
        #         if not request.user.has_perm("forecast.change_forecast"):
        #             errors.append(force_str(_("Permission denied")))
        #         else:
        #             # Build a list of buckets
        #             buckets = {}
        #             horizonbuckets = data.get("horizonbuckets", None)
        #             for b in BucketDetail.objects.using(request.database).filter(
        #                 bucket=horizonbuckets
        #             ):
        #                 buckets[b.name] = (b.startdate, b.enddate)

        #             if not buckets:
        #                 errors.append("No forecast buckets found")
        #             else:
        #                 # Process the updates
        #                 for bckt in data["buckets"]:
        #                     if bckt["bucket"] in buckets:
        #                         data = {
        #                             "startdate": buckets[bckt["bucket"]][0],
        #                             "enddate": buckets[bckt["bucket"]][1],
        #                             "database": request.database,
        #                             "forecast": None,
        #                             "item": item.name,
        #                             "location": location.name,
        #                             "customer": customer.name,
        #                             "session": session,
        #                         }
        #                         for key, val in bckt.items():
        #                             if key not in (
        #                                 "startdate",
        #                                 "enddate",
        #                                 "bucket",
        #                                 "item",
        #                                 "location",
        #                                 "customer",
        #                             ):
        #                                 data[key] = float(val)
        #                         Forecast.updatePlan(**data)

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

        # if errors:
        #     logger.error("Error saving forecast updates: %s" % "".join(errors))
        #     return HttpResponseServerError(
        #         "Error saving forecast updates: %s" % "<br/>".join(errors)
        #     )
        # else:
        #     return HttpResponse(content="OK")