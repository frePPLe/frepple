===================
Operation Resources
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
