=========
Customers
=========

Demands are associated with a customer.

Customers can be organized in a hierarchical tree to represent the
sales organization’s structure.

FrePPLe uses customers only from reporting purposes, no real planning logic is currently linked to them.

**Fields**

============ ================= ===========================================================
Field        Type              Description
============ ================= ===========================================================
name         non-empty string  Unique name of the customer.
                               This is the key field and a required attribute.
description  string            Free format description.
category     string            Free format category.
subcategory  string            Free format subcategory.
owner        customer          Customers are organized in a hierarchical tree.
                               This field defines the parent customer.
members      list of customer  Customers are organized in a hierarchical tree.
                               This field defines a list of child customer.
hidden       boolean           Marks entities that are considered hidden and are normally
                               not shown to the end user.
============ ================= ===========================================================
