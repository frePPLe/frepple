=======================
Operationplan materials
=======================

This table models the material consumption or production associated with an operationplan.

**Fields**

================ ================= =================================================================================
Field            Type              Description
================ ================= =================================================================================
operationplan    operationplan     The operationplan consuming the resource
item             item              The item being produced or consumed.
location         location          The item where material is produced or consumed.
quantity         double            Size of the material consumption or production.
flowdate         dateTime          Date of material consumption or production.
onhand           double            | Inventory in the buffer after the execution of this
                                     operationplan.
                                   | This is field is export only.
status           non-empty string  | This field should have one of the following keywords :
                                   | proposed : Planned consumption computed by frePPLe.
                                   | approved : Approved consumption from the ERP which can still be rescheduled.
                                   | confirmed : Frozen consumption from the ERP that is completely locked.
                                   | closed : Consumption has happened.
================ ================= =================================================================================
