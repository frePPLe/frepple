===============================
Make-to-order and make-to-stock
===============================

FrePPLe can model complex supply chains with make-to-order, make-to-stock
and configure-to-order characteristics.

In this example we demonstrate some typical examples:

* The item A has a **complete make-to-stock** supply path. Its subassembly
  and raw materials are all planned in make-to-stock mode.
  
* The item B has a **complete make-to-order** supply path. All of the 
  subassemblies and raw materials are specific to the sales order.
  
* The item C has a **configure-to-order** supply path. It combines 
  make-to-order manufacturing operations for the final production 
  operations with some make-to-stock components and subassemblies.
  
* | The item D shows **serialized production**. The end items are managed
    and planned in make-to-stock mode, but the manufacturing operations
    are planned in make-to-order mode with serialized production batches
    that move between production stages.
  | This is a common scenario in pharmaceutical or chemical industries
    where full traceability of the production is important.
    
* The item E shows an **attribute-based** supply path. The finished item
  can be sold in different colors (or size, or any other attribute) and the
  supply paths per color need to be kept seperate.

* | There is yet more functionality that is not shown in this example!
  | Make to order items can also have generic supply that can be allocated
    to any batch. The planning algorithm will automatically assign such 
    free and unallocated availability.
  
`Check this feature on a live example <https://demo.frepple.com/make-to-order/data/input/manufacturingorder/>`_

:download:`Download an Excel spreadsheet with the data for this example<make-to-order.xlsx>`

Here is a step by step guide to explore the example:

* | At first sight the supply paths of all products look identical:
    `supply path for item A <https://demo.frepple.com/make-to-order/supplypath/item/A%20-%20end%20item/>`_,
    `supply path for item B <https://demo.frepple.com/make-to-order/supplypath/item/B%20-%20end%20item/>`_,
    `supply path for item C <https://demo.frepple.com/make-to-order/supplypath/item/C%20-%20end%20item/>`_,
    `supply path for item D <https://demo.frepple.com/make-to-order/supplypath/item/D%20-%20end%20item/>`_ and
    `supply path for item E <https://demo.frepple.com/make-to-order/supplypath/item/D%20-%20end%20item/>`_

  .. image:: _images/make-to-order-1.png
     :alt: Supply path
        
* The key tables to study the specifics of this model are:

  * | The type field in the `item table <https://demo.frepple.com/make-to-order/data/input/item/>`_
      can be set to "make to order" or "make to stock".
    | The type is set to "make to order" for all items where inventory, production and
      consumption is managed per batch. Material of different batches is planned 
      seperately and can't be mixed.
    | The type is set to to "make to stock" when the inventory, production and is
      managed aggregated across all demands.
        
  * | The batch field in the `sales order table <https://demo.frepple.com/make-to-order/data/input/demand/>`_
      specifies which items can be used to meet the demand. Cases B, C and E have batch information
      on the sales orders that needs to be passed on to manufacturing orders and purchase orders.

  * | The batch field in the `buffer table <https://demo.frepple.com/make-to-order/data/input/buffer/>`_
      allows to specifies to specify stocks by batch.


* | The item A is a **make-to-stock** product.

  In the input data all items in the supply path are marked "make to stock" :samp:`A`. 
  Also, the sales orders don't have the batch field :samp:`B` filled in.

  In the output plan, the manufacturing orders and purchase orders generated to meet
  the demand all have an empty batch field :samp:`C`.
  
  .. image:: _images/make-to-order-A1.png
     :alt: Configuration for item A

  .. image:: _images/make-to-order-A4.png
     :alt: Sales orders for item A
       
  .. image:: _images/make-to-order-A2.png
     :alt: Manufacturing orders for item A
  
  .. image:: _images/make-to-order-A3.png
     :alt: Purchase orders for item A
  
* | Item B is a **make-to-order** product. 


  | All items in the supply path are marked "make to order". The batch field
    on the sales orders is set to the sales orders' unique name.
    
  | When frePPLe generates the plan, the batch number specified on the demands is 
    automatically propagated to all manufacturing orders and purchase orders in the
    supply path.
 
  | Material cannot be shared/exchanged between batches. In the buffer table you can 
    see there is inventory of component 1, but it can't be used because it's reserved
    for another order "B - order X". (Excercise: change the batch number to one of the 
    sales orders of this end item, regenerate the plan, and verify that this time the
    stock can be used and we have one less purchase order).
  
  .. image:: _images/make-to-order-B1.png
     :alt: Configuration for item B
  
  .. image:: _images/make-to-order-B4.png
     :alt: Sales orders for item B
  
  .. image:: _images/make-to-order-B2.png
     :alt: Manufacturing orders for item A
  
  .. image:: _images/make-to-order-B3.png
     :alt: Purchase orders for item B

* | Item C is a **configure-to-order** product.

  | The end item and the assembly are produced in make-to-order mode. The batch 
    information is propagated from the sales orders to the manufacturing orders
    and the purchase orders of component 1.
    
  | The other parts of the supply path are planned in make-to-stock mode. No batch
    information is seen on these purchase orders and manufacturing orders.
    
  .. image:: _images/make-to-order-C1.png
     :alt: Configuration for item C

  .. image:: _images/make-to-order-C4.png
     :alt: Sales orders for item C
       
  .. image:: _images/make-to-order-C2.png
     :alt: Manufacturing orders for item C
  
  .. image:: _images/make-to-order-C3.png
     :alt: Purchase orders for item C
  
* | Item D shows **serialized production**. 

  | The final product is make-to-stock, but part of the supply path consists
    of "make to order" items. The subassembly, assembly and end item 
    operations are linked to each other with a batch number that is automatically
    generated by frePPLe.

  .. image:: _images/make-to-order-D1.png
     :alt: Configuration for item D

  .. image:: _images/make-to-order-D4.png
     :alt: Sales orders for item D
       
  .. image:: _images/make-to-order-D2.png
     :alt: Manufacturing orders for item D
  
  .. image:: _images/make-to-order-D3.png
     :alt: Purchase orders for item D
  
* | Item E demonstrates **attribute-based planning**. The end item E is available
    in 2 colors: green and yellow.
  | The green version of item E has enough inventory, and no manufacturing orders
    or purchase orders are generated.
  | The inventory of the yellow item E is running low, and we need to launch another
    production batch. The batch field on the manufacturing order tells us the
    color of the item we need to produce.
  
  .. image:: _images/make-to-order-E1.png
     :alt: Configuration for item E

  .. image:: _images/make-to-order-E5.png
     :alt: Sales orders for item E
       
  .. image:: _images/make-to-order-E2.png
     :alt: Manufacturing orders for item E
  
  .. image:: _images/make-to-order-E3.png
     :alt: Purchase orders for item E
  
  .. image:: _images/make-to-order-E4.png
     :alt: Buffers
