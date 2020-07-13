============
Bucket dates
============

The bucket dates table defines individual time buckets in a :doc:`bucket <buckets>`.

When populating this table make sure to respect the following simple guidelines:

* For a given horizon name all dates need to belong to a single time bucket. It not okay to 
  leave gaps between time buckets or have overlapping time bucket.
  
* For a given horizon name the start date of a time bucket must be equal to the end date of
  the time bucket preceding it.
  
* Make sure to cover a period that is long enough: enough periods in the past to cover the
  complete demand history you'll be using for the forecast, and enough periods periods in the
  future to go beyond the furthest future date you want to see in the reports.

This table is typically updated only once a year. There is no point in doing this more frequently. 

================ ================= ===========================================================
Field            Type              Description
================ ================= ===========================================================
bucket           string            References the bucket table.
name             name              Label for this time bucket in the user interface.  
start date       dateTime          Starting date of the time bucket.
end date         dateTime          Ending date of the time bucket.
================ ================= ===========================================================
