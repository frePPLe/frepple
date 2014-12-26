=======
Problem
=======

FrePPLe will automatically detect problems and inconsistencies in the plan.

Problem detection can optionally be disabled on entities by setting the
field “DETECTPROBLEMS” to false.

Problems are export-only, i.e. you can’t read them as input.

**Types**

+-----------------+-------------------+--------------------------------------------+
| Entity          | Category          | Description                                |
+=================+===================+============================================+
| Demand          | unplanned         | No plan exists yet to satisfy this demand. |
|                 +-------------------+--------------------------------------------+
|                 | excess            | A demand is planned for more than the      +
|                 |                   | requested quantity.                        |
|                 +-------------------+--------------------------------------------+
|                 + short             | A demand is planned for less than the      |
|                 |                   | requested quantity.                        |
|                 +-------------------+--------------------------------------------+
|                 + late              | A demand is satisfied later than its due   |
|                 |                   | date.                                      |
|                 +-------------------+--------------------------------------------+
|                 + early             | A demand is planned earlier than its due   |
|                 |                   | date.                                      |
+-----------------+-------------------+--------------------------------------------+
| Resource        | overload          | A resource is being overloaded during a    |
|                 |                   | certain period of time.                    |
|                 +-------------------+--------------------------------------------+
|                 | underload         | A resource is loaded below its minimum     |
|                 |                   | during a certain period of time.           |
|                 |                   | Not implemented yet...                     |
+-----------------+-------------------+--------------------------------------------+
| Buffer          | material excess   | A buffer is carrying too much material     |
|                 |                   | during a certain period of time.           |
|                 +-------------------+--------------------------------------------+
|                 | material shortage | A buffer is having a material shortage     |
|                 |                   | during a certain period of time.           |
+-----------------+-------------------+--------------------------------------------+
| Operationplan   | before current    | Flagged when an operationplan is being     |
|                 |                   | planned in the past, i.e. it starts before |
|                 |                   | the current date of the plan.              |
|                 +-------------------+--------------------------------------------+
|                 | before fence      | Flagged when an operationplan is being     +
|                 |                   | planned before its fence date, i.e. it     |
|                 |                   | starts 1) before the current date of the   |
|                 |                   | plan plus the release fence of the         |
|                 |                   | operation and 2) after the current date of |
|                 |                   | the plan.                                  |
|                 +-------------------+--------------------------------------------+
|                 | precedence        | Flagged when the sequence of two           |
|                 |                   | operationplans in a routing isn’t          |
|                 |                   | respected.                                 |
+-----------------+-------------------+--------------------------------------------+
| | Demand        | invalid data      | Some data problem prevents this object     |
| | or Buffer     |                   | from being planned.                        |
| | or Resource   |                   |                                            |
| | or Operation  |                   |                                            |
+-----------------+-------------------+--------------------------------------------+

**Fields**

============ ================= ===========================================================
Field        Type              Description
============ ================= ===========================================================
name         string            Problem type.
description  string            Description of the problem.
weight       double            A number expressing the seriousness of the problem.
start        dateTime          Date at which the problem starts.
end          dateTime          Date at which the problem ends.
============ ================= ===========================================================

**Example Python code**

Iterate over all problems

::

    for i in frepple.problems():
       print i.entity, i.name, i.description, i.start, i.end, i.weight
