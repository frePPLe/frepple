===============
Resource detail
===============

This table records the assigned resources. The capacity consumption is associated with
on manufacturing orders, purchase orders or distribution orders.

================ ================= ===========================================================
Field            Type              Description
================ ================= ===========================================================
reference        MO/PO/DO/DLVR     The reference of the manufacturing order, purchase order,
                                   distribution order or delivery order consuming the capacity.
resource         resource          The name of the resource being utilized.
quantity         double            Size of the resource loading.
startdate        dateTime          | Start of the resource loading.
                                   | This is an export-only field.
enddate          dateTime          | End of the resource loading.
                                   | This is an export-only field.
setup            string            | Setup of the resource when executing this loadplan.
                                   | This can be either the setup required by this particular
                                     load, or the setup left by any previous loadplans on the
                                     resource.
                                   | This is an export-only field.
================ ================= ===========================================================
