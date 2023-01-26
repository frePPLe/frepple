=========
Resources
=========

Resources represent capacity. They represent a machine, a group of machines,
an operator, a group of operators, or some logical capacity constraint.

`Operations <operations>`_ will consume capacity using `operation resources <operation-resources>`_.

Different types of resources exist:

* | `Default <#default-resource>`_:
  | A default resource is constrained with a maximum load size. The resource
    size defines how many operations that can use the resource in parallel.

  E.g. A resource that can run 1 job at a time.

  .. image:: _images/resource-default.png
     :width: 50%
     :alt: Continuous resource

* | `Time buckets <#time-buckets-resource>`_:
  | A bucketized resource is constrained by the amount of resource-hours per
    time bucket. The detailed scheduling of the resource within this bucket
    isn't considered.

  E.g. A resource that has 40 hours available per week.

  .. image:: _images/resource-time-buckets.png
     :width: 50%
     :alt: Time bucket resource

* | `Quantity buckets <#quantity-buckets-resource>`_:
  | A bucketized resource is constrained with a maximum load quantity per
    time bucket.

  E.g. A resource that can produce 1000 units per week.

  .. image:: _images/resource-quantity-buckets.png
     :width: 50%
     :alt: Quantity bucket resource

* | `Infinite resource <#infinite-resource>`_:
  | An infinite resource has no capacity limit.
  | This can be modeled by setting the "constrained" field to false
    or (deprecated) by setting the resource type to "infinite".

You can see each resource type in action in `this example <../examples/resource/resource-type.html>`_.

==================== ================= ===========================================================
Field                Type              Description
==================== ================= ===========================================================
name                 non-empty string  | Unique name of the resource.
                                       | This is the key field and a required attribute.
description          string            Free format description.
category             string            Free format category.
subcategory          string            | Free format subcategory.
                                       | If this field is set to 'tool', the field 'tool' will
                                         automatically be set to true.
owner                resource          | Resources can be organized in a hierarchical tree.
                                       | This field defines the parent resource.
                                       | When an operation loads a resource which has members, the
                                         planning algorithm will select one of the child resource.
members              list of resource  | Resources can be organized in a hierarchical tree.
                                       | This field defines a list of child resources.
location             location          | Location of the resource.
                                       | Default is null.
                                       | The working hours and holidays for the resource are taken
                                         from the "available" calendar of the location.
constrained          boolean           | This flag controls whether whether or not this resource is
                                         planned in finite capacity mode.
                                       | The default is true, except for resources of type infinite.
maximum              double            | Defines the maximum size of the resource.
                                       | The default value is 1, i.e. a resource that can handle
                                         1 operation at a time (provided of course that this
                                         operation requires 1 unit on the resource).
                                       | A problem is reported when the resource load exceeds
                                         than this limit.
                                       | This field is ignored on resource of type buckets and infinite.
maximum_calendar     calendar          | Refers to a calendar storing the available capacity.
                                       | Use this field when the resource size is varying over time.
                                         If this field is populated, the field maximum is ignored.
                                       | On resources of type buckets this calendar defines the
                                         time buckets as well as the maximum quantity per time bucket.
                                       | This field is ignored on resources of type infinite.
available            calendar          A calendar specifying the working hours for the resource.

                                       The working hours and holidays for a resource are
                                       calculated as the intersection of:

                                       * its availability calendar.

                                       * the availability calendar of its location.

                                       Default is null.

efficiency           double            The efficiency of this resource, expressed as a percentage. The
                                       manufacturing order duration will be extended or shrunk when this field
                                       is different from 100.

                                       The default value is 100.

efficiency_calendar  double            Refers to a calendar storing the resource efficiency when it varies
                                       over time.

                                       If this field is populated, the field efficiency is ignored.

cost                 double            The cost of using 1 unit of this resource for 1 hour.

                                       The default value is 0.

maxearly             duration          Time window before the ask date where we look for available
                                       capacity.

                                       The default value is 100 days.

setup                non-empty string  The name of the current setup of the resource, ie the
                                       setup of the resource at the start of the planning horizon.

setupmatrix          setupmatrix       The name of the setup matrix which specifies the changeover
                                       times between setups.

hidden               boolean           Marks entities that are considered hidden and are normally
                                       not shown to the end user.

tool                 boolean           | A flag to resources that represents tools. Tools represent
                                         holders, fixtures or moulds that are attached to a
                                         manufacturing order over a number of steps in a routing.
                                         The same tool needs to stay attached to all steps in the
                                         manufacturing routing.
                                       | Default is false.
                                       | This field is only visible in the planning engine. In the
                                         user interface you use the subcategory field to set this
                                         field to true.
==================== ================= ===========================================================

Default resource
----------------

A default resource is constrained with a maximum load size. The resource size
defines how many operations that can use the resource in parallel.

For detailed planning and scheduling this is the most suitable resource type.
E.g. A resource that can run 2 jobs at the same time.

No fields are defined in addition to the ones listed above.

Time buckets resource
---------------------

A resource of this type is constrained by the amount of resource-hours
per time bucket. E.g. A resource that has 40 hours available per week.

The available time per capacity bucket is computed using:

* its size, as specified by the maximum or the maximum_calendar field.

* its working hours, as specfied by its available calendar field and its
  location's available calendar field

A manufacturing order will consume the required capacity in the capacity
bucket where it starts.

For master planning and rough cut capacity planning this is most suitable
resource type. Detailed scheduling of the operations within the time
bucket isn't considered useful in this type of plan.

Quantity buckets resource
-------------------------

A resource of this type is constrained by a maximum quantity per time
bucket. E.g. A resource that can produce 1000 units per week

For master planning and rough cut capacity planning this is most suitable
resource type. Detailed scheduling of the operations within the time
bucket isn't considered useful.

The maximum_calendar field defines the time buckets, as well as the
available quantity per time bucket.

A number of specialized operationresource subclasses exist to select
in which bucket the capacity needs to be consumed: at the start of the
operation, at the end of the operation or somewhere between
the start and end.

Infinite resource
-----------------

An infinite resource has no capacity limit. It is useful to monitor the
loading or usage of a resource without constraining the plan.

The fields 'maximum' and 'maximum_calendar' are unused for this resource type.
