====
Item
====

An item represents an end product, intermediate product or a raw material.

Each demand is associated with an item.

A buffer is also associated with an item: it represents a storage of the item
at a certain location.

**Fields**

============ ================= ===========================================================
Field        Type              Description
============ ================= ===========================================================
name         non-empty string  | Name of the item.
                               | This is the key field and a required attribute.
description  string            Free format description.
category     string            Free format category.
subcategory  string            Free format subcategory.
owner        item              | Items are organized in a hierarchical tree.
                               | This field defines the parent item.
members      list of item      | Items are organized in a hierarchical tree.
                               | This field defines a list of child items.
operation    operation         | This is the operation used to satisfy a demand for this
                                 item.
                               | If left unspecified the value is inherited from the parent
                                  item.
                               | See also the OPERATION field on the DEMAND.
price        double            | Cost or price of the item.
                               | Depending on the precise usage and business goal it should
                                 be evaluated which cost to load into this field: purchase
                                 cost, booking value, selling price...
                               | For most applications the booking value is the appropriate
                                 one.
                               | The default value is 0.
buffers      list of buffer    Returns the list of buffers for this item.
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

Adding or changing an item and its delivery operation

.. code-block:: XML

  <plan>
    <items>
      <item name="item A">
        <operation name="Delivery of item A" xsi:type="operation_fixed_time">
          <duration>24:00:00</duration>
        </operation>
        <owner name="Item class A"/>
      </item>
    </items>
  </plan>

Deleting an item

.. code-block:: XML

   <plan>
     <items>
       <item name="item A" action="R"/>
     </items>
   </plan>

**Example Python code**

Adding or changing an item and its delivery operation

::

    oper = frepple.operation_fixed_time(name="Deliver item A", duration=24*3600)
    it1 = frepple.item(name="Item class A")
    it2 = frepple.item(name="item A", operation=oper, owner=it1)

Deleting an item

::

   frepple.item(name="item A", action="R")
