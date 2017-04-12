=============================
Inventory Planning Parameters
=============================

A record should be entered in this table if you wish frepple to calculate 
a safety stock or a reorder quantity for a buffer. The calculation can be
done for raw materials, intermediate materials and/or end items.

**Fields**

=====================================  ================= ========================================================================================
Field                                  Type              Description
=====================================  ================= ========================================================================================
item                                   non-empty string  The item name for which safety stock and reorder quantity should be computed.
location                               non-empty string  The location name for which safety stock and reorder quantity should be computed.
roq type                               non-empty string  | The ROQ type should be one of the following :
                                                         | calculated : The ROQ is calculated to optimize your order cost.
                                                         | quantity : The ROQ is a fixed quantity defined by the user.
                                                         | period of cover : The ROQ covers a number of lead time forecast.
roq minimum quantity                   number            | This field should be populated if the ROQ type is equal to "quantity".
                                                         | It represents the number the ROQ should be equal to.
roq minimum period of cover            number            | This field should be populated if the ROQ type is equal to "period of cover".
                                                         | It represents the number of months of forecast the ROQ should be equal to.
safety stock type                      non-empty string  | The safety stock type should be one of the following :
                                                         | calculated : The safety stock is calculated based on a service level.
                                                         | quantity : The safety stock is a fixed quantity defined by the user.
                                                         | period of cover : The safety stock covers a number of lead time forecast.
safety stock minimum period of cover   number            | This field should be populated if the safety stock type is equal to "period of cover".
                                                         | It represents the number of months of forecast the safety stock should be equal to.
safety stock minimum quantity          number            | This field should be populated if the safety stock type is equal to "quantity".
                                                         | It represents the number the safety stock should be equal to.
service level                          number            This is the desired service level percentage for that buffer, E.g : 97.5
lead time deviation                    number            The lead time standard deviation considered when calculating the safety stock, can be 
                                                         left empty.
demand deviation                       number            The demand standard deviation considered when calculating the safety stock, can be 
                                                         left empty.
do not stock                           boolean           | Indicates whether this buffer should be stocked.
                                                         | Possible values are : 
                                                         | "TRUE" : Default ROQ of 1 and safety stock of 0 will be used.
                                                         | "FALSE" : ROQ and safety stock will be calculated.
segment\_\*                             number           | This values in these columns are not editible by the user. They represent the 
                                                           parameter values computed by the system based on the business rules.
                                                         | When both a user-specified and computed value are provided for a parameter, the
                                                           user-specified value overrides the segment value.  
=====================================  ================= ========================================================================================
                                  
