==================
Item distributions
==================

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
origin          location          Origin location from where we can ship the item.                               
destination     location          | Destination location to where we can ship the item.                                  
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
                                  | When the priority is 0, the item distribution is not
                                    actively used during planning. 
resource        resource          | Optionally, it refers to a resource that represents the
                                    distribution capacity.
                                  | The referenced resource will typically be of type
                                    'buckets'.
resource_qty    positive double   | Resource capacity consumed per distributed unit.
fence           duration          | Release fence for the purchasing operations.
                                  | New purchases cannot be proposed within this time fence
                                    after the plan current date.
=============== ================= ===========================================================
