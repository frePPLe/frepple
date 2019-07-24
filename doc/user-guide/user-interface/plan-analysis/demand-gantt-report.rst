===================
Demand Gantt report
===================

This report shows a graphical representation of the complete plan of a certain demand. The plan show 
all planned activities from raw material purchase orders, distribution orders between locations, 
manufacturing operations, and also the delivery order to the customer.

In the Gantt chart the current date is marked as a black line, and the due date of the demand is 
marked as a red line.

================= ==============================================================================
Field             Description
================= ==============================================================================
Depth             Depth of this operation in the supply path: 0 = delivery, and increases with
                  every level deeper in the bill of distribution and bill of material.
Operation         Operation being planned.
Resource          Resource(s) being loaded.
Quantity          | Quantity allocated to the demand.
                  | In the Gantt chart the operations are shown in detail. Some of the
                    operations may be only partly allocated to the demand being displayed.
================= ==============================================================================

.. image:: ../_images/demand-gantt-report.png
   :alt: Demand Gantt report
