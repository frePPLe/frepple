================
Calendar buckets
================

A calendar represents a numeric value that is varying over time.

A calendar bucket represents a time period on a calendar during which a certain 
numeric value is effective.

See :doc:`calendars <calendars>` for more details.

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
