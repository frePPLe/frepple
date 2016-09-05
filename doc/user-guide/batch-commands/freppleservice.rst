==================
freppleservice.exe
==================

This executable is available only on Windows. It allows controlling a Windows
service that runs the frePPLe web server for the user interface (and optionally
the included PostgreSQL database).

The Windows event log provides information on starts and stops events of the
service.

.. image:: ../../installation-guide/_images/winservice.png

Usage:

* | **freppleservice --install name**
  | Register the new service. After this step, you’ll be able to see the
    service in the Service Manager.
  | The last argument is an extra name given to the service name.

* | **freppleservice --uninstall name**
  | Remove the service.
  | After it’s stopped, the service will be removed from the list shown in
    Service Manager.
  | The last argument is an extra name given to the service name.
