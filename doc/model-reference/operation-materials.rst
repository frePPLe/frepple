===================
Operation materials
===================

Operation materials are used to model the consumption and production of
material by operations.

If an operation Op is consuming 2 units of part A and 1 unit of part B to produce 3 units of
part C, then this table should contain three records:

=========    ========      ====      =====
operation    quantity      item      type
=========    ========      ====      =====
Op           -2            A         Start
Op           -1            B         Start
Op           3             C         End
=========    ========      ====      =====

If the same operation produces 1 units of part C you can leave out the third
record. It's implicitly assumed from the item field in the operation table.

=========    ========      ====      =====
operation    quantity      item      type
=========    ========      ====      =====
Op           -2            A         Start
Op           -1            B         Start
=========    ========      ====      =====

Different types are available:

* | **start**:
  | Consume (or produce) material at the start of a manufacturing order, right
    after any setup time on the loaded resource has been completed.
  | The quantity consumed or produced is proportional to the quantity of the
    manufacturing order.

* | **end**:
  | Produce (or consume) material at the end of a manufacturing order.
  | The quantity consumed or produced is proportional to the quantity of the
    manufacturing order.

* | **transfer_batch**:
  | Consume (or produce) material in a number of batches of fixed size
    at various moments during the total duration of the manufacturing order
    (not including the setup time on the loaded resource).
  | This feature is deprecated. Use
    :doc:`operation dependencies </model-reference/operation-dependencies>`
    or :doc:`operation material offsets </model-reference/operation-materials>`
    instead.

=============== ================= ===========================================================
Field           Type              Description
=============== ================= ===========================================================
item            item              | Material being consumed or produced.
                                  | This is a required field.
operation       operation         | Operation to which the material flow is associated.
                                  | This is a required field.
location        location          | Optional location where the material is consumed or produced.
                                  | This field is empty by default, indicating that the
                                    operation's location is used.
                                  | Only in exceptional cases where the material is to
                                    be consumed or produced at a different location
                                    should this field be filled.                    
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
                                    batches to 50 per manufacturing order.
                                  | This field is deprecated.
offset          duration          | Time offset relative to the start or end date of the manufacturing
                                    order for the material production or consumption.
                                  | Eg offset is 1 day for a flow of type 'end'
                                    -> Material is produced 1 day after the end of the manufacturing order
                                    -> This can be used to model a cooldown, drying or testing time.
                                  | Eg offset is -1 day for a flow of type 'start'
                                    -> Material is consumed 1 day before the start of the manufacturing order
                                    -> This can be used to model a material preparation or picking time.
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
