==========
Operations
==========

An operation is a manufacturing operation consuming some items (a bill of material) to produce a new item.
It also loads a number of resources during this process.

.. rubric:: Key Fields

=====================================  ================= ========================================================================================
Field                                  Type              Description
=====================================  ================= ========================================================================================
name                                   non-empty string  Unique name of the operation.
duration                               duration          Fixed operation time in seconds, independent of the units produced.
duration_per                           duration          The operation time in seconds, per unit produced.
type                                   non-empty string  | Possible values : "time_per", "fixed_time", "routing", "alternate", "split".
                                                         | time_per : The operation duration is multiplied by the number of produced items.
                                                                      This is typical for manufacturing, producing three items takes three times the
                                                                      duration of producing one item.
                                                         | fixed_time : The operation duration is fixed whatever the number of produced items is.
location                               location          The location where the operation takes place.
=====================================  ================= ========================================================================================

.. rubric:: Advanced topics

* Complete table description: :doc:`../../model-reference/operations`

* Modeling operation types: :doc:`../../cookbook/operation/operation-type`

* Modeling post-operation safety time: :doc:`../../cookbook/operation/operation-posttime`
