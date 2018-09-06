====================
Rebalancing requests
====================

Rebalancing requests are a special type of distribution orders.

If there exists an item distribution for a given record from an origin location O to a destination location D then frePPLe will
generate distribution orders for that item from O to D.

Rebalancing requests are designed to send back some material from the destination location D to the origin location O based on some criteria.

The idea behind rebalancing requests is to identify excess inventory and send it back to the source location to possibly make it available to other
locations.

There are three parameters driving the stock rebalancing requests generation :

* | *REBALANCING_PART_COST_THRESHOLD*:
  | The minimum part cost threshold used to trigger a rebalancing. Parts with a cost below the threshold will not be rebalanced.

* | *REBALANCING_TOTAL_COST_THRESHOLD*:
  | The minimum total cost threshold to trigger a rebalancing (equals to rebalanced quantity multiplied by item cost). 
    Rebalancing requests with total cost below the threshold will not be created.

* | *REBALANCING_BURNOUT_THRESHOLD*:
  | If the excess inventory will be consumed and disappear within the "burn up" time window, no rebalancing request will
    be created.
  
.. rubric:: Example

The above Excel file contains the results of the plan in the *Distribution Orders* tab.

:download:`Excel spreadsheet rebalancing-requests <rebalancing-requests.xlsx>`

In this example, we have defined  :

* | *REBALANCING_PART_COST_THRESHOLD* = 20.
  | No part with a cost less than 20 is eligible for a rebalancing request.

* | *REBALANCING_TOTAL_COST_THRESHOLD* = 100.
  | No rebalancing request with a total cost (item cost multiplied by request quantity) less than 100 will be created.

* | *REBALANCING_BURNOUT_THRESHOLD* = 90. 
  | The rebalancing request quantity should not be less than 90 days of forecasted consumption.

Having a look at it, you will notice that the first three records
are actually rebalancing requests as the source location is a shop and the destination location is the regional distribution center (RDC).

The three rebalancing requests proposed by the tool are for parts having unit cost of 20, 75 and 300, therefore more than parameter *REBALANCING_PART_COST_THRESHOLD* value (Tennis tee-shirt long sleeves, All-surface tennis shoes, Novak racket).

The three rebalancing requests proposed by the tool are for a total cost of 1140, 1725 and 34200, therefore more than parameter *REBALANCING_TOTAL_COST_THRESHOLD* value.

**Important**: The quantity of a rebalancing request is equal to (onhand - safety stock - reorder quantity)
but a rebalancing request will only be generated if onhand >= safety stock + reorder quantity + burnout quantity.

For the generated rebalancing requests, here is quick summary of the inventory planning solver :

  buffer=All-surface tennis shoes @ Tennis shop Brussels roq=24.0 ss=3.0 demand=4.0 onhand=50.0

  buffer=Novak racket @ Tennis shop Paris roq=35.0 ss=1.0 demand=35.0 onhand=150.0

  buffer=Tennis tee-shirt long sleeves @ Tennis shop Brussels roq=87.0 ss=16.0 demand=15.0 onhand=160.0

Let's take the Novak racket for instance, the monthly forecast is 35, therefore the burnout quantity is equal to 35*3 = 105.

The rebalancing request will only be triggered if onhand >= safety stock + reorder quantity + burnout quantity = 141.

As onhand is 150, then a rebalancing request is generated for a quantity equals to onhand - safety stock - reorder quantity = 150 - 36 = 114.
