============
Command line
============

The frepplectl utility allows a wide range of different operations
to be launched from the command line.

Usage::

   frepplectl subcommand [options] [args]

Type 'frepplectl.py help <subcommand>' for help on a specific subcommand.

The options will vary from command to command.
There are a number of common options: 

* | **--database=DATABASE**:
  | Specifies which scenario database to run the command for. When left unspecified
    the command will run on the production database.
  | The database names are defined in the djangosettings.py. Note that they can be
    different from the name of the database name configured in postgresql.

* | **-v VERBOSITY, --verbosity=VERBOSITY**:
  | Verbosity level: 0=minimal output, 1=normal output, 2=all output.

* | **-h, --help**:
  | Show a help message either showing all commands or help on a specific command.

The following commands are available.

* Planning workflows

  * :ref:`runplan`
  * :ref:`exportworkbook`
  * :ref:`importworkbook`
  * :ref:`exporttofolder`
  * :ref:`importfromfolder`
  * :ref:`runwebservice`
  * :ref:`scenario_copy`
  * :ref:`backup`
  * :ref:`empty`
  * :ref:`openbravo_import`
  * :ref:`openbravo_export`

* Administrator commands

  * :ref:`loaddata`
  * :ref:`createbuckets`
  * :ref:`migrate`
  * :ref:`restore`
  * :ref:`createsuperuser`
  * :ref:`changepassword`
  * :ref:`flush`
  * :ref:`loadxml`

* Developer commands

  * :ref:`shell`
  * :ref:`dbshell`
  * :ref:`runserver`
  * :ref:`runwebserver`
  * :ref:`test`
  * :ref:`dumpdata`
  * :ref:`createmodel`
  * :ref:`forecast_simulation`
  * :ref:`simulation`

A number of these commands are inherited from the excellent Django web application
framework used by frePPLe. More details on the commands can be found on 
https://docs.djangoproject.com/en/2.0/ref/django-admin/