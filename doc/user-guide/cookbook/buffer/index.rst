======
Buffer
======

A buffer is a (physical or logical) inventory point. It is uniquely identified
based by a item+location combination.

There are different buffer types:

* **default**: a buffer that is replenished with a producing operation
* **procure**: a buffer that is replenished with a procurement operation
* **infinite supply**: a buffer without replenishing operation

.. toctree::
   :maxdepth: 1

   time-based-safety-stock
   transfer-batch
   global-purchase
