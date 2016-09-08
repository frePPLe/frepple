=======================
Time based safety stock
=======================

You can define a time based safety stock for a buffer. This means that we will try
to plan the replenishment a certain time before the material is required. This creates
a temporary inventory that is useful to absorb variability and uncertainty.

From a modelling point of view, this is achieved by defining a post-operation
time on the replenishing operation of the buffer.
See the cookbook recipe :doc:`post-operation safety time <../operation/operation-posttime>`.
