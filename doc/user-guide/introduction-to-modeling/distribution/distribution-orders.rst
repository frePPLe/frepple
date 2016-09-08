===============
Distribution Orders
===============

This table all the confirmed distribution orders of your supply chain.

Note that frepple will populate this table with proposed distribution orders when running the plan.



Key Fields
----------

================ ================= ===========================================================
Field            Type              Description
================ ================= ===========================================================
status           non-empty string  For confirmed distribution orders, the status should be "confirmed"
item             non-empty string  The item transfered from that supplier
origin
destination      non-empty string  The model location where the items will be received
end date         date              The date of the purchase order delivery
quantity         number            The quantity delivered
================ ================= ===========================================================                              
                                  
Advanced topics
---------------

* Complete table description: :doc:`../../model-reference/distribution-orders`
