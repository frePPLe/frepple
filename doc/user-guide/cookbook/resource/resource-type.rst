=============
Resource type
=============

FrePPLe has 2 conceptually different resource types:

* The default resource model has a **continuous** representation of capacity.

  The resource size is the maximum size of the resource.
  The load quantity specifies how much of the resource we use during the complete
  duration of the operationplan.

  This resource model is typically used for short term detailed planning
  and scheduling.

* There is also a **bucketized** resource model where capacity is expressed
  as a total quantity per time bucket.

  The maximum_calendar of the resource defines the time buckets and how much
  capacity (expressed in man-hours/machine-hours) is available per time bucket.
  Each operationplan consumes 'load quantity * operationplan quantity' of the
  resource capacity in the time bucket where it starts.

  This resource model is typically used for mid term master planning.

.. rubric:: Example

:download:`Excel spreadsheet resource-type <resource-type.xlsx>`

In this example there are 3 resources. The first two use the continuous
model and the third is a bucketized resource.

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
