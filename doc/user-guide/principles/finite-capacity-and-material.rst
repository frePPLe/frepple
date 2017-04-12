==========================================
Planning with finite capacity and material
==========================================

A finite-capacity plan should consider the material, capacity, lead time 
constraints and their interaction.

These constraints interact, and the plan should be paced around the most
restricting constraint.

Some examples to illustrate:

- A raw material will only be available in 3 weeks.
  As a consequence, resource capacity for operations using this material 
  shouldn't be happening before 3 weeks.
  Also, the requirements for other raw materials that are used by the 
  same operations should be delayed as well.
  
- A bottleneck resource can only produce a certain manufacturing order 
  in 4 weeks.
  As a consequence, all components and subassemblies required for the 
  manufacturing order should be planned be available only when the 
  manufacturing order is planned to start.
  
This results in a plan respecting the best practices of lean manufacturing 
(ie avoid waste) and the theory of constraints (ie pace everything to the
bottleneck).