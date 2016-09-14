====================
Manufacturing Orders
====================

This table contains the manufacturing orders of your supply chain, either proposed by frePPLe or confirmed.

**Fields**

================ ================= =================================================================================================================================
Field            Type              Description
================ ================= =================================================================================================================================
operation        operation         The operation to perform.
start date       DateTime          The date when the operation is starting.
end date         DateTime          The date when the operation is ending.
quantity         number            The manufactured quantity.
status           non-empty string  | This field should have one of the following keywords :
                                   | proposed : The manufacturing order is proposed by frePPLe to meet the plan (optimization output).
                                   | approved : The manufacturing order has been reviewed by the user and is ready to be exported to your ERP system.
                                   | confirmed : The manufacturing order is confirmed, it has been populated in your ERP system (optimization input).
                                   | closed : The manufacturing order has been completed.
Demands          demand            The demand(s) (and quantity) pegged to the manufacturing order. This is a generated field.
Owner            number            In the case of a suboperation, the identifier of the operation calling this suboperation.
criticality      number            | The criticality is a number calculated by the optimization. This is a generated field.
                                   | It reprensents an indication of the urgency of the purchase order.
                                   | A criticality of 0 indicates that the purchase order is on the critical path of one or more demands.
                                   | Higher criticality values indicate a delay of the purchase order will not immediately impact the delivery of any demand.
                                   | A criticality of 999 indicates a purchase order that isn’t used at all to meet any demand.
================ ================= =================================================================================================================================                            
                                  
