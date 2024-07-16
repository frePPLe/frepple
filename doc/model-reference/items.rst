=====
Items
=====

An item represents an end product, intermediate product or a raw material.

=============== ================= ===========================================================
Field           Type              Description
=============== ================= ===========================================================
name            non-empty string  | Unique name of the item.
                                  | This is the key field and a required attribute.
type            string            Type of item:

                                  * | make to stock (default):
                                    | Inventory, production and consumption of this item is
                                      managed aggregated.

                                  * | make to order:
                                    | Inventory, production and consumption of this item is
                                      managed per batch. Material of different batches is
                                      planned seperately and can't be mixed. A batch can
                                      represent a sales order, a serial number, or an item
                                      attribute (such as color).

                                  | Supply chains can combine items of both types.
                                  | For instance, the manufacturing operations are planned
                                    in make-to-order mode while raw materials are purchased
                                    in make-to-stock mode.
                                  | For instance, end items can be planned in make-to-stock
                                    mode while the manufacturing operations is planned in
                                    make-to-order mode with serialzed batch numbers
                                    that move between production stages.
                                  | For instance, the final production stages of a product
                                    can be make-to-order that configure the product, while
                                    subassemblies going in to the end item can be produced
                                    in make-to-stock mode.
description     string            Free format description.
category        string            Free format category.
subcategory     string            Free format subcategory.
owner           item              | Items are organized in a hierarchical tree.
                                  | This field defines the parent item.
members         list of item      | Items are organized in a hierarchical tree.
                                  | This field defines a list of child items.
cost            double            | Cost or price of the item.
                                  | Depending on the precise usage and business goal it should
                                    be evaluated which cost to load into this field: purchase
                                    cost, booking value, selling price...
                                  | For most applications the booking value is the appropriate
                                    one.
                                  | The default value is 0.
volume          double            | Volume of the item.
                                  | The default value is 0.
weight          double            | Weight of the item.
                                  | The default value is 0.
unit of measure string            | Unit of measure for this item in the plan. All quantities in the
                                    plan for that item are expressed in this unit of measure.
                                  | Typical values are "piece", "kg", "l", "m".
period of cover integer           | Calculated value corresponding to the on hand days of cover.
global_purchase boolean           | When this item flag is set, it will a) prevent any new
                                    purchase orders for the item to be generated until the total
                                    inventory across all locations drops below the total safety
                                    stock and b) sales orders pointing at a location that is
                                    running out of stock will automatically be pointed to other
                                    locations in the network which still carry sufficient stock.
                                  | This field is not available in the standard database schema.
                                    You'll need to add it as a custom attribute, or set this
                                    field through a custom Python script.
buffers         list of buffer    Returns the list of buffers for this item.
hidden          boolean           Marks entities that are considered hidden and are normally
                                  not shown to the end user.
=============== ================= ===========================================================


**Extra fields added by "metrics" app**

This addon app provides some basic metrics that allow easy filtering and sorting for items that
have constrained open sales orders.

The window over which these metrics are computed is configurable with the parameter metrics.demand_window.
Only demands with a due date within this period after the current date are included in the calculation.

======================= ================= ===========================================================
Field                   Type              Description
======================= ================= ===========================================================
latedemandcount         Integer           The number of open sales orders of this item that
                                          is planned to be delivered late.
latedemandquantity      Number            Total quantity of open sales orders of this item that
                                          is planned to be delivered late.
latedemandvalue         Number            Total value of open sales orders of this item that
                                          is planned to be delivered late.
unplanneddemandcount    Integer           The number of unplanned open sales orders of this item.
unplanneddemandquantity Number            Total quantity of unplanned open sales orders of this item.
unplanneddemandvalue    Number            Total value of unplanned open sales orders of this item.
======================= ================= ===========================================================


**Extra fields added by "demand hits" app**

This addon app provides some metrics on the historical demand of the item. This is useful in
identifying fast-moving and slow-moving items that can be used for differentiating the inventory
policies correctly.

======================= ================= ===========================================================
Field                   Type              Description
======================= ================= ===========================================================
orders_6m               Number            The number of sales orders of this item during the
                                          last 6 months.
sales_6m                Number            Total quantity of sales orders of this item during the
                                          last 6 months.
salesvalue_6m           Number            Total value of sales orders of this item during the
                                          last 6 months.
orders_12m              Number            The number of sales orders of this item during the
                                          last 12 months.
sales_12m               Number            Total quantity of sales orders of this item during the
                                          last 12 months.
salesvalue_12m          Number            Total value of sales orders of this item during the
                                          last 12 months.
======================= ================= ===========================================================


**Extra fields added by "forecast" app**

The forecast app enables the calculation of statistical forecasts based on the demand history.
It also includes a categorization of demand patterns, as described on
https://frepple.com/blog/demand-classification/

======================== ================= =============================================================
Field                    Type              Description
======================== ================= =============================================================
demand_pattern           String            Demand pattern: "smooth", "intermittent", "erratic" or
                                           "lumpy".
adi                      Number            | Average demand interval.
                                           | It measures the demand regularity in time by computing
                                            the average interval between two demands.
cv2                      Number            | Square of the coefficient of variation.
                                           | It measures the variation in quantities.
outliers last bucket     Number            | Counts how many outliers were found in the last bucket.
outliers last 6 buckets  Number            | Counts how many outliers were found in the last 6 buckets.
outliers last 12 buckets Number            | Counts how many outliers were found in the last 12 buckets.
======================== ================= =============================================================


**Extra fields added by "inventory planning" app**

This app enables the calculation of safety stocks and reorder quantities.

======================= ================= ===========================================================
Field                   Type              Description
======================= ================= ===========================================================
successor               Item              | Refers to another item that is replacing this item.
                                          | It is used to display a global overview of the inventory
                                            status of an item - across all locations and across its
                                            successor and predecessor items.
======================= ================= ===========================================================


**Extra fields added by "abc_classification" app**

This app categorizes the items into a number of classes. The classification is based on a
`Pareto  analysis <https://en.wikipedia.org/wiki/Pareto_analysis>`_ to identify the items that
contributed most to the sales revenue over the last year.

With the default classification, the A class makes up 20% of the sales revenue. The B class makes
up the sales revenue between 20% and 80%. The rest of the items are put in the C class. Items
without any demand in the last year won't be classified.

The number of classes, the thresholds and the history to use are configurable with the parameters
"abc.classes" and "abc.history".

======================= ================= ===========================================================
Field                   Type              Description
======================= ================= ===========================================================
abc_class               String            | Class of this item.
======================= ================= ===========================================================
