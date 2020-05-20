===============
Resource skills
===============

Resources can be assigned skills, which represent certain qualifications.
Assigned skills can be date effective, and also a priority to define how the
algorithm chooses an resource among the qualified ones.

Resources can also be organized in a hierarchical tree to group
similar resources together.

An operation can load a resource or a resource pool, and you can specify
a skill required to perform the operation. The planning algorithm will then
automatically select an available resource with the required skills from
the pool.

`Check this feature on a live example <https://demo.frepple.com/resource-skills/data/input/resource/>`_

:download:`Download an Excel spreadsheet with the data for this example<resource-skills.xlsx>`

Here is a step by step guide to explore the example:

* This example models a simple job shop. It has a number of machining tools and
  an operator pool. Each operator is only qualified to work on a few of the
  machines.

  This table depicts the skills of each operator. It is defined in the
  `resource <https://demo.frepple.com/resource-skills/data/input/resource/>`_,
  `skill <https://demo.frepple.com/resource-skills/data/input/skill/>`_ and 
  `resource-skill <https://demo.frepple.com/resource-skills/data/input/resource-skill/>`_ 
  tables.
  
  +----------+--------+-------+-------+-----------+-------+-------+-------+
  | Operator | Plasma | Saag  | Boor  | Draaibank | Bou   | Sweis | Verf  |
  |          | skill  | skill | skill | skill     | skill | skill | skill |
  +==========+========+=======+=======+===========+=======+=======+=======+     
  | Andries  |   x    |   x   |   x   |           |       |   x   |       |
  +----------+--------+-------+-------+-----------+-------+-------+-------+
  | Davie    |        |   x   |   x   |           |   x   |       |       |
  +----------+--------+-------+-------+-----------+-------+-------+-------+
  | Gustav   |   x    |   x   |   x   |           |   x   |   x   |       |
  +----------+--------+-------+-------+-----------+-------+-------+-------+
  | Hennie   |        |   x   |   x   |           |       |       |   x   |
  +----------+--------+-------+-------+-----------+-------+-------+-------+
  | Johnny   |        |   x   |   x   |   x       |       |       |   x   |
  +----------+--------+-------+-------+-----------+-------+-------+-------+

  .. image:: _images/resource-skills-1.png
     :alt: Resources

  .. image:: _images/resource-skills-2.png
     :alt: Skills

  .. image:: _images/resource-skills-3.png
     :alt: Resource skills

* | The `resource detail report <https://demo.frepple.com/resource-skills/data/input/operationplanresource/>`_
    shows the assignment of resources (either a machine or an operator) to manufacturing orders.
  
  | In the screenshot below, you can see that the manufacuturing order with reference 6
    uses the resources "bou" and "Davie". Davie has indeed the required skill. In this
    report you can see that the task can also be assigned to Gustav, who also has this skill. 

  .. image:: _images/resource-skills-4.png
     :alt: Resource detail
