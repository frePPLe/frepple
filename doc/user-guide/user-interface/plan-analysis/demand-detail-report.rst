====================
Demand detail report
====================

The report shows the details of the deliveries planned for each demand. Late and short
deliveries can easily be identified.

================= ==============================================================================
Field             Description
================= ==============================================================================
Demand            Name of the demand.
Item              Requested item of the demand.
Customer          Customer of the demand.
Quantity          | Requested quantity.
                  | In case multiple deliveries are planned for a demand, the total requested
                  | quantity of the order is divided across the deliveries.
Planned quantity  | Quantity of this delivery.
                  | In case a certain demand is planned incompletely, a record will exist with
                  | an empty planned quantity. The neighbouring quantity field then shows the
                  | unplanned quantity.
Due date          Due date of the demand.
Planned date      Planned delivery date.
Operationplan     Identifier of the delivery operationplan.
================= ==============================================================================

.. image:: ../_images/demand-detail-report.png
   :alt: Demand detail report
