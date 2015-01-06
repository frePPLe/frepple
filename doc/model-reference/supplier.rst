========
Supplier
========

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

**Example XML structures**

Adding or changing a supplier

.. code-block:: XML

    <plan>
      <suppliers>
        <supplier name="Company X">
          <supplieritems>
             <supplieritem>
               <item name="component A"/>
               <leadtime>P10D</leadtime>
             </supplieritem>
          </supplieritems>
        </supplier>
      </suppliers>
    </plan>

Deleting a supplier

.. code-block:: XML

    <plan>
       <suppliers>
          <supplier name="Compnay X" action="R"/>
       </suppliers>
    </plan>

**Example Python code**

Adding or changing a supplier

::

    sup_X = frepple.supplier(name="Company X")

Deleting a supplier

::

    frepple.supplier(name="Company X", action="R")

Iterate over suppliers and the items they supply

::

    for r in frepple.suppliers():
      print("Supplier:", r.name, r.description, r.category)
      for l in r.supplieritems:
        print("  Item:", l.item.name, l.leadtime, l.cost)
