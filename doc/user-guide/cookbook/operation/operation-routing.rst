==================
Operation Routings
==================

It is possible in frePPLe to declare an operation of type routing.
This operation type represents a set of suboperations that must be run in sequence.
It is not possible to define a buffer between two suboperations of a routing operation.

.. image:: _images/routing.png
   :height: 375 px
   :width: 1210 px
   :scale: 100 %
   :alt: An example of a routing

In the above example, four operations have to be defined in the operation table :

* An operation named "Build Product" of type "routing" : by declaring this operation as a routing operation, 
  you are modeling a virtual operation that is actually composed of other (real) operations in sequence.
  The **item** field of the operation table has to be filled with the produced item of the routing: 
  Product in our example. 

* An operation of type time_per named "GRIND" to grind the raw product. 
  The **item** field of the operation table must be empty. Note that this operation
  consumes the capacity of a resource named "Grinder". The owner field should refer to the routing this 
  operation belongs to. The priority corresponds to the operation sequence and should be equal to 1
  as this is the first operation of the routing.

* An operation of type time_per named "PAINT". The **item** field of the operation table must be empty.
  This operation follows the grinding operation and requires paint pots. The owner field should refer to the routing this 
  operation belongs to. The priority corresponds to the operation sequence and should be equal to 2
  as this is the second operation of the routing.

* An operation named "DRY" that is an operation of type fixed_time as whether one or a hundred parts have to dry,
  it is going to take the same time. The **item** field of the operation table must be empty. The owner field should refer to the routing this 
  operation belongs to. The priority corresponds to the operation sequence and should be equal to 3
  as this is the third operation of the routing.
  
**Operation table:**

===================  ================= ========== =============  ========
Operation            Item              Type       Owner          Priority
===================  ================= ========== =============  ========
Build Product        Product           routing        
GRIND                                  time_per   Build Product  1
PAINT                                  time_per   Build Product  2
DRY                                    fixed_time Build Product  3
===================  ================= ========== =============  ========

Now that the four operations have been declared, we need to fill the table suboperation to declare that operations GRIND, 
PAINT and DRY are suboperations of "Build Product" operation and also declare in which sequence these operations are performed.
To define the suboperations sequence, the priority field should be used :

Last but not least, table operationmaterial has to be filled. Any operation (except the rouing operation) can consume items 
(though this is of course not mandatory) but only the last
suboperation in the sequence can produce an item :

**Operationmaterial table:**

===================  ================= ==========
Operation            item              quantity  
===================  ================= ==========
GRIND                Raw Product       -1
PAINT                Paint pot         -1
DRY                  Product           1
===================  ================= ==========

The model described above can be found in the following Excel file:

:download:`Excel spreadsheet operation-routing <operation-routing.xlsx>`

