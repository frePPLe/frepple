=====
Items
=====

The Items table contains all the items that you want to manage in your supply chain.

.. rubric:: Key Fields

=============== ================= ===========================================================
Field           Type              Description
=============== ================= ===========================================================
name            non-empty string  Unique name of the item.
description     string            Free format description.
cost            number            Cost or price of the item.
owner           item name         Hierarchical parent of the item.
=============== ================= ===========================================================

.. rubric:: Item hierarchy

.. Hint::

   Setting up a good item hierarchy is important if you are interested in the demand forecasting functionality. 
   Otherwise, you can skip modeling an item hierarchy.

Using the owner field the items can be organized in a hierarhical tree structure. This allows,
among other, reviewing the forecast at different levels in the 
:doc:`../../user-interface/plan-analysis/forecast-editor`.

Here is an example to model a tree structure with families and brands:

.. image:: ../_images/item-hierarchy.png
   :width: 50%
   :alt: Example item hierarchy

============= =============
Name          Owner
============= =============
All items  
Family 1      All items
Brand 1A      Family 1
Brand 1B      Family 1
Family 2      All items
Brand 2A      Family 2
Brand 2B      Family 2
============= =============

.. rubric:: Advanced topics

* Complete table description: :doc:`../../model-reference/items`
