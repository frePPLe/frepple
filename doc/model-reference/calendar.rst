========
Calendar
========

A calendar represents a numeric value that is varying over time.

Calendars can be linked to multiple entities: a maximum capacity limit of a
resource, a minimum capacity usage of a resource, a minimum or maximum
inventory limit of a buffer, etc...

A calendar has multiple buckets to define the values over time. To determine
the calendar value at a certain date the calendar will evaluate each of the
buckets and combine the results in the following way:

* | A bucket is only valid from its “start” date (inclusive) till its “end”
    date (exclusive).
  | Outside of this date range a bucket is never selected.

* | If multiple bucket are effective on a date, the one with the lowest
    “priority” value is taken.
  | In case buckets have the same priority, the value of the bucket with the
    latest start date is selected.

* In case no bucket is effective on a certain date, the calendar will return
  the “default” value.

**Fields**

============ ================= ===========================================================
Field        Type              Description
============ ================= ===========================================================
name         non-empty string  Name of the calendar.
                               This is the key field and a required attribute.
default      double            The default value of the calendar when no bucket is
                               effective.
action       A/C/AC/R          | Type of action to be executed:
                               | A: Add an new entity, and report an error if the entity
                                 already exists.
                               | C: Change an existing entity, and report an error if the
                                 entity doesn’t exist yet.
                               | AC: Change an entity or create a new one if it doesn’t
                                 exist yet. This is the default.
                               | R: Remove an entity, and report an error if the entity
                                 doesn’t exist.
============ ================= ===========================================================

**Methods**

+-----------------------------+----------------------------------------------------------+
| Method                      | Description                                              |
+=============================+==========================================================+
| setValue([start date],      | Creates or updates calendar buckets to reflect the       |
| [end date],[value])         | specified value in the given date range.                 |
+-----------------------------+----------------------------------------------------------+
| buckets()                   | Returns an iterator over the calendar buckets.           |
+-----------------------------+----------------------------------------------------------+
| events([start date],        | Returns an iterator over the calendar events starting    |
| [direction])                | from the (optional) start date, either backward or       |
|                             | forward in time. These are the dates at which the        |
|                             | calendar value is changing.                              |
|                             |                                                          |
|                             | Each event is a tuple with 2 fields:                     |
|                             |                                                          |
|                             | - date: date of the event.                               |
|                             |                                                          |
|                             | - value: value that becomes effective at the time of     |
|                             |   the event.                                             |
+-----------------------------+----------------------------------------------------------+

Calendar bucket
---------------

============ ================= ===========================================================
Field        Type              Description
============ ================= ===========================================================
id           integer           | Unique identifier within the calendar of the bucket.
                               | When left unspecified in the input data it is
                                 automatically created.
start        dateTime          | Start date of the validity of this bucket.
                               | When left unspecified, the entry is effective from the
                                 infinite past.
end          dateTime          | End date of the validity of this bucket.
                               | When left unspecified, the entry is effective indefinitely
                                 in the future.
priority     integer           | Priority of this bucket when multiple buckets are
                                 effective for the same date.
                               | Lower values indicate higher priority.
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
value        double            The actual time-varying value.
============ ================= ===========================================================


**Example XML structures**

Adding or changing a calendar and its buckets

.. code-block:: XML

    <plan>
      <calendars>
        <calendar name="cal">
          <default>5</default>
          <buckets>
            <bucket start="2007-01-01T00:00:00" value="10" priority="1"/>
            <!-- This entry overrides the first one during February. -->
            <bucket start="2007-02-01T00:00:00" end="2007-03-01T00:00:00" value="20" priority="0"/>
          </buckets>
        </calendar >
      </calendars>
    </plan>

Removing a calendar

.. code-block:: XML

    <plan>
       <calendars>
          <calendar name="cal" action="R"/>
       </calendars>
    </plan>

**Example Python code**

Adding or changing a calendar and its buckets

::

   cal = frepple.calendar_double(name="cal", default=5)

Removing a calendar

::

   frepple.calendar(name="cal", action="R")

Iterating over all buckets of a calendar

::

   for b in frepple.calendar(name="cal").buckets():
     print b.name, b.value

Iterating over all events of a calendar, going forward in time from a certain date

::

   start = datetime.datetime(2009,1,1)
   for date, value in frepple.calendar(name="cal").events(start, True):
     print date, value
