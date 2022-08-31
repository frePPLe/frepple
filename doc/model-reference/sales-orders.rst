============
Sales orders
============

Defines independent demands for items.

These can be actual customer orders, or forecasted demands.

============== ================= ===========================================================
Field          Type              Description
============== ================= ===========================================================
name           non-empty string  | Unique name of the demand.
                                 | This is the key field and a required attribute.
description    string            Free format description.
category       string            Free format category.
subcategory    string            Free format subcategory.
quantity       double            Requested quantity.
item           item              Requested item.
batch          string            | Blank/unused for make-to-stock items.
                                 | For make-to-order items, it identifies the material
                                   batch that can be used to satisfy the demand. This field
                                   can be set to the sales order name (true make-to-order
                                   production), or it can be set an item attribute (eg color
                                   of the item).
location       location          | Requested shipping location.
                                 | This field can be left blank if there is only a single
                                   location in the model, or if a delivery operation is
                                   specified on the demand or the item.
due            dateTime          Due date of the demand.
priority       integer           | Priority of the demand relative to the other demands.
                                 | A lower number indicates higher priority.
                                 | The default value is 0.
operation      operation         | Operation to be plan to satisfy the demand.
                                 | When left unspecified, frePPLe will automatically create
                                   a delivery operation for the item and location combination.
customer       customer          Customer placing the demand.
status         string            Status of the demand.
                                 Possible values are "inquiry", "open" (default), "closed",
                                 "canceled" and "quote".
maxlateness    duration          | The maximum delay that can be accepted to satisfy this
                                   demand.
                                 | The default value allows a delay of 5 years.
                                 | Use a value of 0 in businesses where the customer will
                                   not accept a late delivery and cancel his order in such
                                   a case.
minshipment    positive double   | The minimum quantity allowed for the delivery orders
                                   that satisfy this demand.
                                 | If this field is not specified, we compute a default
                                   value as round_down(quantity / 10). This means that we allow
                                   the demand to be met only with at most 10 partial deliveries.
owner          string            | A string to group sales order lines together under a parent.
policy         string            | Defines how different sales orders with the same owner are
                                   shipped towards the customer.
                                 | Possible values are:

                                 - | independent:
                                   | All sales orders are planned and shipped independently from
                                     each other. This is the default behavior.

                                 - | alltogether:
                                   | All sales orders with the same owner need to be shipped on
                                     the same date and in full quantity to the customer.

                                 - | inratio:
                                   | CURRENTLY NOT IMPLEMENTED YET!
                                   | This policy assures that partial deliveries maintain the
                                     same ratio as the initial order.
                                   | For instance, imagine a customer orders 5 tables and 20
                                     chairs. You can ship 1 table and 4 chairs, but not 1 tables
                                     and all 20 chairs.

constraints    list of problem   | This field returns the list of reasons why the demand
                                   was planned late or short.
                                 | The field is export-only.
hidden         boolean           Marks entities that are considered hidden and are
                                 normally not shown to the end user.
============== ================= ===========================================================
