==============
Operation Type
==============

Different operation types are available:

* **Fixed_time**

  The duration of the operation is constant, regardless of the quantity being planned.

  A typical example is a transport operation: transporting 1 piece with a truck takes just
  as long as transporting 100 pieces.

* **Time_per**

  The duration of the operation increases linearly with the planned quantity. The total
  duration takes the form of 'A + B * quantity', where A and B are constants.

  A typical example is a production operation: there is a fixed overhead of machine
  setup at the start, and the actual production is linear with the quantity to produce.

* **Alternate**

  This operation type represent the choice between alternate operations to achieve the
  same result. Another cookbook recipe is dedicated to this.

* **Split** (New in 2.2)

  This operation type plans the demand proportionally over a number of operations, based
  on pre-defined percentages.

* **Routing**

  This operation type represent the sequence of operations that need to be run in sequence.

  The duration for the operation refers to available time. If the operation location
  has a calendar with the working hours and holidays, the time between the start and
  end date of an operationplan can be longer than the duration defined on the operation.

.. rubric:: Example

:download:`Excel spreadsheet operation-type <operation-type.xlsx>`

This example has a transport operation of type fixed_time and a production operation of type time_per.
