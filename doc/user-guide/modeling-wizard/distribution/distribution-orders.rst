===================
Distribution Orders
===================

This table all the distribution orders of your supply chain.

Note that frepple will populate this table with proposed distribution orders when running the plan.

For a first simplified model, this table can be left empty, frepple will generate proposed distribution orders to meet the plan. 
As a consequence, some demand records might be delivered late.

.. rubric:: Key Fields

================ ================= ===========================================================
Field            Type              Description
================ ================= ===========================================================
status           non-empty string  For confirmed distribution orders, the status should be "confirmed".
item             item              The item being transfered.
origin           location          The model location where the item is transfered from.
destination      location          The model location where the item will be received.
end date         DateTime          The date of the distribution order delivery.
quantity         number            The quantity delivered.
================ ================= ===========================================================                              
                                  
.. rubric:: Advanced topics

* Complete table description: :doc:`../../model-reference/distribution-orders`
