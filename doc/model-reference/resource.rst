========
Resource
========

Resources represent capacity. They represent a machine, a worker or
a group of workers, or some logical limits.

Operations will consume capacity using loads.

Different types of resources exist:

* | `Resource_default`_:
  | A default resource is constrained with a maximum load size. The resource
    size defines how many operations that can use the resource in parallel.
  | For detailed planning and scheduling this is the most suitable resource
    type.
  | E.g. A resource that can run 2 jobs at the same time.

* | `Resource_buckets`_:
  | A bucketized resource is constrained with a maximum load quantity per
    time bucket.
  | For master planning and rough cut capacity planning this is most suitable
    resource type.
  | E.g. A resource that can produce 1000 units per week.

* | `Resource_infinite`_:
  | An infinite resource has no capacity limit.

**Fields**

================ ================= ===========================================================
Field            Type              Description
================ ================= ===========================================================
name             non-empty string  | Name of the resource.
                                   | This is the key field and a required attribute.
description      string            Free format description.
category         string            Free format category.
subcategory      string            Free format subcategory.
owner            resource          | Resources can be organized in a hierarchical tree.
                                   | This field defines the parent resource.
                                   | When an operation loads a resource which has members, the
                                     planning algorithm will select one of the child resource.
members          list of resource  | Resources can be organized in a hierarchical tree.
                                   | This field defines a list of child resources.
location         location          | Location of the resource.
                                   | Default is null.
                                   | The working hours and holidays for the resource are taken
                                     from the ‘available’ calendar of the location.
maximum          double            | Defines the maximum size of the resource.
                                   | The default value is 1, i.e. a resource that can handle
                                     1 operationplan at a time (provided of course that this
                                     operationplan requires 1 unit on the resource).
                                   | A problem is reported when the resource load exceeds
                                     than this limit.
                                   | This field is ignored on resource of type buckets and infinite.
maximum_calendar calendar          | Refers to a calendar storing the available capacity.
                                   | Use this field when the resource size is varying over time.
                                     If this field is populated, the field maximum is ignored.
                                   | On resources of type buckets this calendar defines the
                                     time buckets as well as the maximum quantity per time bucket.
                                   | This field is ignored on resources of type infinite.
cost             double            | The cost of using 1 unit of this resource for 1 hour.
                                   | The default value is 0.
detectproblems   boolean           | Set this field to false to suppress problem detection on
                                     this resource.
                                   | Default is true.
maxearly         duration          | Time window before the ask date where we look for available
                                     capacity.
                                   | The default value is 100 days.
loads            list of load      Defines the capacity of the operations.
loadplans        list of loadplan  | This field is populated during an export with the plan
                                     results for this resource. It shows the resource load
                                     profile.
                                   | The field is export-only.
                                   | The description of the loadplan model is included in the
                                     section on operationplan.
level            integer           | Indication of how upstream/downstream this entity is
                                     situated in the supply chain.
                                   | Lower numbers indicate the entity is close to the end
                                     item, while a high number will be shown for components
                                     nested deep in a bill of material.
                                   | The field is export-only.
cluster          integer           | The network of entities can be partitioned in completely
                                     independent parts. This field gives the index for the
                                     partition this entity belongs to.
                                   | The field is export-only.
setup            non-empty string  The name of the current setup of the resource, ie the
                                   setup of the resource at the start of the planning horizon.
setupmatrix      setupmatrix       The name of the setup matrix which specifies the changeover
                                   times between setups.
hidden           boolean           Marks entities that are considered hidden and are normally
                                   not shown to the end user.
action           A/C/AC/R          | Type of action to be executed:
                                   | A: Add an new entity, and report an error if the entity
                                     already exists.
                                   | C: Change an existing entity, and report an error if the
                                     entity doesn’t exist yet.
                                   | AC: Change an entity or create a new one if it doesn’t
                                     exist yet. This is the default.
                                   | R: Remove an entity, and report an error if the entity
                                     doesn’t exist.
================ ================= ===========================================================

Resource_default
----------------

A default resource is constrained with a maximum load size. The resource size
defines how many operations that can use the resource in parallel.

For detailed planning and scheduling this is the most suitable resource type.
E.g. A resource that can run 2 jobs at the same time.

No fields are defined in addition to the ones listed above.

Resource_buckets
----------------

A bucketized resource is constrained with a maximum load quantity per time
bucket.

For master planning and rough cut capacity planning this is most suitable
resource type. E.g. A resource that can produce 1000 units per week

No fields are defined in addition to the ones listed above, but the
maximum_calendar field must is be specified.

Resource_infinite
-----------------

An infinite resource has no capacity limit. It is useful to monitor the
loading or usage of a resource without constraining the plan.

The fields ‘maximum’ and ‘maximum_calendar’ are unused for this resource type.

**Example XML structures**

Adding or changing a resource

.. code-block:: XML

    <plan>
      <resources>
        <resource name="machine X">
          <maximum_calendar name="capacity calendar for machine X" />
        </resource>
        <resource name="machine Y">
          <maximum>2</maximum>
        </resource>
      </resources>
    </plan>

Deleting a resource

.. code-block:: XML

    <plan>
       <resources>
          <resource name="machine X" action="R"/>
       </resources>
    </plan>

**Example Python code**

Adding or changing a resource

::

    cal = frepple.calendar(name="capacity calendar for machine X")
    res_X = frepple.resource(name="machine X", maximum_calendar=cal)
    res_Y = frepple.resource(name="machine X", maximum=2)

Deleting a resource

::

    frepple.resource(name="machine X", action="R")

Iterate over resources, loads and loadplans

::

    for r in frepple.resources():
      print "Resource:", r.name, r.description, r.category
      for l in r.loads:
        print "  Load:", l.operation.name, l.quantity,
          l.effective_start, l.effective_end
      for l in r.loadplans:
        print "  Loadplan:", l.operationplan.operation.name,
          l.quantity, l.startdate, l.enddate, l.operationplan.id
