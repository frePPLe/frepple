=========
Suppliers
=========

A supplier ships us items.

**Fields**

================ ================= ===========================================================
Field            Type              Description
================ ================= ===========================================================
name             non-empty string  | Name of the supplier.
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
action           A/C/AC/R          | Type of action to be executed:
                                   | A: Add an new entity, and report an error if the entity
                                     already exists.
                                   | C: Change an existing entity, and report an error if the
                                     entity doesn’t exist yet.
                                   | AC: Change an entity or create a new one if it doesn’t
                                     exist yet. This is the default.
                                   | R: Remove an entity, and report an error if the entity
                                     doesn’t exist.
================ ================= ===========================================================
