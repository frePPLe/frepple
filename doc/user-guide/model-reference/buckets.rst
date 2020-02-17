=======
Buckets
=======

Buckets are used to group time into smaller periods. The buckets are used for reporting, and
also in the forecasting and inventory planning calculations.

Individual time buckets are defined in the :doc:`bucket dates <bucket-dates>` table.

You can define buckets and bucket dates in three different ways:

* Use our standard time buckets. They can be loaded using the "load a dataset" feature in the
  execution screen - select "dates" from the list.
  
* Use the "generate buckets" command from the "execution screen".

* You can upload your own time buckets from a CSV or Excel file.

This table is typically updated only once a year. There is no point in doing this more frequently.

================ ================= ===========================================================
Field            Type              Description
================ ================= ===========================================================
name             string            Unique name.
description      string            Free text description.
level            integer           | Hierarchical indication.
                                   | Higher numbers are used for detailed buckets, eg days.
                                   | Lower numbers are used for coarse buckets, eg years.
================ ================= ===========================================================
