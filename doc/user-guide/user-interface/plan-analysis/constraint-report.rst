=================
Constraint report
=================

This report shows for each demand the reason(s) why it is planned short or late.

It can also be used to show all demands that are delayed or short because of
a certain bottleneck resource or material.

This information is extremely valuable in understanding why the planning algorithm
came up with the resulting plan.

============ ==============================================================================
Field        Description
============ ==============================================================================
demand       Demand impacted by this constraint.
name         Constraint type causing the lateness or shortness:
             
             * | **operation before current**:
               | The demand was planned late (or short) because of a lead time constraint.
               | The operation should have been started some time ago in the past to
                 deliver the demand on time.
                   
             * | **capacity overload**:
               | The demand was planned late (or short) because of a capacity shortage on
                 a resource.

description  Description of the constraint.
weight       A number expressing the seriousness of the constraint.
start        Date at which the constraint starts.
end          Date at which the constraint ends.
============ ==============================================================================


.. image:: ../_images/constraint-report.png
   :alt: Constraint report

.. image:: ../_images/why-short-or-late.png
   :alt: Reasons why a demand is planned late or short
