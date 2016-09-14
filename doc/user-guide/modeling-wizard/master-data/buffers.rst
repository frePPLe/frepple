=======
Buffers
=======

A buffer is a storage for a item. It represents a place where inventory of an item is kept. 
It's often called SKU, i.e. it's a unique item-location combination.


.. rubric:: Key Fields

============ ================= ============================================================
Field        Type              Description
============ ================= ============================================================
name         non-empty string  Name of the buffer, we recommend that you use the format                                
                               "item @ location". E.g : keyboard @ factory1
location     location          Location of the buffer.         
item         item              Item being stored in the buffer.                                   
onhand       number            | Inventory level at the start of the time horizon.
                               | Considered as 0 if left empty.
============ ================= ============================================================                                 
                                  
.. rubric:: Advanced topics

* Complete table description: :doc:`../../model-reference/buffers`
