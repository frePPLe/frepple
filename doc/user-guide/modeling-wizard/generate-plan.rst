===============
Generate a plan
===============

The plan generation screen can be found under the Admin/Execute menu.


.. image:: _images/create_a_plan.png
   :height: 558 px
   :width: 676 px
   :scale: 100 %
   :alt: Generate a plan

This option runs the frePPLe planning engine with the input data from the
database. The planning results are exported back into the database.

Optionally, on the Enterprise edition, the forecast and 
inventory planning modules can be run independantly prior to the plan generation.

The supply plan genaration box has to be ticked to generate purchase orders.

The forecast solver will calculate the forecast based on the historical demand for all
(item, location, customer) intersections declared in the Forecast table.

The inventory planning solver will compute a safety stock and a reorder quantity for
all buffers declared in the inventory planning parameters table.

Two main plan types can be distinguished, based on whether you want to
see demand OR material, lead time and capacity problems to be shown.

* A **constrained plan** respects all enabled constraints. In case of shortages
  the demand is planned late or short. No any material or capacity shortages
  are present in the plan.

* An **unconstrained plan** shows material, capacity and operation problems
  that prevent the demand from being planned in time. The demand is always met
  completely and on time.

In both the constrained and unconstrained plans you can select which constraints
are considered during plan creation.

**Reading the plan**

The forecast calculated by the forecast solver is displayed in the forecast report
and in the forecast editor.

The ROQ and safety stock values calculated by the inventory planning solver can be 
found in the DRP screen under Distribution/Distribution planning menu.

The generated distribution orders (when applicable) can be found under the Distribution/Distribution orders menu.

The generated manufacturing orders (when applicable) can be found under the Manufacturing/Manufacturing orders menu.

The generated purchase orders (when applicable) can be found under the Purchasing/Purchase orders menu.

Note that all the generated orders (purchase, distribution and manufacturing) will have status equal to "proposed" 
as they still have to be approved by the planner to be sent to your ERP system.




