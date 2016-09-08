=======
Buffer
=======

A buffer is a storage for a item. It represents a place where inventory of an item is kept. It's often called SKU, i.e. it's a unique item-location combination.


Key Fields
----------

============ ================= ============================================================
Field        Type              Description
============ ================= ============================================================
name         non-empty string  Name of the buffer, we recommend that you use the format                                
                               "item @ location". E.g : keyboard @ factory1
location     non-empty string          Location of the buffer.         
item         non-empty string              Item being stored in the buffer.                                   
onhand       number            | Inventory level at the start of the time horizon.
                               | Considered as 0 if left empty.
============ ================= ============================================================                                 
                                  
Advanced topics
---------------

* Complete table description: :doc:`../../model-reference/buffer`
