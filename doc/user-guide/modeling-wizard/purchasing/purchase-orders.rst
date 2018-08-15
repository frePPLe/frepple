===============
Purchase orders
===============

This table contains the open purchase orders with your suppliers.

When generating a plan frepple will add new proposed purchase orders to this table.

For a first simplified model, this table can be left empty, frepple will generate proposed purchase orders to meet the plan.
As a consequence, some demand records might be delivered late.

.. rubric:: Key Fields

================ ================= ===========================================================
Field            Type              Description
================ ================= ===========================================================
status           non-empty string  For confirmed purchase orders, the status should be "confirmed".
item             item              The item purchased from that supplier.
location         location          The location where the items will be received.
supplier         supplier          The supplier the items are purchased from.
end date         Date              The date of the purchase order delivery.
quantity         number            The ordered quantity.
================ ================= ===========================================================                              
                                  
.. rubric:: Advanced topics

* Complete table description: :doc:`../../model-reference/purchase-orders`
