====================
Alternate operations
====================

Alternate operations are operations that produce the same item in a given location.

There are many situations where there exists alternate operations.
For example, it is sometimes possible to build an item or to purchase it from a supplier. We could also get an item 
in a warehouse from two different factories or a factory can have distinct operations producing the same item...

If multiple machines can produce the same item, we would recommend to use a modelling with `alternate resources <../resource/resource-alternate.html>`_
but sometimes it might be easier to model this as alternate operations with a different resource linked to each 
operation (one operation linked to 5 alternate resources becomes 5 operations each linked to 1 resource).

`Check this feature on a live example <https://demo.frepple.com/operation-alternate/data/input/operation/>`_

:download:`Download an Excel spreadsheet with the data for this example<operation-alternate.xlsx>`

In the following example, we will explain how to model alternate operations and demistify why frePPLe picks one operation
over another one when generating the supply plan.


.. image:: _images/round_table_supply_path.png
   :alt: Supply path for round table

In this example, there are 2 alternate operations to produce item *round table*. The two operations have the same 
bill of material but are linked to 2 different resources.

By default, there is nothing to do to declare alternate operations in frePPLe (in previous deprecated versions of frePPLe,
the planner had to specify an operation of type *alternate*). If two operations produce the same item (in the same location), 
then frePPLe understands that these two operations are alternate and will apply an alternate logic to pick one or another when generating
the plan.

.. image:: _images/round_table_operation.png
   :alt: Operations to produce round table.
   
The *search mode* field is what will be read by the solver to determine which operation to pick when generating a manufacturing order.
The search mode field must be the same for alternate operations. 
If the search mode is left blank, frePPLe will assume that search mode is *priority*.

  .. rubric:: Priority search mode
  
  FrePPLe will pick the operation with highest priority to generate a manufaturing order. 
  In our example, *Assemble round table with new machine* will be picked (as a reminder, priority 1 is more important than priority 2 in frePPLe).
  
  To be accurate, frePPLe will pick the operation with the highest priority as long as no demand is planned late. In below screenshot, we have 3 demands of 250 units for *round table* item with due date far in the future:

  .. image:: _images/round_table_resource_detail.png
     :alt: Resource detail for round table

  We can see that frePPLe anticipates some demands that are delivered early :samp:`A` to make sure *Assemble round table with new machine* operation is used.

  Now if we change the due date of the 3 demands so that there isn't enough time to deliver on time all 3 demands with
  *Assemble round table with new machine* operation, this is what will happen:

  .. image:: _images/round_table_resource_detail_2.png
     :alt: Resource detail for round table

  We can see from above screenshot that frePPLe has picked operation *Assemble round table with old machine* :samp:`B` to make sure no demand would not be delivered late.

  Time for a clarification: If two or more operations share a same priority, then frePPLe will apply exact same behavior as above, always picking the same
  operation as long as no demand is late. The picked operation is the first one tested.
  
  .. rubric:: Minimum cost search mode
  
  When search mode is set to *minimum cost*, frePPLe will pick the operation that minimizes the cost of production.
  Each upstream cost, whether it is at operation, resource, item supplier or item distribution level is included in the total calulated cost and multiplied by
  the number of parts produced, purchased, shipped.
  
  .. rubric:: Minimum penalty
  
  When search mode is set to *minimum penalty*, frePPLe will pick the operation that minimizes the penalty. 
  A penalty is paid by an operation each time it produces some material earlier than the requested date. 
  
  If we set the search mode to *minimum penalty*, then frePPLe
  will pick the first operation to produce the first demand (both have a penalty of 0 as they can produce on time). Then frePPLe will pick the second operation
  to produce the second demand (as the first operation will pay a penalty because it has been picked for the first demand and can only produce earlier). Then,
  for the third demand, both operation will have the same penalty and frePPle will pick again the first one.
  
  .. rubric:: Minimum cost plus penalty
  
  Obviously, this option is a combination of the cost and the penalty. FrePPLe will compute both the cost and the penalty for an operation and will pick the one
  that minimizes the sum.
  
  
  
  
  
  