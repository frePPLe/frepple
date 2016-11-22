=========
Locations
=========

A location is a (physical or logical) place where resources, buffers
and operations are located.

Each location has an 'available' calendar to model the working hours 
and holidays of resources, buffers and operations in that location.

**Fields**

============ ================= ===========================================================
Field        Type              Description
============ ================= ===========================================================
name         non-empty string  | Unique name of the location.
                               | This is the key field and a required attribute.
description  string            Free format description.
category     string            Free format category.
subcategory  string            Free format subcategory.
available    calendar          Calendar defining the working hours for all operations,
                               resources and buffers in the location.
owner        location          | Locations are organized in a hierarchical tree.
                               | This field defines the parent location.
members      list of location  | Locations are organized in a hierarchical tree.
                               | This field defines a list of child location.
hidden       boolean           Marks entities that are considered hidden and are normally
                               not shown to the end user.
============ ================= ===========================================================
