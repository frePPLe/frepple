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

==================================== =======================================================================
Parameter                            Description
==================================== =======================================================================
currentdate                          | Current date of the plan, preferred format is YYYY-MM-DD HH:MM:SS
                                       but most known formats to represent a date and/or time are accepted.
                                     | When the parameter is set to "today", we use today 00:00 / midnight
                                       as the currrent date.
                                     | When the parameter is set to "now", we use the system time as current date.
                                     | If the parameter is missing, empty or has an uncognized format, the system
                                       time is also used as current date.
currency                             | Currency symbol.
                                     | This parameter may be only set on the default database and will be
                                       globally applied, across all the scenarios.
                                     | If the parameter is missing or empty the currency symbol will be the $.
                                     | By default the symbol will show after the value, i.e. **123 $**.
                                     | For the symbol to show before the value a **,** should be added after the
                                       symbol, i.e. **$,**, resulting in **$ 123**.
display_time                         | This parameter controls if date time fields display the time.
                                     | Accepted values: true or false
                                     | This parameter applies to ALL scenarios.
date_format                          | Date format to be used in the user interface and data imports.
                                     | Accepted values: month-day-year, day-month-year, year-month-day.
                                     | This parameter applies to ALL scenarios.
loading_time_units                   | Time units to be used for the resource report.
                                     | Accepted values are: hours, days, weeks.
excel_duration_in_days               | Determines whether numbers in spreadsheets are considered
                                       as days or seconds. Default is true for days.
                                     | This parameter is only useful for backward compability.
plan.administrativeLeadtime          | Specifies an administrative lead time in days.
                                     | FrePPLe will plan the sales orders this amount of time ahead of their
                                       due date. This creates extra safety in the delivery schedule and also
                                       moves all material and capacity needs early.

                                     | The default value is 0 days, which is a just-in-time plan, where we try
                                       to plan all demands in **backward scheduling mode** from their due date.

                                     | Setting this parameter to a high value (eg 999) will result in a plan
                                       where everything is planned ASAP in **forward scheduling mode**.

plan.autoFenceOperations             | The number of working days the solver should wait for a confirmed
                                       replenishment before generating a proposed order.
                                     | Default: 999 (i.e. wait indefinitely)
plan.move_approved_early             | The planning algorithm by default will leave approved manufacturing at their scheduled
                                       date. In the Enterprise and Cloud Edition they will be delayed automatically
                                       to dates where they are feasible.
                                     | By setting this parameter to true, the algorithm can also try to reschedule
                                       them to earlier dates if there are earlier requirements.
                                     | This parameter has thre possible values:
                                     | - 0: Inactive. Don't move approved operationplans early. This is the default.
                                     | - 1: Active, and preserve existing resource assignments.
                                     | - 2: Active, and re-evaluate all resource assignments.
plan.capacityBufferPercentage       | Percentage of extra capacity to be added to all resources.
plan.deliveryDuration                | The duration (in working hours) for the delivery shipment of a sales order
                                       to the customer.
                                     | Default: 0 (i.e. the sales order due date is treated as the shipping
                                       date from our location, not the arrival date at the customer)
plan.individualPoolResources         | Defines the behavior of aggregate resource.

                                     | A operation-resource record with quantity N for an aggregate resource
                                       can mean either:
                                     | - Find a member resource with size N. Value false, default.
                                     | - Find N member resources of size 1. Value true.
plan.minimalBeforeCurrentConstraints | By default the "why short or late" list for a sales order can include
                                       many operations as lead-time and release-fence constraints.
                                     | When setting this option to true, we will limit the list to show only
                                       the most constraining operation. This make the list easier to interpret
                                       by users.
plan.loglevel                        | Controls the verbosity of the planning log file.
                                     | Accepted values are 0 (silent – default), 1 (minimal) and 2 (verbose).
plan.minimumdelay                    | Specifies a minimum delay the algorithm applies when the requested
                                       date isn't feasible.
                                     | The default value is 3600. This value should only be changed when the
                                       planning run is taking a long time and the log file shows that demands
                                       take many iterations to be planned - where the requested delivery
                                       date for each iteration is advancing only in tiny increments.
plan.fixBrokenSupplyPath             | When set to true (which is the default), frepple will scan for
                                       items that can't be replenished any longer with purchase orders,
                                       distribution orders or manufacturing orders.

                                     | FrePPLe automatically creates a dummy/fake supplier for such items.
                                       In this way broken supply paths are automatically fixed. Planners
                                       will need to review such dummy purchase orders and update the
                                       master data to replace them with the correct replenishment method.

                                     | When this parameter is set to false, broken supply paths will result
                                       in unplanned demand. Analysing the unplanned demand is in most cases
                                       more complex than reviewing the dummy purchase orders.
plan.rotateResources                 | When set to true, the algorithm will better distribute
                                       the demand across alternate suboperations instead of using
                                       the preferred operation.
plan.webservice                      | Specifies whether we keep the plan in memory as a web service for
                                       quick incremental planning. This functionality is only available in
                                       the Enterprise and Cloud Editions.
                                     | Accepted values are false and true (default).
COMPLETED.consume_material           | Determines whether completed manufacturing orders consume material
                                       or not.
                                     | Default is true.
COMPLETED.allow_future               | We assume that completed operations are always ending in the past.
                                       The planning engine will automatically adjust the end date to enforce
                                       this rule, unless this parameter is set to true.
                                     | Default is false.
WIP.consume_material                 | Determines whether confirmed manufacturing orders consume material
                                       or not.
                                     | Default is true.
WIP.consume_capacity                 | Determines whether confirmed manufacturing orders, purchase orders
                                       and distribution orders consume capacity or not.
                                     | Default is true.
WIP.produce_full_quantity            | Controls how material is produced from partially completed
                                       manufacturing orders.
                                     | When set to "false" (the default) a partially completed manufacturing
                                       order is producing only the remaining quantity of material. We assume
                                       that the on hand inventory has already been incremented to reflect
                                       the produced material.
                                     | When set to "true" a partially completed manufacturing ordre will
                                       still produce the full quantity of the material. We assume that the
                                       produced material will only be booked as inventory when the
                                       manufacturing order is fully finished.
==================================== =======================================================================

**Demand forecasting parameters**

The recommended default parameters for the demand forecasting module are different for daily, weekly and
monthly time buckets. The parameters with a value "default" in the parameters screen can get a different
value depending on the configured time bucket.

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
forecast.Net_PastDemand                              | When this parameter is false (default) only sales orders in the current and
                                                       future buckets net from forecast.
                                                     | When set to true also older demands are used for netting forecast.
forecast.Net_IgnoreLocation                          | When this parameter is true the forecasting netting doesn't need a match
                                                       between location of the sales order and the forecast.
                                                     | This can be useful when sales orders are often shipped from a non-standard
                                                       location.
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

**Report manager parameters**

==================================================== ===========================================================================
Parameter                                            Description
==================================================== ===========================================================================
report_download_limit                                | The maximum number of rows that are allowed to be downloaded with a
                                                       custom report. The limit protects against inefficient SQL report queries
                                                       that download excessive ammounts of data.
                                                     | Default value: 20000
==================================================== ===========================================================================

**Plan archiving parameters**

Frepple keeps a history of the key metrics of your plan. These metrics are used to display overall trends in your plan, and can
also be useful to debug the evolution of certain data elements over time.

==================================================== ===========================================================================
Parameter                                            Description
==================================================== ===========================================================================
archive.frequency                                    | Frequency of history snapshot. Accepted values are "week", "month" and
                                                       "none".
													 | Default value: week
archive.duration                                     | Archived data older than this parameter in days will be deleted.
                                                     | Default value: 365
==================================================== ===========================================================================
