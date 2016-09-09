===============
Item Distributions
===============

This table allows you to authorize the transfer of an item from a location in your model to another location in your model.



Key Fields
----------

================ ================= ===========================================================
Field            Type              Description
================ ================= ===========================================================
item             non-empty string  The item to transfer.
location         non-empty string  The destination location where the item can be transfered.
origin           non-empty string  The origin location where the item is transfered from.
leadtime         duration          Transfer lead time, should be expressed in seconds. E.g : 604800 represents 7 days.
================ ================= ===========================================================                              
                                  
Advanced topics
---------------

* Complete table description: :doc:`../../model-reference/item-distributions`
