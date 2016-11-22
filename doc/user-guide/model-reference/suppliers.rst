=========
Suppliers
=========

A supplier ships us items.

**Fields**

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
members          list of supplier  | Suppliers can be organized in a hierarchical tree.
                                   | This field defines a list of child suppliers.
available        calendar          | Calendar defining the holiday schedule of the supplier.
                                   | Procurements will be stretched to account for the
                                     unavailable time.
================ ================= ===========================================================
