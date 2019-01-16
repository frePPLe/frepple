=========
Calendars
=========

A calendar represents a numeric value that is varying over time.

Calendars can be linked to multiple entities: a maximum capacity limit of a
resource, a minimum capacity usage of a resource, a minimum or maximum
inventory limit of a buffer, etc...

A calendar has multiple buckets to define the values over time. See 
:doc:`calendar buckets <calendar-buckets>` for more details. To determine the 
calendar value at a certain date the calendar will evaluate each of the
buckets and combine the results in the following way:

* | A bucket is only valid from its "start" date (inclusive) till its "end"
    date (exclusive).
  | Outside of this date range a bucket is never selected.

* | If multiple bucket are effective on a date, the one with the lowest
    "priority" value is taken.
  | In case buckets have the same priority, the value of the bucket with the
    latest start date is selected.

* In case no bucket is effective on a certain date, the calendar will return
  the "default" value.

**Fields**

============ ================= ===========================================================
Field        Type              Description
============ ================= ===========================================================
name         non-empty string  Unique name of the calendar.
                               This is the key field and a required attribute.
default      double            The default value of the calendar when no bucket is
                               effective.
============ ================= ===========================================================
