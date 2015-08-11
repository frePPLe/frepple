======
Demand
======

Defines independent demands for items.

These can be actual customer orders, or forecasted demands.

**Fields**

============== ================= ===========================================================
Field          Type              Description
============== ================= ===========================================================
name           non-empty string  | Name of the demand.
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
detectproblems boolean           | Set this field to false to supress problem detection on
                                   this demand.
                                 | Default is true.
maxlateness    duration          | The maximum delay that can be accepted to satisfy this
                                   demand.
                                 | The default value allows an infinite delay.
minshipment    positive double   | The minimum quantity allowed for the shipment
                                   operationplans that satisfy this demand.
                                 | The default is 1.
constraints    list of problem   | This field returns the list of reasons why the demand
                                   was planned late or short.
                                 | The field is export-only.
hidden         boolean           Marks entities that are considered hidden and are
                                 normally not shown to the end user.
action         A/C/AC/R          | Type of action to be executed:
                                 | A: Add an new entity, and report an error if the entity
                                   already exists.
                                 | C: Change an existing entity, and report an error if the
                                   entity doesn’t exist yet.
                                 | AC: Change an entity or create a new one if it doesn’t
                                   exist yet. This is the default.
                                 | R: Remove an entity, and report an error if the entity
                                   doesn’t exist.
============== ================= ===========================================================

**Example XML structures**

Adding or changing demands

.. code-block:: XML

    <plan>
      <demands>
       <demand name="order A">
         <quantity>10</quantity>
         <due>2007-01-10T00:00:00</due>
         <priority>1</priority>
         <item name="item 1" />
         <!-- Don't allow any delay -->
         <maxlateness>P0D</maxlateness>
         <!-- Don't create a delivery for less than 5 units -->
         <minshipment>5</minshipment>
       </demand>
       <demand name="order B" quantity="10"
           due="2007-01-10T00:00:00" priority="1" >
         <item name="item 1" />
       </demand>
      </demands>
    </plan>

Removing a demand

.. code-block:: XML

    <plan>
      <demands>
          <demand name="order ABC" action="R"/>
      </demands>
    </plan>

**Example Python code**

Adding or changing demands

::

    it = frepple.item(name="item 1")
    dem1 = frepple.demand(name="order A", quantity=10,
      due=datetime.datetime(2007,01,10), priority=1, item=it,
      # Don't allow any delay
      maxlateness=0,
      # Don't create a delivery for less than 5 units
      minshipment=5)
    dem2 = frepple.demand(name="order B", quantity=10,
        due=datetime.datetime(2007,1,10), priority=1", item=it)

Removing a demand

::

    frepple.demand(name="order ABC", action="R")

Iterating over all demands and their deliveries

::

    for d in frepple.demands():
      print "Demand:", d.name, d.due, d.item.name, d.quantity
      for i in d.operationplans:
        print "  Operationplan:", i.operation.name, i.quantity, i.end

Show the reason(s) why a demand is planned late or short

::

    dmd = frepple.demand(name="a demand")
    for i in dmd.constraints:
      print i.entity, i.name, str(i.owner), i.description,
        i.start, i.end, i.weight