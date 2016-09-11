==========================
Post-operation safety time
==========================

In frePPLe you can define a time gap after the operation has finished. This time
gap adds some safety time in your plan, which can absorb variability or unforeseen events.

This feature is typically used for key operations in your plant. This can be at a
logical decoupling point in the production process, where you have some controlled
work-in-progress buffer stock. Or it can be right before a bottleneck station,
where you want to assure the bottleneck station doesn’t go idle because an upstream
station has a small production delay.

The solver considers the post-operation time as a soft constraint. This means that
we will try to respect it in the plans, but if it is required to avoid planning an
order late we will generate a plan that violates the constraint. In that case we’ll
have a plan with rushed operations planned to follow each other quicker.

.. rubric:: Example

:download:`Excel spreadsheet operation-posttime <operation-posttime.xlsx>`

In this example we model a two-step production process with a decoupling buffer
between both steps. A post-operation delay of 3 days is specified for the first
step: ideally there is a delay of 3 days between production into the decoupling
buffer and the consumption from the decoupling buffer.

There are 4 demands in this model with a different due date.

The first demand is overdue. When you review its delivery plan, you notice that
we planned to consume the material from the decoupling buffer as soon as it is
produced. We violate the 3 day safety time, because it would only delay the
order further. Instead, we rush the order through the different ASAP to minimize
the delivery delay.

The second demand has a due date that is later. In its delivery plan you can
already see a safety time of 8 hours that we can plan in the decoupling buffer.

The next demands are due even later. We could plan this orders on the requested
due date, while fully respecting a safety delay of 3 days in the decoupling buffer.

Note that in this example, there is no inventory planned for the finished product.
We plan to ship the product as soon as the second step of the production process
is finished. Only the decoupling buffer is planned to carry inventory.
In the cookbook recipe on quantity based safety stock we will pick up this very
same example and add safety stock targets for the finished product.
