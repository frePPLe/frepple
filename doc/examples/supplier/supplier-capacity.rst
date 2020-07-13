=================
Supplier capacity
=================

The resource field on the item supplier allows us the model the supply 
constraints of a supplier. Purchase order placed to the supplier will
then be respect this limit in the constrained plan.

Supplier can also be associated with a calendar to model their working
days, shutdown period and public holidays. The ordering lead time will
be extended to account for these unavailable periods.

`Check this feature on a live example <https://demo.frepple.com/supplier-capacity/data/input/itemsupplier/>`_

:download:`Download an Excel spreadsheet with the data for this example <supplier-capacity.xlsx>`

Here is a step by step guide to explore the example:

* | We have a single supplier that can ship us 100 parts per week. We need to buy
    material to meet 3 sales orders from him.  

  | You can review this setup in the 
    `item supplier table <https://demo.frepple.com/supplier-capacity/data/input/itemsupplier/>`_
    which associates a resource with the purchasing. The 
    `resource table <https://demo.frepple.com/supplier-capacity/data/input/resource/>`_
    associates a capacity calendar, which can be reviewed in detail in the  
    `calendar bucket table <https://demo.frepple.com/supplier-capacity/data/input/calendarbucket/>`_.
    
  .. image:: _images/supplier-capacity-1.png
     :alt: Item suppliers

  .. image:: _images/supplier-capacity-2.png
     :alt: Resources

  .. image:: _images/supplier-capacity-3.png
     :alt: Calendar buckets

* | The supplier is also shutting down for summer holidays during July.

  | This can be reviewed in the 
    `location table <https://demo.frepple.com/supplier-capacity/data/input/location/>`_
    which associates an availability calendar to the supplier location. The details of that
    calendar can be reviewed in the
    `calendar bucket table <https://demo.frepple.com/supplier-capacity/data/input/calendarbucket/>`_.

  .. image:: _images/supplier-capacity-4.png
     :alt: Locations

* | The resulting plan can be reviewed from 
    `purchase order report <https://demo.frepple.com/supplier-capacity/data/input/purchaseorder/>`_
    and the
    `resource report <https://demo.frepple.com/supplier-capacity/resource/>`_.
    
  | The material purchases for the 1st sales order of quantity 370 are
    distributed over 4 weeks.
  
  | The material purchases for the 2nd sales order of quantity 40 take the remaining
    supplier capacity in week 4, and part of week 5. Note that for every purchase
    of product Y we consume 2 units from the supplier capacity (ie the supplier can
    only provide us 50 units/week of this item.

  | The material purchases for the 3rd sales order are placed in week 5.

  | The purchase orders for the 4th sales order due on August 2nd are adjusted
    to take this into account. We place the purchase order already at the end
    of June.
    
  .. image:: _images/supplier-capacity-5.png
     :alt: Purchase orders
    
  .. image:: _images/supplier-capacity-6.png
     :alt: Resource report
    