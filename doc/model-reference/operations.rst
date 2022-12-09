==========
Operations
==========

An operation represents an activity: these consume and produce material,
take time and also require capacity.

An operation consumes and produces material, modeled through flows.

An operation requires capacity, modeled through loads.

Different operation types exist:

* | `Operation_fixed_time`_:
  | Models an operation with a duration that is independent of the quantity.
    A good example is a transport or a procurement operation.

* | `Operation_time_per`_:
  | Models an operation where the duration increases linear with the quantity.
    A good example is a manufacturing operation where the duration is
    determined by the production rate of a machine.

* | `Operation_alternate`_:
  | Models a choice between different operations.
  | FrePPLe automatically builds an alternate operation if the same item-location
    can be replenished in multiple ways: eg multiple operations to produce an item,
    multiple vendors for an item, multiple source locations for a distribution order,
    a choice between making the item or purchasing it, etc... **Explicitly adding
    alternate operations in your model is no longer required.**

* | `Operation_split`_:
  | This operation type plans the demand proportionally over a number of
    sub-operations, using some pre-defined percentages.

* | `Operation_routing`_:
  | Models a sequence a number of step sub-operations, to be executed
    sequentially.

====================== ================= ===========================================================
Field                  Type              Description
====================== ================= ===========================================================
name                   non-empty string  | Unique name of the operation.
                                         | This is the key field and a required attribute.

item                   item              | Reference to the item being produced.
                                         | We will try to determine the item as the producing records
                                           from the operation-material records: if an operation has
                                           only a single operation-material with a positive quantity
                                           then we use its item as the item of the operation.
                                         | Only in exceptional modeling situations should you worry
                                           about setting this field yourself. Eg when an operation
                                           produces multiple items.

location               location          Location of the operation.

                                         The working hours and holidays for the operation are
                                         calculated as the intersection of:

                                         - the availability calendar of the operation.
                                         - the availability calendar of the operation's location.
                                         - the availability calendar of all resources loaded by the
                                           operation.
                                         - the availability calendar of the location of all resources
                                           loaded by the operation.

                                         Default is null.

available              calendar          A calendar specifying the working hours for the operation.

                                         The working hours and holidays for the operation are
                                         calculated as the intersection of:

                                         - the availability calendar of the operation.
                                         - the availability calendar of the operation's location.
                                         - the availability calendar of all resources loaded by the
                                           operation.
                                         - the availability calendar of the location of all resources
                                           loaded by the operation.

                                         Default is null.

effective_start        dateTime          Date when the operation becomes valid.

                                         The value of this field is only used when the item field is
                                         populated on the operation. Only then is the operation registered
                                         as a replenishment method for the item at this location.

effective_end          dateTime          Date after which the operation becomes invalid.

                                         The value of this field is only used when the item field is
                                         populated on the operation. Only then is the operation registered
                                         as a replenishment method for the item at this location.

priority               integer           Priority of this operation to produce the specified item.

                                         This is useful when there are multiple operations
                                         producing the same item-location, or the same item-location
                                         can also be replenished with :doc:`purchase orders<item-suppliers>`
                                         and/or :doc:`distribution orders<item-distributions>`.

                                         The value of this field is only used when the item field is
                                         populated on the operation. Only then is the operation registered
                                         as a replenishment method for the item at this location.

                                         When the priority is 0, the operation is not automatically used
                                         during planning. Only a planner can manually create manufacturing
                                         orders on it.

description            string            Free format description.

category               string            Free format category.

subcategory            string            Free format subcategory.

fence                  duration          Time window from the current date of the plan during
                                         which all manufacturing orders are expected to be
                                         frozen/released. The duration refers to available time (i.e.
                                         respecting the working hours and holiday calendars mentioned above).

                                         When the 'FENCE' constraint is enabled in the solver, it
                                         won't create any new operation plans in this time fence.
                                         Only the externally supplied and locked manufacturing orders
                                         will then exist in this time window.

                                         By default the fence is 0, we can plan operations to be
                                         started immediately.

batchwindow            duration          The solver algorithm will scan for opportunities to create
                                         batches within this time window before and after the
                                         requirement date.

                                         By default the batching windows is 0, which disables this
                                         feature.

size_minimum           positive double   A minimum quantity for manufacturing orders.

                                         A request for a lower, non-zero quantity will be rounded up.

                                         This field also influences the alternate choices when multiple
                                         operations are available to produce an item. The planning
                                         algorithm will try to plan on those alternates where the
                                         requirement is between the size_minimum and size_maximum.

                                         The default value is 1.

size_minimum_calendar  calendar          A calendar to define the minimum size of manufacturing orders
                                         when this value varies over time. The end date of the
                                         manufacturing orders determines which date we use as lookup in the
                                         calendar.

                                         If both the size_minimum and size_minimum_calendar are
                                         specified, we use the highest value.

size_multiple          positive double   A multiple quantity for manufacturing orders.
size_maximum           positive double   | The maximum quantity for manufacturing orders.

                                         | Note that this value limits the size of individual
                                           manufacturing orders. The solver can create multiple manufacturing
                                           orders of this maximum size, so this value does NOT constrain the
                                           total planned quantity on the operation. The field is
                                           useful to break big manufacturing orders in smaller ones.

                                         | This field also influences the alternate choices when multiple
                                           operations are available to produce an item. The planning
                                           algorithm will try to plan on those alternates where the
                                           requirement is between the size_minimum and size_maximum.

cost                   double            | The cost of executing this operation, per unit of the
                                           operation_plan.

                                         | Depending on what the operation models, this
                                           represents transportation costs, manufacturing costs,
                                           procurement costs, delivery costs, etc...

                                         | The raw material cost and the resource usage cost are added
                                           to this cost and should not be included in this value.

                                         | The default value is 0.
posttime               duration          | A post-operation time, used as a buffer for uncertain
                                           capacity or operation duration.

                                         | The solver will try to respect this time as a soft
                                           constraint. Ie when required to meet demand on time the
                                           post-operation time can be violated.

                                         | Resources are not loaded during the post-operation time.

                                         | This field is used to model time-based safety stock
                                           targets, aka days of inventory. It is then set for the
                                           producing operation of a certain buffer.

                                         | If you want to model a safety stock quantity, you can use
                                           the minimum or minimum_calendar fields on the buffer.
====================== ================= ===========================================================

Operation_fixed_time
--------------------

Models an operation with a fixed duration regardless of the quantity.
E.g. a transport operation.

This is the default operation type.

================ ================= ===========================================================
Field            Type              Description
================ ================= ===========================================================
duration         duration          | Duration of the operation.
                                   | The default value is 0.
================ ================= ===========================================================

Operation_time_per
------------------

Models an operation where the duration changes linear with the quantity.
E.g. a production operation.

The total duration of the operation plan is the sum of:

* A fixed DURATION.

* A variable duration, computed as the manufacturing order quantity multiplied by
  a DURATION_PER.

================ ================= ===========================================================
Field            Type              Description
================ ================= ===========================================================
duration         duration          | Fixed component of the duration of the manufacturing
                                     order.
                                   | The default value is 0.
duration_per     duration          | Variable component of the duration of the manufacturing
                                     order.
                                   | The default value is 0.
================ ================= ===========================================================

Operation_alternate
-------------------

Models a choice between different operations. It has a list of alternate
sub-operations listed, each with a priority.

Operation minimum, multiple and maximum size constraints of each individual
alternate sub-operation are respected. The ones on the operation_alternate
operation itself are ignored.

================ ================= ===========================================================
Field            Type              Description
================ ================= ===========================================================
search           string            Defines the order of preference among the alternate loads.

                                   The valid choices are:

                                   * | PRIORITY
                                     | Select the alternate with the lowest priority number.
                                     | This is the default.

                                   * | MINCOST
                                     | Select the alternate which gives the lowest cost.
                                     | The cost includes the cost of all upstream operations,
                                        resources and materials.

                                   * | MINPENALTY
                                     | Select the alternate which gives the lowest penalty.
                                     | The penalty includes the penalty of all penalties
                                       incurred in the upstream plan.

                                   * | MINCOSTPENALTY
                                     | Select the alternate which gives the lowest sum of
                                       the cost and penalty.
                                     | The sum is computed for the complete upstream path.
suboperations    List of           | List of alternate sub-operations.
                 suboperation      | See :doc:`suboperations`
================ ================= ===========================================================

Operation_split
---------------

This operation type plans the demand proportionally over a number of operations.
It has a list of alternate sub-operations listed, each with a percentage.

The percentages are treated as a hard constraint by the solver. This means that
if one of the alternates can’t deliver the requested quantity, the complete split
operation is considered as infeasible. (If we’ld treat it as a soft constraint,
we would distribute the infeasible quantity among the other alternates).

Minimum, multiple and maximum size constraints on the sub-operations are respected.
This means that we can end up with a split that deviates to some extent from the
specified percentages.

The percentages don't need to add up to 100%. We use the relative ratio's of
the sub-operations.

================ ================= ===========================================================
Field            Type              Description
================ ================= ===========================================================
suboperations    List of           | List of sub-operations to divide the plan across.
                 suboperation      | See :doc:`suboperations`
================ ================= ===========================================================


Operation_routing
-----------------

Models a sequence a number of ‘step’ sub-operations, to be executed sequentially.

================ ================= ===========================================================
Field            Type              Description
================ ================= ===========================================================
suboperations    List of           | List of sub-operations to execute in sequence.
                 suboperation      | See :doc:`suboperations`
hard_posttime    Boolean           | A flag to mark whether the post-operation time of the
                                     routing steps should be used as a hard or soft constraint.
                                   | The default is false, i.e. a soft constraint.
                                   | Note that this field currently is not defined in the
                                     user interface or database. It is only available to
                                     customizations working in the planning engine.
================ ================= ===========================================================
