====================
Manufacturing orders
====================

This table contains the manufacturing orders of your supply chain, either proposed by frePPLe or confirmed.

This table is populated with new proposed manufacturing orders when frePPLe generates a plan.
It is also possible to load manufacturing orders that are already approved or confirmed in your ERP
system.

================== ================= =================================================================================================================================
Field              Type              Description
================== ================= =================================================================================================================================
reference          string            | Unique identifier for the manufacturing order.
                                     | For approved or confirmed manufacturing orders that are imported from your ERP system this field should be
                                       populated with the identifier the ERP generated.
                                     | For manufacturing orders newly proposed by frePPLe, a unique numeric identifier will automatically be generated.
operation          operation         The operation to perform.
start date         DateTime          The date when the operation is starting.
end date           DateTime          The date when the operation is ending.
quantity           number            The quantity to manufacture.
quantity_completed number            | The quantity already manufactured.
                                     | It is only used when the status is "approved" or "confirmed".
batch              string            | Blank/unused for make-to-stock items.
                                     | Identification of the batch for make-to-order items.
status             non-empty string  This field should have one of the following values:

                                     * | proposed:
                                       | The manufacturing order is proposed by frePPLe to meet the plan (optimization output).

                                     * | approved:
                                       | The manufacturing order is present in the ERP system but can still be rescheduled by frePPLe (optimization input).

                                     * | confirmed:
                                       | The manufacturing order is confirmed, it has been populated in your ERP system (optimization input).

                                     * | completed:
                                       | The manufacturing order has been executed, but the stock hasn't been increased yet (optimization input).

                                     * | closed : The manufacturing order has been completed. It is ignored for planning.

demands            list              | The demand(s) (and quantity) pegged to the manufacturing order.
                                     | This is a read-only computed field.
end items          list              | The end item(s) (and quantity) pegged to the manufacturing order.
                                     | This is a read-only computed field.
demand             demand            | The field marks this manufacturing order as the shipment delivery
                                       of a demand.
                                     | This is only needed in very exceptional use case. 99% of frepple configurations
                                       to not require this field to be specified.
owner              number            In the case of a suboperation, the identifier of the operation calling this suboperation.
inventory status   number            | The Inventory Status is a calculated field that highlights the urgency of the manufacturing order.
                                     | The cells have a background color that can be green, orange or red. Sorting
                                     | the manufacturing orders using the Inventory Status column (red ones first) allows the planner to
                                     | immediately focus on the manufacturing orders that should be treated first.
feasible           boolean           | Read-only boolean flag indicating whether the manufacturing order is violating any
                                       material, lead time or capacity constraints.
                                     | This is very handy in interpreting unconstrained plans.
criticality        number            | The criticality is a read-only field, calculated by the planning engine.
                                     | It represents an indication of the slack time in the usage of the manufacturing order.
                                     | A criticality of 0 indicates that the manufacturing order is on the critical path of one or more demands.
                                     | Higher criticality values indicate a delay of the manufacturing order will not immediately impact the shipment of any demand.
                                     | A criticality of 999 indicates a manufacturing order that isn’t used at all to meet any demand.
                                     | Note that the criticality is independent of whether the customer demand will be shipped on time or not.
delay              duration          | The delay is a read-only field, calculated by the planning engine.
                                     | It compares the end data of the manufacturing order with the latest possible end date to ship all demands it feeds on time.
remark             string            | A free text field for additional information.                                   
================== ================= =================================================================================================================================
