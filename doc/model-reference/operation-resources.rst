===================
Operation resources
===================

Operation resources are used to model the capacity consumption of an operation.

=============== ================= ===========================================================
Field           Type              Description
=============== ================= ===========================================================
operation       operation         | Operation loading the resource.
                                  | This is a required field.
resource        resource          | Resource being loaded.
                                  | This is a required field.
skill           skill             | Skill required of the resource.
                                  | This field is optional.
quantity        double            | Required quantity of the resource.
                                  | The default value is 1.0.
                                  | The use of the value is different per resource type:

                                  * | Type 'default':
                                    | The resource is used during the complete duration of the
                                      manufacturing order.
                                    | If the resource has a size of 1 and the
                                      operationresource record has a quantity of 1, then only
                                      1 operation can be planned in parallel.

                                  * | Type 'time buckets' and 'quantity buckets':
                                    | The total capacity consumed by a manufacturing order
                                      is equal to the (quantity_fixed + quantity * manufacturing
                                      order quantity) / efficiency.
                                    | This quantity is consumed from the capacity bucket where
                                      the manufacturing order starts.

quantity_fixed  double            | For a resource of type 'time buckets' or 'quantity buckets'
                                    the total capacity consumed by a manufacturing order
                                    is equal to the (quantity_fixed + quantity * manufacturing
                                    order quantity) / efficiency.
                                  | The default value is 0.0.
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

                                  * | MINCOST
                                    | Select the cheapest resource.

                                  * | MINPENALTY
                                    | Select the alternate which gives the lowest penalty.
                                    | Building before the requirement date incurs a penalty,
                                      so this mode favors resources that are readily available.
                                    | This is the default.

                                  * | MINCOSTPENALTY
                                    | Select the alternate which gives the lowest sum of
                                      the cost and penalty.
=============== ================= ===========================================================

On *default resources* the resource is used during the complete duration
of the operation.

On *bucketized resources* the capacity is consumed from the capacity bucket
at a single moment of time. Different loading policies can be specified:

* | default:
  | By default capacity is consumed at the start of the operation.

* | load_bucketized_end:
  | A load of this type that loads a bucketized resource at a specified
    offset from the end date of the operation.
  | An offset of 0 means loading the resource at the end of the operation.
  | An offset of 1 day means loading the resource 1 day before the operation
    end date. If the operation takes less than 1 day we load the resource
    at the start date.
  | The offset is computed based on the available periods of the operation,
    and skips unavailable periods.
  | THIS FUNCTIONALITY IS NOT AVAILABLE IN THE USER INTERFACE, AND IT IS ONLY IN
    BETA STATE IN THE PLANNING ENGINE.

* | load_bucketized_start:
  | A load of this type loads a bucketized resource at a specified
    offset from the start date of the operation.
  | An offset of 0 means loading the resource at the start of the operation.
  | An offset of 1 day means loading the resource 1 day after the operation
    start date. If the operation takes less than 1 day we load the resource
    at the end date.
  | The offset is computed using the available periods of the operation,
    and skips unavailable periods.
  | THIS FUNCTIONALITY IS NOT AVAILABLE IN THE USER INTERFACE, AND IT IS ONLY IN
    BETA STATE IN THE PLANNING ENGINE.

* | load_bucketized_percentage:
  | A load of this type loads a bucketized resource at a percentage of the
    operation duration.
  | An offset of 0 means loading the resource at the start of the operation.
  | An offset of 100 means loading the resource at the end of the operation.
  | The calculations consider the available periods of the operations, and
    skip unavailable periods.
  | THIS FUNCTIONALITY IS NOT AVAILABLE IN THE USER INTERFACE, AND IT IS ONLY IN
    BETA STATE IN THE PLANNING ENGINE.
