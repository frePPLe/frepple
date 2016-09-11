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

.. rubric:: Example

:download:`Excel spreadsheet resource-skills <resource-skills.xlsx>`

This example models a simple job shop. It has a number of machining tools and
an operator pool. Each operator is only qualified to work on a few of the
machines.

Each operation loads both the required machine and a qualified member of the
operator pool.