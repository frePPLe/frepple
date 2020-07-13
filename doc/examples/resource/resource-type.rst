=============
Resource type
=============

Planners can think in different ways on their capacity limits:

* "We can do N jobs at a time"

* "We can produce N units per week (or day, or month)"

* "We have N hours available per week (or day, or month)"

FrePPLe has different resource types that represent these different views on
the concept of capacity.

* The **default** resource model has a continuous representation of capacity.

  The resource size is the maximum size of the resource.
  The load quantity specifies how much of the resource we use during the complete
  duration of the operation.

  This resource model is typically used for short term detailed planning
  and scheduling.
  
  .. image:: ../../model-reference/_images/resource-default.png
     :width: 50%
     :alt: Continuous resource

* There is also a **quantity buckets** resource model where capacity is expressed
  as a total quantity per capacity bucket.

  The maximum_calendar of the resource defines the time buckets and how much
  capacity (expressed in man-hours/machine-hours) is available per time bucket.
  Each operation consumes 'load quantity * operation quantity' of the
  resource capacity in the time bucket where it starts.

  This resource model is typically used for mid term master planning.

  .. image:: ../../model-reference/_images/resource-quantity-buckets.png
     :width: 50%
     :alt: Quantity bucket resource

* There is also a **times buckets** resource model where capacity is expressed
  as a total available resource-hours per capacity bucket.

  The available hours per capacity bucket are computed using the resource
  size and its availabile working hours.

  This resource model is typically used for mid term master planning.

  .. image:: ../../model-reference/_images/resource-time-buckets.png
     :width: 50%
     :alt: Time bucket resource

* There is also a **infinite** resource model where capacity remains unconstrained.

.. rubric:: Example

`Check this feature on a live example <https://demo.frepple.com/resource-type/data/input/resource/>`_

In this example there are 5 resources. The first two use the continuous
model. The third is a resource with quantity buckets resource. The example
also contains a time buckets resource and an infinite resource. 

The first resource represents a machine of which we have two installed. The
constrained plan will never allocate more than 2 jobs simultaneously on the
resource. The total available capacity in a weekly time bucket is 2*7
machine-days (or machine-hours if the parameter 'loading_time_units' is set
to 'hours')

The second resource is similar to the first, except that now the resource
size is varying over time. Until April 1st we have 1 resource available, and
after that date we have 2 available.

The third resource represent a work center that is capable of producing
10000 units per week. The plan of the resource doesn't bother at all during
which days of the week we plan the production.

The fourth and fith resource mirror the loading of the second resource. 
Resource D does this with monthly capacity buckets. Resource E does it in a
fully unconstrained way.

.. image:: _images/resource-type.png
  :alt: Resource report
