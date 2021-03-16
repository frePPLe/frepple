=========
Calendars
=========

A calendar represents a numeric value that is varying over time.

Different other models refer to calendars for any property that changes over time:

* A location refers to a calendar to define the working hours and holidays.
* A resource refers to a calendar to define the working hours and holidays.
* A supplier refers to a calendar to define the working hours and holidays.
* An operation refers to a calendar to define the working hours and holidays.
* A resource refers to a calendar to define the efficiency varying over time.
* A resource refers to a calendar to define the resource size varying over time.
* A buffer refers to a calendar to define the safety stock varying over time.

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

============ ================= ===========================================================
Field        Type              Description
============ ================= ===========================================================
name         non-empty string  Unique name of the calendar.
                               This is the key field and a required attribute.
default      double            The default value of the calendar when no bucket is
                               effective.
============ ================= ===========================================================
