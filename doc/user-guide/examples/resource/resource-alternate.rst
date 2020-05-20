===================
Alternate resources
===================

In many industries, the same operation can be performed by different machines, tools
or operators.
However we might want to restrict a given operation to some resources only, this is achieved in
frePPLe by using the concept of skills.

Examples are:

* A new machine can perform the same tasks as an old machine (and often faster).

* Only operators with a specific skill can complete a given operation.

| In this example, the operation duration is the same for all of the alternate resources.
| If the duration of an operation depends on the selected alternate, you can check out
  `the resource efficiency example <resource-efficiency.html>`_
  and `the alternate operations example <../operation/operation-alternate.html>`_.

`Check this feature on a live example <https://demo.frepple.com/resource-alternate/data/input/resource/>`_

:download:`Download an Excel spreadsheet with the data for this example <resource-alternate.xlsx>`

Here is a step by step guide to explore the example:

* We are modelling an operation that assembles round tables. To assemble a round table we 
  need both an operator and a machine. Check out the 
  `supply path of a sales order <https://demo.frepple.com/resource-alternate/supplypath/demand/Demand%2001/>`_.

  .. image:: _images/resource-alternate-1.png
     :alt: Supply path

* | The machine parks consists of "machine A", "machine B" and "machine C". Only machine A and machine B
    can assemble a round table. Machine A is prefered over machine B as it is faster (efficiency set at 120%).

  | "Antonio", "Carl" and "Philippe" are the three operators. Only "Antonio" and "Carl" can make a round table. 
  
  | Check out the
    `resource <https://demo.frepple.com/resource-alternate/data/input/resource/>`_,
    `skill <https://demo.frepple.com/resource-alternate/data/input/skill/>`_
    and `resource skill <https://demo.frepple.com/resource-alternate/data/input/resourceskill/>`_
    tables to review this.    
     
  .. image:: _images/resource-alternate-2.png
     :alt: Resources
  
  .. image:: _images/resource-alternate-3.png
     :alt: Resource skills

* | The `operation resources table <https://demo.frepple.com/resource-alternate/data/input/operationresource/>`_
    links an operation with both a machine and an operator. This association is at the resource group level.
    The solver understands it has to pick a resource in the pool of resources that satisfies the skill criteria.

  The *search mode* column lets the solver know how the resource has to be picked. Possible options
  for the search mode are:
  
  * **Priority**
    
    When search mode is set to *priority*, frePPLe will pick the resources by priority 
    (lowest values first, defined in resource skill table) as long as the demand is planned on time.
    
  * **Minimum cost search mode**
    
    When search mode is set to *minimum cost*, frePPLe will pick the resource that minimizes the cost of production.
    Each upstream cost, whether it is at operation, resource, item supplier or item distribution 
    level is included in the total calulated cost and multiplied by the number of parts produced, purchased, shipped.
    
  * **Minimum penalty**
    
    When search mode is set to *minimum penalty*, frePPLe will pick the resource that minimizes the penalty.
    A penalty is paid by an resource each time it produces some material earlier than the requested date. 
    
    If we set the search mode to *minimum penalty*, then frePPLe
    will pick the first resource to produce the first demand (both have a penalty of 0 as they can produce on time).
    FrePPLe will then pick the second resource to produce the second demand (as the first resource will pay a
    penalty because it has been picked for the first demand and can only produce earlier). Then, for the third
    demand, both resources will have the same penalty and frePPle will pick again the first one.
    
  * **Minimum cost plus penalty**
    
    Obviously, this option is a combination of the cost and the penalty. FrePPLe will compute both the cost and
    the penalty for a resource and will pick the one that minimizes the sum.
  
  For the machine park, we have set the search mode to *priority* as we want frePPLe
  to choose machine A over machine B. For the operators, we are also using *minimum cost plus penalty*
  search mode with a cost of 120 for Antonio and 100 for Carl.
  
  .. image:: _images/resource-alternate-4.png
     :alt: Operation resources

* | In the generated plan we can review that, as long as the demand can be met on time (or early), 
    the solver will pick the combination *machine A* and *Carl* to plan the demand.
  | Try adjusting the due date or quantity of the 
    `sales orders <https://demo.frepple.com/resource-alternate/data/input/demand/>`_
     to make some demands late. You will see the alternates *machine B* and *Antonio* start
     to be used.

  | The `resource detail report <https://demo.frepple.com/resource-alternate/data/input/operationplanresource/>`_
    and `plan editor <https://demo.frepple.com/resource-alternate/planningboard/>`_
    are good places to review the machine and operator assignments. You can also use this report
    to manually adjust the assignments. Note that operator "Philippe" and "machine C"
    cannot be selected as they don't have the required skill.
     
  .. image:: _images/resource-alternate-5.png
     :alt: Sales orders

  .. image:: _images/resource-alternate-6.png
     :alt: Resource detail

