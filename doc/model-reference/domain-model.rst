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
|      :doc:`operations` (references items, locations, calendars, customers and itself)
|        :doc:`sales-orders` (references items, customers, operations, locations and itself)
|        :doc:`buffers` (references items, locations, calendars and itself)
|        :doc:`operation-dependencies` (references operations)
|        :doc:`operation-resources` (references resources, skills and operations)
|        :doc:`operation-materials` (references items and operations)
|        :doc:`item-suppliers` (references suppliers, items, resources and locations)
|        :doc:`item-distributions` (references locations, items and resources)
|        :doc:`resource-skills` (references skills and resources)
|        :doc:`Setup rule <setup-matrices>` (references setup matrix and resource)
|        :doc:`manufacturing-orders` (references operations and itself)
|        :doc:`purchase-orders` (references items, suppliers and locations)
|        :doc:`distribution-orders` (references items and locations)
|          :doc:`operationplan-materials` (references items, manufacturing orders, purchase orders, distribution orders and locations)
|          :doc:`operationplan-resources` (references resources, manufacturing orders, purchase orders and distribution orders)
|  :doc:`buckets`
|  :doc:`parameters`

.. image:: _images/dependencies.png
   :alt: Model dependencies

Note that it is possible to extend the data model to match your
own domain model. During an implementation additional data types can be added
that map more accurately to your business and/or data sources.

..
    The image above is generated online with https://dreampuf.github.io/GraphvizOnline/

    It uses graphviz to visualize the following network:

      digraph G {
      rankdir=LR;
      "calendar" -> "supplier";
      "calendar" -> "location";
      "calendar" -> "operation";
      "calendar" -> "resource";
      "calendar" -> "calendar bucket";
      "calendar" -> "buffer";
      "customer" -> "customer";
      "customer" -> "demand";
      "demand" -> "delivery order";
      "item" -> "item";
      "item" -> "operation";
      "item" -> "manufacturing order";
      "item" -> "purchase order";
      "item" -> "distribution order";
      "item" -> "inventory detail";
      "item" -> "operation material";
      "item" -> "item supplier";
      "item" -> "item distribution";
      "item" -> "buffer";
      "item" -> "demand";
      "location" -> "location";
      "location" -> "demand";
      "location" -> "operation";
      "location" -> "manufacturing order";
      "location" -> "purchase order";
      "location" -> "distribution order";
      "location" -> "inventory detail";
      "location" -> "resource";
      "location" -> "item supplier";
      "location" -> "item distribution";
      "location" -> "buffer";
      "operation" -> "demand";
      "operation" -> "operation";
      "operation" -> "manufacturing order";
      "operation" -> "suboperation";
      "operation" -> "operation resource";
      "operation" -> "operation material";
      "operation" -> "operation dependency";
      "manufacturing order" -> "manufacturing order";
      "manufacturing order" -> "resource detail";
      "manufacturing order" -> "inventory detail";
      "purchase order" -> "resource detail";
      "purchase order" -> "inventory detail";
      "distribution order" -> "resource detail";
      "distribution order" -> "inventory detail";
      "resource" -> "resource";
      "resource" -> "resource detail";
      "resource" -> "resource skill";
      "resource" -> "operation resource";
      "resource" -> "item supplier";
      "resource" -> "item distribution";
      "resource" -> "setup rule";
      "setup matrix" -> "resource";
      "setup matrix" -> "setuprule";
      "skill" -> "resource skill";
      "skill" -> "operation resource";
      "supplier" -> "supplier";
      "supplier" -> "purchase order";
      "supplier" -> "item supplier";
      }

