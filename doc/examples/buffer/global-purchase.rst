=================
Global purchasing
=================

By default the planning algorithm will trigger a replenishment for a
buffer as soon as its inventory level drops below the safety stock.
This logic is based on the local needs at the buffer.

In a distribution network with inventory at multiple locations,
considering the inventory across the entire network for the purchasing
decisions can significantly reduce the inventory and obsolesence costs.

Using the global purchase flag we can prevent a new purchase order
to be created when sufficient inventory is still available at other
locations in the network. And it directs demands to locations that
have available inventory.

This feature has 2 specific planning behavior:

* | Generation of a new purchase order for an item is blocked when
    the total inventory of the item across all locations is above the
    sum of the safety stock of the item across all locations.

* | By default frePPLe *only* plans a demand on the location where it is
    pointing at.
  | When the global_purchase flag for the item is set, the
    planning algorithm will first plan at the demand location. If the
    demand can't be satisfied from that location the algorithm will try to
    satisfy the demand from other locations that have the item on stock.
    Candidate locations are sorted in descending order by the amount
    inventory above the safety stock level they carry of the item.

.. rubric:: Example

Imagine a distribution network with inventory at a number of warehouses
across the country for a particular item:

======== ========= ============
Location Inventory Safety stock
======== ========= ============
WH1      100       10
WH2      0         10
WH3      20        10
======== ========= ============

A sales order from a customer close to WH2 can easily be shipped from
WH1 instead. With the global_purchase flag set, we will automatically
redirect the demand to WH1 (which has highest inventory above its safety
stock) and WH3.

Any new purchase orders for this item are deplayed until the total
inventory across all location drops below 30 = 10 + 10 + 10.
