=======================
Operationplan resources
=======================

This table records the planned capacity consumption. The capacity consumption is associated with 
on manufacturing orders, purchase orders or distribution orders.

**Fields**

================ ================= ===========================================================
Field            Type              Description
================ ================= ===========================================================
operationplan    operationplan     The operationplan consuming the resource.
resource         resource          The name of the resource being utilized.
quantity         double            Size of the resource loading.
startdate        dateTime          Start of the resource loading.
enddate          dateTime          End of the resource loading.
setup            string            | Setup of the resource when executing this loadplan.
                                   | This can be either the setup required by this particular
                                     load, or the setup left by any previous loadplans on the
                                     resource.
                                   | This is an export-only field.                        
================ ================= ===========================================================
