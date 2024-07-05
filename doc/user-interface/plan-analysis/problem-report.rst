==============
Problem report
==============

This screen shows a list of issues requiring the planner’s attention.

Each entity type has it’s own set of exceptions:

* **Demand**:

  * | **unplanned**:
    | No plan exists yet to satisfy this demand.

  * | **excess**:
    | A demand is planned for more than the requested quantity.

  * | **short**:
    | A demand is planned for less than the requested quantity.

  * | **late**:
    | A demand is satisfied later than the accepted tolerance after its due date.

  * | **early**:
    | A demand is planned earlier than the accepted tolerance before its due date.

  * | **invalid data**:
    | Some data problem prevents this object from being planned.

* **Resource**:

  * | **overload**:
    | A resource is being overloaded during a certain period of time.

  * | **underload**:
    | A resource is loaded below its minimum during a certain period of time.

* **Buffer**:

  * | **material shortage**:
    | A buffer is having a material shortage during a certain period of time.

  * | **invalid data**:
    | Flagged when a buffer has no ways of replenishment or too many.

* **Operation**:

  * | **before current**:
    | Flagged when an operation is being planned in the past.
    | For operations in the status approved or proposed, the start date is before the
      current date of the plan.
    | For operations in the status confirmed, the end date is before
      the current date of the plan (ie they are overdue and should have been finished
      already).

  * | **before fence**:
    | Flagged when an operation in the status approved or proposed
      is being planned before its fence date, i.e. it starts 1) after the current date of
      the plan, 2) it starts before the current date of the plan plus the release fence of
      the operation, and 3) the status is approved or proposed.

  * | **precedence**:
    | Flagged when the sequence of two operations within a routing isn't respected.

============ ==============================================================================
Field        Description
============ ==============================================================================
name         Problem type.
description  Description of the problem.
weight       | A number expressing the seriousness of the problem.
             | Sorting on this field allows the user to focus on the most important
               problems first.
start        Date at which the problem starts.
end          Date at which the problem ends.
============ ==============================================================================

+--------------------------------+
| Related permissions            |
+================================+
| Can view problem report        |
+--------------------------------+

.. image:: ../_images/problem-report.png
   :alt: Problem report

