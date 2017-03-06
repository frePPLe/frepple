=====
Items
=====

An item represents an end product, intermediate product or a raw material.

Each demand is associated with an item.

A buffer is also associated with an item: it represents a storage of the item
at a certain location.

**Fields**

=============== ================= ===========================================================
Field           Type              Description
=============== ================= ===========================================================
name            non-empty string  | Unique name of the item.
                                  | This is the key field and a required attribute.
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
