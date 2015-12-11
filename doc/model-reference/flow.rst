====
Flow
====

Flows are used to model the consumption and production of material from buffers.

Different types of flows exist:

* | **flow_start**:
  | Flows that consume (or produce) material at the start of an operationplan.
  | The quantity consumed or produced is proportional to the quantity of the
    operationplan.

* | **flow_end**:
  | Flows that produce (or consume) material at the end of an operationplan.
  | The quantity consumed or produced is proportional to the quantity of the
    operationplan.

* | **flow_fixed_start**:
  | Flows that consume (or produce) material at the start of an operationplan.
  | The quantity consumed or produced is constant and independent of the
    quantity of the operationplan.

* | **flow_fixed_end**:
  | Flows that produce (or consume) material at the end of an operationplan.
  | The quantity consumed or produced is constant and independent of the
    quantity of the operationplan.

**Fields**

=============== ================= ===========================================================
Field           Type              Description
=============== ================= ===========================================================
buffer          buffer            | Buffer from which material will be moved or transferred
                                    into.
                                  | This is a required field.
operation       operation         | Operation to which the material flow is associated.
                                  | This is a required field.
quantity        double            Material quantity being consumed or produced per unit of
                                  the operationplan.
effective_start dateTime          | Date after which the material consumption is valid.
                                  | Before this date the planned quantity is always 0.
effective_end   dateTime          | Date at which the material consumption becomes invalid.
                                  | After this date (and also at the exact date) the planned
                                    quantity is always 0.
priority        integer           | Priority of the flow, used in case of alternate flows.
                                  | The default is 1.
                                  | Lower numbers indicate more preferred flows.
name            non-empty string  | Optional name of the flow.
                                  | All flows with the same name are considered to be
                                    alternates of each other.
search          string            | Defines the order of preference among the alternate flows.
                                  | The valid choices are:

                                  * | PRIORITY
                                    | Select the alternate with the lowest priority number.
                                    | This is the default.

                                  * | MINCOST
                                    | Select the alternate which gives the lowest cost.
                                    | The cost includes the cost of all upstream operations,
                                      resources and buffers.

                                  * | MINPENALTY
                                    | Select the alternate which gives the lowest penalty.
                                    | The penalty includes the penalty of all penalties
                                      incurred in the upstream plan along the flow.

                                  * | MINCOSTPENALTY
                                    | Select the alternate which gives the lowest sum of
                                      the cost and penalty.
                                    | The sum is computed for the complete upstream path.

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

Defining a flow

.. code-block:: XML

    <plan>
       <flows>
          <flow xsi:type="flow_start">
            <buffer name="buffer component"/>
            <operation name="operation B"/>
            <quantity>-2</quantity>
          </flow>
       </flows>
    </plan>

Defining a flow nested in an operation structure.
A quantity 2 of component A OR 3 of component B are consumed, and 1 unit of the end item is produced.

.. code-block:: XML

    <plan>
       <operations>
         <operation name="operation B">
           <flows>
             <flow xsi:type="flow_start">
               <buffer name="buffer component A"/>
               <quantity>-2</quantity>
               <name>group1</name>
               <priority>1</priority>
             </flow>
             <flow xsi:type="flow_start">
               <buffer name="buffer component B"/>
               <quantity>-3</quantity>
               <alternate>group1</alternate>
               <priority>2</priority>
             </flow>
             <flow xsi:type="flow_end">
               <buffer name="buffer end item"/>
               <quantity>1</quantity>
             </flow>
           </flows>
         </operation>
       </operations>
    </plan>

Defining a flow nested in a buffer structure

.. code-block:: XML

    <plan>
       <buffers>
         <buffer name="buffer component">
           <flows>
             <flow xsi:type="flow_start">
               <operation name="operation A"/>
               <quantity>-2</quantity>
             </flow>
             <flow xsi:type="flow_start">
               <operation name="operation B"/>
               <quantity>-1</quantity>
             </flow>
           </flows>
         </buffer>
       </buffers>
    </plan>

Deleting a flow

::

    <plan>
       <flows>
          <flow action="R">
            <buffer name="buffer component"/>
            <operation name="operation B"/>
          </flow>
       </flows>
    </plan>
