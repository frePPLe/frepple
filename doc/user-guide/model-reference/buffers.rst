=======
Buffers
=======

A buffer is in (logical of physical) inventory point for a item at a certain location.

Different types of buffers exist:

* | Default:
  | The default buffer uses an "producing" operation to replenish it with
    additional material.

* | Infinite:
  | An infinite buffer is unconstrained and has an infinite supply of the material.
  | Propagation through a bill of material will be stopped at an infinite buffer.

**Fields**

================ ================= ===========================================================
Field            Type              Description
================ ================= ===========================================================
name             non-empty string  | Unique name of the buffer.
                                   | This is the key field and a required attribute.
                                   | You have to use the convention of using "item @ location"
                                     as the buffer name.
item             item              | Item being stored in the buffer.
                                   | This is a required field.
location         location          | Location of the buffer.
                                   | This is a required field.
                                   | The working hours and holidays for the buffer are taken
                                     from the ‘available’ calendar of the location.
description      string            Free format description.
category         string            Free format category.
subcategory      string            | Free format subcategory.
                                   | If this field is set to 'tool', the field 'tool' will
                                     automatically be set to true.
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
                                   | From version 4.0 onwards, this field is deprecated. It is
                                     left only for backwards compatibility. New implementations
                                     and upgraded installs should use the easier modeling
                                     constructs itemsupplier, itemdistribution and operation.
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
================ ================= ===========================================================
