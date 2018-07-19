===================
Operation materials
===================

Operation materials are used to model the consumption and production of 
material from buffers by operations.

Different types are available:

* | **start**:
  | Consume (or produce) material at the start of an operationplan, right
    after any setup time on the loaded resource has been completed.
  | The quantity consumed or produced is proportional to the quantity of the
    operationplan.

* | **end**:
  | Produce (or consume) material at the end of an operationplan.
  | The quantity consumed or produced is proportional to the quantity of the
    operationplan.
    
* | **transfer_batch**:
  | Consume (or produce) material in a number of batches of fixed size
    at various moments during the total duration of the operationplan
    (not including the setup time on the loaded resource).

**Fields**

=============== ================= ===========================================================
Field           Type              Description
=============== ================= ===========================================================
buffer          buffer            | Buffer from which material will be moved or transferred
                                    into.
                                  | This is a required field.
operation       operation         | Operation to which the material flow is associated.
                                  | This is a required field.
quantity        double            | Material quantity being consumed or produced per unit of
                                    the manufacturing order.
                                  | Default value is 1.0.
quantity_fixed  double            | Fixed material consumption or production per manufacturing
                                    order, independent of the size of the manufacturing order.
                                  | This is useful to model a constant scrap rate for calibration
                                    or testing, modeling a throw-away prodcution tool, etc...
                                  | Default value is 0.0.
transferbatch   double            | Batch size by in which material is produced or consumed.
                                  | Only relevant for flows of type batch_transfer.
                                  | The default value is null, in which case we default to 
                                    produce at the end when the quantity is positive, or 
                                    consume at the start when the quantity is negative.
                                  | To protect against a big impact on performance and 
                                    memory footprint we limit the number of material transfer
                                    batches to 50 per operationplan.                            
effective_start dateTime          | Date after which the material consumption is valid.
                                  | Before this date the planned quantity is always 0.
effective_end   dateTime          | Date at which the material consumption becomes invalid.
                                  | After this date (and also at the exact date) the planned
                                    quantity is always 0.
priority        integer           | Priority of the flow, used in case of alternate flows.
                                  | The default is 1.
                                  | Lower numbers indicate more preferred flows.
name            non-empty string  | Optional name of the flow.
                                  | All flows with the same name are considered to be
                                    alternates of each other.
search          string            | Defines the order of preference among the alternate flows.
                                  | The valid choices are:

                                  * | PRIORITY
                                    | Select the alternate with the lowest priority number.
                                    | This is the default.

                                  * | MINCOST
                                    | Select the alternate which gives the lowest cost.
                                    | The cost includes the cost of all upstream operations,
                                      resources and buffers.

                                  * | MINPENALTY
                                    | Select the alternate which gives the lowest penalty.
                                    | The penalty includes the penalty of all penalties
                                      incurred in the upstream plan along the flow.

                                  * | MINCOSTPENALTY
                                    | Select the alternate which gives the lowest sum of
                                      the cost and penalty.
                                    | The sum is computed for the complete upstream path.

=============== ================= ===========================================================
