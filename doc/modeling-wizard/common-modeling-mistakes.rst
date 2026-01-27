========================
Common modeling mistakes
========================

When populating frepple you've got a learning path to follow. And there are
a number of pitfalls along that path.

On this page we want to share our learnings on the most common modeling
mistakes made by first-time frepple users.

Want to share your own learning and add it to this list? We'd be happy to hear
your feedback on https://github.com/frePPLe/frepple/discussions

Here's our shortlist:

1. :ref:`broken_supply_path`
2. :ref:`resource_max_calendar`
3. :ref:`supply_path_loops`

.. _broken_supply_path:

Broken supply paths
-------------------

The :doc:`/modeling-wizard/concepts` page describe how you define a buffer's replenishment
through either a) purchase orders, b) distribution orders or c) manufacturing orders.
To generate a valid plan frepple needs the complete replenishment chain for all buffers
between the end item and the raw materials.

The most common modeling mistake is to forget this definition for one or more buffers.

Symptoms:
  - When generating a constrained plan, your sales order is not planned.

Diagnosis:
  - | Drill into the sales order and check the "why short or late" tab.
    | You will see a constraint with a description "no replenishment defined
      for <item> @ <location>".

Correction:
  Apply one of these solutions:

  - Define either an operation, an item supplier or an item distribution for the buffer.
  - Switch the buffer type to be "infinite".
  - Set the parameter "plan.fixBrokenSupplyPath" parameter to "true". In this case we automatically
    define a fake replenishment to purchase this item from a dummy "unknown supplier".
    Your demand will now be planned, but you should review these dummy purchase order!

  The parameter "plan.fixBrokenSupplyPath" is "true" by default. This will protect first-time
  users from making this rookie mistake...

.. _resource_max_calendar:

Resource max calendar with zero-size periods
--------------------------------------------

Another common mistake is to use a resource maximum calendar that also
reflects the working hours of the resource.

Symptoms:
  - Some sales orders are not getting planned in a capacity constrained plan.
  - In a capacity UNconstrained plan all sales orders are getting planned.

Diagnosis:
  - | Your resource is of type "default" and has "maximum calendar".
    | Your maximum calendar has some calendar buckets where the size is 0.
  - | Some operations have a duration that is larger than the time between
      0-size periods.
  - | In the log file you find a message "no free capacity slot found".

Correction:
  Apply one of these solutions:

  - | Change the maximum calendar to reflect only the real changes in the resource
      size. Don't use the maximum calendar to reflect the working hours of the resource.
      Instead, use an availability calendar on the resources. In many models this means
      that you can leave the maximum calendar blank on your resources.
  - | In case you still need or want a maximum calendar with 0-size periods,
      make sure all your manufacturing orders fit between the 0-size periods.
    | You can use the "operation.size maximum" field to break up large
      manufacturing orders into smaller ones.

  | This problem is caused by the fact that frepple doesn't allow a manufacturing
    order to be planned over a period where the size is 0.
  | E.g. If the resource size is 0 every weekday between 18:00 and 24:00, we will
    not be able to find any time slot for a manufacturing order that takes more
    than 18 hours on the resource.

  | Note that frepple does allow a manufacturing order to be planned over a period
    where the resource is unavailable. We will just extend the duration of the
    manufacturing order to account for the unavailable time.
  | E.g. If the resource is unavailable every weekday between 18:00 and 24:00, we
    can plan a job to start on Monday and finish on Tuesday. The 6 unavaible hours
    aren't counted as production time.

.. _supply_path_loops:

Supply path loops
-----------------

Cycles in the supply path are also a common data mistake.

For instance, an item at location A is replenished with a distribution order
from location B. The item at location B is replenished with a distribution
order from location A.

When the planning algorithm plans a sales order through such a supply path, we
end up in an infinite loop. There are built-in protections against loops like the
above example. However, some more subtle and complex cycles can still go undetected.

Symptoms:
  - The plan generation hangs or takes a veeeeery long time. It eventually
    crashes with an out-of-memory error.

Diagnosis:
  - The supply path of the sales orders in question shows a cycle.

Correction:
  It's pretty simple - the cycles must be removed. The supply path should be
  thought as a uni-directional graph.

  In most cases the cycles are data mistakes. But some supply chains can
  contain cycles.

  A typical example would be in metals industry were a percentage of the output
  is rejected. The rejected material can be melted again and reused as raw material.
  In this particular example, cycles can be avoided if the rejected material doesn't
  define a replenishment. The algorithm will then uses any available rejected scrap
  material but not plan to create more scrap.
