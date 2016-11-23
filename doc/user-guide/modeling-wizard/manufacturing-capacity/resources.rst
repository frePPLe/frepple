=========
Resources
=========

| This table contains all the resources you wish to introduce in your supply chain.
| There are three types of resources in frepple: continuous resources, bucketized 
  resources and infinite resources.
| This page will only consider continuous resources, please refer to the advanced 
  topics for details about other resource types.

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
type         non-empty string  | Possible values are : "Default", "Buckets", "Infinite"
                               | For continuous resources, the Default type should be used.
maximum      number            The resource capacity.
============ ================= ===========================================================

.. rubric:: Advanced topics

* Complete table description: :doc:`../../model-reference/resources`

* Modeling resource types: :doc:`../../cookbook/resource/resource-type`

* Modeling resource skills: :doc:`../../cookbook/resource/resource-skills` 

