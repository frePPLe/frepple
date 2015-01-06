=============
Supplier Item
=============

Defines an item that can be procured from a certain supplier.

The association can be date effective and also has a priority.

**Fields**

=============== ================= ===========================================================
Field           Type              Description
=============== ================= ===========================================================
supplier        supplier          | Reference to the supplier.
                                  | This is a key field and a required attribute.
item            item              | Reference to the item.
                                  | This is a key field and a required attribute.
cost            positive double   Purchasing cost.
leadtime        duration          Procurement lead time.
size_minimum    positive double   | Minimum size for procurements.
                                  | The default is 1.
size_multiple   positive double   | All procurements must be a multiple of this quantity.
                                  | The default is 0, i.e. no multiple to be considered.                                  
effective_start dateTime          Date when the resource gains this skill.
effective_end   dateTime          Date when the resource loses this skill.
priority        integer           | Priority of this supplier among all suppliers from which
                                    this item can be procured.
                                  | A lower number indicates that this supplier is preferred
                                    when the item is required. This field is used when the
                                    search policy is PRIORITIY.
action          A/C/AC/R          | Type of action to be executed:
                                  | A: Add an new entity, and report an error if the entity
                                    already exists.
                                  | C: Change an existing entity, and report an error if the
                                    entity doesn’t exist yet.
                                  | AC: Change an entity or create a new one if it doesn’t
                                    exist yet. This is the default.
                                  | R: Remove an entity, and report an error if the entity
                                    doesn’t exist.
=============== ================= ===========================================================

**Example XML structures**

Adding or changing supplier items

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

Deleting a supplier item

.. code-block:: XML

    <plan>
       <suppliers>
         <supplier name="Company X">
            <supplieritems>
               <supplieritem name="Component A" action="R"/>
            </supplieritems>
         <supplier>
       </suppliers>
    </plan>

**Example Python code**

Adding or changing supplier items

::

    item = frepple.item(name="Component A")
    supplier = frepple.supplier(name="Company X")
    frepple.supplieritem(resource=resource, skill=skill, priority=1)

Iterate over suppliers and assigned items

::

    for m in frepple.suppliers():
      print("Following items are supplier by '%s':" % m.name)
      for i in m.supplieritems:
        print(" ", i.item.name, i.cost, i.effective_start, i.effective_end)

Iterate over items and possible suppliers

::

    for m in frepple.items():
      print("Item '%s' has suppliers:" % m.name)
      for i in m.resourceskills:
        print(" ", i.supplier.name, i.cost, i.effective_start, i.effective_end)
