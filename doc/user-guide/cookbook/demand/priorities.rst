==========
Priorities
==========

FrePPLe's planning algorithm processes demand per demand. One by one, each demands gets planned and reserves the stock, raw materials and capacity it needs.

Demands that are planned first thus get a first chance to search for available supply and are more likely to be planned for delivery at the requested date. In case the total supply is insufficient, the demands that are near the end of the list are more likely to be planned late or short.

FrePPLe orders the demands based on the following attributes:

1. **Priority**

   Lower values get planned first. We first plan all demands of priority 1, then 2, then 3...

2. **Due date**

   In case the priority of 2 demands is the same, the demand is ordered based on the due date. Earlier due dates are planned first.

.. rubric:: Example

:download:`Excel spreadsheet demand-priorities <demand-priorities.xlsx>`

In this example we have a number of overdue orders that have to be manufactured on a bottleneck resource.
The order of the shipping and production operations reflects the ranking criteria described above.

The problem screen also illustrates that the low priority orders are shipped with greater delays.