========
Customer
========

Demands are associated with a customer.

Customers can be organized in a hierarchical tree to represent the
sales organization’s structure.

FrePPLe uses customers only from reporting purposes, no real planning logic is currently linked to them.

**Fields**

============ ================= ===========================================================
Field        Type              Description
============ ================= ===========================================================
name         non-empty string  Name of the customer.
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
action       A/C/AC/R          | Type of action to be executed:
                               | A: Add an new entity, and report an error if the entity
                                 already exists.
                               | C: Change an existing entity, and report an error if the
                                 entity doesn’t exist yet.
                               | AC: Change an entity or create a new one if it doesn’t
                                 exist yet. This is the default.
                               | R: Remove an entity, and report an error if the entity
                                 doesn’t exist.
============ ================= ===========================================================

**Example XML structures**

Adding or changing a customer

.. code-block:: XML

  <plan>
    <customers>
       <customer name="customer A" category="Direct"/>
    </customers>
  </plan>

Deleting a customer

.. code-block:: XML

  <plan>
    <customers>
       <customer name="customer A" action="R"/>
    </customers>
  </plan>

**Example Python code**

Adding or changing a customer

::

   cust = frepple.customer(name="customer A", category="Direct")

Deleting a customer

::

  cust = frepple.customer(name="customer A", action="R")
