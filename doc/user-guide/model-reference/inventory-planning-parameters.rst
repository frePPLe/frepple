=============================
Inventory planning parameters
=============================

A record should be entered in this table if you wish to calculate a safety stock
and a reorder quantity for a buffer. The calculation can be done for raw materials,
intermediate materials and/or end items.

**Fields**

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
service level                          number            This is the desired service level percentage for that buffer, E.g : 97.5
lead time deviation                    number            The lead time standard deviation considered when calculating the safety stock, can be 
                                                         left empty.
demand deviation                       number            The demand standard deviation considered when calculating the safety stock, can be 
                                                         left empty.
do not stock                           boolean           | Indicates whether this buffer should be stocked.
                                                         | Possible values are : 
                                                         | "TRUE" : Default reorder quantity of 1 and safety stock of 0 will be used.
                                                         | "FALSE" : Reorder quantity and safety stock will be calculated.
segment\_\*                             number           This values in these columns are not editible by the user. They represent the 
                                                         parameter values computed by the system based on the business rules.
                                                         
                                                         When both a user-specified and computed value are provided for a parameter, the
                                                         user-specified value overrides the segment value.  
=====================================  ================= ========================================================================================
                                  
