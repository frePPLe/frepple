=========
Resources
=========

Resources represent capacity. They represent a machine, a group of machines,
an operator, a group of operators, or some logical capacity constraint.

There are four types of resources:

* | Default resources:
  | Have a continuous timeline to represent the resource.

* | Time bucket resources:
  | Represent capacity as a number of hours per daily, weekly 
    or monthly time bucket.

* | Quantity bucket resources:
  | Represent capacity as a number of units per daily, weekly or
    monthly time bucket.

* | Infinite resources:
  | Have no capacity constraint.

This page will only consider the default continuous resource type. Check out to the
links at the bottom of this page for information on the other types.

By default, frepple will create for an operation as many work orders as needed to 
meet the demand. You might not this to happen if an operation is modeling a machine
that can only produce one batch at a time. Therefore you will need a continuous 
resource of capacity one to make sure that only one work order can use an operation
at the same time.

You can also use continuous resources to model a pool of machines. If you have 3 
identical machines, then you can model only one operation in frepple and use a 
continuous resource of capacity 3 to allow a maximum of 3 work orders to use that
operation at the same time.

.. rubric:: Key Fields

============ ================= ===========================================================
Field        Type              Description
============ ================= ===========================================================
name         non-empty string  Unique name of the resource.
location     location          The resource location.
type         non-empty string  Possible values are:
                               
                               * default
                               * buckets
                               * buckets_day
                               * buckets_week
                               * buckets_month
                               * infinite
                               
maximum      number            The resource capacity.
============ ================= ===========================================================

.. rubric:: Advanced topics

* Complete table description: :doc:`../../model-reference/resources`

* Modeling resource types: :doc:`../../examples/resource/resource-type`

* Modeling resource skills: :doc:`../../examples/resource/resource-skills` 

