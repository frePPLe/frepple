=========
Suppliers
=========

A supplier from which we can purchase items.

================ ================= ===========================================================
Field            Type              Description
================ ================= ===========================================================
name             non-empty string  | Unique name of the supplier.
                                   | This is the key field and a required attribute.
description      string            Free format description.
category         string            Free format category.
subcategory      string            Free format subcategory.
owner            resource          | Suppliers can be organized in a hierarchical tree.
                                   | This field defines the parent supplier.
available        calendar          | Calendar defining the holiday schedule of the supplier.
                                   | Procurements will be stretched to account for the
                                     unavailable time.
================ ================= ===========================================================
