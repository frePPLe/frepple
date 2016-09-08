===============
Purchase Orders
===============

This table declare which items a supplier can procure.

Note that frepple will populate this table with proposed purchase orders when running the plan.


Key Fields
----------

================ ================= ===========================================================
Field            Type              Description
================ ================= ===========================================================
status           non-empty string  For confirmed purchase orders, the status should be "confirmed".
item             non-empty string  The item purchased from that supplier.
location         non-empty string  The model location where the items will be received.
supplier         non-empty string  The supplier the items are purchased from.
end date         date              The date of the purchase order delivery.
quantity         number            The quantity delivered.
================ ================= ===========================================================                              
                                  
Advanced topics
---------------

* Complete table description: :doc:`../../model-reference/purchase-orders`
