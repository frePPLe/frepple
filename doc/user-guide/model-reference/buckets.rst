=======
Buckets
=======

Buckets are used to group time into smaller periods. The buckets are used for reporting, and
also in the forecasting and inventory planning calculations.

You can populate these in three different ways:

* Use our standard time buckets. They can be loaded using the "load a dataset" feature in the
  execution screen - select "dates" from the list.
  
* Use the "generate buckets" command from the "execution screen".

* You can of course upload your own time buckets from a CSV or Excel file.

**Fields**

================ ================= ===========================================================
Field            Type              Description
================ ================= ===========================================================
name             string            Unique name.
description      string            Free text description.
level            integer           Hierarchical indication. Higher numbers are used for 
                                   detailed buckets, eg days. Lower numbers are used for 
                                   coarse buckets, eg years.
================ ================= ===========================================================

Bucket detail
-------------

The bucket detail table define how the time horizon is divided in buckets.

When populating this table make sure to respect the following simple guidelines:

* For a given horizon name all dates need to belong to a single time bucket. It not okay to 
  leave gaps between time buckets or have overlapping time bucket.
  
* For a given horizon name the start date of a time bucket must be equal to the end date of
  the time bucket preceding it.
  
* Make sure to cover a period that is long enough: eg from 2014 till 2019.

**Fields**

================ ================= ===========================================================
Field            Type              Description
================ ================= ===========================================================
bucket           string            References the bucket table.
name             name              Label for this time bucket in the user interface.  
start date       dateTime          Starting date of the time bucket.
end date         dateTime          Ending date of the time bucket.
================ ================= ===========================================================
