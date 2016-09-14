===============
Purchase Orders
===============

This table contains the purchase orders of your supply chain (replenishment you are purchasing from your suppliers), either proposed by frePPLe or confirmed.

**Fields**

================ ================= =================================================================================================================================
Field            Type              Description
================ ================= =================================================================================================================================
status           non-empty string  | This field should have one of the following keywords :
                                   | proposed : The purchase order is proposed by frePPLe to meet the plan (optimization output).
                                   | approved : The purchase order has been reviewed by the user and is ready to be exported to your ERP system.
                                   | confirmed : The purchase order is confirmed, it has been populated in your ERP system (optimization input).
                                   | closed : The purchase order has been delivered and the stock quantity increased.
item             item              The item being purchased.
location         location          The location receiving the purchase order.
supplier         supplier          The supplier shipping the purchase order.
quantity         number            The quantity delivered.
start date       DateTime          The date when the purchase order is leaving the supplier location.
end date         DateTime          The date of the purchase order delivery.
Demands          demand            The demand(s) (and quantity) pegged to the purchase order. This is a generated field.
criticality      number            | The criticality is a number calculated by the optimization. This is a generated field.
                                   | It reprensents an indication of the urgency of the purchase order.
                                   | A criticality of 0 indicates that the purchase order is on the critical path of one or more demands.
                                   | Higher criticality values indicate a delay of the purchase order will not immediately impact the delivery of any demand.
                                   | A criticality of 999 indicates a purchase order that isn’t used at all to meet any demand.
================ ================= =================================================================================================================================                            
                                  
