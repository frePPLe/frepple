===============
Forecast module
===============

.. Important::

   This module is only available in the Enterprise Edition.

This module provides the functionality to manage the forecasted
customer demand.

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

The module support the following configuration parameters:

* | *DueWithinBucket*:
  | Specifies whether forecasted demand is due at the 'start', 'middle' or
    'end' of the bucket.
  | Using the middle of the bucket gives the most realistic approximation and
    is the recommended default value.
  | Using the start date of the bucket is a more conservative setting: it
    assures that all forecast supply is already available at the start of the
    month.

* | *Net_CustomerThenItemHierarchy*:
  | As part of the forecast netting a demand is assiociated with a certain
    forecast. When no matching forecast is found for the customer and item of
    the demand, frePPLe looks for forecast at higher level customers and items.
  | This flag allows us to control whether we first search the customer
    hierarchy and then the item hierarchy, or the other way around.
  | The default value is true, ie search higher customer levels before
    searching higher levels of the item.

* | *Net_MatchUsingDeliveryOperation*:
  | Specifies whether or not a demand and a forecast require to have the same
    delivery operation to be a match.
  | The default value is true.

* | *Net_NetEarly*:
  | Defines how much time before the due date of an order we are allowed to
    search for a forecast bucket to net from.
  | The default value is 0, meaning that we can net only from the bucket where
    the demand is due.

* | *Net_NetLate*:
  | Defines how much time after the due date of an order we are allowed to
    search for a forecast bucket to net from.
  | The default value is 0, meaning that we can net only from the bucket where
    the demand is due.

* | *Forecast_Iterations*:
  | Specifies the maximum number of iterations allowed for a forecast method to
    tune its parameters.
  | Only positive values are allowed and the default value is 10.
  | Set the parameter to 1 to disable the tuning and generate a forecast based
    on the user-supplied parameters.

* | *Forecast_smapeAlfa*:
  | Specifies how the sMAPE forecast error is weighted for different time
    buckets. The sMPAPE value in the most recent bucket is 1.0, and the weight
    decreases exponentially for earlier buckets.
  | Acceptable values are in the interval 0.5 and 1.0, and the default is 0.95.

* | *Forecast_Skip*:
  | Specifies the number of time series values used to initialize the
    forecasting method. The forecast error in these bucket isn’t counted.

* | *Forecast_MovingAverage_buckets*:
  | This parameter controls the number of buckets to be averaged by the moving
    average forecast method.

* | *Forecast_SingleExponential_initialAlfa, Forecast_SingleExponential_minAlfa,*
    *Forecast_SingleExponential_maxAlfa*:
  | Specifies the initial value and the allowed range of the smoothing parameter
    in the single exponential forecasting method.
  | The allowed range is between 0 and 1. Values lower than about 0.05 are not
    advisable.

* | *Forecast_DoubleExponential_initialAlfa, Forecast_DoubleExponential_minAlfa,*
    *Forecast_DoubleExponential_maxAlfa*:
  | Specifies the initial value and the allowed range of the smoothing parameter
    in the double exponential forecasting method.
  | The allowed range is between 0 and 1. Values lower than about 0.05 are not
    advisible.

* | *Forecast_DoubleExponential_initialGamma, Forecast_DoubleExponential_minGamma,*
    *Forecast_DoubleExponential_maxGamma*:
  | Specifies the initial value and the allowed range of the trend smoothing
    parameter in the double exponential forecasting method.
  | The allowed range is between 0 and 1.

* | *Forecast_DoubleExponential_dampenTrend*:
  | Specifies how the trend is dampened for future buckets.
  | The allowed range is between 0 and 1, and the default value is 0.8.

* | *Forecast_Seasonal_initialAlfa, Forecast_Seasonal_minAlfa,*
    *Forecast_Seasonal_maxAlfa*:
  | Specifies the initial value and the allowed range of the smoothing parameter
    in the seasonal forecasting method.
  | The allowed range is between 0 and 1. Values lower than about 0.05 are not
    advisible.

* | *Forecast_Seasonal_initialBeta, Forecast_Seasonal_minBeta,*
    *Forecast_Seasonal_maxBeta*:
  | Specifies the initial value and the allowed range of the trend smoothing
    parameter in the seasonal forecasting method.
  | The allowed range is between 0 and 1.

* | *Forecast_Seasonal_initialGamma, Forecast_Seasonal_minGamma,*
    *Forecast_Seasonal_maxGamma*:
  | Specifies the initial value and the allowed range of the seasonal
    smoothing parameter in the seasonal forecasting method.
  | The allowed range is between 0 and 1.

* | *Forecast_Seasonal_minPeriod, Forecast_Seasonal_maxPeriod*:
  | Specifies the periodicity of the seasonal cycles to check for.
  | The interval of cycles we try to detect should be broad enough. For
    instance, if we expect to find a yearly cycle use a minimum period of 10
    and maximum period of 14.

* | *Forecast_Seasonal_dampenTrend*:
  | Specifies how the trend is dampened for future buckets.
  | The allowed range is between 0 and 1, and the default value is 0.8.

* | *Forecast_Croston_initialAlfa, Forecast_Croston_minAlfa,*
    *Forecast_Croston_maxAlfa*:
  | Specifies the initial value and the allowed range of the smoothing
    parameter in the Croston forecasting method.
  | The allowed range is between 0 and 1. Values lower than about 0.05 are
    not advisable.

* | *Forecast_Croston_minIntermittence*:
  | Minimum intermittence (defined as the percentage of zero demand buckets)
    before the Croston method is applied.
  | When the intermittence exceeds this value, only Croston and moving average
    are considered suitable forecast methods.
  | The default value is 0.33.

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
