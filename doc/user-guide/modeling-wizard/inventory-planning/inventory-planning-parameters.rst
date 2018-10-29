=============================
Inventory planning parameters
=============================

A record should be entered in this table if you wish frePPLe to calculate 
a safety stock and a reorder quantity for an item-location. The calculation can be
done for raw materials, intermediate materials and/or end items.

.. rubric:: Key Fields

=====================================  ================= ========================================================================================
Field                                  Type              Description
=====================================  ================= ========================================================================================
item                                   non-empty string  The item name for which safety stock and reorder quantity should be computed.
location                               non-empty string  The location name for which safety stock and reorder quantity should be computed.
roq minimum quantity                   number            Imposes a minimum constraint for the reorder quantity.
roq maximum quantity                   number            Imposes a maximum constraint for the reorder quantity.
roq minimum period of cover            number            Imposes a constraint on the minimum period of demand (expressed in days) to be covered 
                                                         with the reorder quantity.
roq maximum period of cover            number            Imposes a constraint on the maximum period of demand (expressed in days) to be covered 
                                                         with the reorder quantity.
safety stock minimum period of cover   number            Imposes a constraint on the minimum period of demand (expressed in days) to be covered
                                                         with the safety stock.
safety stock maximum period of cover   number            Imposes a constraint on the maximum period of demand (expressed in days) to be covered
                                                         with the safety stock.
safety stock minimum quantity          number            Imposes a minimum constraint for the safety stock.
safety stock maximum quantity          number            Imposes a maximum constraint for the safety stock.
service level                          number            This is the desired service level percentage for that buffer.
=====================================  ================= ========================================================================================
                                  
.. rubric:: Advanced topics

* Complete table description: :doc:`../../model-reference/inventory-planning-parameters`
