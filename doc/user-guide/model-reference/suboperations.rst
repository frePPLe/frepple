=============
Suboperations
=============

Suboperations apply to operations of type operation_routing, operation_alternate,
operation_split.

Each of these refer to child-operations.

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
