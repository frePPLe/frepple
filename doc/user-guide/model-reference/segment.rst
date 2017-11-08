=======
Segment
=======

A segment is a group of item+locations, all satisfying a specific filter criterion.

**Fields**

================ ================= =====================================================================
Field            Type              Description
================ ================= =====================================================================
name             non-empty string  A unique name for this segment
description      string            A free text description.
query            string            | A SQL-like expression to identify the item-locations belonging to 
                                     the segment. All item attributes and location attributes are 
                                     available to define the filter expression
                                   | For example : item.cost between 10 and 100 and location.name 
                                     like '%shop%'
sku_count        integer           | The number of item-location combinations in the segment. 
                                   | The value is read-only and is automatically updated when a 
                                     segment is created/updated or when an inventory planning task is
                                     run.                                   
================ ================= =====================================================================
