=========
Parameter
=========

Global settings and parameters are stored in a specific table.

Some of these parameters are used by the planning algorithm, others are used
by the web application. Extension modules also add additional configuration
parameters to this table.

**Fields**

================ ================= ===========================================================
Field            Type              Description
================ ================= ===========================================================
name             string            Unique name of the parameter.
value            string            Value of the parameter.
description      string            Description of the parameter.
================ ================= ===========================================================

**Standard parameters**

The table below shows the parameters that are recognized by the standard
application.


=========================== =======================================================================
Parameter                   Description
=========================== =======================================================================
currentdate                 | Current date of the plan, formatted as YYYY-MM-DD HH:MM:SS.
                              If the parameter is missing or empty the system time is used as current date.
currency                    | Currency symbol.
                            | This parameter may be only set on the default database and will be
                             globally applied, including in all the scenarios.
                            | If the parameter is missing or empty the currency symbol will be the $.
                            | By default the symbol will show after the value, i.e. **123 $**.
                            | For the symbol to show before the value a **,** should be added after the
                             symbol, i.e. **$,**, resulting in **$ 123**.
loading_time_units          | Time units to be used for the resource report.
                            | Accepted values are: hours, days, weeks.
plan.administrativeLeadtime | Specifies an administrative lead time in days.
                            | FrePPLe will plan the sales orders one administrative lead time ahead of the due date.
                            | Accepted values : Any positive decimal number.
plan.autoFenceOperations    | The number of days the solver should wait for a confirmed 
                              replenishment before generating a proposed order. 
                            | Default:0 (deactivated).
plan.calendar               | Name of a calendar to align new operationplans with.
                            | When this parameter is used, the plan results are effectively grouped
                             in the time buckets defined in this calendar.
                            | This feature is typically used for medium and long term plans.
                            | Such plans are reviewed in monthly or weekly buckets rather than at individual dates.
plan.loglevel               | Controls the verbosity of the planning log file.
                            | Accepted values are 0 (silent – default), 1 (minimal)
                            | and 2 (verbose).
plan.planSafetyStockFirst   | Controls whether safety stock is planned before or after the demand.
                            | Accepted values are false (default) and true.
plan.rotateResources        | When set to true, the algorithm will better distribute
                             the demand across alternate suboperations instead of using
                             the preferred operation.
plan.webservice             | Specifies whether to use the web service or not.
                            | Accepted values are false (default) and true.

=========================== =======================================================================

**Extension modules parameters**

The table below shows the parameters that are regognized by all the extension modules and therefore only available on the Enterprise edition.
By convention, these parameters are formatted module.name to clearly state to which module they apply.

==================================================== ===========================================================================
Parameter                                            Description
==================================================== ===========================================================================
forecast.calendar                                    Name of a calendar model to define the granularity of the time buckets
                                                     for forecasting.
forecast.Croston_initialAlfa                         Initial parameter for the Croston forecast method.
forecast.Croston_maxAlfa                             Maximum parameter for the Croston forecast method.
forecast.Croston_minAlfa                             Minimum parameter for the Croston forecast method.
forecast.Croston_minIntermittence                    Minimum intermittence (defined as the percentage of zero demand buckets)
                                                     before the Croston method is applied.
forecast.DeadAfterInactivity                         Number of days of inactivity before a forecast is marked dead and it's
                                                     baseline forecast will be 0. Default is 365.                            
forecast.DoubleExponential_dampenTrend               Dampening factor applied to the trend in future periods.
forecast.DoubleExponential_initialAlfa               Initial smoothing constant.
forecast.DoubleExponential_initialGamma              Initial trend smoothing constant.
forecast.DoubleExponential_maxAlfa                   Maximum smoothing constant.
forecast.DoubleExponential_maxGamma                  Maximum trend smoothing constant.
forecast.DoubleExponential_minAlfa                   Minimum smoothing constant.
forecast.DoubleExponential_minGamma                  Minimum trend smoothing constant.
forecast.DueWithinBucket                             Specifies whether forecasted demand is due at the 'start', 'middle' or
                                                     'end' of the bucket.
forecast.Horizon_future                              Specifies the number of days in the future we generate a forecast for.
forecast.Horizon_history                             Specifies the number of days in the past we use to compute
                                                     a statistical forecast.
forecast.Iterations                                  Specifies the maximum number of iterations allowed for a forecast method
                                                     to tune its parameters.
forecast.loglevel                                    Verbosity of the forecast solver
forecast.MovingAverage_order                         This parameter controls the number of buckets to be averaged by the moving
                                                     average forecast method.
forecast.Net_CustomerThenItemHierarchy               This flag allows us to control whether we first search the customer
                                                     hierarchy and then the item hierarchy, or the other way around.
forecast.Net_MatchUsingDeliveryOperation             Specifies whether or not a demand and a forecast require to have the same
                                                     delivery operation to be a match.
forecast.Net_NetEarly                                Defines how much time (expressed in days) before the due date of an order
                                                     we are allowed to search for a forecast bucket to net from.
forecast.Net_NetLate                                 Defines how much time (expressed in days) after the due date of an order
                                                     we are allowed to search for a forecast bucket to net from.
forecast.Outlier_maxDeviation                        Multiple of the standard deviation used to detect outliers
forecast.populateForecastTable                       Populates automatically the forecast table based on the item/location
                                                     combinations found in the demand table using parent customer when available.
                                                     Default : true
forecast.Seasonal_dampenTrend                        Dampening factor applied to the trend in future periods.
forecast.Seasonal_gamma                              Value of the seasonal parameter
forecast.Seasonal_initialAlfa                        Initial value for the constant parameter
forecast.Seasonal_initialBeta                        Initial value for the trend parameter
forecast.Seasonal_maxAlfa                            Maximum value for the constant parameter
forecast.Seasonal_maxBeta                            Maximum value for the trend parameter
forecast.Seasonal_maxPeriod                          Maximum seasonal cycle to be checked.
forecast.Seasonal_minAlfa                            Minimum value for the constant parameter
forecast.Seasonal_minBeta                            Initial value for the trend parameter
forecast.Seasonal_minPeriod                          Minimum seasonal cycle to be checked.
forecast.Seasonal_minAutocorrelation                 Minimum autocorrelation below which the seasonal forecast method
                                                     is never selected.
forecast.Seasonal_maxAutocorrelation                 Maximum autocorrelation above which the seasonal forecast method
                                                     is always selected.
forecast.SingleExponential_initialAlfa               Initial smoothing constant.
forecast.SingleExponential_maxAlfa                   Maximum smoothing constant.
forecast.SingleExponential_minAlfa                   Minimum smoothing constant.
forecast.Skip                                        Specifies the number of time series values used to initialize
                                                     the forecasting method. The forecast error in these bucket isn't counted.
forecast.SmapeAlfa                                   Specifies how the sMAPE forecast error is weighted for different
                                                     time buckets.
inventoryplanning.average_window_duration            The number of days used to average the demand to limit reorder quantity
                                                     and safety stock variability over periods. Default value : 180
inventoryplanning.calendar                           Name of a calendar model to define the granularity of the time buckets
                                                     for inventory planning.
inventoryplanning.fixed_order_cost                   Holding cost percentage to compute economic reorder quantity.
                                                     Default value: 20
inventoryplanning.holding_cost                       Fixed order cost to compute the economic reorder quantity.
                                                     Default value: 0.05
inventoryplanning.horizon_end                        Specifies the number of days in the future for which we generate safety
                                                     stock and reorder quantity values. Default: 365
inventoryplanning.horizon_start                      Specifies the number of days in the past for which we generate safety
                                                     stock and reorder quantity values. Default: 0
inventoryplanning.loglevel                           Controls the verbosity of the inventory planning solver.
                                                     Accepted values are 0(silent - default), 1 and 2 (verbose)
inventoryplanning.rebalancing_burnout_threshold      The minimum time to burn up excess inventory (compared to forecast) that can be rebalanced (in periods).
                                                     If the burn out period (Excess Quantity/Forecast) is less than the threshold, the rebalancing will not occur.
                                                     Default value: 0
inventoryplanning.rebalancing_part_cost_threshold    The minimum part cost threshold used to trigger a rebalancing. Parts with cost below the threshold will not be rebalanced.
                                                     Default value: 0
inventoryplanning.rebalancing_total_cost_threshold   The minimum total cost threshold to trigger a rebalancing (equals to rebalanced qty multiplied by item cost).
                                                     Rebalancing requests with total cost below the threshold will not be created. Default value: 0
inventoryplanning.service_level_on_average_inventory Flag whether the service level is computed based on the expected average
                                                     inventory. When set to false the service level estimation is based only
                                                     on the safety stock. Default value: false
==================================================== ===========================================================================
