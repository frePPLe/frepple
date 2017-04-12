=============
Business Rule
=============

This table allows to declare business rules. 

A business rule define an inventory planning parameter for all item-locations belonging to a segment. 
In this way the maintenance of inventory planning parameters can be done at a high level and in 
user-friendly way. The inventory planning parameters can still be overridden for individual 
item-locations if required.

**Fields**

================ ================= =====================================================================
Field            Type              Description
================ ================= =====================================================================
segment          non-empty string  The segment on which the business rule should apply.
business rule    non-empty string  The business rule type.
value            non-empty string  The value associated to the business rule.                                   
description      string            A description for the business rule.
================ ================= =====================================================================
