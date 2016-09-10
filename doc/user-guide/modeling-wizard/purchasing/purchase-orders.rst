===============
Purchase Orders
===============

Tihs table contains the purchase orders you passed to your suppliers.

Note that frepple will populate this table with proposed purchase orders when running the plan.

For a first simplified model, this table can be left empty, frepple will generate proposed purchase orders to meet the plan.
As a consequence, some demand records might be delivered late.

.. rubric:: Key Fields

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
                                  
.. rubric:: Advanced topics

* Complete table description: :doc:`../../model-reference/purchase-orders`
