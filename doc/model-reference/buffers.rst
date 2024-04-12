=======
Buffers
=======

A buffer is a (logical of physical) inventory point for an item at a certain location.

Different types of buffers exist:

* | Default:
  | The default buffer uses an "producing" operation to replenish it with
    additional material.

* | Infinite:
  | An infinite buffer is unconstrained and has an infinite supply of the material.
  | Propagation through a bill of material will be stopped at an infinite buffer.

================ ================= ===========================================================
Field            Type              Description
================ ================= ===========================================================
item             item              | Item being stored in the buffer.
                                   | The combination item+location+batch is the unique primary
                                     key of this table.
location         location          | Location of the buffer.
                                   | The working hours and holidays for the buffer are taken
                                     from the available calendar of the location.
                                   | The combination item+location+batch is the unique primary
                                     key of this table.
batch            string            | Blank, unused for make-to-stock items.
                                   | Batch identification for make-to-order items.
                                   | The combination item+location+batch is the unique primary
                                     key of this table.
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
                                   | Default is 0, indicating no safety stock.
minimum_calendar calendar          | Refers to a calendar storing the desired minimum inventory
                                     level, aka safety stock.
                                   | Use this field when the minimum inventory level is varying
                                     over time. Otherwise use the minimum field. If both fields
                                     are specified, the minimum field is ignored.
maximum          double            | Desired maximum inventory, aka order-up-to level.
                                   | When the buffer needs to be replenished, the planning algorithm
                                     tries to refill to this level.
                                   | Default is 0, indicating replenishments of any quantity are
                                     accepted. Note that operations can still define constraints
                                     on the replenishment size.
maximum_calendar calendar          | Refers to a calendar storing the maximum inventory level.
                                   | Use this field when the maximum inventory level is varying
                                     over time. Otherwise use the maximum field. If both fields
                                     are specified, the maximum field is ignored.
tool             boolean           | A flag to mark buffers that are actually representing a tool.
                                   | Default is false.
                                   | The impact on the planning results is visible in the
                                     pegging and criticality calculations.
                                   | This field is only visible in the planning engine. In the
                                     user interface you use the subcategory field to set this
                                     field to true.
================ ================= ===========================================================
