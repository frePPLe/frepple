===================
Operation materials
===================

The Operation Materials table defines what item(s) an operation is consuming and producing.

If an operation Op is consuming 2 units of part A and 1 unit of part B to produce 1 unit of
part C, then this table should contain three records:

=========    ========      ====      =====  
operation    quantity      item      type
=========    ========      ====      =====
Op           -2            A         Start
Op           -1            B         Start
Op           1             C         End
=========    ========      ====      =====

.. rubric:: Key Fields

=====================================  ================= ========================================================================================
Field                                  Type              Description
=====================================  ================= ========================================================================================
operation                              operation         The operation name consuming and producing items.
quantity                               number            The quantity of item consumed or produced. A negative quantity should be used for 
                                                         consumed items and positive quantity should be used for produced items.
item                                   item              The item being consumed or produced.  
type                                   non-empty string  | This field is used to specify whether the stock should be consumed/produced at the 
                                                           start or at the end of the operation.
                                                         | Possible values : "Start", "End", "Fixed start", "Fixed end".
                                                         | Start : This is typical to consumed items. The item is consumed at the beginning of
                                                           the operation.
                                                         | End : This is typical to produced items. The item is produced at the end of the 
                                                           operation.
=====================================  ================= ========================================================================================
                                  
.. rubric:: Advanced topics

* Complete table description: :doc:`../../model-reference/operation-materials`
