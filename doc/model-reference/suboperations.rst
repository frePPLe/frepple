=============
Suboperations
=============

Suboperations apply to operations of type operation_routing, operation_alternate,
operation_split.

Each of these operation types have child operations belonging to them, as defined in this table.

================ ================= ===========================================================
Field            Type              Description
================ ================= ===========================================================
operation        operation         Sub-operation.
owner            operation         Parent operation.
priority         integer           | For alternate operations: Priority of this alternate.
                                   | For routing operations: Sequence number of the step.
                                   | For split operations: Proportion of the demand planned
                                     along this suboperation.
                                   | Lower numbers indicate higher priority.
                                   | When the priority is equal to 0, this alternate is
                                     considered unavailable and it can’t be used for planning.
                                   | Default value is 1.
effective_start  dateTime          Earliest allowed end date for using this suboperation.
effective_end    dateTime          Latest allowed end date for using this suboperation.
================ ================= ===========================================================

  .. Important::

   This table is now deprecated.

   All information can now be defined in the operation table.

   * **Old data model**:

     Operation table:

     ============ ========== ========= ================ ==============
     Name         Type       Priority  Effective start  Effective end
     ============ ========== ========= ================ ==============
     Paint        routing
     Apply paint  time_per
     Dry paint    fixed_time
     Make X       alternate
     Make X Alt1  time_per
     Make X Alt2  time_per
     ============ ========== ========= ================ ==============

     Suboperation table:

     ============ ============ ======== =============== =============
     Operation    Suboperation Priority Effective-start Effective-end
     ============ ============ ======== =============== =============
     Paint        Apply paint  1
     Paint        Dry paint    2
     Make X       Make X Alt1  1                        2020-01-01
     Make X       Make X Alt2  2        2019-12-01
     ============ ============ ======== =============== =============

   * **New data model**:

     Operation table:

     ============ ========== ======== ================ ============= ========
     Name         Type       Priority  Effective-start Effective-end Owner
     ============ ========== ======== ================ ============= ========
     Paint        routing
     Apply paint  time_per   1                                       Paint
     Dry paint    fixed_time 2                                       Paint
     Make X       alternate
     Make X Alt1  time_per   1                          2020-01-01   Make X
     Make X Alt2  time_per   2         2019-12-01                    Make X
     ============ ========== ======== ================ ============= ========
