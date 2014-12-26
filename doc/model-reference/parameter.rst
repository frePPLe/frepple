=========
Parameter
=========

Global settings and parameters are stored in a specific table.

Some of these parameters are used by the planning algorithm, others are used
by the web application. Extension modules also add additional configuration
parameters to this table.

**Fields**

================ ================= ===========================================================
Field            Type              Description
================ ================= ===========================================================
name             string            Unique name of the parameter.
value            string            Value of the parameter.
description      string            Description of the parameter.
================ ================= ===========================================================

Standard parameters

The table below shows the parameters that are recognized by the standard
application. Look at the documentation of extension modules to see which
additional parameters they introduce.

=================== =============================================================
Parameter           Description
=================== =============================================================
currentdate         | Current date of the plan, formatted as YYYY-MM-DD HH:MM:SS
                    | If the parameter is missing or empty the system time is
                      used as current date.
plan.loglevel       | Controls the verbosity of the planning log file.
                    | Accepted values are 0 (silent – default), 1 (minimal) and
                      2 (verbose).
loading_time_units  | Time units to be used for the resource report.
                    | Accepted values are: hours, days, weeks.
=================== =============================================================

**Example XML structures**

Note that not all parameters can be defined in an XML file. The parameter
table is nothing but a generic place to store various configuration settings.

Global initialization section

.. code-block:: XML

   <plan>
     <name>Demo model</name>
     <description>A demo model demonstrating frePPLe</description>
     <current>2013-01-01T00:00:00</current>
     <logfile>frepple.log</logfile>
   </plan>

**Example Python code**

Note that not all parameters can be defined in Python code. The parameter
table is nothing but a generic place to store various configuration settings.

Global initialization section

::

    frepple.settings.name = "Plan name"
    frepple.settings.description = "Plan description"
    frepple.settings.current = datetime.datetime(2013,1,1)
    frepple.settings.logfile = "frepple.log"
