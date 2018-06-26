============
Sales orders
============

Defines independent demands for items.

These can be actual customer orders, or forecasted demands.

**Fields**

============== ================= ===========================================================
Field          Type              Description
============== ================= ===========================================================
name           non-empty string  | Unique name of the demand.
                                 | This is the key field and a required attribute.
description    string            Free format description.
category       string            Free format category.
subcategory    string            Free format subcategory.
owner          demand            | Demands are organized in a hierarchical tree.
                                 | This field defines the parent demand.
members        list of demand    | Demands are organized in a hierarchical tree.
                                 | This field defines a list of child demand.
quantity       double            Requested quantity.
item           item              Requested item.
location       location          | Requested shipping location.
                                 | This field can be left blank if there is only a single
                                   location in the model, or if a delivery operation is
                                   specified on the demand or the item.
due            dateTime          Due date of the demand.
priority       integer           | Priority of the demand relative to the other demands.
                                 | A lower number indicates higher priority.
                                 | The default value is 0.
operation      operation         | Operation to be used to satisfy the demand.
                                 | If left unspecified the operation on the item will be
                                   used.
                                 | New in version 3.0: If no operation is specified on the
                                   demand or the item, frePPLe will automatically try to create
                                   a delivery operation for the requested item and location.
                                   A data error is created when we this isn't possible.
customer       customer          Customer placing the demand.
status         string            Status of the demand.
                                 Possible values are "open" (default), "closed", "canceled"
                                 and "quote".
maxlateness    duration          | The maximum delay that can be accepted to satisfy this
                                   demand.
                                 | The default value allows an infinite delay.
                                 | Use a value of 0 in businesses where the customer will
                                   not accept a late delivery and cancel his order in such
                                   a case. 
minshipment    positive double   | The minimum quantity allowed for the shipment
                                   operationplans that satisfy this demand.
                                 | If this field is not specified, we compute a default
                                   value as round_up(quantity / 10). This means that we allow
                                   the demand to be met only with at most 10 partial deliveries.
constraints    list of problem   | This field returns the list of reasons why the demand
                                   was planned late or short.
                                 | The field is export-only.
hidden         boolean           Marks entities that are considered hidden and are
                                 normally not shown to the end user.
============== ================= ===========================================================
