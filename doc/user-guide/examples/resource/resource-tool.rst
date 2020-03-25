=====
Tools
=====

| Tools are resources that are claimed at a certain operation and released
  again at a later operation. They stay with the job between those operations.
| They can be physical: e.g. moulds, fixtures, tooling, ...
| They can also be virtual: e.g. electronic kanban/QRM cards to limit the
  work-in-progress in a certain manufacturing cell.

`Check this feature on a live example <https://demo.frepple.com/resource-tool/data/input/operationmaterial/>`_

:download:`Download an Excel spreadsheet with the data for this example <resource-tool.xlsx>`

* | They are modeled as a buffer for which the subcategory field is set
    to "tool".
  | The operation that claims the tool gets an 
    `operation-material <https://demo.frepple.com/resource-tool/data/input/operationmaterial/>`_
    record to consume the tool item.
  | The operation that releases the tool get an operation-material
    record to produce the tool item.
  | The flows are typically (but not necessary) of type "fixed_start" and
    "fixed_end" to keep the tool quantity independent of the size of the
    manufacturing order quantity.

* | In this example we have a production consisting of 5 subsequent steps.
  | We model a (virtual) tool to control the level of work-in-progress
    across the operations 2 through 4: only 2 jobs are allowed simultaneously
    in this cell. You can think of this as a kanban card which we need
    to obtain when entering the cell, and which we release when leaving the cell.

* | Use the 
    `manufacturing order report <https://demo.frepple.com/resource-tool/data/input/manufacturingorder/>`_
    to verify that the kanban card constraint is
    correctly respected. You'll find that new operations at step 2 are only
    created at the moment when an operation at step 4 finishes (respecting also
    the working hours of the location, of course).

  .. image:: _images/resource-tool-1.png
     :alt: Manufacturing orders

* | You can change the initial inventory of the kanban cards 
    in the `buffer table <https://demo.frepple.com/resource-tool/data/input/buffer/>`_
    to see how it impacts the delivery performance.
  | How many cards do you need at least to bring the lateness to its minimum? And
    can you explain that result?
