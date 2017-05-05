===============
Remote commands
===============

All operations from the execution screen can also be launched and
monitored remotely through an web service API.

Example usage with curl::

   Run a task on the default database:
   curl -u <user>:<password> http(s)://<server>:<port>/execute/api/<command>/ 
      --data "<argument1>=<value1>&<argument2>=<value2>"
   
   Run a task on a scenario database:
   curl -u <user>:<password> http(s)://<server>:<port>/<scenario>/execute/api/<command>/ 
     --data "<argument1>=<value1>&<argument2>=<value2>"

The following URLS are available.

* | **GET /execute/api/status/**
  | **GET /execute/api/status/?id=<taskid>**:
  | Returns the list of all running and pending tasks. The second format
    returns the details of a specific task.

* | **POST /execute/api/frepple_run/?constraint=15&plantype=1&env=supply** 
  | Generates a plan.

* | **POST /execute/api/frepple_flush/?models=input.demand,input.operationplan** 
  | Returns the list of all running and pending tasks. The second format
    returns the details of a specific task.

* | **POST /execute/api/frepple_importfromfolder/**
  | Load CSV-formatted data files from a configured data folder into the
    frePPLe database.

* | **POST /execute/api/frepple_exporttofolder/**
  | Dump planning results in CSV-formatted data files into a configured
    data folder on the frePPLe server.

* | **POST /execute/api/loaddata/?fixture=demo**
  | Loads a predefined dataset.
  
* | **POST /execute/api/frepple_copy/?copy=1&source=db1&destination=db2&force=1**
  | Creates a copy of a database into a scenario.

* | **POST /execute/api/frepple_backup/**
  | Backs up the content of the database to a file (which stays on the
    frePPLe application server).

* | **POST /execute/api/openbravo_import/?delta=7**
  | Execute the Openbravo import connector, which downloads data from Openbravo.
  
* | **POST /execute/api/openbravo_export/?filter=1**
  | Execute the Openbravo export connector, which uploads data to Openbravo.
  
* | **POST /execute/api/odoo_import/**
  | Execute the Odoo import connector, which downloads data from Odoo.

* | **POST /execute/api/frepple_createbuckets/?start=2012-01-01&end=2020-01-01&weekstart=1**
  | Initializes the date bucketization table in the database.
  
All these APIs return a JSON object and they are synchronous, i.e. they 
don't wait for the actual command to finish. In case you need to wait
for a task to finish, you will need to use a loop which periodically
polls the /execute/api/status URL to monitor the status.

For security reasons we strongly recommend the use of a HTTPS
configuration of the frePPLe server when using this API.
