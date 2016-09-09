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
|      :doc:`operations` (references locations)
|        :doc:`resource-skills` (references skills and resources)
|        :doc:`operation-resources` (references resources, skills and operations)
|        :doc:`Sub operation <operations>` (references operations)
|        :doc:`operationplan` (references operations)
|          :doc:`items` (references operations and itself)
|            :doc:`item-suppliers` (references suppliers, items and locations)
|            :doc:`item-distributions` (references locations and items)
|            :doc:`sales-orders` (references items, customers, operations, locations and itself)
|            :doc:`buffers` (references items, operations, locations, calendars and itself)
|              :doc:`operation-materials` (references buffers and operations)

.. image:: _images/dependencies.png
   :alt: Model dependencies

Note that it is pretty straightforward to extend the data model to match your
own domain model. During an implementation additional data types can be added
that map more accurately to your business and/or data sources.

The diagram below gives a more detailed overview of the models, their fields
and relations. You can also get is :download:`as a pdf <_images/domain-model.pdf>`.

.. image:: _images/domain-model.png
   :alt: Domain model
