===================
Distribution Orders
===================

This table contains the distribution orders of your supply chain, either proposed by frePPLe or confirmed.
A distribution order is a transfer order of some material from one location of your supply chain to another location of your supply chain (stock rebalancing).

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
criticality      number            | The criticality is a read-only field, calculated by the planning engine. 
                                   | It represents an indication of the slack time in the usage of the distribution order.
                                   | A criticality of 0 indicates that the distribution order is on the critical path of one or more demands.
                                   | Higher criticality values indicate a delay of the distribution order will not immediately impact the shipment of any demand.                                   
                                   | A criticality of 999 indicates a distribution order that isn’t used at all to meet any demand.
                                   | Note that the criticality is independent of whether the customer demand will be shipped on time or not.
delay            Duration          | The delay is a read-only field, calculated by the planning engine.
                                   | It compares the end data of the distribution order with the latest possible end date to ship all demands it feeds on time.
================ ================= =================================================================================================================================                            
                                  
