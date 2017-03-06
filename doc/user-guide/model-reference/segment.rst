=======
Segment
=======

This table allows to specify segments.

**Fields**

================ ================= =====================================================================
Field            Type              Description
================ ================= =====================================================================
name             non-empty string  A unique name for this segment
description      string            A description for this forecast record.
query            string            A SQL-like query to identify the SKUs belonging to that segment.
                                   For example : item.cost between 10 and 100 and location.name 
                                   like '%shop%'
sku_count        integer           The number of SKUs in the segment. The value is updated when a 
                                   segment is created/updated or when an inventory planning task is run.                                   
================ ================= =====================================================================
