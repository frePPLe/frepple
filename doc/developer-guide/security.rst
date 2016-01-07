========
Security
========

.. important::

   If you find a security issue in the code, please report it with an
   email to info@frepple.com rather than publishing it on the user forum
   or filing a bug report.

All frePPLe code is developed with security in mind. When frePPLe is used
in a networked multi-user environment, security is very important.

Here are some notes and considerations on this topic:

* Consider using HTTPS for security of the web server.

* | FrePPLe can validate incoming XML data with an XML-schema.
  | Invalid data will be rejected and an error message is generated.
  | The XML Schema files frepple.xsd and frepple_core.xsd define the
    valid structures.
  | When integrating frePPLe with other systems it is strongly recommended
    to validate the incoming XML data against a small and well-controlled
    subset of the default XML-schema.

* | The python XML processing instruction allows execution of arbitrary
    python statements with the privilege of the user running the frePPLe
    executable.
  | While allowing a maximum of flexibility for configuring and customizing
    frePPLe, it also creates an open door to access your system. Access to
    this command should be restricted, and/or frePPLe should be run by a
    user account with limited privileges.

