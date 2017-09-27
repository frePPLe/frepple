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
  consumes the capacity of a resource named "Grinder".

* An operation of type time_per named "PAINT". The **item** field of the operation table must be empty.
  This operation follows the grinding operation and requires paint pots.

* An operation named "DRY" that is an operation of type fixed_time as whether one or a hundred parts have to dry,
  it is going to take the same time. The **item** field of the operation table must be empty.
  
**Operation table:**

===================  ================= ==========
Operation            Item              Type  
===================  ================= ==========
Build Product        Product           routing
GRIND                                  time_per
PAINT                                  time_per
DRY                                    fixed_time
===================  ================= ==========

Now that the four operations have been declared, we need to fill the table suboperation to declare that operations GRIND, 
PAINT and DRY are suboperations of "Build Product" operation and also declare in which sequence these operations are performed.
To define the suboperations sequence, the priority field should be used :

**Suboperation table:**

===================  ================= ==========
Operation            suboperation      priority  
===================  ================= ==========
Build Product        GRIND             1
Build Product        PAINT             2
Build Product        DRY               3
===================  ================= ==========

Last but not least, table operationmaterial has to be filled. Any suboperation can consume items 
(though this is not of course mandatory) but only the last
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

