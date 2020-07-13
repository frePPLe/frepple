=======================
Operation detail report
=======================

The report shows the details of all manufacturing orders. It displays their start
date, end date and quantity.

================= ==============================================================================
Field             Description
================= ==============================================================================
Reference         Reference of this operation instance.
Operation         Name of the operation.
Quantity          Quantity of the manufacturing order.
Start date        Start date of the manufacturing order.
End date          | End date of the manufacturing orders.
                  | Note that in case of unavailable time, the difference between the start and
                    end date can be bigger than the specified duration of the operation. For
                    instance, if the weekends are modelled as unavailable time, an operation
                    with a duration of 1 day can start on friday 7AM and end on monday 7AM.
Feasible          | Boolean field indicating whether the manufacturing order is violating any
                    material, lead time or capacity constraints.
                  | This is very handy in interpreting unconstrained plans.
Criticality       | Indication of the urgency of the manufacturing order.
                  | A criticality of 0 indicates that the manufacturing order is on the critical
                    path of one or more demands.
                  | Higher criticality values indicate a delay of the manufacturing order will
                    not immediately impact the delivery of any demand.
                  | A criticality of 999 indicates an manufacturing order that isn't used at all to
                    meet any demand.
Status            Status of the manufacturing order:

                  - proposed: newly proposed by the planning tool
                  - approved: approved by the planner, but not yet launched in the ERP system
                  - confirmed: ongoing transaction, controlled by the ERP system and not changeable
                    in frePPLe
                  - closed: operation has finished
Unavailable       | Total unavailable time over the duration of the manufacturing order.
                  | Continuing on the above example, the unavailable time would be 2 days.
Owner             In case of nested manufacturing order this field shows the identifier of the
                  owning manufacturing order. This applies to operations of type "alternate" and
                  "routing".
================= ==============================================================================

.. image:: ../_images/operation-detail-report.png
   :alt: Operation detail report
