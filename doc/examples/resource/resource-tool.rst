=====
Tools
=====

| Tools are resources that are claimed at a certain operation and released
  again at a later operation. They stay with the job between those operations.
| They can be physical: e.g. moulds, fixtures, tooling, ...
| They can also be virtual: e.g. electronic kanban/QRM cards to limit the
  work-in-progress in a certain manufacturing cell.

FrePPLe has 3 constructs to model different types of tools.

* | A first approach is to use a dummy material for modeling the tooling.
  | Use this type if the **tools are used across multiple operations that are not
    suboperations in a routing**.

* | When the **tool is used for different steps within the same routing operation**,
    there are 2 variations.

  | With the **first variation** the same amount of tools is used, **regardless of the
    quantity** of the manufacturing order.
  | Eg a box, a container, a pallet, ... to store the pieces while they are on the shopfloor.

  | With the **second variation** the tool requirement is **proportional to the quantity**
    of the manufacturing order. A bigger manufacturing order needs more tools than
    a small manufacturing order.
  | Eg a frame that needs to be put around each individual piece while it is on the shop floor.

`Check this feature on a live example <https://demo.frepple.com/resource-tool/data/input/operationmaterial/>`_

:download:`Download an Excel spreadsheet with the data for this example <resource-tool.xlsx>`

The **first type** of tool is modeled very much as a material.

* | They are modeled as a buffer for which the subcategory field is set
    to "tool".
  | The operation that claims the tool gets an
    `operation-material <https://demo.frepple.com/resource-tool/data/input/operationmaterial/>`_
    record to consume the tool item.
  | The operation that releases the tool get an operation-material
    record to produce the tool item.
  | The operation-materials records will typically (but not necessary) be populated using
    the "fixed quantity" column to keep the tool quantity independent of the size of the
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

The **second type** of tool is modeled as a resource:

* The tool resources are marked with the subcategory "tool" (when independent of the MO quantity)
  or "tool per piece" (when proportional to the MO quantity)
  in the `resource table <https://demo.frepple.com/resource-tool/data/input/resource/>`_.

  In this example, we'll be using pallets to model "tool" resources and frames to model "tool per piece" resources.
  This example has 3 pallets, 10 frames of type #1, 5 frames of type #2 and
  7 frames of type #3.

  .. image:: _images/resource-tool-2.png
     :alt: Manufacturing orders

* | Use the
    `manufacturing order report <https://demo.frepple.com/resource-tool/data/input/manufacturingorder/>`_
    to verify the following behavior:

  | For **tool** resources:

  - The same tool is used for all steps in a routing. You cannot perform step A with pallet #2 and
    step B with pallet #1.

  - Manufacturing orders always use 1 pallet, regardless of their quantity.

  | For **tool per piece** resources:

  - | Manufacturing orders use as many frames as the quantity of the manufacturing order.
      A big manufacturing order needs more frames than a smaller one.
    | Can you find out what happens if the requirements exceeds the number of frames
      we have available?  There are some customer demands in this example that are big
      enough to analyse this behavior...

  .. image:: _images/resource-tool-3.png
     :alt: Manufacturing orders