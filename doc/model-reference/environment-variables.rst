=====================
Environment variables
=====================

A number of environment variables influence frePPLe.

=================== ===============================================================
Variable            Description
=================== ===============================================================
FREPPLE_HOME        FrePPLe read some initialization and configuration files during
                    the execution of the program:

                    * The file frepple.xsd points to the xsd schema for the
                      frePPLe XML files. This xsd file typically references
                      additional xsd files located in the same directory.

                    * If present, the XML data in the file init.xml are processed
                      automatically when frePPLe is started. This is the recommended
                      place to load any standard data entities your application may
                      need.

                    * If present, the Python code in the file init.py is executed
                      automatically when frePPLe is started. This is the recommended
                      place to define any Python functions or classes your
                      application may need. FrePPLe extension modules are also
                      typcially loaded in this file.

                    * Plugin module libraries.

                    FrePPLe searches the following directories in sequence to
                    locate these files.

                    * The current directory.

                    * The directory pointed to by the FREPPLE_HOME environment
                      variable.

                    * On Linux: the /etc/frepple directory where the default
                      configuration files are installed.

                    * On Linux: The library /usr/lib/frepple directory where the
                      default module libraries are installed.

                    * For the loading module libraries frePPLe also searches the
                      standard path for location shared libraries. Configuring this
                      is platform dependent.

                    By setting the FREPPLE_HOME environment variable you can control
                    the directories where the application looks for your application
                    files.

TZ                  FrePPLe uses the C-library functions for date and time
                    manipulations.

                    These functions are respecting time zones and
                    daylight saving time, which can give sometimes give unexpected
                    results: twice a year you’ll find a day with 25 or 23 hours.

                    To disable any effects of daylight saving time, change the TZ
                    variable to a time zone without daylight saving time, e.g. ‘EST’.
=================== ===============================================================
