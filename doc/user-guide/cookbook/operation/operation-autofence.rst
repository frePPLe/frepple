==========================================
Operation auto-update of the release fence
==========================================

A release fence can be set to specify a frozen zone in the planning horizon
in which the planning algorithm cannot propose any new manufacturing orders, 
purchase order or distribution order. The fence represent a period during 
which the plan is already being executed and can no longer be changed.

The fence can be set differently on each operation.

Optionally, this concept is further extended with an automatically computed
release fence that is based on confirmed supply.

Imagine a situation where the lead time is 7 days, and we have a confirmed
purchase order coming in on day 10. Do you want that frePPLe can propose a new 
purchase order earlier than day 10? Probably not, and you'll prefer to await
the existing purchase order (eventually calling the supplier to expedite
the delivery).

Imagine the same situation but the confirmed purchase order is coming in
after 40 days. Do you want that frePPLe can propose a new purchase order
earlier than day 40?  Probably yes.

With the parameter plan.autoFenceOperations you can control how long you are
prepared to wait for existing/confirmed supply before proposing a new supply
order.
The default value is 0, which basically means we don't wait at all for the
confirmed supply.

.. rubric:: Example

:download:`Excel spreadsheet operation-autofence <operation-autofence.xlsx>`

This example shows two products. Each of these products can be manufactured
in house, or we can outsource the production to a subcontractor.
We have confirmed purchases orders with the subcontractor going as far out
as the 30 days.

For one of the products, frePPLe chooses to wait for the incoming shipment
from our subcontractor (and that means delivering our sales order late).

For the other product the supply arrives much later, and frePPLe propose to
launch a new in-house manufacturing order.
