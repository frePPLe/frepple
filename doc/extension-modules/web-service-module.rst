==================
Web service module
==================

.. important::

   This module is only available in the Enterprise Edition.

This module implements a multi-threaded REST webservice server. Using the
web service frePPLe can make the plan information on-line accessible to other
systems and users, and also receive updated input data. FrePPLe can thus
integrate flexibly in a Service Oriented Architecture (SOA), sharing
information with other applications.

An overall overview is provided in the index page at the root level http\://<address>:<port>/.

* **Read data**

  HTTP GET-requests to the following URLs are used to read information from frePPLe:

  * | http\://<address>:<port>/:
    | Returns the complete model

  * | http\://<address>:<port>/buffer/:
    | Returns all buffers.

  * | http\://<address>:<port>/buffer/<name>/:
    | Returns the specific buffer.

  * | http\://<address>:<port>/calendar/:
    | Returns all calendars.

  * | http\://<address>:<port>/calendar/<name>/:
    | Returns the specific calendar.

  * | http\:/<address>:<port>/customer/:
    | Returns all customers.

  * | http\://<address>:<port>/customer/<name>/:
    | Returns the specific customer.

  * | http\://<address>:<port>/demand/:
    | Returns all demands.

  * | http\://<address>:<port>/demand/<name>/:
    | Returns the specific demand.

  * | http\://<address>:<port>/flow/:
    | Returns all flows.

  * | http\://<address>:<port>/item/:
    | Returns all items.

  * | http\://<address>:<port>/item/<name>/:
    | Returns the specific item.

  * | http\://<address>:<port>/load/:
    | Returns all loads.

  * | http\://<address>:<port>/location/:
    | Returns all locations.

  * | http\://<address>:<port>/location/<name>/:
    | Returns the specific location.

  * | http\://<address>:<port>/operation/:
    | Returns all operations.

  * | http\://<address>:<port>/operation/<name>/:
    | Returns the specific operation.

  * | http\://<address>:<port>/operationplan/:
    | Returns all operationplans.

  * | http\://<address>:<port>/operationplan/<id>/:
    | Returns the specific operationplan.

  * | http\://<address>:<port>/problem/:
    | Returns all problems.

  * | http\://<address>:<port>/resource/:
    | Returns all resources.

  * | http\://<address>:<port>/resource/<name>/:
    | Returns the specific resource.

* **Write data**

  | HTTP POST- and PUT-requests to the following URLs are used to write
    information to frePPLe.
  | Multiple fields can be specified as parameters to the URL.
  | The web service return the string “OK” or a description of the error(s)
    found.

  * | http\://<address>:<port>/:
    | Create or update entities in frePPLe from an uploaded XML file.
    | The XML-file must follow this XSD-schema: http\://<address>:<port>/frepple.xsd
      (which references also http\://<address>:<port>/frepple_core.xsd). You
      can also look at the XML output format of the GET requests to get examples.

  * | http\://<address>:<port>/buffer/<name>/?<field>=<value>:
    | Create or update a buffer.

  * | http\://<address>:<port>/calendar/<name>/?<field>=<value>:
    | Create or update a calendar.

  * | http\://<address>:<port>/customer/<name>/?<field>=<value>:
    | Create or update a customer.

  * | http\://<address>:<port>/demand/<name>/?<field>=<value>:
    | Create or update a demand.

  * | http\://<address>:<port>/item/<name>/?<field>=<value>:
    | Create or update a item.

  * | http\://<address>:<port>/location/<name>/?<field>=<value>:
    | Create or update a location.

  * | http\://<address>:<port>/operation/<name>/?<field>=<value>:
    | Create or update a operation.

  * | http\://<address>:<port>/operationplan/<id>/?<field>=<value>:
    | Create or update a operationplan.

  * | http\://<address>:<port>/resource/<name>/?<field>=<value>:
    | Create or update a resource.

* **Control actions**

  HTTP requests to the following URLs are used to control the service:

  * | http\://<address>:<port>/reload/:
    | Erase the current data from memory and reload the model again from
      the database.

  * | http\://<address>:<port>/replan/:
    | Erase the previous plan and generate a new one.

  * | http\://<address>:<port>/stop/:
    | Stop handling requests and shut down the planning service.

The web service is started by calling the Python function
freppledb.quoting.Server(database=’default’) in a commands.py file. The address
and port are configured with the parameter quoting.service_url and default to
localhost:8001.

Note that the module works with the frePPLe objects loaded in memory. Unless
configured accordingly, it does not persist any data in the database (with the
exception or order quotes). This is different from the screens in the frePPLe
user interface, which all display planning data stored in the database.

Access to the service is open and unauthenticated by default, and hence only
suitable for local connections or on a secure internal network. Plugins can
be developed to implement authentication and access restrictions, using the
CherryPy HTTP framework. Contact us for info or assistance.
