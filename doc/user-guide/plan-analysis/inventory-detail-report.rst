=======================
Inventory detail report
=======================

The report shows the details of all material production into and consumption from buffers.

================= ==============================================================================
Field             Description
================= ==============================================================================
Buffer            Buffer name.
Operation         Name of the operation producing or consuming material.
Quantity          Amount being produced (positive number) or consumed (negative number).
Date              | Date of the stock movement.
                  | Inventory that is reported as onhand at the start of the plan will be shown
                    with 1/1/1971 as date.
Onhand            Available inventory in the buffer after this particular stock movement.
Criticality       | Indication of the urgency of the operationplan.
                  | A criticality of 0 indicates that the operationplan is on the critical
                    path of one or more demands.
                  | Higher criticality values indicate a delay of the operationplan will
                    not immediately impact the delivery of any demand.
                  | A criticality of 999 indicates an operationplan that isn't used at all to
                    meet any demand.
Locked            Locked operationplans are frozen and can’t be touched during planning.
                  Such operationplans model for instance confirmed supplier deliveries,
                  work in progress operations, etc.
Operationplan     Identifier of the operation plan planning the stock movement.
================= ==============================================================================

.. image:: ../_images/inventory-detail-report.png
   :alt: Inventory detail report
