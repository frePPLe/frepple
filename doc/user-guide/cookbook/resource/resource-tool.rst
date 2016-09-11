=====
Tools
=====

| Tools are resources that are claimed at a certain operation and released
  again at a later operation. They stay with the job between those operations.
| They can be physical: e.g. moulds, fixtures, tooling, ...
| They can also be virtual: e.g. electronic kanban/QRM cards to limit the
  work-in-progress in a certain manufacturing cell.

| They are  modelled as a buffer for which the subcategory field is set
  to "tool".
| The operation that claims the tool gets a flow to consume from this buffer.
| The operation that releases the tool get a flow to produce into this buffer.
| The flows are typically (but not necessary) of type "flow_fixed_start" and
  "flow_fixed_end" to keep the tool quantity independent of the size of the
  operationplan quantity.

.. note:: In a future release it is envisioned to replace the above model
          construct with a simpler and more intuitive representation as a
          resource.

.. rubric:: Example

:download:`Excel spreadsheet resource-tool <resource-tool.xlsx>`

In this example we have a production consisting of 5 subsequent steps.
We model a (virtual) tool to control the level of work-in-progress
across the operations 2 through 4: only 2 jobs are allowed simultaneously
in this cell. You can think of this as a kanban card which we need
to obtain when entering the cell, and which we release when leaving the cell.

Use the operation plan detail report to verify that the constraint is
correctly respected. You'll find that new operations at step 2 are only
created at the moment when an operation at step 4 finishes (considering also
working hours).

You can change the initial inventory of the kanban cards to see how it
impacts the delivery performance.
How many cards do you need at least to bring the lateness to its minimum? And
can you explain that result?
