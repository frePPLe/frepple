==============
Item Suppliers
==============

This table defines the supplier(s) that can procure an item.


Key Fields
----------

=============== ================= ===========================================================
Field           Type              Description
=============== ================= ===========================================================
supplier        non-empty string  The name of the supplier.
item            non-empty string  The name of the item you procurable from that supplier.
location        non-empty string  The name of the location where the supplier can be used to purchase this item.                                 
cost            number            Purchasing cost.
leadtime        duration          Procurement lead time, should be expressed in seconds. E.g : 604800 represents 7 days.
priority        integer           | Priority of this supplier among all suppliers from which
                                    this item can be procured.
                                  | A lower number indicates that this supplier is preferred
                                    when the item is required. 
                                  | If a demand cannot be delivered on time with the primary supplier, the algorithm will try with secondary supplier(s).
=============== ================= ===========================================================
                                  
Advanced topics
---------------

* Complete table description: :doc:`../../model-reference/item-suppliers`
