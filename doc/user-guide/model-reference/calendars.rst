=========
Calendars
=========

A calendar represents a numeric value that is varying over time.

Calendars can be linked to multiple entities: a maximum capacity limit of a
resource, a minimum capacity usage of a resource, a minimum or maximum
inventory limit of a buffer, etc...

A calendar has multiple buckets to define the values over time. To determine
the calendar value at a certain date the calendar will evaluate each of the
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

Calendar bucket
---------------

============ ================= ===========================================================
Field        Type              Description
============ ================= ===========================================================
value        double            The actual time-varying value.
start        dateTime          | Start date of the validity of this bucket.
                               | When left unspecified, the entry is effective from the
                                 infinite past.
                               | Makes up the key together with the end and priority
                                 fields.
end          dateTime          | End date of the validity of this bucket.
                               | When left unspecified, the entry is effective indefinitely
                                 in the future.
                               | Makes up the key together with the start and priority
                                 fields.
priority     integer           | Priority of this bucket when multiple buckets are
                                 effective for the same date.
                               | Lower values indicate higher priority.
                               | Makes up the key together with the start and end
                                 fields.
days         integer           | Bit pattern representing the days on which the calendar
             between 0 and 127   bucket is valid:
                               | Bit 0 = 1 = Sunday
                               | Bit 1 = 2 = Monday
                               | Bit 2 = 4 = Tuesday
                               | Bit 3 = 8 = Wednesday
                               | Bit 4 = 16 = Thursday
                               | Bit 5 = 32 = Friday
                               | Bit 6 = 64 = Saturday
                               | The default value is 127, ie valid on every day of
                                 the week.
starttime    duration          | Time when this entry becomes effective on valid days in
                                 the valid date horizon.
                               | The default value is PT0S, ie midnight.
endtime      duration          | Time when this entry becomes ineffective on valid days
                                 in the valid date horizon.
                               | The default value is PT23H59M59S, ie right before
                                 midnight of the next day.
============ ================= ===========================================================
