=============
Operationplan
=============

Used to model an existing or planned activity.

When used as input the operationplans represent work-in-progress, in-transit
shipments, planned material receipts, frozen manufacturing plans, etc...

In the output plan, the operationplans represent the planned activities in
the future. The frozen operationplans from the input data are still present
in the plan as well.

| The operationplan has two closely related models.
| A flowplan represents the planned production or consumption of material.
| A loadplan represents the planned consumption of capacity.
| These models are never created directly, but they are automatically managed
  by the operationplan.

**Fields**

================ ================= ===========================================================
Field            Type              Description
================ ================= ===========================================================
operation        operation         Operation being instantiated.
id               unsigned long     | Unique identifier of the operationplan.
                                   | If left unspecified an identifier will be automatically
                                     generated.
                                   | This field is required when updating existing instances.
reference        string            | Identifier or reference of this operationplan in 
                                     external system.
                                   | We don't impose a restriction for its uniqueness.                                   
start            dateTime          | Start date.
                                   | If left unspecified (or set to 1971-01-01), this field
                                     will be computed based on the end date.
end              dateTime          | End date.
                                   | If left unspecified (or set to 1971-01-01), this field
                                     will be computed based on the start date.
demand           demand            | Points to the demand being satisfied with this
                                    operationplan.
                                   | This field is only non-null for the actual delivery
                                    operationplans.
quantity         double            | Quantity being planned.
                                   | For unlocked operationplans, this quantity will be rounded
                                     to the respect the min, max and multiple constraints set
                                     on the operation.
                                   | Locked operationplans don't need to respect these limits.
locked           boolean           | A locked operation plan is not allowed to be changed by any
                                     solver algorithm.
                                   | This field is deprecated. Please use the status field instead.
status           string            | Status of the operationplan.
                                   | The valid choices are:

                                   * | proposed:
                                     | An operationplan in this state is a draft one. When 
                                       regenerating the plan operationplans in this state can be
                                       changed and even deleted by the planning algorithm.
                                     | This is the default.

                                   * | approved:
                                     | An operationplan in this state is reviewed by the user 
                                       and ready for exporting to your ERP system. Once exported
                                       the status will become confirmed.
                                     | The planning algorithm will not change or create 
                                       operationplans in this state.

                                   * | confirmed:
                                     | Confirmed operationplans are ongoing transactions read 
                                       as input from your ERP system.
                                     | The planning algorithm will not change or create 
                                       operationplans in this state.

consume_material boolean           | Controls whether this operationplan should consume material
                                     or not.
                                   | Only locked operationplans respect this flag.
produce_material boolean           | Controls whether this operationplan should produce material
                                     or not.
                                   | Only locked operationplans respect this flag.
consume_capacity boolean           | Controls whether this operationplan should consume capacity
                                     or not.
                                   | Only locked operationplans respect this flag.
owner            operationplan     | Points to a parent operationplan.
                                   | The default is NULL.
flowplans        list of flowplan  | A list of flowplans owned by this operationplan.
                                   | This list is export-only.
                                   | See the field buffer.flowplans to see all flowplans of a
                                     particular buffer.
loadplans        list of loadplan  | A list of loadplans owned by this operationplan.
                                   | This list is export-only.
                                   | See the field resource.loadplans to see all loadplans of
                                     a particular resource.
criticality      double            | The criticality reflects the urgency of the operationplan.
                                   | A criticality of 0 indicates that the operationplan is
                                     on the critical path of one or more orders. This is
                                     what you will find in a just-in-time plan.
                                   | A criticality of 10 indicates that the operationplan
                                     can be delayed for 10 days before any demand is
                                     impacted. This is what you will find in a plan with
                                     safety stocks in the buffers and security time on
                                     operations.
                                   | This field is export-only.
unavailable      duration          | Amount of time that the operationplan is interrupted
                                     due to the unavailability (modelled through the
                                     availability calendar of the operation location).
                                   | This field is export-only.
action           A/C/AC/R          | Type of action to be executed:
                                   | A: Add an new entity, and report an error if the entity
                                     already exists.
                                   | C: Change an existing entity, and report an error if the
                                     entity doesn’t exist yet.
                                   | AC: Change an entity or create a new one if it doesn’t
                                     exist yet. This is the default.
                                   | R: Remove an entity, and report an error if the entity
                                     doesn’t exist.
================ ================= ===========================================================

Flowplan
--------

Models the material production or consumption associated with an operationplan.

Flowplans are fully controlled by the owning operationplan.

================ ================= ===========================================================
Field            Type              Description
================ ================= ===========================================================
operationplan    operationplan     Operationplan owning the flowplan.
flow             flow              Flow model of which this is a planned instance.
quantity         double            Size of the material consumption or production.
date             dateTime          Date of material consumption or production.
onhand           double            Inventory in the buffer after the execution of this
                                   flowplan.
================ ================= ===========================================================

Loadplan
--------

Models the capacity usage associated with an operationplan.

Loadplans are fully controlled by the owning operationplan.

================ ================= ===========================================================
Field            Type              Description
================ ================= ===========================================================
operationplan    operationplan     Operationplan owning the flowplan.
load             load              Load model of which this is a planned instance.
quantity         double            Size of the resource loading.
startdate        dateTime          Start of the resource loading.
enddate          dateTime          End of the resource loading.
setup            string            | Setup of the resource when executing this loadplan.
                                   | This can be either the setup required by this particular
                                     load, or the setup left by any previous loadplans on the
                                     resource.
================ ================= ===========================================================

**Example XML structures**

Adding an operationplan to represent a planned receipt of material

.. code-block:: XML

   <plan>
      <operationplans>
        <operationplan>
          <operation name="Purchase component A"/>
          <quantity>100</quantity>
          <start>2007-01-10T00:00:00</start>
          <locked>true</locked>
        </operationplan>
      </operationplans>
    </plan>

Deleting an operationplan

.. code-block:: XML

    <plan>
       <operationplans>
          <operationplan id="1020" action="R"/>
       </operationplans>
    </plan>

**Example Python code**

Adding an operationplan to represent a planned receipt of material

::

   op = frepple.operation(name="Purchase component A", action="C")
   opplan = frepple.operationplan(
     operation=op,
     quantity=100,
     start=datetime.datetime(2007,1,10),
     locked=True
     )

Deleting an operationplan

::

    frepple.operationplan(id="1020",action="R")

Iterate over operationplans

::

    for i in frepple.operationplans():
      print i.operation.name, i.quantity, i.start, i.end

Iterate over flowplans

::

    for i in frepple.operationplans():
      for j in i.flowplans:
        print i.operation.name, j.quantity, j.date, j.buffer.name

Iterate over loadplans

::

    for i in frepple.operationplans():
      for j in i.loadplans:
        print i.operation.name, j.quantity, j.resource.name,
          j.startdate, j.enddate
