#
# Copyright (C) 2019 by frePPLe bv
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
from datetime import timedelta
from dateutil.parser import parse
import json

from django.conf import settings
from django.contrib.admin.views.decorators import staff_member_required
from django.core import management
from django.db import connections
from django.http import HttpResponse, HttpResponseServerError
from django.http import HttpResponseNotAllowed, HttpResponseRedirect
from django.shortcuts import render
from django.utils.decorators import method_decorator
from django.utils.translation import gettext_lazy as _
from django.views import View
from django.views.generic.base import TemplateView

from freppledb import __version__
from freppledb.common.report import getCurrency, getCurrentDate
from freppledb.common.models import Bucket, BucketDetail, Parameter
from freppledb.common.utils import sendEmail
from freppledb.input.models import (
    Location,
    Item,
    Customer,
    Demand,
    ItemSupplier,
    ItemDistribution,
    Operation,
    PurchaseOrder,
    Buffer,
    Supplier,
    ManufacturingOrder,
    DistributionOrder,
    OperationMaterial,
    OperationResource,
    Resource,
)

import logging

logger = logging.getLogger(__name__)

if "freppledb.forecast" in settings.INSTALLED_APPS:
    from freppledb.forecast.models import ForecastPlan


def parseDuration(v):
    d = v.strip().split(": ")
    args = len(d)
    try:
        if args == 0:
            return timedelta(0)
        elif args == 1:
            return timedelta(seconds=int(d[0]))
        elif args == 2:
            return timedelta(minutes=int(d[0]), seconds=int(d[1]))
        elif args == 3:
            return timedelta(hours=int(d[0]), minutes=int(d[1]), seconds=int(d[2]))
        elif args > 3:
            return timedelta(
                days=int(d[0]), hours=int(d[1]), minutes=int(d[2]), seconds=int(d[3])
            )
    except Exception:
        return timedelta(0)


def getWizardSteps(request, mode):
    try:
        versionnumber = __version__.split(".", 2)
        docurl = "%s/docs/%s.%s" % (
            settings.DOCUMENTATION_URL,
            versionnumber[0],
            versionnumber[1],
        )
    except Exception:
        docurl = "%s/docs/current" % settings.DOCUMENTATION_URL
    context = {
        "docroot": docurl,
        "prefix": request.prefix,
        "label_data": '<span class="badge bg-primary">Data entry</span>',
        "label_config": '<span class="badge bg-primary">Configuration</span>',
        "label_action": '<span class="badge bg-danger">Action</span>',
        "label_check": '<span class="badge bg-primary">Check</span>',
        "label_analysis": '<span class="badge bg-success">Analyis</span>',
    }

    # Possible icons to display on the right hand side
    ICON_DONE = "fa-check-square-o"
    ICON_AVAILABLE = "fa-square-o"
    ICON_LOCK = "fa-lock"

    index = 0
    steps = []
    script = ""
    locked = False
    done = False

    # Welcome step
    if mode:
        welcome = """
           <p>Work towards the goal!</p>
           <p>New steps unlock only if you complete the previous one.</p>
           """
    else:
        welcome = """This wizard will guide you through the steps to load your data and configure up a
           first basic planning model.<br>
           <br>
           Before you start, we need to set some expectations right:
           <ol>
           <li style="list-style-type: disc">
           <p>It <b>will take you considerable time</b> before you get valid planning results
           with frePPLe. You will need to read through quite a bit of documentation,
           collect quite some data file and more forward by trial and error.</p>
           </li>
           <li style="list-style-type: disc">
           <p>This wizard guides you towards a <b>basic model only</b>. The goal is simply to get
           you started as quick and easy as possible.<br>You will find links to more
           advanced features in the bonus section of the wizard.<br>
           </p>
           </li>
           </ol>
           <p>Ready to get going? Select the type of model you want to build.</p>
           <div class="row">
           <div class="col-md-4 text-center">
             <a class="btn btn-primary" href="{prefix}/wizard/load/forecast/">Start data load wizard<br>for forecasting</a>
           </div>
           <div class="col-md-4 text-center">
             <a class="btn btn-primary" href="{prefix}/wizard/load/production/">Start data load wizard<br>for production planning</a>
           </div>
           </div>
        """
    steps.append(
        {
            "index": index,
            "title": "Welcome",
            "icon": None,
            "locked": False,
            "content": welcome.format(**context),
        }
    )
    index += 1

    if "freppledb.forecast" in settings.INSTALLED_APPS and mode == "forecast":
        # Forecasting master data
        done = (
            Item.objects.using(request.database).exists()
            and Location.objects.using(request.database).exists()
            and Customer.objects.using(request.database).exists()
        )
        locked = not done
        steps.append(
            {
                "index": index,
                "title": "Step %s: Load master data: items, locations and customers"
                % index,
                "icon": ICON_AVAILABLE if not done else ICON_DONE,
                "locked": False,
                "content": """
         <p>Unsurprisingly, we start by loading some basic master data: items, locations and customers.</p>
         <p>You can either enter some sample records one by one, or (even better) load an Excel
         or CSV file you extract from another system.</p>
         <table class="table">
         <thead>
         <tr>
           <th style="width:90px"></th>
           <th>Step</th>
           <th style="text-align: center; width:250px">Screenshot</th>
         </tr>
         </thead>
         <tbody>
           <tr><td>
           1<br>{label_data}
           </td>
           <td>
           <p><b><a href="{prefix}/data/input/item/" class="text-decoration-underline" target="_blank">Load item data</a></b>
             &nbsp;&nbsp;
             <a href="{docroot}/modeling-wizard/master-data/items.html" target="_blank">
             <i class="fa fa-book fa-2x" aria-hidden="true" data-bs-toggle="tooltip" title="Documentation"></i>
             </a>
             &nbsp;&nbsp;
             <a href="/static/wizard/sample_data/item.fcst.xlsx">
             <i class="fa fa-file-excel-o fa-2x" aria-hidden="true" data-bs-toggle="tooltip" title="Sample data in Excel format"></i>
             </a>
           </p>
           <p>Load the items you want to forecast. You can do this in various ways:<br>
           <span class="circle">A</span> Click on the plus sign to add data records one by one in form.<br>
           <span class="circle">B</span> Edit data directly in the grid.<br>
           <span class="circle">C</span> Click the up arrow icon to import a data file in Excel or CSV format. Have a look
           at the sample data to see how your data file should look like. You can even drag and drop your data
           file directly on the grid area <span class="circle">B</span>.<br>
           <span class="circle">D</span> You can click the down arrow icon to export the existing data as a spreadsheet,
           make changes to the spreadsheet and then upload it again with the up arrow icon <span class="circle">C</span>.</p>
           </td>
           <td style="text-align: center">
           <a href="#" onclick="showModalImage(event, 'Load items')"><img src="/static/wizard/img/item.png" style="width: 200px"></a>
           </td></tr>

           <tr><td>
           2<br>{label_data}
           </td>
           <td><p><b><a href="{prefix}/data/input/location/" class="text-decoration-underline" target="_blank">Load location data</a></b>
             &nbsp;&nbsp;
             <a href="{docroot}/modeling-wizard/master-data/locations.html" target="_blank">
             <i class="fa fa-book fa-2x" aria-hidden="true" data-bs-toggle="tooltip" title="Documentation"></i>
             </a>
             &nbsp;&nbsp;
             <a href="/static/wizard/sample_data/location.xlsx">
             <i class="fa fa-file-excel-o fa-2x" aria-hidden="true" data-bs-toggle="tooltip" title="Sample data in Excel format"></i>
             </a>
           </p>
           <p>Load all locations from where items are sold to customers or where inventory is stored.<br>
           Location can be structured in a hierachical tree which allows intuitive
           navigation through the forecast data at aggregated levels.</p>
           </td>
           <td style="text-align: center">
           <a href="#" onclick="showModalImage(event, 'Load locations')"><img src="/static/wizard/img/location.png" style="width: 200px"></a>
           </td></tr>

           <tr><td>
           3<br>{label_data}
           </td>
           <td><p><b><a href="{prefix}/data/input/customer/" class="text-decoration-underline" target="_blank">Load customer data</a></b>
             &nbsp;&nbsp;
             <a href="{docroot}/modeling-wizard/master-data/customers.html" target="_blank">
             <i class="fa fa-book fa-2x" aria-hidden="true" data-bs-toggle="tooltip" title="Documentation"></i>
             </a>
             &nbsp;&nbsp;
             <a href="/static/wizard/sample_data/customer.xlsx">
             <i class="fa fa-file-excel-o fa-2x" aria-hidden="true" data-bs-toggle="tooltip" title="Sample data in Excel format"></i>
             </a>
           </p>
           <p>Load all customers for which you want to compute a forecast.<br>
           In a first model we recommend to keep the customer hierarchy simple: for instance,
           map all sales to a single aggregate customer.</p>
           </td>
           <td style="text-align: center">
           <a href="#" onclick="showModalImage(event, 'Load customers')"><img src="/static/wizard/img/customer.png" style="width: 200px"></a>
           </td></tr>
         </tbody></table>
         """.format(
                    **context
                ),
            }
        )
        index += 1

        # Forecasting sales history
        if not locked:
            done = Demand.objects.using(request.database).exists()
        steps.append(
            {
                "index": index,
                "title": "Step %s: Load historical sales data" % index,
                "icon": ICON_LOCK if locked else ICON_DONE if done else ICON_AVAILABLE,
                "locked": locked,
                "content": """
         <p>With the master data in place we can now proceed and load the sales order history.</p>
         <p>You will need to load the historical demand values for a period that is typically
         2 to 3 times as long as the future time window you want to forecast for. For instance, if you
         want to forecast for next year, you will need to load 2 to 3 years of historical sales data.
         If your demand presents seasonal patterns, you should also provide at least 3 past
         cycles so that we can correctly forecast the next cycle.
         The forecasting algorithms in frePPLe are able to generate a forecast with less historical
         data than the rules of thumb described above, but the statistical accuracy will then obviously
         be somewhat lower.</p>

         <table class="table">
         <thead>
         <tr>
           <th style="width:90px"></th>
           <th>Step</th>
           <th style="text-align: center; width:250px">Screenshot</th>
         </tr>
         </thead>
         <tbody>
         <tr>
           <td style="text-align: center">1<br>{label_data}</td>
           <td><p><b><a href="{prefix}/data/input/demand/" class="text-decoration-underline" target="_blank">Load sales order data</a></b>
             &nbsp;&nbsp;
             <a href="{docroot}/modeling-wizard/master-data/sales-orders.html" target="_blank">
             <i class="fa fa-book fa-2x" aria-hidden="true" data-bs-toggle="tooltip" title="Documentation"></i>
             </a>
             &nbsp;&nbsp;
             <a href="/static/wizard/sample_data/salesorder.fcst.xlsx">
             <i class="fa fa-file-excel-o fa-2x" aria-hidden="true" data-bs-toggle="tooltip" title="Sample data in Excel format"></i>
             </a>
           </p>
           <p>Load all sales orders for the time window described above.<br>
           As the majority of these orders will already have been shipped, their status
           be "closed". Overdue backlog orders can be loaded with the status "open".<br>
           Unless the number of sales orders exceeds 2 million, we recommend to load them
           directly. For larger data volumes you might consider aggregating the data per time bucket.</p>
           </td>
           <td style="text-align: center">
           <a href="#" onclick="showModalImage(event, 'Load sales orders')"><img src="/static/wizard/img/salesorder.png" style="width: 200px"></a>
           </td></tr>
         </tbody></table>
         """.format(
                    **context
                ),
            }
        )
        index += 1
        if not locked:
            locked = not done

        # Forecasting generate plan
        if not locked:
            done = ForecastPlan.objects.using(request.database).exists()
        parameter_forecast_calendar = Parameter.getValue(
            "forecast.calendar", request.database, None
        )
        parameter_forecast_horizonfuture = int(
            Parameter.getValue("forecast.Horizon_future", request.database, "365")
        )
        parameter_currentdate = Parameter.getValue(
            "currentdate", request.database, "now"
        )
        steps.append(
            {
                "index": index,
                "title": "Step %s: Calculate statistical forecast" % index,
                "icon": ICON_LOCK if locked else ICON_DONE if done else ICON_AVAILABLE,
                "locked": locked,
                "content": """
         <p>Almost there! First, let's configure a few important parameters so
         that we can compute the statistical forecast for you.</p>

         <table class="table">
         <thead>
         <tr>
           <th style="width:90px"></th>
           <th>Step</th>
           <th style="text-align: center; width:250px">Screenshot</th>
         </tr>
         </thead>
         <tbody>

         <tr><td style="text-align: center">1<br>{label_config}</td>
         <td><p><b><a href="{prefix}/data/common/parameter/?name=forecast.calendar" class="text-decoration-underline" target="_blank">Configure the forecasting time bucket size</a></b>:</p>
         <p>Forecast values are computed by time bucket.<br>
         You need to configure what time bucket size you wish to use.</p>
         <div class="form-check ps-5 mb-2">
           <input class="form-check-input" type="radio" id="fcstbckt_month" name="fcstbckt" data-forecastbucketsize="month"
         """.format(
                    **context
                )
                + (
                    ' checked="checked"'
                    if parameter_forecast_calendar == "month"
                    else ""
                )
                + """><label for="fcstbckt_month" class="form-check-label">Monthly</label>
         </div>
         <div class="form-check ps-5 mb-3">
           <input class="form-check-input" type="radio" id="fcstbckt_week" name="fcstbckt" data-forecastbucketsize="week"
         """.format(
                    **context
                )
                + (
                    ' checked="checked"'
                    if parameter_forecast_calendar == "week"
                    else ""
                )
                + '''><label for="fcstbckt_week" class="form-check-label">Weekly</label>
         </div>
         <p class=mt-3">You can always review and update your choice with the parameter "forecast.calendar"
         in the <a href="{prefix}/data/common/parameter/" class="text-decoration-underline" target="_blank">parameter table</a>
         (available in the "admin" menu).</p>
         </td>
         <td></td>
         </tr>

         <tr>
         <td style="text-align: center">2<br>{label_config}</td>
         <td><p><b><a href="{prefix}/data/common/parameter/?name=forecast.Horizon_future" class="text-decoration-underline" target="_blank">Configure the forecasting horizon</a></b>:</p>
         <p>You also need to configure how far in the future you wish to forecast for:<br>
         <div class="ps-5 mt-2">
         <input class="form-control d-inline w-auto" style="width:20em" size="10" value="'''.format(
                    **context
                )
                + str(parameter_forecast_horizonfuture)
                + '''" data-parameter="forecast.Horizon_future"> days</div></p>
         <p>You can always review and update your choice with the parameter "forecast.Horizon_future"
         in the <a href="{prefix}/data/common/parameter/" class="text-decoration-underline" target="_blank">parameter table</a>
         (available in the "admin" menu).</p>
         </td><td colspan="2"></td></tr>

         <tr>
         <td style="text-align: center">3<br>{label_config}</td>
         <td><p><b><a href="{prefix}/data/common/parameter/?name=forecast.currentdate" class="text-decoration-underline" target="_blank">Configure the current date</a></b>:</p>
         <p>In normal situations you'll want to compute the forecast starting from today onwards.<br>
         When your dataset is not recent you may want to step back to a moment in the past, and simulate
         generating a forecast from that moment onwards.</p>
         <p>Specify here the current date (in the format YYYY-MM-DD HH:MM:SS), or leave the default
         value "now" to use the system clock.<br>
         <div class="ps-5 mt-2">
         <input class="form-control d-inline w-auto" style="width:20em" size="17" value="'''.format(
                    **context
                )
                + str(parameter_currentdate)
                + """" data-parameter="currentdate"></div></p>
         <p>You can always review and update your choice with the parameter "currentdate"
         in the <a href="{prefix}/data/common/parameter/" class="text-decoration-underline" target="_blank">parameter table</a>
         (available in the "admin" menu).</p>
         </td><td colspan="2"></td></tr>

         <tr><td style="text-align: center">4<br>{label_action}</td>
         <td><p><b><a href="{prefix}/execute/" class="text-decoration-underline" target="_blank">Generate statistical forecast</a></b>:</p>
         <p>You can now compute the first statistical forecast.</p>
         <p>Open the <a href="{prefix}/execute/">execution screen</a> (available in the "admin" menu) and select
         the "generate plan" <span class="circle">A</span> task. Make sure the option "generate forecast"
         <span class="circle">B</span>is checked.</p>
         <p><span class="circle">C</span> Launch the task and wait for it to complete. <span class="circle">D</span></p>
         <p>Whenever you change any of the intput data, you will need to come back here to recompute the forecast.</p>
         </td>
         <td style="text-align: center">
         <a href="#" onclick="showModalImage(event, 'Generate statistical forecast')"><img src="/static/wizard/img/generate_forecast.png" style="width: 200px"></a>
         </td></tr>
         </tbody></table>
         """.format(
                    **context
                ),
            }
        )
        script += (
            '''
         $("input[data-forecastbucketsize]").on('change', function(event) {
         $.ajax({
           type: 'POST',
           url: "'''
            + request.prefix
            + """/api/common/parameter/",
           data: {
             name: "forecast.calendar",
             value: $(this).attr("data-forecastbucketsize")
             }
           });
       });
      """
        )
        index += 1
        if not locked:
            locked = not done

        # Forecasting - review results
        steps.append(
            {
                "index": index,
                "title": "Step %s: Review results" % index,
                "icon": ICON_LOCK if locked else None,
                "locked": locked,
                "content": """
         <p>Now that the forecast has been computed, let's take some time to visit the main screens to
         review and update the results.</p>
         <table class="table">
         <thead>
         <tr>
         <th style="width:90px"></th>
         <th>Step</th>
         <th style="text-align: center; width:250px">Screenshot</th>
         </tr>
         </thead>
         <tbody>
         <tr>
         <td style="text-align: center">1<br>{label_analysis}</td>
         <td><p><b><a href="{prefix}/forecast/editor/" class="text-decoration-underline" target="_blank">Review forecast editor</a></b><br>
         <p>The <a href="{prefix}/forecast/editor/" class="text-decoration-underline" target="_blank">forecast editor</a> (available
         in the "sales" menu) is the main screen for reviewing the results.<p>
         <p><span class="circle">A</span> Select a combination of item + location + customer in the top pane, and
         review the details in the bottom pane.</p>
         <p><span class="circle">B</span> You can override the forecast proposed by the system. If you edit at a
         higher level the value is distributed automatically to all child levels.</p>
         <p><span class="circle">C</span> You can adjust the sales history to adjust for exceptional demands.</p>
         <p><span class="circle">D</span> You can switch from units to monetary value.</p>
         <p><span class="circle">E</span> You can also visualize the report in different time bucket sizes.</p>
         </p>
         </td>
         <td style="text-align: center">
         <a href="#" onclick="showModalImage(event, 'Forecast editor')"><img src="/static/wizard/img/forecast_editor.png" style="width: 200px"></a>
         </td>
         </tr>
         <tr><td style="text-align: center">2<br>{label_analysis}</td>
         <td><p><a href="{prefix}/forecast/" class="text-decoration-underline" target="_blank"><b>Review forecast report</b></a></p>
         <p>The <a href="{prefix}/forecast/" class="text-decoration-underline" target="_blank">forecast report</a> (available in the "sales" menu)
         is handy for going through a larger list of forecasts.</p>
         <p><span class="circle">A</span> In this screen you can easily export forecast data as a spreadsheet.<p>
         <p><span class="circle">B</span> You can also upload an Excel spreadsheet with forecast values from your sales team.</p>
         </td>
         <td style="text-align: center">
         <a href="#" onclick="showModalImage(event, 'Forecast report')"><img src="/static/wizard/img/forecast_report.png" style="width: 200px"></a>
         </td>
         </tr>
         </tbody>
         </table>
         <p class="mt-3">Congratulations! You are now able to use the forecasting capabilities of frePPLe.</p>
         """.format(
                    **context
                ),
            }
        )
        index += 1

        # Forecasting - advanced features
        steps.append(
            {
                "index": index,
                "title": "Bonus: Advanced forecasting functionality",
                "icon": ICON_LOCK if locked else None,
                "locked": locked,
                "content": """
         <p>With the basics under your belt, you are ready to dig into some more advanced
         modeling and configuration topics.</p>
         <table class="table">
         <thead>
         <tr>
         <th>Topic</th>
         <th>Description</th>
         </tr>
         </thead>
         <tbody>
         <tr>
         <td><a href="{docroot}/videos/demand-forecasting/filter-outliers.html?highlight=outlier" class="text-decoration-underline" target="_blank">Outlier detection</a></td>
         <td><p>Exceptional one-off sales can seriously impact the accuracy of the forecast.
         FrePPLe provides mechanism to automatically detect and filter them out.</p>
         </td>
         </tr>
         <tr>
         <td><a href="{docroot}/examples/forecasting/forecast-method" class="text-decoration-underline" target="_blank">Forecasting methods</a></td>
         <td><p>This example model digs into the forecasting algorithms and their configuration.</p></td>
         </tr>
         <tr>
         <td><a href="{docroot}/examples/forecasting/middle-out-forecast" class="text-decoration-underline" target="_blank">Middle-out forecasting</a></td>
         <td><p>The statistical forecast is computed by default at the lowest level in the
         hierarchies. In some situations, it's more appropriate to calculate the forecast at a higher level
         to achieve more accurate results.</p></td>
         </tr>
         <tr>
         <td><a href="{docroot}/examples/forecasting/forecast-netting" class="text-decoration-underline" target="_blank">Forecast netting</a></td>
         <td><p>Demand in the near future mostly consists of customer sales orders. Demand far out in the
         future consists mostly of forecast. In many industries, both sales and forecast
         will coexist in the same time bucket.</p>
         <p>The forecast netting (aka forecast consumption) subtracts the sales orders from the
         forecast to avoid double-planning the same demand.</p>
         </td>
         </tr>
         </tbody>
         </table>
         """.format(
                    **context
                ),
            }
        )
        index += 1
    if mode == "production":
        # Production master data
        done = (
            Item.objects.using(request.database).exists()
            and Location.objects.using(request.database).exists()
            and Customer.objects.using(request.database).exists()
        )
        locked = not done
        steps.append(
            {
                "index": index,
                "title": "Step %s: Load master data: items, locations and customers"
                % index,
                "icon": ICON_DONE if done else ICON_AVAILABLE,
                "locked": False,
                "content": """
         <p>It won't be a surprise that we start by loading some basic master data: items, locations and customers.</p>
         <p>You can either enter some sample records one by one, or (even better) load an Excel
         or CSV file you extract from some existing database.</p>

         <table class="table">
         <thead>
         <tr>
           <th style="width:90px"></th>
           <th>Step</th>
           <th style="text-align: center; width:250px">Screenshot</th>
         </tr>
         </thead>
         <tbody>
           <tr><td>
           1<br>{label_data}
           </td>
           <td>
           <p><b><a href="{prefix}/data/input/item/" class="text-decoration-underline" target="_blank">Load item data</a></b>
             &nbsp;&nbsp;
             <a href="{docroot}/modeling-wizard/master-data/items.html" target="_blank">
             <i class="fa fa-book fa-2x" aria-hidden="true" data-bs-toggle="tooltip" title="Documentation"></i>
             </a>
             &nbsp;&nbsp;
             <a href="/static/wizard/sample_data/item.mfg.xlsx">
             <i class="fa fa-file-excel-o fa-2x" aria-hidden="true" data-bs-toggle="tooltip" title="Sample data in Excel format"></i>
             </a>
           </p>
           <p>Load all items: end items sold to customers, intermediate items in the production process and
           raw materials purchased from suppliers.</p>
           <p> Data can be loaded by:<br>
           <span class="circle">A</span> Click on the plus sign to add data records one by one in form.<br>
           <span class="circle">B</span> Edit data directly in the grid.<br>
           <span class="circle">C</span> Click the up arrow icon to import a data file in Excel or CSV format. Have a look
           at the sample data to see how your data file should look like. You can even drag and drop your data
           file directly on the grid area <span class="circle">B</span>.<br>
           <span class="circle">D</span> You can click the down arrow icon to export the existing data as a spreadsheet,
           make changes to the spreadsheet and then upload it again with the up arrow icon <span class="circle">C</span>.</p>
           </td>
           <td style="text-align: center">
           <a href="#" onclick="showModalImage(event, 'Load items')"><img src="/static/wizard/img/item.png" style="width: 200px"></a>
           </td></tr>

           <tr><td>
           2<br>{label_data}
           </td>
           <td><p><b><a href="{prefix}/data/input/location/" class="text-decoration-underline" target="_blank">Load location data</a></b>
             &nbsp;&nbsp;
             <a href="{docroot}/modeling-wizard/master-data/locations.html" target="_blank">
             <i class="fa fa-book fa-2x" aria-hidden="true" data-bs-toggle="tooltip" title="Documentation"></i>
             </a>
             &nbsp;&nbsp;
             <a href="/static/wizard/sample_data/location.xlsx">
             <i class="fa fa-file-excel-o fa-2x" aria-hidden="true" data-bs-toggle="tooltip" title="Sample data in Excel format"></i>
             </a>
           </p>
           <p>Load all locations from where items are sold to customers or where inventory is stored.</p>
           </td>
           <td style="text-align: center">
           <a href="#" onclick="showModalImage(event, 'Load locations')"><img src="/static/wizard/img/location.png" style="width: 200px"></a>
           </td></tr>

           <tr><td>
           3<br>{label_data}
           </td>
           <td><p><b><a href="{prefix}/data/input/customer/" class="text-decoration-underline" target="_blank">Load customer data</a></b>
             &nbsp;&nbsp;
             <a href="{docroot}/modeling-wizard/master-data/customers.html" target="_blank">
             <i class="fa fa-book fa-2x" aria-hidden="true" data-bs-toggle="tooltip" title="Documentation"></i>
             </a>
             &nbsp;&nbsp;
             <a href="/static/wizard/sample_data/customer.xlsx">
             <i class="fa fa-file-excel-o fa-2x" aria-hidden="true" data-bs-toggle="tooltip" title="Sample data in Excel format"></i>
             </a>
           </p>
           <p>Load all customers to which products are sold.</p>
           </td>
           <td style="text-align: center">
           <a href="#" onclick="showModalImage(event, 'Load customers')"><img src="/static/wizard/img/customer.png" style="width: 200px"></a>
           </td></tr>
         </tbody></table>
         """.format(
                    **context
                ),
            }
        )
        index += 1

        # Production - sales orders
        if not locked:
            done = Demand.objects.using(request.database).exists()
        steps.append(
            {
                "index": index,
                "title": "Step %s: Load sales order data" % index,
                "icon": ICON_LOCK if locked else ICON_DONE if done else ICON_AVAILABLE,
                "locked": locked,
                "content": """
         <p>With the master data in place we can now proceed and load the sales order book.</p>

         <table class="table">
         <thead>
         <tr>
         <th style="width:90px"></th>
         <th>Step</th>
         <th style="text-align: center; width:250px">Screenshot</th>
         </tr>
         </thead>
         <tbody>
         <tr>
         <td style="text-align: center">1<br>{label_data}</td>
         <td>
           <p><b><a href="{prefix}/data/input/demand/" class="text-decoration-underline" target"_blank">Load sales order data</a></b>
             &nbsp;&nbsp;
             <a href="{docroot}/modeling-wizard/master-data/sales-orders.html" target="_blank">
             <i class="fa fa-book fa-2x" aria-hidden="true" data-bs-toggle="tooltip" title="Documentation"></i>
             </a>
             &nbsp;&nbsp;
             <a href="/static/wizard/sample_data/salesorder.mfg.xlsx">
             <i class="fa fa-file-excel-o fa-2x" aria-hidden="true" data-bs-toggle="tooltip" title="Sample data in Excel format"></i>
             </a>
           </p>
           For planning we only need the open sales orders, the remaining quantity to ship
           and the delivery date expected by customers.</p>
         </td>
         <td style="text-align: center">
         <a href="#" onclick="showModalImage(event, 'Load sales orders')"><img src="/static/wizard/img/salesorder.png" style="width: 200px"></a>
         </td></tr>
         </tbody></table>
         """.format(
                    **context
                ),
            }
        )
        index += 1
        if not locked:
            locked = not done

        # Production - define production operations
        if not locked:
            done = (
                Operation.objects.using(request.database).exists()
                and OperationMaterial.objects.using(request.database).exists()
            )
        steps.append(
            {
                "index": index,
                "title": "Step %s: Define operations and bill of material" % index,
                "icon": ICON_LOCK if locked else ICON_DONE if done else ICON_AVAILABLE,
                "locked": locked,
                "content": """
         <p>Before moving on please read
         <a href="{docroot}/modeling-wizard/concepts.html" class="text-decoration-underline" target="_blank">this page</a>.
         You'll learn how the supply chain network is built up with operations
         that are connecting buffers.<p>

         <p>There are 2 common model structures:
         <ul>
         <li style="list-style: disc">
         <p><img style="width: 200px; float: left" src="/static/wizard/img/operation_single.png">
         <b>Models with single operation production</b><br>
         These models use a single operation to produce an item.
         </li>
         <li style="list-style: disc; clear: both">
         <img style="width: 200px; float: left" src="/static/wizard/img/operation_routing.png">
         <b>Models with multiple steps per operation</b><br>
         The operation of an item is modeled as a sequence of step operations that are grouped
         together in a routing.
         </li>
         </ol>

         <table class="table">
         <thead>
         <tr>
         <th style="width:90px"></th>
         <th>Step</th>
         <th style="text-align: center; width:250px">Screenshot</th>
         </tr>
         </thead>
         <tbody>
         <tr>
         <td style="text-align: center">1<br>{label_data}</td>
         <td>
           <p><b><a href="{prefix}/data/input/operation/" class="text-decoration-underline" target="_blank">Load operation data</a></b>
             &nbsp;&nbsp;
             <a href="{docroot}/modeling-wizard/manufacturing-bom/operations.html" target="_blank">
             <i class="fa fa-book fa-2x" aria-hidden="true" data-bs-toggle="tooltip" title="Documentation"></i>
             </a>
             &nbsp;&nbsp;
             <a href="/static/wizard/sample_data/operation.xlsx">
             <i class="fa fa-file-excel-o fa-2x" aria-hidden="true" data-bs-toggle="tooltip" title="Sample data in Excel format"></i>
             </a>
           </p>
           <p>Defines the operations and their duration.</p>
           <p>An operation of type "routing" defines the producion routings. Extra records
           defines the step operations and their duration.</p>
           </td>
           <td style="text-align: center">
           <a href="#" onclick="showModalImage(event, 'Load operations')"><img src="/static/wizard/img/operation.png" style="width: 200px"></a>
           </td>
           </tr>
         <tr>
         <td style="text-align: center">2<br>{label_data}</td>
         <td>
           <p><b><a href="{prefix}/data/input/operationmaterial/" class="text-decoration-underline" target="_blank">Load operation material data</a></b>
             &nbsp;&nbsp;
             <a href="{docroot}/modeling-wizard/manufacturing-bom/operation-materials.html" target="_blank">
             <i class="fa fa-book fa-2x" aria-hidden="true" data-bs-toggle="tooltip" title="Documentation"></i>
             </a>
             &nbsp;&nbsp;
             <a href="/static/wizard/sample_data/operationmaterial.xlsx">
             <i class="fa fa-file-excel-o fa-2x" aria-hidden="true" data-bs-toggle="tooltip" title="Sample data in Excel format"></i>
             </a>
           </p>
           <p>Defines the materials produced and consumed by the operations.</p>
           </td><td style="text-align: center">
           <a href="#" onclick="showModalImage(event, 'Load operation materials')"><img src="/static/wizard/img/operationmaterial.png" style="width: 200px"></a>
           </td></tr>
         </tbody></table>
         """.format(
                    **context
                ),
            }
        )
        index += 1
        if not locked:
            locked = not done

        # Production - item supplier
        if not locked:
            done = ItemSupplier.objects.all().using(request.database).exists()
        steps.append(
            {
                "index": index,
                "title": "Step %s: Define suppliers and lead time for procured items"
                % index,
                "icon": ICON_LOCK if locked else ICON_DONE if done else ICON_AVAILABLE,
                "locked": locked,
                "content": """
         <p>In this step you define all suppliers and the lead times for purchasing items from them.</p>

         <table class="table">
         <thead>
         <tr>
         <th style="width:90px"></th>
         <th>Step</th>
         <th style="text-align: center; width:250px">Screenshot</th>
         </tr>
         </thead>
         <tbody>
         <tr>
         <td style="text-align: center">1<br>{label_data}</td>
         <td>
           <p><b><a href="{prefix}/data/input/supplier/" class="text-decoration-underline" target="_blank">Load supplier data</a></b>
             &nbsp;&nbsp;
             <a href="{docroot}/modeling-wizard/purchasing/suppliers.html" target="_blank">
             <i class="fa fa-book fa-2x" aria-hidden="true" data-bs-toggle="tooltip" title="Documentation"></i>
             </a>
             &nbsp;&nbsp;
             <a href="/static/wizard/sample_data/supplier.mfg.xlsx">
             <i class="fa fa-file-excel-o fa-2x" aria-hidden="true" data-bs-toggle="tooltip" title="Sample data in Excel format"></i>
             </a>
           </p>
           <p>Load all the suppliers from which you can purchase items.</p>
           </td>
           <td style="text-align: center">
           <a href="#" onclick="showModalImage(event, 'Load suppliers')"><img src="/static/wizard/img/supplier.png" style="width: 200px"></a>
           </td></tr>
           <tr>
           <td style="text-align: center">2<br>{label_data}</td>
           <td>
           <p><b><a href="{prefix}/data/input/itemsupplier/" class="text-decoration-underline" target="_blank">Load item supplier data</a></b>
             &nbsp;&nbsp;
             <a href="{docroot}/modeling-wizard/purchasing/item-suppliers.html" target="_blank">
             <i class="fa fa-book fa-2x" aria-hidden="true" data-bs-toggle="tooltip" title="Documentation"></i>
             </a>
             &nbsp;&nbsp;
             <a href="/static/wizard/sample_data/itemsupplier.mfg.xlsx">
             <i class="fa fa-file-excel-o fa-2x" aria-hidden="true" data-bs-toggle="tooltip" title="Sample data in Excel format"></i>
             </a>
           </p>
           <p>In this table you define which item can be purchased from which supplier.</p>
           </td>
           <td style="text-align: center">
           <a href="#" onclick="showModalImage(event, 'Load item suppliers')"><img src="/static/wizard/img/itemsupplier.png" style="width: 200px"></a>
           </td></tr>
         </tbody></table>
         """.format(
                    **context
                ),
            }
        )
        index += 1
        if not locked:
            locked = not done

        # Production - review the network
        if not locked:
            done = (
                Operation.objects.all().using(request.database).exists()
                or ItemSupplier.objects.all().using(request.database).exists()
            )
        steps.append(
            {
                "index": index,
                "title": "Step %s: Review the supply network" % index,
                "icon": ICON_LOCK if locked else ICON_DONE if done else ICON_AVAILABLE,
                "locked": locked,
                "content": """
         <p>All right, it's time to for a first checkpoint. We'll verify the supply chain structure
         you have modeled in the previous steps.</p>
         <table class="table">
         <thead>
         <tr>
         <th style="width:90px"></th>
         <th>Step</th>
         <th style="text-align: center; width:250px">Screenshot</th>
         </tr>
         </thead>
         <tbody>
         <tr>
         <td style="text-align: center">1<br>{label_check}</td>
         <td><p><b>Review the supply path of some sales orders</b></p>
         <p>Go to the <a href="{prefix}/data/input/demand/" class="text-decoration-underline" target="_blank">sales order list</a>
         and click the triangle icon <span class="circle">A</span> to investigate some example sales orders.</p>
         <p>Select the "supply path" tab <span class="circle">B</span>, and study the graph.</p>
         <p>On the far right you find the end items, and moving towards the left we move to operations
         deeper in the bill of material. On the far left we find the raw materials
         and their purchasing operations.</p>
         <p>If the path is complete and correct, congratulations! You have successfully
         understood and implemented the previous steps.</p>
         <p>If your paths are broken or contain cycles, you will need to review and correct the operations
         to get the supply path correct.</p>
         </td>
         <td style="text-align: center">
         <a href="#" onclick="showModalImage(event, 'Sales order drilldown')"><img src="/static/wizard/img/salesorder_drilldown.png" style="width: 200px"></a>
         <br><br>
         <a href="#" onclick="showModalImage(event, 'Sales order supply path')"><img src="/static/wizard/img/supplypath_mfg.png" style="width: 200px"></a>
         </td>
         </tr>
         </tbody></table>
         """.format(
                    **context
                ),
            }
        )
        index += 1

        # Production - generate unconstrained plan
        parameter_populateForecastTable = Parameter.getValue(
            "forecast.populateForecastTable", request.database, "true"
        )
        steps.append(
            {
                "index": index,
                "title": "Step %s: Generate and review the unconstrained MRP-plan"
                % index,
                "icon": ICON_LOCK if locked else ICON_DONE if done else ICON_AVAILABLE,
                "locked": locked,
                "content": """
         <p>We'll generate a first unconstrained plan and review the list of proposed manufacturing orders and
         purchase orders.</p>
         <table class="table">
         <thead>
         <tr>
         <th style="width:90px"></th>
         <th>Step</th>
         <th style="text-align: center; width:250px">Screenshot</th>
         </tr>
         </thead>
         <tbody>

         <tr><td style="text-align: center">1<br>{label_config}</td>
         <td><p><b><a href="{prefix}/data/common/parameter/?name=forecast.populateForecastTable" class="text-decoration-underline" target="_blank">Enable or disable the use of forecast</a></b>:</p>
         <div class="form-check ps-5">
           <input class="form-check-input" id="fcst_auto" type="radio" name="fcstbckt" data-parameter="forecast.populateForecastTable" data-parameter-value="true"
           """.format(
                    **context
                )
                + (
                    ' checked="checked"'
                    if parameter_populateForecastTable.lower() == "true"
                    else ""
                )
                + """>
           <label class="form-check-label" for="fcst_auto">Automatically populate the <a href="{prefix}/data/forecast/forecast/" class="text-decoration-underline" target="_blank">forecast table</a>.<br>
           Use this option if you want to plan forecast.
           </label>
         </div>
         <div class="form-check ps-5">
           <input class="form-check-input" type="radio" id="fcst_man" name="fcstbckt" data-parameter="forecast.populateForecastTable" data-parameter-value="false"
           """.format(
                    **context
                )
                + (
                    ' checked="checked"'
                    if parameter_populateForecastTable.lower() != "true"
                    else ""
                )
                + """>
           <label class="form-check-label" for="fcst_man">Do NOT populate the <a href="{prefix}/data/forecast/forecast/" class="text-decoration-underline" target="_blank">forecast table</a> automatically.<br>
           Use this option if you do NOT want to plan forecast.
           </label>
         </div>
         <p>You can always update your choice later with the parameter "forecast.populateForecastTable"
         in the <a href="{prefix}/data/common/parameter/" class="text-decoration-underline" target="_blank">parameter table</a> (available in the "admin" menu).</p>
         </td>
         <td></td>
         </tr>

         <tr>
         <td style="text-align: center">2<br>{label_action}</td>
         <td><p><b><a href="{prefix}/execute/" class="text-decoration-underline" target="_blank">Generate an unconstrained plan</a></b></p>
         <p>You can now compute the first plan.</p>
         <p>Open the <a href="{prefix}/execute/">execution screen</a> (available in the "admin" menu) and select
         the "generate plan" task. Make sure the "generate supply plan" option <span class="circle">A</span>
         is checked, and make sure to generate an unconstrained plan <span class="circle">B</span>.<p>
         <p><span class="circle">C</span> Launch the task and wait for it to complete. <span class="circle">D</span></p>
         <p><b>Whenever you change any of the input data, you will need to come back to this screen to recompute the plan.</b></p>
         </td>
         <td>
         <a href="#" onclick="showModalImage(event, 'Generate unconstrained plan')"><img src="/static/wizard/img/generate_unconstrained.png" style="width: 200px"></a>
         </td>
         </tr>

         <tr>
         <td style="text-align: center">3<br>{label_analysis}</td>
         <td>
         <p><b><a href="{prefix}/data/input/manufacturingorder/" class="text-decoration-underline" target="_blank">Load Manufacturing order data</a></b></p>
         <p>The <a href="{prefix}/data/input/manufacturingorder/" class="text-decoration-underline" target="_blank">manufacturing order</a> screen
         (available in the "Manufacturing" menu) gives an overview of all manufacturing orders.
         The plan generated in the previous step created a set of proposed manufacturing
         orders to deliver your sales orders.</p>
         <p>If the list is empty, it is very likely you made a mistake in any of the
         previous steps. You should review the supply path of the sales orders again.</p>
         <p>If the list isn't empty, you can review that the timing, duration and quantity
         of the proposed manufacturing orders is matching your expectations. The result will
         match a textbook <a href="https://en.wikipedia.org/wiki/Material_requirements_planning" class="text-decoration-underline" target="_blank">MRP explosion</a>.</p>
         </td>
         <td>
         <a href="#" onclick="showModalImage(event, 'Manufacturing orders')"><img src="/static/wizard/img/manufacturingorder.png" style="width: 200px"></a><br>
         </td>
         </tr>

         <tr>
         <td style="text-align: center">4<br>{label_analysis}</td>
         <td>
         <p><b><a href="{prefix}/data/input/purchaseorder/" class="text-decoration-underline" target="_blank">Load purchase order data</a></b></p>
         <p>The purchase order report (available in the "purchasing" menu) gives an overview of all
         purchase orders. The plan generated in the previous step created a set of
         proposed purchase orders to meet your sales orders.</p>
         <p>If the list is empty, it is very likely you made a mistake in any of the
         previous steps. You should review the supply path of the sales orders again.</p>
         <p>If the list isn't empty, you can review that the timing, duration and quantity
         of the proposed purchase orders is matching your expectations. The result will
         match a classic textbook <a href="https://en.wikipedia.org/wiki/Material_requirements_planning" class="text-decoration-underline" target="_blank">MRP explosion</a>.</p>
         </td>
         <td>
         <a href="#" onclick="showModalImage(event, 'Purchase orders')"><img src="/static/wizard/img/purchaseorder.png" style="width: 200px"></a><br>
         </td>
         </tr>
         </tbody>
         </table>
         """.format(
                    **context
                ),
            }
        )
        index += 1
        if not locked:
            locked = not done

        # Production - load inventories, open PO and open MO
        if not locked:
            done = (
                Buffer.objects.all().using(request.database).exists()
                or PurchaseOrder.objects.all()
                .using(request.database)
                .filter(status="confirmed")
                .exists()
                or ManufacturingOrder.objects.all()
                .using(request.database)
                .filter(status="confirmed")
                .exists()
            )
        steps.append(
            {
                "index": index,
                "title": "Step %s: Load inventories, open purchase orders and work-in-progress manufacturing orders"
                % index,
                "icon": ICON_LOCK if locked else ICON_DONE if done else ICON_AVAILABLE,
                "locked": locked,
                "content": """
         <p>The plan in of the previous steps started with an empty factory and empty inventories.
         A correct plan obviously needs to consider the current stock and all purchase orders and
         manufacturing orders that are already ongoing or confirmed to start.</p>
         <table class="table">
         <thead>
         <tr>
         <th style="width:90px"></th>
         <th>Step</th>
         <th style="text-align: center; width:250px">Screenshot</th>
         </tr>
         </thead>
         <tbody>
         <tr>
         <td style="text-align: center">1<br>{label_data}</td>
         <td>
           <p><b><a href="{prefix}/data/input/buffer/" class="text-decoration-underline" target="_blank">Load inventory data</a></b>
             &nbsp;&nbsp;
             <a href="{docroot}/modeling-wizard/master-data/buffers.html" target="_blank">
             <i class="fa fa-book fa-2x" aria-hidden="true" data-bs-toggle="tooltip" title="Documentation"></i>
             </a>
             &nbsp;&nbsp;
             <a href="/static/wizard/sample_data/buffer.mfg.xlsx">
             <i class="fa fa-file-excel-o fa-2x" aria-hidden="true" data-bs-toggle="tooltip" title="Sample data in Excel format"></i>
             </a>
           </p>
           <p>Load the current stock of all items. If the stock is 0, no record is required.</p>
           </td>
           <td style="text-align: center">
           <a href="#" onclick="showModalImage(event, 'Load on hand inventory')"><img src="/static/wizard/img/buffer.png" style="width: 200px"></a>
           </td></tr>
         <tr>
         <td style="text-align: center">2<br>{label_data}</td>
         <td>
           <p><b><a href="{prefix}/data/input/purchaseorder/" class="text-decoration-underline" target="_blank">Load purchase order data</a></b>
             &nbsp;&nbsp;
             <a href="{docroot}/modeling-wizard/purchasing/purchase-orders.html" target="_blank">
             <i class="fa fa-book fa-2x" aria-hidden="true" data-bs-toggle="tooltip" title="Documentation"></i>
             </a>
             &nbsp;&nbsp;
             <a href="/static/wizard/sample_data/purchaseorder.mfg.xlsx">
             <i class="fa fa-file-excel-o fa-2x" aria-hidden="true" data-bs-toggle="tooltip" title="Sample data in Excel format"></i>
             </a>
           </p>
           <p>Load all purchase orders that you have already opened with suppliers.<br>
           The status field of the records should be "confirmed" to seperate them from the
           proposed purchase orders that were generated in the previous step.</p>
           <p>This table is thus used both as input and output.</p>
           </td>
           <td style="text-align: center">
           <a href="#" onclick="showModalImage(event, 'Load purchase order data')"><img src="/static/wizard/img/purchaseorder.png" style="width: 200px"></a>
           </td></tr>
         <tr>
         <td style="text-align: center">3<br>{label_data}</td>
         <td>
           <p><b><a href="{prefix}/data/input/manufacturingorder/" class="text-decoration-underline" target="_blank">Load manufacturing order data</a></b>
             &nbsp;&nbsp;
             <a href="{docroot}/modeling-wizard/manufacturing-bom/manufacturing-orders.html" target="_blank">
             <i class="fa fa-book fa-2x" aria-hidden="true" data-bs-toggle="tooltip" title="Documentation"></i>
             </a>
             &nbsp;&nbsp;
             <a href="/static/wizard/sample_data/manufacturingorder.xlsx">
             <i class="fa fa-file-excel-o fa-2x" aria-hidden="true" data-bs-toggle="tooltip" title="Sample data in Excel format"></i>
             </a>
           </p>
           <p>Load all manufacturing orders already released to the shop floor as work-in-progress.<br>
           The status field of the records should be "confirmed" to seperate them from the
           proposed manufacturing orders that were generated in the previous step.</p>
           <p>This table is thus used both as input and output.</p>
           </td>
           <td style="text-align: center">
           <a href="#" onclick="showModalImage(event, 'Load manufacturing order data')"><img src="/static/wizard/img/manufacturingorder.png" style="width: 200px"></a>
           </td></tr>
         </tbody></table>
         """.format(
                    **context
                ),
            }
        )
        index += 1

        # Production - resources
        if not locked:
            done = OperationResource.objects.all().using(request.database).exists()
        steps.append(
            {
                "index": index,
                "title": "Step %s: Define resources and capacity consumption" % index,
                "icon": ICON_LOCK if locked else ICON_DONE if done else ICON_AVAILABLE,
                "locked": locked,
                "content": """
         <p>Let's add some capacity constraints.</p>
         <p>FrePPLe has different resource types (see
         <a class="text-decoration-underline" href="{docroot}/examples/resource/resource-type.html" target="_blank">here</a>
         for more detail). The most common types are:</p>
         <ul>
         <li style="list-style: disc">
         <p><img style="width: 200px; float: left" src="/static/wizard/img/resource-default.png">
         <b>"default"</b>: for a resource with a continuous representation of capacity.<br>
         This resource model is typically used for short-term detailed planning and scheduling.</p>
         </li>
         <li style="list-style: disc; clear: both">
         <p><img style="width: 200px; float: left" src="/static/wizard/img/resource-time-buckets.png">
         <b>"bucket_week" / "bucket_month"</b>: for a resource with capacity is expressed
         as available resource-hours per time bucket.<br>
         This resource model is typically used for mid-term master planning and rough cut
         capacity planning.</p>
         </li>
         </ul>
         <table class="table">
         <thead>
         <tr>
         <th style="width:90px"></th>
         <th>Step</th>
         <th style="text-align: center; width:250px">Screenshot</th>
         </tr>
         </thead>
         <tbody>
         <tr>
         <td style="text-align: center">1<br>{label_data}</td>
         <td>
           <p><b><a href="{prefix}/data/input/resource/" class="text-decoration-underline" target="_blank">Load resource data</a></b>
             &nbsp;&nbsp;
             <a href="{docroot}/modeling-wizard/manufacturing-capacity/resources.html" target="_blank">
             <i class="fa fa-book fa-2x" aria-hidden="true" data-bs-toggle="tooltip" title="Documentation"></i>
             </a>
             &nbsp;&nbsp;
             <a href="/static/wizard/sample_data/resource.xlsx">
             <i class="fa fa-file-excel-o fa-2x" aria-hidden="true" data-bs-toggle="tooltip" title="Sample data in Excel format"></i>
             </a>
           </p>
           <p>Load all resources.<br>
           A resource models a machine, a group of machines, an operator, a group of operators,
           or other capacity constraints.</p>
           </td>
           <td style="text-align: center">
           <a href="#" onclick="showModalImage(event, 'Load resource data')"><img src="/static/wizard/img/resource.png" style="width: 200px"></a>
           </td></tr>
         <tr>
         <td style="text-align: center">2<br>{label_data}</td>
         <td>
           <p><b><a href="{prefix}/data/input/operationresource/" class="text-decoration-underline" target="_blank">Load operation resource data</a></b>
             <a href="{docroot}/modeling-wizard/manufacturing-capacity/operation-resources.html" target="_blank">
             <i class="fa fa-book fa-2x" aria-hidden="true" data-bs-toggle="tooltip" title="Documentation"></i>
             </a>
             <a href="/static/wizard/sample_data/operationresource.xlsx">
             <i class="fa fa-file-excel-o fa-2x" aria-hidden="true" data-bs-toggle="tooltip" title="Sample data in Excel format"></i>
             </a>
           </p>
           <p>This table associates each operation with the resources it utilizes.</p>
           </td>
           <td style="text-align: center">
           <a href="#" onclick="showModalImage(event, 'Load operation resource data')"><img src="/static/wizard/img/operationresource.png" style="width: 200px"></a>
           </td></tr>
         </tbody></table>
         """.format(
                    **context
                ),
            }
        )
        index += 1
        if not locked:
            locked = not done

        # Production - generate plan
        if not locked:
            done = (
                PurchaseOrder.objects.all()
                .using(request.database)
                .filter(status="proposed")
                .exists()
                or ManufacturingOrder.objects.all()
                .using(request.database)
                .filter(status="proposed")
                .exists()
            )
        steps.append(
            {
                "index": index,
                "title": "Step %s: Generate a constrained plan" % index,
                "icon": ICON_LOCK if locked else ICON_DONE if done else ICON_AVAILABLE,
                "locked": locked,
                "content": """
         <p>You can now generate a more realistic plan.</p>
         <p>The unconstrained plan you generated earlier doesn't respect constraints: it will
         plan in the past and overload resources. It does plan all the demands on time.</p>
         <p>The constrained plan generated in this step will respect all the capacity, material
         availability, and procurement lead times. In case of lead time or capacity shortages,
         demands will be planned late.</p>
         <table class="table">
         <thead>
         <tr>
         <th style="width:90px"></th>
         <th>Step</th>
         <th style="text-align: center; width:250px">Screenshot</th>
         </tr>
         </thead>
         <tbody>
         <tr>
         <td style="text-align: center">1<br>{label_action}</td>
         <td>
         <p><b><a href="{prefix}/execute/" class="text-decoration-underline" target="_blank">Generate constrained plan</a></b></p>
         <p>Navigate to the <a href="{prefix}/execute/" class="text-decoration-underline">execution screen</a> (available in the "admin"
         menu) and select the "generate plan" task <span class="circle">A</span>. Make sure the options "generate supply
         plan" and "constrained plan" <span class="circle">B</span> are both checked.</p>
         <p><span class="circle">C</span> Launch the task and wait for it to complete. <span class="circle">D</span></p>
         <p><b>Whenever you change any of the input data, you will need to come back here to regenerate the plan.</b></p>
         </td>
         <td style="text-align: center">
         <a href="#" onclick="showModalImage(event, 'Generate constrained plan')"><img src="/static/wizard/img/generate_constrained.png" style="width: 200px"></a>
         </td></tr>
         </tbody></table>
         """.format(
                    **context
                ),
            }
        )
        index += 1

        # Production - review results
        steps.append(
            {
                "index": index,
                "title": "Step %s: Review results" % index,
                "icon": ICON_LOCK if locked else None,
                "locked": locked,
                "content": """
         <p>A number of new screens are ready to be explored now!</p>
         <table class="table">
         <thead>
         <tr>
         <th style="width:90px"></th>
         <th>Step</th>
         <th style="text-align: center; width:250px">Screenshot</th>
         </tr>
         </thead>
         <tbody>
         <tr>
         <td style="text-align: center">1<br>{label_analysis}</td>
         <td>
         <p><b><a href="{prefix}/resource/" class="text-decoration-underline" target="_blank">Capacity report</a></b></p>
         <p>This report visualizes the utilization of all resources per time bucket.</p>
         <p><span class="circle">A</span> The results can be displayed as a graph or as a table. You can click on
         cells in the table or buckets in the graph to get more detailed information.</p>
         <p><span class="circle">B</span> You can adjust the time buckets and horizon of the report.</p>
         <p><span class="circle">C</span> The down arrow icon allows to export the results in an
         Excel spreadsheet.</p>
         <p><span class="circle">D</span> In all reports you can customize which fields to display and
         their order.</p>
         <td style="text-align: center">
         <a href="#" onclick="showModalImage(event, 'Capacity report')"><img src="/static/wizard/img/resourcereport.png" style="width: 200px"></a>
         </td></tr>
         <tr>
         <td style="text-align: center">2<br>{label_analysis}</td>
         <td><p><b><a href="{prefix}/data/input/demand/" class="text-decoration-underline" target="_blank">Sales order</a></b></p>
         <p>At the start of the planning run, you loaded the sales orders in frePPLe. The constrained
         planning run you have just completed has 1) computed the planned delivery date for all sales
         orders and 2) collected the reasons why a certain demand was planned short or late.</p>
         <p><span class="circle">A</span> Review the list of
         <a href="{prefix}/data/input/demand/" class="text-decoration-underline" target="_blank">sales orders</a> and
         sort on the delay field to find some sales orders that can't be delivered on time.<p>
         <p><span class="circle">B</span> Click on the triangle icon next to a demand to drill into its details.<p>
         <p><span class="circle">C</span> The "plan" tab shows all operations planned to deliver the order.<p>
         <p><span class="circle">D</span> The "why short or late" tab shows all constraints causing lateness
         in the delivery of the order.</p>
         </td>
         <td style="text-align: center">
         <a href="#" onclick="showModalImage(event, 'Sales order drilldown')"><img src="/static/wizard/img/salesorder_analysis.png" style="width: 200px"></a>
         <br><br>
         <a href="#" onclick="showModalImage(event, 'Gantt plan editor')"><img src="/static/wizard/img/salesorder_why_short_or_late.png" style="width: 200px"></a>
         </td></tr>
         <tr>
         <td style="text-align: center">3<br>{label_analysis}</td>
         <td>
         <p><b><a href="{prefix}/buffer/" class="text-decoration-underline" target="_blank">Inventory report</a></b></p>
         <p>This report visualizes the planned inventory for all item-locations per time bucket.</p>
         </td>
         <td style="text-align: center">
         <a href="#" onclick="showModalImage(event, 'Inventory report')"><img src="/static/wizard/img/inventoryreport.png" style="width: 200px"></a>
         </td></tr>
         </tbody>
         </table>
         <p>Congratulations! You are now able to use the production planning capabilities of frePPLe.</p>
         """.format(
                    **context
                ),
            }
        )
        index += 1

        # Production - advanced features
        steps.append(
            {
                "index": index,
                "title": "Bonus: Advanced production planning functionality",
                "icon": ICON_LOCK if locked else None,
                "locked": locked,
                "content": """
         <p>With the basics under your belt, you are ready to dig into some more advanced
         modeling and configuration topics.</p>
         <table class="table">
         <thead>
         <tr>
         <th>Topic</th>
         <th>Description</th>
         </tr>
         </thead>
         <tbody>
         <tr>
         <td><a href="{docroot}/modeling-wizard/common-modeling-mistakes.html" class="text-decoration-underline" target="_blank">Common mistakes</a></td>
         <td>Learn about the most common gotchas and mistakes made by first-time users.</td>
         </tr>
         <tr>
         <td><a href="{docroot}/examples/calendar/calendar-working-hours.html" class="text-decoration-underline" target="_blank">Working&nbsp;hours</a></td>
         <td>Modeling working hours, shifts and holidays is required to get a realistic plan.</td>
         </tr>
         <tr>
         <td><a href="{docroot}/examples/operation/operation-type.html" class="text-decoration-underline" target="_blank">Operation&nbsp;types</a></td>
         <td>This example model demonstrates the different operation types.</td>
         </tr>
         <tr>
         <td><a href="{docroot}/examples/resource/resource-type.html" class="text-decoration-underline" target="_blank">Resource&nbsp;types</a></td>
         <td>This example model demonstrates the different resource types.</td>
         </tr>
         <tr>
         <td><a href="{docroot}/examples/resource/resource-skills.html" class="text-decoration-underline" target="_blank">Resource&nbsp;skills</a></td>
         <td>Resources can be assigned skills, which represent certain qualifications.<br>
         You can specify a required skill for an operation.</td>
         </tr>
         <tr>
         <td><a href={docroot}/examples/resource/resource-setup-matrices.html" class="text-decoration-underline" target="_blank">Setup&nbsp;matrices</a></td>
         <td>Resources can require a setup time to change the configuration between different setups/configurations.
         This models the time required for cleaning, installation of new tooling, re-calibration, feeding new
         raw materials, etc.</td>
         </tr>
         <tr>
         <td><a href="{docroot}/examples/demand/demand-priorities.html" class="text-decoration-underline" target="_blank">Demand&nbsp;priorities</a></td>
         <td>Demand priorities give you control over the allocation of constrained supply.
         Top priority orders will be the first to get the required material and capacity.
         Less prioritized orders are planned with the remaining availability and have
         a higher chance of being planned late or short.</td>
         </tr>
         <tr>
         <td><a href="{docroot}/examples/demand/demand-policies.html" class="text-decoration-underline" target="_blank">Demand&nbsp;policies</a></td>
         <td>This model describes how to model demand policies like "ship all in full", "allow
         partial deliveries", "don't plan late shipments", etc.</td>
         </tr>
         <tr>
         <td><a href="{docroot}/examples/operation/operation-autofence.html" class="text-decoration-underline" target="_blank">Release&nbsp;fence</a></td>
         <td>A release fence can be set to specify a frozen zone in the planning horizon in which
         the planning algorithm cannot propose any new manufacturing orders, purchase orders or distribution
         orders. The fence represents a period during which the plan is already being executed and can no
         longer be changed.</td>
         </tr>
         <tr>
         <td><a href="{docroot}/examples/buffer/transfer-batch.html" class="text-decoration-underline" target="_blank">Transfer&nbsp;batching</a></td>
         <td>Transfer batching refers to operations that are planned with some overlap. The subsequent
         operation can already start when the previous one hasn't completely finished yet.</td>
         </tr>
         <tr>
         <td><a href="{docroot}/examples/buffer/alternate-materials.html" class="text-decoration-underline" target="_blank">Alternate&nbsp;materials</a></td>
         <td>In many industries the bill of materials can contain alternate materials: the same product
         can be produced using different components.</td>
         </tr>
         </tbody>
         </table>
         """.format(
                    **context
                ),
            }
        )
        index += 1

    # Feedback step
    if index > 2:
        steps.append(
            {
                "index": index,
                "title": "Give us feedback",
                "icon": None,
                "content": """
          <table style="width:100%">
            <tr>
              <td style="width:50px">
                <span id="happy" class="fa fa-smile-o" style="font-size: 40px; color: green"></span>
              </td>
              <td rowspan="3">
              <textarea id='textarea' class="form-control" style="width: 100%" rows=10
                placeholder="We're eager to hear how well you found your way around.

Choose a smiley and share your comments to help us improve frePPLe!"></textarea>
            </td>
          </tr>
          <tr>
            <td style="width:50px">
            <span id="average" class="fa fa-meh-o" style="font-size: 40px; color: #DCDCDC"></span>
            </td>
          </tr>
          <tr>
            <td style="width:50px">
            <span id="nothappy" class="fa fa-frown-o" style="font-size: 40px; color: #DCDCDC"></span>
            </td>
          </tr>
          <tr>
          <td></td>
          <td>
          <div class="pt-1">
          <button class="btn btn-primary" disabled id='submit'>Send us feedback</button>
          </div>
          </td>
          </tr>
        </table>
      """.format(
                    **context
                ),
            }
        )
        script += (
            '''
       var $textarea = $('#textarea');
       var $submit = $('#submit');
       var $happy = $('#happy');
       var $average = $('#average');
       var $nothappy = $('#nothappy');

       // Set the onkeyup events
       $textarea.on('keyup', function() {
         $submit.prop('disabled', $.trim($textarea.val()) === '');
       });

       // Set default value of smiley to happy (let's be optimistic)
       $happy.click( function() {
         $happy.css("color", "green");
         $average.css("color", "#DCDCDC");
         $nothappy.css("color", "#DCDCDC");
         });
       $average.click( function() {
         $happy.css("color", "#DCDCDC");
         $average.css("color", "orange");
         $nothappy.css("color", "#DCDCDC");
         });
       $nothappy.click( function() {
         $happy.css("color", "#DCDCDC");
         $average.css("color", "#DCDCDC");
         $nothappy.css("color", "red");
         });

       $('#submit').click(function(e) {
           $.ajax({
               type: "POST",
               url: '/wizard/sendsurveymail/',
               data: {
                 'feeling': $happy.css("color") == "rgb(0, 128, 0)" ? "Happy" : ($nothappy.css("color") == "rgb(255, 0, 0)" ? "Not happy" : "Average"),
                 'comments': $textarea.val()
                 },
               success: function() {
                 $textarea.val("Thank you for your comments!");
                 $submit.prop('disabled', true);
                 },
               error: function() {
                 $textarea.val(
                   $textarea.val()
                   + "\\n\\nOuch, our server couldn't send an email. Please email your feedback to info@frepple.com"
                   );
                 }
           });
       });

       $("input[data-parameter]").on('change', function(event) {
         var val = $(this).attr("data-parameter-value");
         if (typeof val === typeof undefined || val === false)
           val = $(this).val();
         $.ajax({
           type: 'POST',
           url: "'''
            + request.prefix
            + """/api/common/parameter/",
           data: {
             name: $(this).attr("data-parameter"),
             value: val
             }
           });
       });
       """
        )
        index += 1

    if steps:
        return {"steps": steps, "script": script, "mode": mode}
    else:
        return None


@staff_member_required
def WizardLoad(request, mode=None):
    db = request.database
    steps = getWizardSteps(request, mode)
    with_fcst_module = "freppledb.forecast" in settings.INSTALLED_APPS
    with_ip_module = "freppledb.inventoryplanning" in settings.INSTALLED_APPS
    if mode == "forecast" and with_fcst_module:
        title = _("Data loading wizard for forecasting")
    elif mode == "inventory" and with_ip_module:
        title = _("Data loading wizard for inventory planning")
    elif mode == "production":
        title = _("Data loading wizard for production planning")
    elif not mode:
        title = _("Get started - Data loading wizard")
    else:
        return HttpResponseServerError("Invalid wizard mode")
    context = {
        "prefix": "/" + request.prefix,
        "mode": mode,
        "wizard": steps,
        "with_fcst_module": with_fcst_module,
        "with_inventory_module": with_ip_module,
        "currentstep": int(request.GET.get("currentstep", 0)),
        "title": title,
        "bucketnames": Bucket.objects.order_by("-level").values_list("name", flat=True),
        "currency": getCurrency(),
    }
    if steps:
        context.update(
            {
                "noItem": not Item.objects.using(db).exists(),
                "noLocation": not Location.objects.using(db).exists(),
                "noCustomer": not Customer.objects.using(db).exists(),
                "noDemand": not Demand.objects.using(db).exists(),
                "noSupplier": not Supplier.objects.using(db).exists(),
                "noItemSupplier": not ItemSupplier.objects.using(db).exists(),
                "noItemDistribution": not ItemDistribution.objects.using(db).exists(),
                "noOperation": not Operation.objects.using(db).exists(),
                "noBuffer": not Buffer.objects.using(db).exists(),
                "noMO": not ManufacturingOrder.objects.using(db).exists(),
                "noMOproposed": not ManufacturingOrder.objects.filter(status="proposed")
                .using(db)
                .exists(),
                "noDO": not DistributionOrder.objects.using(db).exists(),
                "noPO": not PurchaseOrder.objects.using(db).exists(),
                "noResource": not Resource.objects.using(db).exists(),
                "noOperationMaterial": not OperationMaterial.objects.using(db).exists(),
                "noOperationResource": not OperationResource.objects.using(db).exists(),
            }
        )
        if with_fcst_module:
            context.update(
                {"noForecastPlan": not ForecastPlan.objects.using(db).exists()}
            )
    return render(request, "wizard/load.html", context=context)


class SendSurveyMail:
    @staticmethod
    @staff_member_required
    def action(request):
        # Dispatch to the correct method
        try:
            if request.method == "POST":
                sendEmail(
                    to="devops@frepple.com",
                    subject="Survey received from %s : %s"
                    % (request.build_absolute_uri()[:-23], request.POST.get("feeling")),
                    body=request.POST.get("comments"),
                )
                return HttpResponse("OK")
            else:
                return HttpResponseNotAllowed(["post"])
        except Exception:
            return HttpResponseServerError(
                "An error occurred when sending your comments"
            )


@staff_member_required
def CheckSupplyPath(request):
    item = request.GET.get("item", None)
    location = request.GET.get("location", None)
    if item and location:
        with connections[request.database].cursor() as cursor:
            cursor.execute(
                """
                with requesteditem as (
                  select name, lft, rght
                  from item where name = %s
                  )
                select distinct 'po'
                from itemsupplier
                inner join item
                  on itemsupplier.item_id = item.name
                inner join requesteditem
                  on requesteditem.lft between item.lft and item.rght
                where itemsupplier.location_id = %s or itemsupplier.location_id is null
                union all
                select distinct 'do'
                from itemdistribution
                inner join item
                  on itemdistribution.item_id = item.name
                inner join requesteditem
                  on requesteditem.lft between item.lft and item.rght
                where itemdistribution.location_id = %s or itemdistribution.location_id is null
                union all
                select distinct 'mo'
                from operation
                where operation.location_id = %s and operation.item_id = %s
                """,
                (item, location, location, location, item),
            )
            response = [rec[0] for rec in cursor.fetchall()]
    else:
        response = []
    return HttpResponse(
        content=json.dumps(response),
        content_type="application/json; charset=%s" % settings.DEFAULT_CHARSET,
    )


class QuickStartProduction(View):
    @method_decorator(staff_member_required())
    def get(self, request, *args, **kwargs):
        post = request.session.get("post", False)
        if post:
            del request.session["post"]
        return render(
            request,
            "wizard/quickstart_production.html",
            context={"title": _("Quickstart production planning"), "post": post},
        )

    @method_decorator(staff_member_required())
    def post(self, request, *args, **kwargs):
        try:
            db = request.database
            data = json.loads(
                request.body.decode(request.encoding or settings.DEFAULT_CHARSET)
            )
            post = {"salesorder": data["name"], "messages": []}

            items = 0
            locations = 0
            customers = 0
            suppliers = 0
            resources = 0
            itemsuppliers = 0
            itemdistributions = 0
            demands = 0
            operations = 0
            operationmaterials = 0
            operationresources = 0

            # Create item
            item, created = Item.objects.using(db).get_or_create(name=data["item"])
            if created:
                items += 1

            # Create location
            location, created = Location.objects.using(db).get_or_create(
                name=data["location"]
            )
            if created:
                locations += 1

            # Create customer
            customer, created = Customer.objects.using(db).get_or_create(
                name=data["customer"]
            )
            if created:
                customers += 1

            # Create demand
            created = Demand.objects.using(db).get_or_create(
                name=data["name"],
                defaults={
                    "item": item,
                    "location": location,
                    "customer": customer,
                    "due": parse(data["due"]),
                    "quantity": float(data["quantity"]),
                    "status": "open",
                },
            )
            if created:
                demands += 1
            for supply in data["supply"]:
                item, created = Item.objects.using(db).get_or_create(
                    name=supply["item"]
                )
                if created:
                    items += 1
                location, created = Location.objects.using(db).get_or_create(
                    name=supply["location"]
                )
                if created:
                    locations += 1
                if supply["type"] == "PO":
                    supplier, created = Supplier.objects.using(db).get_or_create(
                        name=supply["supplier"]
                    )
                    if created:
                        suppliers += 1
                    created = ItemSupplier.objects.using(db).get_or_create(
                        supplier=supplier,
                        item=item,
                        location=location,
                        defaults={
                            "leadtime": timedelta(days=float(supply["leadtime"]))
                        },
                    )[1]
                    if created:
                        itemsuppliers += 1
                elif supply["type"] == "DO":
                    origin, created = Location.objects.using(db).get_or_create(
                        name=supply["origin"]
                    )
                    if created:
                        locations += 1
                    created = ItemDistribution.objects.using(db).get_or_create(
                        item=item,
                        location=location,
                        origin=origin,
                        defaults={
                            "leadtime": timedelta(days=float(supply["leadtime"]))
                        },
                    )[1]
                    if created:
                        itemdistributions += 1
                elif supply["type"] == "MO":
                    operation, created = Operation.objects.using(db).get_or_create(
                        name=supply["operation"],
                        defaults={
                            "item": item,
                            "location": location,
                            "duration": parseDuration(supply["duration"]),
                            "duration_per": parseDuration(supply["durationper"]),
                            "type": "time_per",
                        },
                    )
                    if created:
                        operations += 1
                    if supply.get("resource", None):
                        resource, created = Resource.objects.using(db).get_or_create(
                            name=supply["resource"]
                        )
                        if created:
                            resources += 1
                        created = OperationResource.objects.using(db).get_or_create(
                            resource=resource,
                            operation=operation,
                            defaults={"quantity": 1},
                        )
                        if created:
                            operationresources += 1
                    consumedindex = 0
                    while True:
                        key = "consumeditem-%s" % consumedindex
                        if key not in supply:
                            break
                        if supply[key]:
                            item, created = Item.objects.using(db).get_or_create(
                                name=supply[key]
                            )
                            if created:
                                items += 1
                            try:
                                qty = -float(
                                    supply["consumedquantity-%s" % consumedindex]
                                )
                            except Exception:
                                qty = -1
                            created = OperationMaterial.objects.using(db).get_or_create(
                                item=item,
                                operation=operation,
                                defaults={"quantity": qty, "type": "start"},
                            )[1]
                            if created:
                                operationmaterials += 1
                        consumedindex += 1

            # Compile the messages
            if items > 0:
                post["messages"].append(
                    "Created %s new <a target='_blank' class='text-decoration-underline' href='%s/data/input/item/?noautofilter&sidx=lastmodified&amp;sord=desc'>item</a>"
                    % (items, request.prefix)
                )
            if locations > 0:
                post["messages"].append(
                    "Created %s new <a target='_blank' class='text-decoration-underline' href='%s/data/input/location/?noautofilter&sidx=lastmodified&amp;sord=desc'>location</a>"
                    % (locations, request.prefix)
                )
            if customers > 0:
                post["messages"].append(
                    "Created %d new <a target='_blank' class='text-decoration-underline' href='%s/data/input/customer/?noautofilter&sidx=lastmodified&amp;sord=desc'>customer</a>"
                    % (customers, request.prefix)
                )
            if demands > 0:
                post["messages"].append(
                    "Created %d new <a target='_blank' class='text-decoration-underline' href='%s/data/input/demand/?noautofilter&sidx=lastmodified&amp;sord=desc'>sales order</a>"
                    % (demands, request.prefix)
                )
            if suppliers > 0:
                post["messages"].append(
                    "Created %d new <a target='_blank' class='text-decoration-underline' href='%s/data/input/supplier/?noautofilter&sidx=lastmodified&amp;sord=desc'>supplier</a>"
                    % (suppliers, request.prefix)
                )
            if itemsuppliers > 0:
                post["messages"].append(
                    "Created %d new <a target='_blank' class='text-decoration-underline' href='%s/data/input/itemsupplier/?noautofilter&sidx=lastmodified&amp;sord=desc'>item supplier</a>"
                    % (itemsuppliers, request.prefix)
                )
            if itemdistributions > 0:
                post["messages"].append(
                    "Created %d new <a target='_blank' class='text-decoration-underline' href='%s/data/input/itemdistribution/?noautofilter&sidx=lastmodified&amp;sord=desc'>item distribution</a>"
                    % (itemdistributions, request.prefix)
                )
            if resources > 0:
                post["messages"].append(
                    "Created %d new <a target='_blank' class='text-decoration-underline' href='%s/data/input/resource/?noautofilter&sidx=lastmodified&amp;sord=desc'>resource</a>"
                    % (resources, request.prefix)
                )
            if operations > 0:
                post["messages"].append(
                    "Created %d new <a target='_blank' class='text-decoration-underline' href='%s/data/input/operation/?noautofilter&sidx=lastmodified&amp;sord=desc'>operation</a>"
                    % (operations, request.prefix)
                )
            if operationresources > 0:
                post["messages"].append(
                    "Created %d new <a target='_blank' class='text-decoration-underline' href='%s/data/input/operationresource/?noautofilter&sidx=lastmodified&amp;sord=desc'>operation resource</a>"
                    % (operationresources, request.prefix)
                )
            if operationmaterials > 0:
                post["messages"].append(
                    "Created %d new <a target='_blank' class='text-decoration-underline' href='%s/data/input/operationmaterial/?noautofilter&sidx=lastmodified&amp;sord=desc'>operation material</a>"
                    % (operationmaterials, request.prefix)
                )

            # Generate the plan
            management.call_command(
                "runplan",
                database=request.database,
                env="fcst,supply",
                constraint=13,
                background=True,
            )
            post["messages"].append(
                "<a target='_blank' class='text-decoration-underline' href='%s/execute/'>Generated the plan</a>"
                % request.prefix
            )

            # Leave feedback messages on the session
            request.session["post"] = post
            return HttpResponse(content="OK")

        except Exception as e:
            logger.error("Error creating supply path: %s" % e)
            post["messages"] = ["Error creating the supply path: %s" % e]
            request.session["post"] = post
            return HttpResponseServerError("Error creating supply path")


class FeatureDashboard(TemplateView):
    template_name = "wizard/features.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["title"] = "Explore features"
        return context


class QuickStartForecast(View):
    @method_decorator(staff_member_required())
    def get(self, request, *args, **kwargs):
        post = request.session.get("post", False)
        if post:
            del request.session["post"]
        return render(
            request,
            "wizard/quickstart_forecast.html",
            context={
                "title": _("Quickstart forecasting"),
                "post": post,
                "buckets": {
                    "day": _("days"),
                    "week": _("weeks"),
                    "month": _("months"),
                    "quarter": _("quarters"),
                }.get(
                    Parameter.getValue("forecast.calendar", request.database, None),
                    _("months"),
                ),
            },
        )

    @method_decorator(staff_member_required())
    def post(self, request, *args, **kwargs):
        post = {
            "item": request.POST["item"],
            "location": request.POST["location"],
            "customer": request.POST["customer"],
            "messages": [],
        }

        # Create item
        item, created = Item.objects.using(request.database).get_or_create(
            name=post["item"]
        )
        if created:
            post["messages"].append(
                "Created a new <a target='_blank' class='text-decoration-underline' href='%s/data/input/item/?noautofilter&sidx=lastmodified&amp;sord=desc'>item</a>"
                % request.prefix
            )

        # Create location
        location, created = Location.objects.using(request.database).get_or_create(
            name=post["location"]
        )
        if created:
            post["messages"].append(
                "Created a new <a target='_blank' class='text-decoration-underline' href='%s/data/input/location/?noautofilter&sidx=lastmodified&amp;sord=desc'>location</a>"
                % request.prefix
            )

        # Create customer
        customer, created = Customer.objects.using(request.database).get_or_create(
            name=post["customer"]
        )
        if created:
            post["messages"].append(
                "Created a new <a target='_blank' class='text-decoration-underline' href='%s/data/input/customer/?noautofilter&sidx=lastmodified&amp;sord=desc'>customer</a>"
                % request.prefix
            )

        # Create demand
        created = False
        Demand.objects.using(request.database).filter(
            item=item, customer=customer, location=location, source="wizard"
        ).delete()
        history = request.POST["history"].split()
        cal = Parameter.getValue("forecast.calendar", request.database, "month")
        currentdate = getCurrentDate(request.database, lastplan=True).date()
        if not Bucket.objects.all().using(request.database).exists():
            management.call_command("createbuckets", database=request.database, task=-1)
        buckets = list(
            BucketDetail.objects.filter(bucket__name=cal, enddate__lte=currentdate)
            .order_by("-enddate")
            .only("name", "startdate", "enddate")[: len(history)]
        )
        idx = len(history)
        for qty in history:
            created = True
            idx -= 1
            (buckets[idx].enddate - buckets[idx].startdate) / 2
            Demand(
                name="History %s - %s - %s - %s"
                % (item.name, location.name, customer.name, buckets[idx].name),
                item=item,
                location=location,
                customer=customer,
                due=(
                    buckets[idx].startdate
                    + (buckets[idx].enddate - buckets[idx].startdate) / 2
                ).date(),
                quantity=float(qty),
                status="closed",
                source="wizard",
            ).save(using=request.database)
        if created:
            post["messages"].append(
                "Created %d closed <a target='_blank' class='text-decoration-underline' href='%s/data/input/demand/?noautofilter&sidx=lastmodified&amp;sord=desc'>sales orders</a>"
                % (len(history), request.prefix)
            )

        # Generate the plan
        management.call_command(
            "runplan",
            database=request.database,
            env="fcst,supply",
            constraint=13,
            background=True,
        )
        post["messages"].append(
            "<a target='_blank' class='text-decoration-underline' href='%s/execute/'>Generated the plan</a>"
            % request.prefix
        )

        # Don't return HTML, but a redirect after leaving info on the session
        request.session["post"] = post
        return HttpResponseRedirect("%s%s" % (request.prefix, request.path))
