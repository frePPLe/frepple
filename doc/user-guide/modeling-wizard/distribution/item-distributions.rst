==================
Item Distributions
==================

This table allows you to authorize the transfer of an item from one location to another location in your model.

.. rubric:: Key Fields

================ ================= ===========================================================
Field            Type              Description
================ ================= ===========================================================
item             item              The item to transfer.
location         location          The destination location where the item can be transfered.
origin           location          The origin location where the item is transfered from.
leadtime         duration          Transfer lead time, should be expressed in seconds. E.g : 604800 represents 7 days.
================ ================= ===========================================================                              
                                  
.. rubric:: Advanced topics

* Complete table description: :doc:`../../model-reference/item-distributions`
