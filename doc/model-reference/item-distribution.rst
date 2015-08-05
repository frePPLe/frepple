=================
Item Distribution
=================

Defines an item that can be shipped from an origin location to a destination location.

The association can be date effective and also has a priority.

**Fields**

=============== ================= ===========================================================
Field           Type              Description
=============== ================= ===========================================================
item            item              | Reference to the item.
                                  | This is a required attribute.
                                  | The item can point to a parent level in the item 
                                    hierarchy. All child items can then be distributed using
                                    this definition.
origin          location          | Origin location from where we can ship the item.
                                  | The location can point to a higher level in the location
                                    hierarchy. Any child location can then ship the item.
                                  | The default value of this field is empty. In such case
                                    any location can be used as origin.
destination     location          | Destination location to where we can ship the item.
                                  | The location can point to a higher level in the location
                                    hierarchy. Any child location can then receive the item.
                                  | The default value of this field is empty. In such case
                                    any location can be used as destination.
cost            positive double   Shipment cost.
leadtime        duration          Shipment lead time.
size_minimum    positive double   | Minimum size for shipments.
                                  | The default is 1.
size_multiple   positive double   | All shipments must be a multiple of this quantity.
                                  | The default is 0, i.e. no multiple to be considered.                                  
effective_start dateTime          Date when the record becomes valid.
effective_end   dateTime          Date when the record becomes valid.
priority        integer           | Priority of this shipment among all other methods to
                                    replenish a buffer.
                                  | A lower number indicates that this shipment is preferred
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

Adding or changing item distributions

.. code-block:: XML

    <plan>
       <items>
         <item name="All components">
            <itemdistributions>
               <itemdistribution/>
                 <origin name="Location A"/>
                 <destination name="Location B"/>
                 <leadtime>P7D</leadtime>
               </itemdistribution>
            </itemdistributions>
         <item>
       </items>
    </plan>

Deleting an item distribution

.. code-block:: XML

    <plan>
       <items>
         <item name="All components">
            <itemdistributions>
               <itemdistribution action="R"/>
                 <origin name="Location A"/>
                 <destination name="Location B"/>
               </itemdistribution>
            </itemdistributions>
         <item>
       </items>
    </plan>

**Example Python code**

Adding or changing item distributions

::

    item = frepple.item(name="All components")
    ori = frepple.location(name="Location A")
    dest = frepple.location(name="Location B")
    frepple.itemdistribution(item=item, origin=ori, destination=dest, leadtime=7*86400, priority=1)

Iterate over item distributions

::

    for m in frepple.items():
      print("Following shipments are possible with item '%s':" % m.name)
      for i in m.itemdistributions:
        print(
          " ", i.origin.name if i.origin else None, 
          i.destination.name if i.destionation else None, 
          i.cost, i.effective_start, i.effective_end
          )
