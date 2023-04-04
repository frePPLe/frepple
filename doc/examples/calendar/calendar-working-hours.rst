=============
Working hours
=============

Each location is associated with a working hour calendar through the field *location.available*.

A value 0 of the calendar buckets indicates unavailable time.
Other values (typically 1) indicate available time.

The easiest way to assign a working hour calendar, is to assign calendar to all operations
and resources in that location.
Use the field *operation.location* to stretch the duration of an operation to consider the non-working hours.
Use the field *resource.location* to represent the off-shift hours on the resources.

When resources or operations with different working hours exist within the same location, you can
use the *operation.avaiable* or *resource.location* fields to define the working hours on a more
detailed level.

It is fine to leave theses fields empty, which indicates 24 by 7 availability.
If the fields are populated, you should populate them consistently. You'll run into strange situations when planning
an operation in location A that loads a resource in location B using another calendar.

`Check this feature on a live example <https://demo.frepple.com/calendar-working-hours/data/input/location/>`_

:download:`Download an Excel spreadsheet with the data for this example <calendar-working-hours.xlsx>`

* | The attached example models a warehouse where the manufacturing operations are running on 
    weekdays (Monday through Friday) from 8am till 5pm with a lunch break of an hour. The manufacturing 
    site is also not working on Christmas, December 25th.

  | You can review this setup in the 
    `location table <https://demo.frepple.com/calendar-working-hours/data/input/location/>`_,
    `calendar table <https://demo.frepple.com/calendar-working-hours/data/input/calendar/>`_,
    `calendar bucket table <https://demo.frepple.com/calendar-working-hours/data/input/calendarbucket/>`_

  .. image:: _images/calendar-working-hours-1.png
     :alt: Locations

  .. image:: _images/calendar-working-hours-2.png
     :alt: Calendars

  .. image:: _images/calendar-working-hours-3.png
     :alt: Calendar buckets
  
* | The results can be review from the 
    `manufacturing order <https://demo.frepple.com/calendar-working-hours/data/input/manufacturingorder/>`_.
    and `distribution order <https://demo.frepple.com/calendar-working-hours/data/input/distributionorder/>`_.
    
  | The distribution operation is available 24-by-7: it takes 48 hours, and is planned to
    last exactly 48 hours.

  | The manufacturing operation takes also 48 hours, but due to the working hours it lasts much longer. 
    The manufacturing ends right before the Christmas break starts at 24/12 17:00:00 and uses 8 hours 
    available time on the following days: 24/12, 23/12, 22/12, 19/12, 18/12 
    and 17/12. The replenishment thus starts on 17/12 08:00:00.

  .. image:: _images/calendar-working-hours-4.png
     :alt: Distribution orders

  .. image:: _images/calendar-working-hours-5.png
     :alt: Manufacturing orders
    