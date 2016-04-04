===============
Forecast module
===============

.. Important::

   This module is only available in the Enterprise Edition.

This module provides the functionality to manage the forecasted
customer demand. An overview presentation of the module is
available at http://frepple.com/frePPLe_forecasting.pdf

.. image:: _images/forecasting-process.png
   :alt: Forecasting process

It provides the following capabilities to support the forecasting process
in your company:

* | **Statistical forecast calculation to extrapolate historical demand**
    **into the future**
  | A first step in the process is to collect the historical demand and
    run a time series analysis to predict the future demand.

  FrePPLe implements the following classic time series methods:

  * Single exponential smoothing, which is applicable for constant demands

  * Double exponential smoothing, which is applicable for trended demands

  * Holt-Winter’s exponential smoothing with mutiplicative seasonality, which
    is applicable for seasonal demands

  * Croston’s method, which is applicable for intermittent demand (i.e. demand
    patterns with a lot of zero demand buckets)

  * Moving average, which is applicable when there is little demand history

  The algorithm will automatically tune the parameters of each of these
  methods to minimize the forecast error.

  During the calculation the algorithm scans for exceptional demand outliers,
  and filter them out from the demand history.

  The algorithm also automatically selects the most appropriate forecasting
  method. The user has the ability to override this automatic selection.

  .. Hint::

     The M3 competition is an industry recognized benchmark for forecasting algorithms.
     It provides 3003 time series from different domains and industries. Competing
     forecasting tools compute the forecasted values, and the forecast error with
     the actuals is used as a score.

     Details, results and findings can be found in this excellent paper:
     http://forecastingprinciples.com/files/Makridakia-The%20M3%20Competition.pdf

     FrePPLe’s planning algorithm scores among the top, as can be seen from our
     benchmark results: http://frepple.com/frePPLe_m3_forecast_benchmark.xlsx

  The statistical base forecast is normally computed in batch mode.

* | **Forecast review and manual corrections**
  | In a second step users will review the statistical forecast proposed by
    the system. Users have the ability to override the forecast, and apply
    their business knowledge (eg new products, products phasing out,
    promotions, competition, etc...) to come up with the final sales forecast.

  See :doc:`forecast report<../user-guide/plan-analysis/forecast-report>`.

  The process of reviewing the sales forecast is typically a weekly or
  monthly process, involving both the sales and production departments.

* | **Preprocess the sales forecast for production planning**
  | The sales forecast needs some preprocessing to make it suitable for the
    production planning.

  * | **Profiling the forecast in smaller time buckets**
    | This functionality allows to translate between different time
      granularities.
    | The forecast entered by the sales department could for instance be
      in monthly buckets, while the manufacturing department requires the
      forecast to be in weekly or even daily buckets to generate accurate
      manufacturing and procurement plans.
    | Another usage is to model a delivery date profile of the customers.
      Each bucket has a weight that is used to model situations where the
      demand is not evenly spread across buckets: e.g. when more orders
      are expected due on a monday than on a friday, or when a peak of
      orders is expected for delivery near the end of a month.

  * | **Consuming/netting the forecast with actual sales orders**
    | As customer orders are being received they need to be deducted
      from the forecast to avoid double-counting it.
    | For example, assume the forecast for customer A in January is 100
      pieces, and we have already received orders of 20 from the customer.
      Without the forecast netting the demand in January would be 120 pieces,
      which is (very likely) not correct.
    | The netting solver will deduct the orders of 20 from the forecast.
      The total demand that is planned in January will then be equal to
      100: 80 remaining net forecast + 20 orders.
    | The netting algorithm has logic to match a demand with the most
      appropriate forecast at the right level in the customer and product
      hierarchies, and it can also consider netting in previous and subsequent
      time buckets.

  | This process step is recalculated as part of the production plan
    generation.

**Module configuration**

Detailed documentation of the module and its configuration parameters is available on our customer portal.

**Example Python code**

Adding or changing a forecast

::

    it = frepple.item(name="item")
    cust = frepple.customer(name="customer")
    cal = frepple.calendar(name="planningbuckets")
    fcst = frepple.demand_forecast(name="My forecast",
      item=it, customer=cust, calendar=cal)

Loading the module

::

    frepple.loadmodule("mod_forecast.so",
       Net_CustomerThenItemHierarchy=True,
       Net_MatchUsingDeliveryOperation=True,
       Net_NetEarly="P7D",
       Net_NetLate="P7D")

Creating a time series forecast

::

    # The first argument is the demand history in previous buckets.
    # The second argument are the time buckets where we want to create a forecast value.
    thebuckets = [ i.start for i in thecalendar.buckets ]
    fcst.timeseries([10,12,9,11,8,15,19,11], thebuckets)

Netting customer orders from the forecast

::

   frepple_forecast.solver_forecast(name="Netting", loglevel=1).solve()
