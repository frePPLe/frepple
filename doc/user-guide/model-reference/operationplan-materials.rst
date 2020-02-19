================
Inventory detail
================

This table models the material consumption or production. The material movements are associated with 
on hand inventory, purchase orders, distribution orders, manufacturing orders or delivery orders to customers. 

================ ================= =================================================================================
Field            Type              Description
================ ================= =================================================================================
reference        MO/PO/DO/DLVR     A reference to the manufacturing order, purchase order or distribution order
                                   consuming or producing the material.
item             item              The item being produced or consumed.
location         location          The item where material is produced or consumed.
quantity         double            Size of the material consumption or production.
date             dateTime          Date of material consumption or production.
onhand           double            | Inventory in the buffer after the execution of this manufacturing order, 
                                     purchase order or distribution order.
                                   | This is field is export only.
status           string            This field should have one of the following keywords:

                                   - | proposed:
                                     | Planned consumption computed by frePPLe.
                                     | These records are output of the planning algorithm.
                                     
                                   - | confirmed:
                                     | Frozen consumption from the ERP that is completely locked.
                                     | These records are input to the planning algorithm.

                                   - | closed:
                                     | Consumption has happened.
                                     | These records are input to the planning algorithm.
================ ================= =================================================================================
