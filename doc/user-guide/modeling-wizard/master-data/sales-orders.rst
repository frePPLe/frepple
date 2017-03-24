============
Sales orders
============

The sales orders table contains all the orders placed by your customers.
Orders in the status "open" will be planned.

You should also add sales order history to this table if you want frePPLe
to generate a statistical forecast. The sales history should be included
using the "closed" status.

.. rubric:: Key Fields

============== ================= ===========================================================
Field          Type              Description
============== ================= ===========================================================
name           non-empty string  Unique name of the demand (E.g: Order1, SO125124...)
quantity       number            Requested quantity.
item           item              Requested item.
location       location          Requested shipping location.
due            dateTime          Due date of the demand.
customer       customer          Customer placing the demand.
status         string            | Status of the demand.
                                 | Possible values are "open", "closed".
============== ================= ===========================================================               

.. rubric:: Advanced topics

* Complete table description: :doc:`../../model-reference/sales-orders`

* Modeling demand priorities: :doc:`../../cookbook/demand/priorities`

* Modeling demand policies: :doc:`../../cookbook/demand/policies`
