==============
Item suppliers
==============

This table defines which items can be procured from which supplier.

Multiple suppliers can be defined for the same item.


.. rubric:: Key Fields

=============== ================= ===========================================================
Field           Type              Description
=============== ================= ===========================================================
supplier        supplier          The name of the supplier.
item            item              The name of the item you procure from that supplier.
location        location          The name of the location where the supplier can be used to purchase this item.                                 
leadtime        duration          Procurement lead time, should be expressed in seconds. E.g : 604800 represents 7 days.
cost            number            Purchasing cost. This info is optional.
priority        integer           | Priority of this supplier among all suppliers from which
                                    this item can be procured.
                                  | A lower number indicates that this supplier is preferred
                                    when the item is required. 
                                  | If a demand cannot be delivered on time with the primary supplier, the algorithm will try with secondary supplier(s).
=============== ================= ===========================================================
                                  
.. rubric:: Advanced topics

* Complete table description: :doc:`../../model-reference/item-suppliers`
