====================
Order quoting module
====================

.. Important::

   This module is only available in the Enterprise Edition.

When receiving a new order or a quote traditional ERP systems will promise
a delivery date that is based on the inventory of the end product and a fixed
lead time. For make-to-order environments with complex capacity and material
constraints this will result in infeasible or extra-conservative delivery
dates being promised to your customers.

FrePPLe’s order quoting module performs a capable-to-promise check which
allows you to obtain much more accurate and reliable delivery dates. It
performs an on-line check of all available stock, capacity and raw material
availability. The promise date it computes considers all material, capacity
and time constraints.

Features:

* Capable-to-promise check across all levels in the bill of material.

* Returns the earliest feasible delivery date for the complete quantity,
  or can also propose partial shipments.

* In case the delivery date requested by the customer isn’t feasible, the
  module also returns the reasons why this is the case.

* Very fast reply in less than a second through a memory-resident planning
  engine.

* The module can be used from a screen in the frePPLe user interface.

* It is also possible to access the functionality as a web service. This
  allows the functionality to be accessed on-line by other systems.

.. raw:: html

   <iframe width="640" height="360" src="http://www.youtube.com/embed/0vSkR1a3e5w" frameborder="0" allowfullscreen=""></iframe>
