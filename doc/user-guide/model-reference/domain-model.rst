============
Domain model
============

The different entities in a model reference each other, and input data must
thus be entered in the correct order. This list show the correct order and
dependencies. Entities with a higher indentation depend on entities with
less indentation.

Start populating the entities at the top of the list and work your way down.

|  :doc:`customers` (references itself)
|  :doc:`setup-matrices`
|  :doc:`skills`
|  :doc:`calendars`
|    :doc:`Calendar bucket <calendars>` (references calendars)
|    :doc:`locations` (references calendars and itself)
|    :doc:`suppliers` (references calendars and itself)
|      :doc:`resources` (references setup matrices, calendars, locations and itself)
|      :doc:`items` (references itself)
|      :doc:`operations` (references items, locations and customers)
|        :doc:`sales-orders` (references items, customers, operations, locations and itself)
|        :doc:`buffers` (references items, locations, calendars and itself)
|        :doc:`operation-resources` (references resources, skills and operations)
|        :doc:`operation-materials` (references items and operations)
|        :doc:`item-suppliers` (references suppliers, items, resources and locations)
|        :doc:`item-distributions` (references locations, items and resources)
|        :doc:`resource-skills` (references skills and resources)
|        :doc:`Sub operation <operations>` (references operations)
|        :doc:`manufacturing-orders` (references operations)
|        :doc:`purchase-orders` (references items, suppliers and locations)
|        :doc:`distribution-orders` (references items and locations)
|  :doc:`buckets`
|  :doc:`parameters`

.. image:: _images/dependencies.png
   :alt: Model dependencies

Note that it is pretty straightforward to extend the data model to match your
own domain model. During an implementation additional data types can be added
that map more accurately to your business and/or data sources.
