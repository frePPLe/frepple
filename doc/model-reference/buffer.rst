======
Buffer
======

A buffer is a storage for a item. It represents a place where inventory of an
item is kept. It’s often called SKU.

Different types of buffers exist:

* | `Buffer_default`_:
  | The default buffer uses an “producing” operation to replenish it with
    additional material.

* | `Buffer_procure`_:
  | A buffer that is replenished by a supplier. A number of parameters
    control the re-ordering policy: classic re-order point, fixed time
    ordering, fixed quantity ordering, etc…

* | `Buffer_infinite`_:
  | An infinite buffer has an infinite supply of the material is available.

**Fields**

================ ================= ===========================================================
Field            Type              Description
================ ================= ===========================================================
name             non-empty string  | Name of the buffer.
                                   | This is the key field and a required attribute.
description      string            Free format description.
category         string            Free format category.
subcategory      string            | Free format subcategory.
                                   | If this field is set to 'tool', the field 'tool' will
                                     automatically be set to true.
owner            buffer            | Buffers can be organized in a hierarchical tree.
                                   | This field defines the parent buffer.
                                   | No specific planning behavior is currently linked to such
                                     a hierarchy.
members          list of buffer    | Buffers can be organized in a hierarchical tree.
                                   | This field defines a list of child buffers.
location         location          | Location of the buffer.
                                   | Default is null.
                                   | The working hours and holidays for the buffer are taken
                                     from the ‘available’ calendar of the location.
item             item              | Item being stored in the buffer.
                                   | Default is null.
onhand           double            | Inventory level at the start of the time horizon.
                                   | Default is 0.
minimum          double            | Desired minimum inventory, aka safety stock.
                                   | Use this field if the safety stock doesn't change over
                                     time.
                                   | The solver treats this as a soft constraint, ie it tries
                                     to meet this inventory level but will go below the
                                     minimum level if required to meet the demand.
                                   | A problem is reported when the inventory drops below
                                     this level.The safety stock target is expressed as a
                                     quantity. If you want to define a safety stock target
                                     as a time value (aka days of inventory), you can set a
                                     post-operation timeon the producing operation of the
                                     buffer.
minimum_calendar calendar          | Refers to a calendar storing the desired minimum inventory
                                     level, aka safety stock.
                                   | Use this field when the minimum inventory level is varying
                                     over time. Otherwise use the minimum field. If both fields
                                     are specified, the minimum field is ignored.
maximum          double            | Refers to a calendar storing the maximum inventory level.
                                   | This field is not used by the solver.
                                   | A problem is reported when the inventory level is higher
                                     than this limit.
maximum_calendar calendar          | Refers to a calendar storing the maximum inventory level.
                                   | Use this field when the maximum inventory level is varying
                                     over time. Otherwise use the maximum field. If both fields
                                     are specified, the maximum field is ignored.
mininterval      duration          | Replenishment batching window.
                                   | When multiple replenishments for the buffer are planned
                                     closer than the time window specified in this field, the
                                     solver algorithm will try to combine them into a single
                                     larger replenishment.
                                   | The default value of the batching window is -1, which keeps
                                     the batching logic deactivated.
producing        operation         | This operation will be instantiated by the solver to
                                     replenish the buffer with additional material.
                                   | You can specify this operation explicitly.
                                   | Or, you can leave this field blank and let the system
                                     automatically create an operation. The generated operation
                                     is using the ItemSupplier and ItemDistribution models as
                                     input.
                                   | In versions before 3.0 the only way was the explicit
                                     construction of the operation to populate this field. From
                                     version 3.0 onwards we recommend to use the auto-generated
                                     operations, unless you have some very specific modeling
                                     requirements.
detectproblems   boolean           | Set this field to false to supress problem detection on this
                                     buffer.
                                   | Default is true.
flows            list of flow      Defines material flows consuming from or producing into this
                                   buffer.
flowplans        list of flowplan  | This field is populated during an export with the plan results
                                     for this buffer. It shows the complete inventory profile.
                                   | The field is export-only.
                                   | The description of the flowplan model is included in the
                                     section on operationplan.
tool             boolean           | A flag to mark buffers that are actually representing a tool.
                                   | Default is false.
                                   | The impact on the planning results is visible in the
                                     pegging and criticality calculations.
level            integer           | Indication of how upstream/downstream this entity is situated
                                     in the supply chain.
                                   | Lower numbers indicate the entity is close to the end item,
                                     while a high number will be shown for components nested deep
                                     in a bill of material.
                                   | The field is export-only.
cluster          integer           | The network of entities can be partitioned in completely
                                     independent parts. This field gives the index for the
                                     partition this entity belongs to.
                                   | The field is export-only.
hidden           boolean           Marks entities that are considered hidden and are normally not
                                   shown to the end user.
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

Buffer_default
--------------

The default buffer uses an “producing” operation to replenish it.
No fields are defined in addition to the ones listed above.

Buffer_procure
--------------

A procurement buffer is replenished by a supplier.

A number of parameters control the re-ordering policy: classic re-order point,
fixed time ordering, fixed quantity ordering, etc...

The fields LEADTIME, MININVENTORY and MAXINVENTORY define a replenishment with
a classical re-orderpoint policy. The inventory profile will show the typical
sawtooth shape.

The fields MININTERVAL and MAXINTERVAL put limits on the frequency of
replenishments. The inventory profile will have “teeth” of variable size but
with a controlled interval.

The fields SIZE_MINIMUM, SIZE_MAXIMUM and SIZE_MULTIPLE put limits on the size
of the replenishments. The inventory profile will have “teeth” of controlled
size but with variable intervals.

Playing with these parameters allows flexible and smart procurement policies
to be modelled.

Note that frePPLe doesn’t include any logic to compute these parameters. The
parameters are to be generated externally and frePPLe only executes based on
the parameter settings. At a later stage a module to compute these parameters
could be added.

The PRODUCING field is unused for this buffer type. Propagation through a bill
of material will be stopped at a procurement buffer.

================ ================= ===========================================================
Field            Type              Description
================ ================= ===========================================================
leadtime         duration          | Time taken between placing the purchase order with the
                                     supplier and the delivery of the material.
                                   | When the “LEADTIME” constraint is enabled in the solver,
                                     it won’t create any new procurement orders that would
                                     need to start in the past.
fence            duration          | Time window (from the current date of the plan) during
                                     which procurement orders are expected to be released.
                                   | When the “FENCE” constraint is enabled in the solver, it
                                     won’t create any new operation plans in this time fence.
                                     Only the externally supplied existing procurement plans
                                     will then exist in this time window.
mininventory     positive double   Lowest inventory level we're trying to respect.
maxinventory     positive double   | Inventory level to which we try to replenish.
                                   | The actual inventory can exceed this value.
mininterval      duration          | Minimum time between replenishments.
                                   | The order quantity will be increased such that it covers
                                     at least the demand in the minimum interval period. The
                                     actual inventory can exceed the target set by the
                                     mininventory field.
maxinterval      duration          | Maximum time between replenishments.
                                   | The order quantity will replenish to an inventory value
                                     less than the maximum when this maximum interval is
                                     reached.
size_minimum     positive double   | Minimum quantity for a replenishment.
                                   | This parameter can cause the actual inventory to exceed
                                     the target set by the MinimumInventory parameter.
size_maximum     positive double   | Maximum quantity for a replenishment.
                                   | This parameter can cause the maximum inventory target
                                     never to be reached.
size_multiple    positive double   All replenishments are rounded up to a multiple of this
                                   value.
================ ================= ===========================================================

Buffer_infinite
---------------

An infinite buffer has an infinite supply of the material is available.

The PRODUCING field is unused for this buffer type.

Propagation through a bill of material will be stopped at an infinite buffer.

**Example XML structures**

Adding or changing a buffer

.. code-block:: XML

    <plan>
      <buffers>
        <buffer name="item a @ location b">
          <item name="item a" />
          <location name="location b" />
          <onhand>10</onhand>
        </buffer>
      </buffers>
    </plan>

Update the current inventory information of an existing buffer

.. code-block:: XML

    <plan>
      <buffers>
        <buffer name="item a @ location b" onhand="100"  action="C" />
      </buffers>
    </plan>

Deleting a buffer

.. code-block:: XML

    <plan>
       <buffers>
          <buffer name="item a @ location b" action="R"/>
       </buffers>
    </plan>

**Example Python code**

Adding or changing a buffer

::

    it = frepple.item(name="item a")
    loc = frepple.location(name="location b")
    buf = frepple.buffer(name="item a @ location b",
            onhand=10, item=it, location=loc)

Update the current inventory information of an existing buffer

::

    buf = frepple.buffer(name="item a @ location b",
            onhand=10, action="C")

Deleting a buffer

::

    buf = frepple.buffer(name="item a @ location b", action="R")

Iterate over buffers, flows and flowplans

::

   for b in frepple.buffers():
     print "Buffer:", b.name, b.description, b.category
     for l in b.flows:
       print " Flow:", l.operation.name, l.quantity,
         l.effective_start, l.effective_end
     for l in b.flowplans:
       print " Flowplan:", l.operationplan.operation.name,
         l.quantity, l.date
