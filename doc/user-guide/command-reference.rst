=================
Command reference
=================

FrePPLe provides a list of commands that perform actions on the 
database, the input data and/or the output data.

The commands can be accessed in three different ways:

* From the execution screen: :doc:`/user-guide/user-interface/execute`
* From the command line: :doc:`/integration-guide/batch-commands`
* Through a web-based API: :doc:`/integration-guide/remote-commands` 

This section provides an overview of the available actions:

* `Planning workflows`_

	* :ref:`runplan`
	* :ref:`exportworkbook`
	* :ref:`importworkbook`
	* :ref:`exporttofolder`
	* :ref:`importfromfolder`
	* :ref:`runwebservice`
	* :ref:`scenario_copy`
	* :ref:`backup`
	* :ref:`empty`

* `Administrator commands`_

	* :ref:`restore`
	* :ref:`loaddata`
	* :ref:`createbuckets`
	* :ref:`migrate`

* `Developer commands`_

	* :ref:`shell`
	* :ref:`dbshell`
	* :ref:`simulation`
	* :ref:`forecast_simulation`

The list can be extended with custom commands from an extension module.


Planning workflows
~~~~~~~~~~~~~~~~~~

.. _runplan:

Generate a plan
---------------

This option runs the frePPLe planning engine with the input data from the
database. The planning results are exported back into the database.

Two main plan types can be distinguished, based on whether you want to
see demand OR material, lead time and capacity problems to be shown.

* A **constrained plan** respects all enabled constraints. In case of shortages
  the demand is planned late or short. No any material or capacity shortages
  are present in the plan.

* An **unconstrained plan** shows material, capacity and operation problems
  that prevent the demand from being planned in time. The demand is always met
  completely and on time.

In both the constrained and unconstrained plans you can select which constraints
are considered during plan creation.

This command is available in the user interface, the command line and the web API:

* Execution screen:  
  
  .. image:: /user-guide/user-interface/_images/execution-plan.png
     :alt: Execution screen - Plan generation

* Command line::

    frepplectl runplan --constraints=15 --plantype=1 --env=fcst,invplan,balancing,supply
    
    Deprecated:
    frepplectl frepple_run --constraints=15 --plantype=1 --env=fcst,invplan,balancing,supply

* Web API::

    POST /execute/api/runplan/?constraint=15&plantype=1&env=fcst,invplan,balancing,supply
    
    Deprecated:
    POST /execute/api/frepple_run/?constraint=15&plantype=1&env=fcst,invplan,balancing,supply

.. _exportworkbook:

Export a spreadsheet
--------------------

This task allows you to download the complete model as a single spreadsheet
file. The spreadsheet can be opened with Excel or Open Office.

A separate sheet in the workbook is used for each selected entity.

The exported file can be imported back with the task described just below.

This command is available only in the user interface:

* Execution screen:
  
  .. image:: /user-guide/user-interface/_images/execution-export.png
     :alt: Execution screen - Spreadsheet export

.. _importworkbook:

Import a spreadsheet
--------------------

This task allows you to import an Excel spreadsheet.

A separate sheet in the workbook is used for each selected entity.

The sheet must have the right names - in English or your language. The first row
in each sheet must contain the column names.

This command is available only in the user interface:

* Execution screen:

  .. image:: /user-guide/user-interface/_images/execution-import.png
     :alt: Execution screen - Spreadsheet import

.. _exporttofolder:

Export plan result to folder
----------------------------

This task allows exporting data to a set of GZ-compressed CSV-formatted files.
The purpose of this task is to help the exchange of information with other systems.

The files are all placed in a folder UPLOADFILEFOLDER/export/, which can be configured
per scenario with the UPLOADFILEFOLDER value in the djangosettings.py file.
The log file exporttofolder.log records file exports, in addition to any data errors 
identified during their processing.

In this option you can see a list of files present in the specified folder, and download
each file by clicking on the arrow down button, or delete a file by clicking on the
red button.

.. image:: /user-guide/user-interface/_images/execution-exportplantofolder.png
   :alt: Execution screen - Export plan data to folder

.. _importfromfolder:

Import data files from folder
-----------------------------

This task allows importing data from a set of CSV-formatted files (eventually GZ-compressed).
The purpose of this task is to help the exchange of information with other systems.

The files are all placed in a folder that is configurable per scenario with the
UPLOADFILEFOLDER in the djangosettings.py configuration file. The log file importfromfolder.log records
all data imports, in addition to any data errors identified during their processing.

The data files to be imported must meet the following criteria:

* The name must match the data object they store: eg demand.csv, item.csv, ...

* The first line of the file should contain the field names.

* The file should be in CSV format, and may be compressed with GZ (eg demand.csv.gz).
  The delimiter depends on the default language (configured with LANGUAGE_CODE
  in djangosettings.py).
  For English-speaking countries it's a comma. For European countries
  it's a semicolon.

* The file should be encoded in UTF-8 (configurable with the CSV_CHARSET
  setting in djangosettings.py).

In this option you can see a list of files present in the specified folder, and download
each file by clicking on the arrow down button, or delete a file by clicking on the
red button.
The arrow up button will give the user the possibility of selecting multiple files
to upload to that folder.

This command is available in the user interface, the command line and the web API:

* Execution screen:  
  
  .. image:: /user-guide/user-interface/_images/execution-importfilesfromfolder.png
     :alt: Execution screen - Import data files from folder

* Command line::

    frepplectl importfromfolder
    
    Deprecated:
    frepplectl frepple_importfromfolder

* Web API::

    POST /execute/api/importfromfolder/
  
    Deprecated:
    POST /execute/api/frepple_importfromfolder/
  
.. _runwebservice:

Web service
-----------

In the Enterprise Edition users have the option to start and stop the web service
which keeps the plan in memory.

.. image:: /user-guide/user-interface/_images/execution-webservice.png
   :alt: Execution screen - Web service

.. _scenario_copy:

Scenario management
-------------------

This option allows a user to create copies of a dataset into a
what-if scenario.

When the data is successfully copied, the status changes from 'Free'
to 'In use'.

When the user doesn't need the what-if scenario any more, it can be released
again.

The label of a scenario, which is displayed in the dropdown list in the 
upper right hand corner, can also be updated here.

This command is available in the user interface, the command line and the web API:

* Execution screen:  
  
  .. image:: /user-guide/user-interface/_images/execution-scenarios.png
     :alt: Execution screen - what-if scenarios

* Command line::

    frepplectl scenario_copy db1 db2
    
    Deprecated:
    frepplectl frepple_copy db1 db2

* Web API::

    POST /execute/api/scenario_copy/?copy=1&source=db1&destination=db2&force=1
    
    Deprecated:
    POST /execute/api/frepple_copy/?copy=1&source=db1&destination=db2&force=1


.. _backup:

Back up database
----------------

This task dumps the contents of the current database schema to a flat file.

The file is created in the log folder configured in the configuration files
djangosettings.py.

This option is not active for cloud users. We automatically manage the
data backups for cloud users.

This command is available in the user interface, the command line and the web API:

* Execution screen:  

  .. image:: /user-guide/user-interface/_images/execution-backup.png
     :alt: Execution screen - backup

* Command line::

    frepplectl backup
    
    Deprecated:
    frepplectl frepple_backup

* Web API::
  
    POST /execute/api/backup/
   
    Deprecated:
    POST /execute/api/frepple_backup/
   
.. _empty:

Empty the database
------------------

This will delete all data from the current scenario (except for some internal
tables for users, permissions, task log, etc...).

This command is available in the user interface, the command line and the web API:

* Execution screen:

  .. image:: /user-guide/user-interface/_images/execution-erase.png
     :alt: Execution screen - erase

* Command line::

    frepplectl empty --models=input.demand,input.operationplan
    
    Deprecated:
    frepplectl frepple_flush --models=input.demand,input.operationplan

* Web API::

    POST /execute/api/frepple_flush/?models=input.demand,input.operationplan
  
    Deprecated:
    POST /execute/api/empty/?models=input.demand,input.operationplan


Administrator commands
~~~~~~~~~~~~~~~~~~~~~~    
     
.. _loaddata:

Load a dataset in the database
------------------------------

A number of demo datasets are packaged with frePPLe. Using this action you can
load one of those in the database.

The dataset is loaded incrementally in the database, **without** erasing any
previous data. In most cases you'll want to erase the data before loading any
of these datasets.

You can use the dumpdata command to export a model to the appropriate format
and create your own predefined datasets.

This command is available in the user interface, the command line and the web API:

* Execution screen:

  .. image:: /user-guide/user-interface/_images/execution-fixture.png
     :alt: Execution screen - load a dataset

* Command line::

    frepplectl loaddata manufacturing_demo

* Web API::

    POST /execute/api/loaddata/?fixture=manufacturing_demo
    
.. _createbuckets:

Generate time buckets
---------------------

A number of output reports are displaying the plan results aggregated into time
buckets. These time buckets are defined with the tables dates and bucket dates.
This tasks allows you to populate these tables in an easy way.

This command is available in the user interface, the command line and the web API:

* Execution screen:

  .. image:: /user-guide/user-interface/_images/execution-buckets.png
     :alt: Execution screen - generate time buckets
   
* Command line::

    frepplectl createbuckets --start=2012-01-01 --end=2020-01-01 --weekstart=1
    
    Deprecated:
    frepplectl frepple_createbuckets --start=2012-01-01 --end=2020-01-01 --weekstart=1

* Web API::
   
    POST /execute/api/createbuckets/?start=2012-01-01&end=2020-01-01&weekstart=1
    
    Deprecated:
    POST /execute/api/frepple_createbuckets/?start=2012-01-01&end=2020-01-01&weekstart=1


Developer commands
~~~~~~~~~~~~~~~~~~    
