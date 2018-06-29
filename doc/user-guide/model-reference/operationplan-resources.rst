=======================
Operationplan resources
=======================

This table models the resource consumption associated with an operationplan.

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
================ ================= ===========================================================
