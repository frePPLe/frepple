========
Policies
========

Two fields on the demand configure what deliveries are being accepted by the customer:

* **Minimum shipment**

  Defines the minimum delivery size accepted by the customer.

  If the minimum delivery size is set equal to the demand quantity, the customer only
  accepts a single delivery in full.

  If the minimum delivery size is smaller than the demand quantity, the customer will
  accept partial shipments.

  If the minimum delivery size is greater than the demand quantity, the customer will receive
  more than he actually ordered (eg order 2 units and get shipped the smallest box with 10 units).

* **Maximum lateness**

  Determines the maximum delay the customer will accept before cancelling his or her order.
  When the demand isn’t feasible within this delay frePPLe will plan the order short.

  In some businesses demand that can't be met on time is lost - the customer will simply buy
  the product from your competitor. Another usage is for forecasted demand - typically you don't
  want to plan them later planned later than the demand bucket.

.. rubric:: Example

:download:`Excel spreadsheet demand-policies <demand-policies.xlsx>`

In this example we have 6 identical items, served from inventory and with a simple stock
replenishment operation. Each item has a single demand with a different delivery policy.

The demands are delivered differently according to their policies.

Demands 1, 2 and 3 are allowed to be planned late, and we see late deliveries.
For demand 1 we also see a partial shipment at the requested date.

Demands 4, 5 and 6 aren't allowed to be planned late.
Only for demand 4 we can plan a partial shipment. Orders 5 and 6 remain unplanned.
