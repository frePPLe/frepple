===============
Purchase orders
===============

This table contains the purchase orders of your supply chain (replenishment you are purchasing from your 
suppliers), either proposed by frePPLe or confirmed.

This table is populated with new proposed purchase orders when frePPLe generates a plan.
It is also possible to load purchase orders that are already approved or confirmed in your ERP
system.

**Fields**

================ ================= =================================================================================================================================
Field            Type              Description
================ ================= =================================================================================================================================
reference        string            | Unique identifier for the purchase order.
                                   | This field will be empty for newly proposed purchase orders, but for approved or confirmed purchase orders that
                                     already exist in the ERP system this field should be populated with the identifier the ERP generated.
item             item              The item being purchased.
location         location          The location receiving the purchase order.
supplier         supplier          The supplier shipping the purchase order.
quantity         number            The quantity delivered.
ordering date    datetime          The date when the purchase order is leaving the supplier location.
receipt date     datetime          The date of the purchase order delivery.
start date       datetime          Deprecated alias for the ordering date.
end date         datetime          Deprecated alias for the receipt date.
status           non-empty string  | This field should have one of the following keywords :
                                   | proposed : The purchase order is proposed by frePPLe to meet the plan (optimization output).
                                   | approved : The purchase order is present in the ERP system but can still be rescheduled by frePPLe (optimization input).
                                   | confirmed : The purchase order is confirmed, it has been populated in your ERP system (optimization input).
                                   | closed : The purchase order has been delivered and the stock quantity increased.
demands          demand            The demand(s) (and quantity) pegged to the purchase order. This is a generated field.
inventory status number            | The Inventory Status is a calculated field that highlights the urgency of the purchase order.
                                   | The cells have a background color that can be green, orange or red. Sorting 
                                   | the purchase orders using the Inventory Status column (red ones first) allows the planner to 
                                   | immediately focus on the purchase orders that should be treated first. 
feasible         boolean           | Read-only boolean flag indicating whether the operationplan is violating any
                                     material, lead time or capacity constraints.
                                   | This is very handy in interpreting unconstrained plans.                                     
criticality      number            | The criticality is a read-only field, calculated by the planning engine. 
                                   | It represents an indication of the slack time in the usage of the purchase order.
                                   | A criticality of 0 indicates that the purchase order is on the critical path of one or more demands.
                                   | Higher criticality values indicate a delay of the purchase order will not immediately impact the shipment of any demand.                                   
                                   | A criticality of 999 indicates a purchase order that isn’t used at all to meet any demand.
                                   | Note that the criticality is independent of whether the customer demand will be shipped on time or not.
delay            duration          | The delay is a read-only field, calculated by the planning engine.
                                   | It compares the end data of the purchase order with the latest possible end date to ship all demands it feeds on time.
================ ================= =================================================================================================================================                            
