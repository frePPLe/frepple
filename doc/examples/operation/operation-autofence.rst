===========================================
Release fence and awaiting confirmed supply
===========================================

A release fence can be set to specify a frozen zone in the planning horizon
in which the planning algorithm cannot propose any new manufacturing orders,
purchase order or distribution order. The fence represent a period during
which the plan is already being executed and can no longer be changed.

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

`Check this feature on a live example <https://demo.frepple.com/operation-autofence/>`_

:download:`Download an Excel spreadsheet with the data for this example<operation-autofence.xlsx>`

Here is a step by step guide to explore the example:

* | This example shows two items. Each of these items can be manufactured
    in house, or we can outsource the production to a subcontractor. The in house
    production is defined in the
    `operation table <https://demo.frepple.com/operation-autofence/data/input/operation/>`_.
    The outsourcing is defined in the
    `item supplier table <https://demo.frepple.com/operation-autofence/data/input/itemsupplier/>`_.
    As described in another example :doc:`operation-alternate`, the priority field controls
    selection between these alternates.

  | Each item has a single
    `sales order <https://demo.frepple.com/operation-autofence/data/input/demand/>`_.

  | We have confirmed
    `purchases orders <https://demo.frepple.com/operation-autofence/data/input/purchaseorder/>`_
    with the subcontractor going as far out as 30 days.

* | The release fence can be set differently on each
    `operation <https://demo.frepple.com/operation-autofence/data/input/operation/>`_.

  .. image:: _images/operation-autofence-1.png
     :alt: Operation table

* | With the
    `parameter plan.autoFenceOperations <https://demo.frepple.com/operation-autofence/data/common/parameter/>`_
    you can control how long you are prepared to wait for existing/confirmed supply
    before proposing a new replenishment. The default value is 999 (days), which basically means
    that we use up all confirmed supply before proposing new supply.

  .. image:: _images/operation-autofence-2.png
     :alt: Parameters

  This picture illustrates the concept of this parameter (note: the numbers in the picture don't match
  the example model).

  .. image:: _images/autofence.png
     :alt: Illustration of autofence parameter

* | For item "widget B", frePPLe chooses to wait for the incoming shipment
    from our subcontractor. The difference between the requirement date of Jan 8th
    and the arrival of the supply on Jan 16th is within the allowed delay of 12 days.

  | This delay creates extra lateness for our sales order.

  .. image:: _images/operation-autofence-3.png
     :alt: Sales order widget B

  .. image:: _images/operation-autofence-4.png
     :alt: Purchase order widget B

* | For the item "widget A" the supply arrives much later, and frePPLe proposes to
    launch a new in-house manufacturing order.

  | The sales order is now delivered a bit earlier. However, the incoming purchase
    order of widget A is now unused (notice the empty "demand" column) and we create
    excess inventory.

  .. image:: _images/operation-autofence-5.png
     :alt: Sales order widget A

  .. image:: _images/operation-autofence-6.png
     :alt: Purchase order widget A

  .. image:: _images/operation-autofence-7.png
     :alt: Manufacturing order widget A
