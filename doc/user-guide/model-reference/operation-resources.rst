===================
Operation resources
===================

Operation resources are used to model the capacity consumption of an operation.

**Fields**

=============== ================= ===========================================================
Field           Type              Description
=============== ================= ===========================================================
operation       operation         | Operation loading the resource.
                                  | This is a required field.
resource        resource          | Resource being loaded.
                                  | This is a required field.
skill           skill             | Skill required of the resource.
                                  | This field is optional.
quantity        double            | Load factor of the resource.
                                  | The default value is 1.0.
effective_start dateTime          | Date after which the resource load is valid.
                                  | Before this date the planned quantity is always 0.
effective_end   dateTime          | Date at which the resource load becomes invalid.
                                  | After this date (and also at the exact date) the planned
                                    quantity is always 0.
priority        integer           | Priority of the load, used in case of alternate load.
                                  | The default is 1. Lower numbers indicate more preferred
                                    loads.
name            non-empty string  | Optional name of the load.
                                  | All loads with the same name are considered to be
                                    alternates of each other.
setup           non-empty string  Name of the required setup on the resource.
search          string            | Defines the order of preference among the alternate loads.
                                  | The valid choices are:

                                  * | PRIORITY
                                    | Select the alternate with the lowest priority number.
                                    | This is the default.

                                  * | MINCOST
                                    | Select the alternate which gives the lowest cost.
                                    | The cost includes the cost of all upstream operations,
                                      resources and buffers.

                                  * | MINPENALTY
                                    | Select the alternate which gives the lowest penalty.
                                    | The penalty includes the penalty of all penalties
                                      incurred in the upstream plan along the load.

                                  * | MINCOSTPENALTY
                                    | Select the alternate which gives the lowest sum of
                                      the cost and penalty.
                                    | The sum is computed for the complete upstream path.
=============== ================= ===========================================================

**Types**

On *default resources* the resource is used during the complete duration
of the operationplan.

On *bucketized resources* the capacity is consumed from the capacity bucket
at a single moment of time. Different loading policies can be specified:

* | default:
  | By default capacity is consumed at the start of the operationplan.

* | load_bucketized_end:
  | A load of this type that loads a bucketized resource at a specified
    offset from the end date of the operationplan.
  | An offset of 0 means loading the resource at the end of the operationplan.
  | An offset of 1 day means loading the resource 1 day before the operationplan
    end date. If the operationplan takes less than 1 day we load the resource
    at the start date.
  | The offset is computed based on the available periods of the operationplan,
    and skips unavailable periods.

* | load_bucketized_start:
  | A load of this type loads a bucketized resource at a specified
    offset from the start date of the operationplan.
  | An offset of 0 means loading the resource at the start of the operationplan.
  | An offset of 1 day means loading the resource 1 day after the operationplan
    start date. If the operationplan takes less than 1 day we load the resource
    at the end date.
  | The offset is computed using the available periods of the operationplan,
    and skips unavailable periods.

* | load_bucketized_percentage:
  | A load of this type loads a bucketized resource at a percentage of the
    operationplan duration.
  | An offset of 0 means loading the resource at the start of the operationplan.
  | An offset of 100 means loading the resource at the end of the operationplan.
  | The calculations consider the available periods of the operationplan, and
    skip unavailable periods.
