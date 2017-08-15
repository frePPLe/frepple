===================
Distribution Orders
===================

This table contains the distribution orders of your supply chain, either proposed by frePPLe or confirmed.
A distribution order is a transfer order of some material from one location of your supply chain to another location of your supply chain.
A distribution order will be proposed by frePPLe for a given item if a record has been defined in the item distribution table for that item
(or for one of its parents in the hierarchy) from the origin location to the destination location.
However note that there is a special type of distribution orders called rebalancing requests. 
Rebalancing requests are sending back some material from the destination location to the origin location based on some criteria. The idea
behind rebalancing requests is to identify excess inventory and send it back to the source location to possibly make it available to other
locations.
The parameters driving the stock rebalancing requests generation are the following :

*REBALANCING_PART_COST_THRESHOLD* : The minimum part cost threshold used to trigger a rebalancing. Parts with cost below the threshold will not be rebalanced.

*REBALANCING _TOTAL_COST_THRESHOLD* : The minimum total cost threshold to trigger a rebalancing (equals to rebalanced qty multiplied by item price). Rebalancing requests with total cost below the threshold will not be created.

*REBALANCING _BURNOUT_THRESHOLD* : The minimum time to "burn up" excess inventory (compared to forecast) that can be rebalanced (in periods). If the "burn out" period (Excess Quantity/Forecast) is less than the threshold, the rebalancing will not occur. (E.g : If the rebalanced quantity corresponds to less than 3 months of forecast at the destination location, do not perform rebalancing).


**Fields**

================ ================= =================================================================================================================================
Field            Type              Description
================ ================= =================================================================================================================================
status           non-empty string  | This field should have one of the following keywords :
                                   | proposed : The distribition order is proposed by frePPLe to meet the plan (optimization output).
                                   | approved : The distribution order has been reviewed by the user and is ready to be exported to your ERP system.
                                   | confirmed : The distribution order is confirmed, it has been populated in your ERP system (optimization input).
                                   | closed : The distribution order has been delivered and the stock quantity increased.
item             item              The item being transfered.
origin           location          The model location where the item is transfered from.
destination      location          The model location where the item will be received.
quantity         number            The quantity delivered.
start date       DateTime          The date when the distribution order is leaving the origin location.
end date         DateTime          The date of the distribution order delivery.
Demands          demand            | The demand(s) (and quantity) pegged to the distribution order. This is a generated field.
Inventory Status Number            | The Inventory Status is a calculated field that highlights the urgency of the purchase order.
                                   | The cells have a background color that can be green, orange or red. Sorting 
                                   | the distribution orders using the Inventory Status column (red ones first) allows the planner to 
                                   | immediately focus on the distribution orders that should be treated first. 
criticality      number            | The criticality is a read-only field, calculated by the planning engine. 
                                   | It represents an indication of the slack time in the usage of the distribution order.
                                   | A criticality of 0 indicates that the distribution order is on the critical path of one or more demands.
                                   | Higher criticality values indicate a delay of the distribution order will not immediately impact the shipment of any demand.                                   
                                   | A criticality of 999 indicates a distribution order that isn’t used at all to meet any demand.
                                   | Note that the criticality is independent of whether the customer demand will be shipped on time or not.
delay            Duration          | The delay is a read-only field, calculated by the planning engine.
                                   | It compares the end data of the distribution order with the latest possible end date to ship all demands it feeds on time.
================ ================= =================================================================================================================================                            
                                  
