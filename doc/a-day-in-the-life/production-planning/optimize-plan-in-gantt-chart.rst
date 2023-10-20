==========================================================
How can I optimize my plan in the GANTT chart plan editor?
==========================================================

FrePPLe's planning algorithm automaticaly generates a production plan. The production
planner can review the plan and manually override some details in the plan.

Typcially, these changes are done only for the schedule in the next few days. You'll want
leave the plan further out in the future as a proposal only - that part of the plan will
continue to evolve as demand and supply change over time, and you'll only commit to that
schedule when it comes close to the current date.

1) Navigate to Plan Editor in the Manufacturing menu and select an order on the GANTT chart.
2) You can modify the start/end time of an order by dragging and dropping the block or editing dates in the Manufacturing Order widget.
3) You can pick an alternate operation when possible.
4) You can select an alternate resource when possible.

Any of the above change will trigger a plan update, frePPLe will make sure that the plan remains feasible.

.. raw:: html

   <iframe width="1038" height="584" src="https://www.youtube.com/embed/j6O-WmqxgHQ" frameborder="0" allowfullscreen></iframe>