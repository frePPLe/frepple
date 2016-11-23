====================
Manufacturing orders
====================

The manufacturing orders table contains the confirmed manufacturing orders in your supply chain.

When generating a plan frepple will add new proposed manufacturing orders to this table.

For a first simplified model, this table can be left empty, frepple will generate proposed manufacturing orders to meet the plan.

.. rubric:: Key Fields

================ ================= ===========================================================
Field            Type              Description
================ ================= ===========================================================
status           non-empty string  For confirmed purchase orders, the status should be "confirmed".
operation        operation         The operation that should be run for the manufacturing orders.
end date         DateTime          The date the manufacturing order ends.
quantity         number            The produced item quantity.
================ ================= ===========================================================                              
                      
.. rubric:: Advanced topics

* Complete table description: :doc:`../../model-reference/manufacturing-orders`
