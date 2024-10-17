======================
Operation dependencies
======================

This table defines relations between operations. This is used to represent the
following situations:

* | Define which **steps in a routing operation can be executed in parallel**.
  | By default routing steps are executed in sequence.
  | You use the dependencies to configure a non-sequential order of the steps.

* | Define relations between **different steps in a project-oriented business**.
  | In most manufacturing oriented business, a bill-of-material is used to define
    different levels in the product structure.
  | As an alternative for project-oriented businesses, this table allows you to
    directly link subprojects and tasks with each other, without defining
    intermediate items.

===================== ================= ===========================================================
Field                 Type              Description
===================== ================= ===========================================================
operation             operation         Operation.
blockedby             operation         This operation needs to be completed before the other
                                        operation can start.
quantity              double            | Defines the quantity relation between both operations.
                                        | Default value is 1, i.e. the quantity of both
                                          operations is identical.
safety_leadtime       duration          | Defines a desired time gap between both operations.
                                        | This time gap is a soft constraint. It can be compressed 
                                          to deliver an order faster.
                                        | Default is 0 seconds.
hard_safety_leadtime  duration          | Shortest time that must pass between both operations.
                                        | This time gap is a hard constraint.
                                        | Default is 0 seconds.
===================== ================= ===========================================================
