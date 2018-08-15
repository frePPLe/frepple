===============
Delivery orders
===============

The table contains all deliveries planned for each sales order or forecast.

This table is populated with new proposed deliveries when frePPLe generates a plan.
It is also possible to load deliveries that are already approved or confirmed in your ERP
system.

**Fields**

================= ================= =================================================================================================================================
Field             Type              Description
================= ================= =================================================================================================================================
reference         string            | Unique identifier for the delivery order.
                                    | This field will be empty for newly proposed delivery orders, but for approved or confirmed purchase orders that
                                      already exist in the ERP system this field should be populated with the identifier the ERP generated.
demand            demand            Name of the demand.
item              item              | Item being shipped to the customer.
                                    | This is normally the same as the item specified on the sales order, but we
                                      could also ship an alternate item.
customer          customer          | Customer of the sales order.
                                    | This is an export-only field.
quantity          number            Shipped quantity.                                    
demand quantity   number            | Quantity of this demand.
                                    | This is an export-only field.
start date        datetime          Starting date of shipment, aka ex-works date.
end date          datetime          Planned delivery date at the customer.
due date          datetime          | Due date of the demand.
                                    | This is an export-only field.
delay             duration          Time difference between the end date of the delivery and the due date of the sales order.                               
status            non-empty string  | This field should have one of the following keywords:
                                    | proposed : The manufacturing order is proposed by frePPLe to meet the plan (optimization output).
                                    | approved : The manufacturing order is present in the ERP system but can still be rescheduled by frePPLe (optimization input).
                                    | confirmed : The manufacturing order is confirmed, it has been populated in your ERP system (optimization input).
                                    | closed : The manufacturing order has been completed.
================= ================= =================================================================================================================================
