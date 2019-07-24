=========
Parameter
=========

Global settings and parameters are stored here.

Some of these parameters are used by the planning algorithm, others are used
by the web application. Extension modules also add additional configuration
parameters to this table.

**Standard parameters**

The table below shows the parameters that are recognized by the standard
application.

=========================== =======================================================================
Parameter                   Description
=========================== =======================================================================
allowsplits                 | When set to true (default value), a sales order or forecast is
                              allowed to be planned in multiple manufacturing orders. An order of
                              eg 100 pieces can be planned with 2 manufacturing of 50 pieces.
                            | When the parameter is set to false, this splitting is disabled. This
                              will result in a plan with less manufacturing orders. The plan 
                              generation will be considerably faster, but can have additional 
                              delivery delays of the customer orders and forecasts.
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
                            | FrePPLe will plan the sales orders this amount of time ahead of their 
                              due date. This creates extra safety in the delivery schedule and also
                              moves all material and capacity needs early.
                            | Default value: 0 days
                            | Accepted values : Any positive decimal number.
plan.autoFenceOperations    | The number of days the solver should wait for a confirmed 
                              replenishment before generating a proposed order. 
                            | Default: 999 (wait indefinitely)
                            | Default before release 5.0.0: 0 (don't wait)
plan.calendar               | Name of a calendar to align the end date of new manufacturing orders,
                              purchase orders, distribution orders and delivery orders with.
                            | When this parameter is used, the plan results are effectively grouped
                             in the time buckets defined in this calendar.
                            | This feature is typically used for medium and long term plans.
                            | Such plans are reviewed in monthly or weekly buckets rather than at
                              individual dates.
plan.loglevel               | Controls the verbosity of the planning log file.
                            | Accepted values are 0 (silent – default), 1 (minimal) and 2 (verbose).
plan.minimumdelay           | Specifies a minimum delay the algorithm applies when the requested
                              date isn't feasible.                            
                            | The default value is 3600. This value should only be changed when the
                              planning run is taking a long time and the log file shows that demands
                              take many iterations to be planned - where the requested delivery
                              date for each iteration is advancing only in tiny increments.              
plan.planSafetyStockFirst   | Controls whether safety stock is planned before or after the demand.
                            | Accepted values are false (default) and true.
plan.rotateResources        | When set to true, the algorithm will better distribute
                             the demand across alternate suboperations instead of using
                             the preferred operation.
plan.webservice             | Specifies whether we keep the plan in memory as a web service for
                              quick incremental planning. This functionality is only available in
                              the Enterprise and Cloud Editions. 
                            | Accepted values are false and true (default).
WIP.consume_material        | Determines whether confirmed manufacturing orders consume material 
                              or not.
                            | Default is true.
WIP.consume_capacity        | Determines whether confirmed manufacturing orders, purchase orders 
                              and distribution orders consume capacity or not.
                            | Default is true.
=========================== =======================================================================

**Demand forecasting parameters** 

The recommended default parameters for the demand forecasting module are different for weekly and
monthly time buckets. The datasets parameters_month_forecast and parameters_week_forecast allow
you to reset the defaults values applicable to your configuration.

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
forecast.DueWithinBucket                             Specifies whether forecasted demand is due at the 'start', 'middle'
                                                     (default value) or 'end' of the bucket.
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
forecast.populateForecastTable                       | Populates automatically the forecast table based on the item/location
                                                       combinations found in the demand table using parent customer when available.
                                                     | Default : true
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
==================================================== ===========================================================================
                                      
**Inventory planning parameters** 

==================================================== ===========================================================================
Parameter                                            Description
==================================================== ===========================================================================    
inventoryplanning.average_window_duration            | The number of days used to average the demand to limit reorder quantity
                                                       and safety stock variability over periods.
                                                     | Default value : 180
inventoryplanning.calendar                           Name of a calendar model to define the granularity of the time buckets
                                                     for inventory planning.
inventoryplanning.fixed_order_cost                   | Holding cost percentage to compute economic reorder quantity.
                                                     | Default value: 20
inventoryplanning.holding_cost                       | Fixed order cost to compute the economic reorder quantity.
                                                     | Default value: 0.05
inventoryplanning.horizon_end                        | Specifies the number of days in the future for which we generate safety
                                                       stock and reorder quantity values.
                                                     | Default: 365
inventoryplanning.horizon_start                      Specifies the number of days in the past for which we generate safety
                                                     stock and reorder quantity values. Default: 0
inventoryplanning.loglevel                           | Controls the verbosity of the inventory planning solver.
                                                     | Accepted values are 0(silent - default), 1 and 2 (verbose)
inventoryplanning.service_level_on_average_inventory | Flag whether the service level is computed based on the expected average
                                                       inventory. When set to false the service level estimation is based only
                                                       on the safety stock.
                                                     | Default value: false
==================================================== ===========================================================================
                                      
**Inventory rebalancing parameters** 

==================================================== ===========================================================================
Parameter                                            Description
==================================================== ===========================================================================    
inventoryplanning.rebalancing_burnout_threshold      | The minimum time to burn up excess inventory (compared to forecast) that
                                                       can be rebalanced (in days). If the burn out period (Excess Quantity / 
                                                       Forecast) is less than the threshold, the rebalancing will not occur.
                                                     | Default value: 60
inventoryplanning.rebalancing_part_cost_threshold    | The minimum part cost threshold used to trigger a rebalancing. Parts with
                                                       a cost below the threshold will not be rebalanced.
                                                     | Default value: 100000
inventoryplanning.rebalancing_total_cost_threshold   | The minimum total cost threshold to trigger a rebalancing (equals to 
                                                       rebalanced qty multiplied by item cost). Rebalancing requests with total
                                                       cost below the threshold will not be created.
                                                     | Default value: 1000000
==================================================== ===========================================================================
                                                     