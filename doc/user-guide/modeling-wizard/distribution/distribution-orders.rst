===================
Distribution Orders
===================

This table all the distribution orders of your supply chain.

When generating a plan frepple will add new proposed distribution orders to this table.

For a first simplified model, this table can be left empty, frepple will generate proposed distribution orders to meet the plan. 
As a consequence, some demand records might be delivered late.

.. rubric:: Key Fields

================ ================= ===========================================================
Field            Type              Description
================ ================= ===========================================================
status           non-empty string  For confirmed distribution orders, the status should be "confirmed".
item             item              The item being transfered.
origin           location          The location where the item is transfered from.
destination      location          The location where the item will be received.
end date         DateTime          The date of the distribution order delivery.
quantity         number            The quantity being transferred.
================ ================= ===========================================================                              
                                  
.. rubric:: Advanced topics

* Complete table description: :doc:`../../model-reference/distribution-orders`
