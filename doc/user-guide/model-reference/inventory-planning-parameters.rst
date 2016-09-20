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
buffer                                 non-empty string  The bufer name for which safety stock and reorder quantity should be computed
description                            string            A description for this inventory planning record.
category                               string            A category for this inventory planning record.
subcategory                            string            A subcategory for this inventory planning record.
roq type                               non-empty string  | The ROQ type should be one of the following :
                                                         | calculated : The ROQ is calculated to optimize your order cost.
                                                         | quantity : The ROQ is a fixed quantity defined by the user.
                                                         | period of cover : The ROQ covers a given number of forecast periods.
roq minimum quantity                   number            | This field should be populated if the ROQ type is equal to "quantity".
                                                         | It reprensents the number the ROQ should be equal to.
roq minimum period of cover            number            | This field should be populated if the ROQ type is equal to "period of cover".
                                                         | It reprensents the number of months of forecast the ROQ should be equal to.
safety stock type                      non-empty string  | The safety stock type should be one of the following :
                                                         | calculated : The safety stock is calculated based on a service level.
                                                         | quantity : The safety stock is a fixed quantity defined by the user.
                                                         | period of cover : The safety stock covers a given number of forecast periods.
safety stock minimum period of cover   number            | This field should be populated if the safety stock type is equal to "period of cover".
                                                         | It reprensents the number of months of forecast the safety stock should be equal to.
safety stock minimum quantity          number            | This field should be populated if the safety stock type is equal to "quantity".
                                                         | It reprensents the number the safety stock should be equal to.
service level                          number            This is the desired service level percentage for that buffer, E.g : 97.5
lead time deviation                    number            The lead time standard deviation considered when calculating the safety stock, can be 
                                                         left empty.
demand deviation                       number            The demand statndard deviation considered when calculating the safety stock, can be 
                                                         left empty.
do not stock                           boolean           | Indicates whether this buffer should be stocked.
                                                         | Possible values are : 
                                                         | "TRUE" : Default ROQ of 1 and safety stock of 0 will be used.
                                                         | "FALSE" : ROQ and safety stock will be calculated.
=====================================  ================= ========================================================================================
                                  
