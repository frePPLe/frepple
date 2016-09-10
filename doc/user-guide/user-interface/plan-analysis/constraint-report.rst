=================
Constraint report
=================

This report shows for each demand the reason(s) why it is planned short or late.

It can also be used to show all demands that are delayed or short because of
a certain bottleneck resource or material.

============ ==============================================================================
Field        Description
============ ==============================================================================
demand       Demand that is affected by this constraint.
name         Problem type.
description  Description of the problem.
weight       | A number expressing the seriousness of the problem.
             | Sorting on this field allows the user to focus on the biggest problems first.
start        Date at which the problem starts.
end          Date at which the problem ends.
============ ==============================================================================


.. image:: ../_images/constraint-report.png
   :alt: Constraint report

.. image:: ../_images/why-short-or-late.png
   :alt: Reasons why a demand is planned late or short
