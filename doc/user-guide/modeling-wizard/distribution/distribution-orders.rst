===================
Distribution Orders
===================

This table all the confirmed distribution orders of your supply chain.

Note that frepple will populate this table with proposed distribution orders when running the plan.

For a first simplified model, this table can be left empty, frepple will generate proposed distribution orders to meet the plan. 
As a consequence, some demand records might be delivered late.

Key Fields
----------

================ ================= ===========================================================
Field            Type              Description
================ ================= ===========================================================
status           non-empty string  For confirmed distribution orders, the status should be "confirmed".
item             non-empty string  The item being transfered.
origin           non-empty string  The model location where the item is transfered from.
destination      non-empty string  The model location where the item will be received.
end date         date              The date of the distribution order delivery.
quantity         number            The quantity delivered.
================ ================= ===========================================================                              
                                  
Advanced topics
---------------

* Complete table description: :doc:`../../model-reference/distribution-orders`
