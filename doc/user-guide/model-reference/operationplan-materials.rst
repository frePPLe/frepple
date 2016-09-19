=======================
operationplan materials
=======================

This table models the material consumption or production associated with an operationplan.

**Fields**

================ ================= ===========================================================
Field            Type              Description
================ ================= ===========================================================
operationplan    operationplan     The operationplan consuming the resource
buffer           buffer            The buffer where the operationplan is producing or
                                   consuming material.
quantity         double            Size of the material consumption or production.
flowdate         dateTime          Date of material consumption or production.
onhand           double            Inventory in the buffer after the execution of this
                                   operationplan.
================ ================= ===========================================================
