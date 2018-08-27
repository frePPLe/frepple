=================
Supplier capacity
=================

The resource field on the item supplier allows us the model the supply 
constraints of a supplier. Purchase order placed to the supplier will
then be respect this limit in the constrained plan.

Supplier can also be associated with a calendar to model their working
days, shutdown period and public holidays. The ordering lead time will
be extended to account for these unavailable periods.

.. rubric:: Example

:download:`Excel spreadsheet supplier-capacity <supplier-capacity.xlsx>`

In this example we have a single supplier that can ship us 100 parts per week.
We need to buy material to meet 3 sales orders from him.  

The supplier is also shutting down for summer holidays during July. 

- The material purchases for the 1st sales order of quantity 370 are
  distributed over 4 weeks.
  
- The material purchases for the 2nd sales order of quantity 40 take the remaining
  supplier capacity in week 4, and part of week 5. Note that for every purchase
  of product Y we consume 2 units from the supplier capacity (ie the supplier can
  only provide us 50 units/week of this item.

- The material purchases for the 3rd sales order are placed in week 5.

- The purchase orders for the 4th sales order due on August 2nd are adjusted
  to take this into account. We place the purchase order already at the end
  of June.
