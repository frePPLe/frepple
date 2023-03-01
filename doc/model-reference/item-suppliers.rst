==============
Item suppliers
==============

Defines an item that can be purchased from a certain supplier.

The association can be date effective and also has a priority.

===================== ================= ===========================================================
Field                 Type              Description
===================== ================= ===========================================================
supplier              supplier          | Reference to the supplier.
                                        | This is a key field and a required attribute.
item                  item              | Reference to the item.
                                        | This is a key field and a required attribute.
                                        | The item can point to a parent level in the item
                                          hierarchy. The supplier can then be used for any item
                                          belonging to that group.
location              location          | Reference to the location where the supplier can be used
                                          to purchase this item.
                                        | The default value of this field is empty. In such case
                                          the supplier is valid at any location.
cost                  positive double   Purchasing cost.
leadtime              duration          Procurement lead time.
size_minimum          positive double   | Minimum size for procurements.
                                        | The default is 1.
size_multiple         positive double   | All procurements must be a multiple of this quantity.
                                        | The default is 0, i.e. no multiple to be considered.
size_maximum          positive double   | Maximum size for procurements.
                                        | The default is infinite, i.e. no maximum to be considered.
batchwindow           duration          | Allows to group proposed purchase orders within this window
                                          together into a single one.
                                        | The default is 7 days, i.e. the algorithm will not propose
                                          to buy the same item twice during the same week.
hard_safety_leadtime  duration          | Adds additional time on top of the standard lead time.
                                        | This additional lead time is a hard constraint: material
                                          can only be used a certain time after the purchase order
                                          is received. This delay represents time for quality control,
                                          material reception, administrative time, etc... that cannot
                                          be reduced or skipped.
                                        | The default is 0.
soft_safety_leadtime  duration          | Adds a safety lead time on top of standard lead time.
                                        | The soft safety lead time is a soft constraint: we try
                                          to receive the material this amount of time before the
                                          actual requirement date. But in case of shortages we can
                                          relax this and receive material closer to the requirement
                                          date.
                                        | The default is 0.
effective_start       dateTime          Date when the record becomes valid.
effective_end         dateTime          Date when the record becomes valid.
resource              resource          | Optionally, it refers to a resource that represents the
                                          supplier capacity.
                                        | The referenced resource will typically be of type
                                          'buckets'.
resource_qty          positive double   | Resource capacity consumed per purchased unit.
fence                 duration          | Release fence for the distribution operation.
                                        | New shipments cannot be proposed within this time fence
                                          after the plan current date.
priority              integer           | Priority of this supplier among all suppliers from which
                                          this item can be procured.
                                        | A lower number indicates that this supplier is preferred
                                          when the item is required. This field is used when the
                                          search policy is PRIORITIY.
                                        | When the priority is 0, the item supplier is not
                                          automatically used during planning. Only a planner can
                                          manually create purchase orders on it.
===================== ================= ===========================================================