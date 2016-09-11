========================
Calendar bucket priority
========================

Calendar buckets define a value for the calendar.
Calendar buckets are effective only during specific periods, specified through:

* Start and end date of the validity
* Weekdays on which they are effective
* Hours between which they are effective

If multiple calendar buckets are effective at the same moment in time, the value with the lowest priority field overrides the others.

A calendar also has a default value that is valid when no calendar bucket is effective.

The above rules allow you to determine the value of a calendar at any moment in time, as illustrated in the example below.


.. rubric:: Example

:download:`Excel spreadsheet calendar-working-hours <calendar-working-hours.xlsx>`

The attached example models a warehouse where the replenishment operations are running on weekdays
(Monday through Friday) from 8am till 5pm with a lunch break of an hour. The warehouse is not
working on Christmas, December 25th.

A calendar is used to define these working hours. It has 3 calendar buckets, whose effectivity is illustrated in this picture.

.. image:: calendar_buckets.png

At 20 dec 2014 13:00, or any other moment during the weekend, no calendar bucket is effective. The value of the calendar is then 0, the default value.

22 dec 2014 11:00 falls during regular working hours. The value of the calendar is now 1, as the first calendar bucket is effective.

At 23 dec 2014 12:15 the value of the calendar value is 0 again. There are 2 effective calendar buckets at this moment, but the second calendar bucket has the lowest priority value and overrides the other.

At 25 dec 2014 14:00, or any other moment on December 25, the value of the calendar value is also 0. The third calendar bucket has the lowest priority.
