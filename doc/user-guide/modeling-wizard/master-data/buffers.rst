=======
Buffers
=======

A buffer is in (logical of physical) inventory point for a item at a certain location.

.. rubric:: Key Fields

============ ================= ============================================================
Field        Type              Description
============ ================= ============================================================
name         non-empty string  The name of the buffer must follow the pattern                                
                               "item @ location", ie a concatenation of the next 2 columns.
location     location          Location of the buffer.         
item         item              Item being stored in the buffer.                                   
onhand       number            | Inventory level at the start of the time horizon.
                               | Considered as 0 if left empty.
============ ================= ============================================================                                 
                                  
.. rubric:: Advanced topics

* Complete table description: :doc:`../../model-reference/buffers`
