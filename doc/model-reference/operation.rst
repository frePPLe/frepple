=========
Operation
=========

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

* | `Operation_split`_ (new in 2.2):
  | This operation type plans the demand proportionally over a number of
    sub-operations, using some pre-defined percentages.

* | `Operation_routing`_:
  | Models a sequence a number of ‘step’ sub-operations, to be executed
    sequentially.

**Fields**

================ ================= ===========================================================
Field            Type              Description
================ ================= ===========================================================
name             non-empty string  | Name of the operation.
                                   | This is the key field and a required attribute.
description      string            Free format description.
category         string            Free format category.
subcategory      string            Free format subcategory.
location         location          | Location of the operation.
                                   | Default is null.
                                   | The working hours and holidays for the operation are
                                     taken from the ‘available’ calendar of the location.
fence            duration          | Time window from the current date of the plan during
                                     which all operationplans are expected to be
                                     frozen/released.
                                   | When the “FENCE” constraint is enabled in the solver, it
                                     won’t create any new operation plans in this time fence.
                                     Only the externally supplied and locked operationplans will
                                     then exist in this time window.
size_minimum     positive double   | A minimum quantity for operationplans.
                                   | The default value is 1.
                                   | A request for a lower, non-zero quantity will be rounded up.
size_minimum_    calendar          | A calendar to define the minimum size of operationplans
 calendar                            when this value varies over time. The end date of the
                                     operationplan determines which date we use as lookup in the
                                     calendar.
                                   | If this field is used, the size_minimum field is ignored.
size_multiple    positive double   A lotsize quantity for operationplans.
size_maximum     positive double   | The maximum quantity for operationplans.
                                   | Note that this value limits the size of individual
                                     operationplans. The solver can create multiple operationplans
                                     of this maximum size, so this value does NOT constrain the
                                     total planned quantity on the operation. The field is
                                     useful to break big operationplans in smaller ones.
cost             double            | The cost of executing this operation, per unit of the
                                     operation_plan.
                                   | Depending on what the operation models, this
                                     represents transportation costs, manufacturing costs,
                                     procurement costs, delivery costs, etc...
                                   | The raw material cost and the resource usage cost are added
                                     to this cost and should not be included in this value.
                                   | The default value is 0.
posttime         duration          | A post-operation time, used as a buffer for uncertain
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
detectproblems   boolean           | Set this field to false to skip problem detection on
                                     this operation.
                                   | The default value is true.
loads            list of load      A list of all resources loaded by this operation.
flows            list of flow      A list of all buffers where material is consumed from or
                                   produced into.
level            integer           | Indication of how upstream/downstream this entity is
                                     situated in the supply chain.
                                   | Lower numbers indicate the entity is close to the end
                                     item, while a high number will be shown for components
                                     nested deep in a bill of material.
                                   | The field is export-only.
cluster          integer           | The network of entities can be partitioned in completely
                                     independent parts. This field gives the index for the
                                     partition this entity belongs to.
                                   | The field is export-only.
hidden           boolean           Marks entities that are considered hidden and are normally
                                   not shown to the end user.
action           A/C/AC/R          | Type of action to be executed:
                                   | A: Add an new entity, and report an error if the entity
                                     already exists.
                                   | C: Change an existing entity, and report an error if the
                                     entity doesn’t exist yet.
                                   | AC: Change an entity or create a new one if it doesn’t
                                     exist yet. This is the default.
                                   | R: Remove an entity, and report an error if the entity
                                     doesn’t exist.
================ ================= ===========================================================

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

* A variable duration, computed as the operationplan quantity multiplied by
  a DURATION_PER.

================ ================= ===========================================================
Field            Type              Description
================ ================= ===========================================================
duration         duration          | Fixed component of the duration of the operationplan.
                                   | The default value is 0.
duration_per     duration          | Variable component of the duration of the operationplan.
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
                                        resources and buffers.

                                    * | MINPENALTY
                                      | Select the alternate which gives the lowest penalty.
                                      | The penalty includes the penalty of all penalties
                                        incurred in the upstream plan.

                                    * | MINCOSTPENALTY
                                      | Select the alternate which gives the lowest sum of
                                        the cost and penalty.
                                      | The sum is computed for the complete upstream path.
suboperations    List of           List of alternate sub-operations.
                 suboperation
================ ================= ===========================================================


Suboperation fields:

================ ================= ===========================================================
Field            Type              Description
================ ================= ===========================================================
operation        operation         Sub-operation.
owner            operation         Parent operation
priority         integer           | For alternate operations: Priority of this alternate.
                                   | For routing operations: Sequence number of the step.
                                   | For split operations: Proportion of the demand planned
                                     along this suboperation.
                                   | Lower numbers indicate higher priority.
                                   | When the priority is equal to 0, this alternate is
                                     considered unavailable and it can’t be used for planning.
                                   | Default value is 1.
effective_start  dateTime          Earliest allowed start date for using this suboperation.
effective_end    dateTime          Latest allowed end date for using this suboperation.
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
                 suboperation      | See above for the definition of the suboperation.
================ ================= ===========================================================


Operation_routing
-----------------

Models a sequence a number of ‘step’ sub-operations, to be executed sequentially.

================ ================= ===========================================================
Field            Type              Description
================ ================= ===========================================================
suboperations    List of           | List of sub-operations to execute in sequence.
                 suboperation      | See above for the definition of the suboperation.
================ ================= ===========================================================

**Example XML structures**

Adding or changing operations

.. code-block:: XML

    <plan>
      <operations>
        <operation name="buy item X from supplier" xsi:type="operation_fixed_time">
          <duration>P1D</duration>
        </operation>
        <operation name="make item X" xsi:type="operation_time_per">
          <duration>PT1H</duration>
          <duration_per>PT5M</duration_per>
        </operation>
        <operation name="make or buy item X" xsi:type="operation_alternate">
          <suboperations>
            <suboperation>
              <operation name="make item X" />
              <priority>1</priority>
            </suboperation>
            <suboperation>
              <operation name="buy item X from supplier" />
              <priority>2</priority>
            </suboperation>
          </suboperations>
        </operation>
        <operation name="make subassembly" xsi:type="operation_routing">
          <suboperations>
            <suboperation>
              <operation name="make subassembly step 1" duration="PT1H"/>
              <priority>1</priority>
            </suboperation>
            <suboperation>
              <operation name="make subassembly step 2" duration="PT5M"/>
              <priority>2</priority>
            </suboperation>
          </suboperations>
        </operation>
      </operations>
    </plan>

Deleting an operation

.. code-block:: XML

    <plan>
       <operations>
          <operation name="make item X" action="R"/>
       </operations>
    </plan>

**Example Python code**

Adding or changing operations

::

    op1 = frepple.operation_fixed_time(name="buy item X from supplier", duration=24*3600)
    op2 = frepple.operation_time_per(name="make item X", duration=3600, duration_per=60*5)
    op3 = frepple.operation_alternate(name="make or buy item X")
    frepple.suboperation(owner=op3, operation=op1, priority=1)
    frepple.suboperation(owner=op3, operation=op2, priority=2, effective_end=datetime.datetime(2009,10,10))
    op4 = frepple.operation_routing(name="make subassembly")
    frepple.suboperation(
      owner=op3,
      operation=frepple.operation_fixed_time(name="make subassembly step 1", duration=3600),
      priority=1
      )
    frepple.suboperation(
      owner=op3,
      operation=frepple.operation_fixed_time(name="make subassembly step 2", duration=300),
      priority=2
      )


Deleting an operation

::

    frepple.operation(name="make item X", action="R")

Iterate over operations, loads and flows

::

    for o in frepple.operations():
      print("Operation:", o.name, o.description, o.category)
      for l in o.loads:
        print("  Load:", l.resource.name, l.quantity, l.effective_start, l.effective_end)
      for l in o.flows:
        print("  Flow:", l.buffer.name, l.quantity, l.effective_start, l.effective_end)
