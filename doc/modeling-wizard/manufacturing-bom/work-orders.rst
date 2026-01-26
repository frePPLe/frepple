===========
Work orders
===========

A work order is a detailed step within a manufacturing order.
The owner of a work order is a manufacturing order whose operation is of type "routing".
The routing operation defines a list of step suboperations that need to be executed.

The work orders table contains the confirmed work orders in your supply chain.

When generating a plan frepple will add new proposed work orders to this table.

For a first simplified model, this table can be left empty, frepple will generate proposed work orders to meet the plan.

.. rubric:: Key Fields

================ ================= ===========================================================
Field            Type              Description
================ ================= ===========================================================
reference        string            Unique identifier of the manufacturing order.
owner            string            The reference of the manufacturing order this work order
                                   belongs to.
status           string            For frozen and work-in-progress manufacturing orders, the
                                   status should be "confirmed".
operation        operation         The operation that should be run for the manufacturing orders.
end date         DateTime          The date the manufacturing order ends.
quantity         number            The produced item quantity.
================ ================= ===========================================================

.. rubric:: Advanced topics

* Complete table description: :doc:`../../model-reference/work-orders`
