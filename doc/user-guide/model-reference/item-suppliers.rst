==============
Item suppliers
==============

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
                                  | The item can point to a parent level in the item
                                    hierarchy. The supplier can then be used for any item
                                    belonging to that group.
location        location          | Reference to the location where the supplier can be used
                                    to purchase this item.
                                  | The default value of this field is empty. In such case
                                    the supplier is valid at any location.
cost            positive double   Purchasing cost.
leadtime        duration          Procurement lead time.
size_minimum    positive double   | Minimum size for procurements.
                                  | The default is 1.
size_multiple   positive double   | All procurements must be a multiple of this quantity.
                                  | The default is 0, i.e. no multiple to be considered.
effective_start dateTime          Date when the record becomes valid.
effective_end   dateTime          Date when the record becomes valid.
resource        resource          | Optionally, it refers to a resource that represents the
                                    supplier capacity.
                                  | The referenced resource will typically be of type
                                    'buckets'.
resource_qty    positive double   | Resource capacity consumed per purchased unit.
fence           duration          | Release fence for the distribution operation.
                                  | New shipments cannot be proposed within this time fence
                                    after the plan current date.
priority        integer           | Priority of this supplier among all suppliers from which
                                    this item can be procured.
                                  | A lower number indicates that this supplier is preferred
                                    when the item is required. This field is used when the
                                    search policy is PRIORITIY.
                                  | When the priority is 0, the item supplier is not
                                    actively used during planning.                                     
=============== ================= ===========================================================
