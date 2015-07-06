==========
frepplectl
==========

.. note::

  Before 2.1 this command was called manage.py (manage.exe on windows)

This command has a long list of subcommands that allow different operations
on the user interface and the database.

Usage::

   frepplectl subcommand [options] [args]

Type ‘frepplectl.py help <subcommand>’ for help on a specific subcommand.

Some subcommands optionally expect application names as arguments. The frePPLe
user interface has the following applications: “input”, “output”, “execute”,
“common”, “auth”, “forecast” (Enterprise Edition only) and “quoting” (Enterprise
Edition only).

Commonly used subcommands are:

* | **dumpdata**:
  | Output the contents of the database as a fixture of the given format.

* | **frepple_copy**:
  | Creates a copy of a database schema into another database schema.

* | **frepple_flush**:
  | Deletes the data from the frePPLe database.

* | **frepple_import_openbravo**:
  | Execute the openbravo import connector, which downloads data from openbravo.

* | **frepple_export_openbravo**:
  | Execute the openbravo export connector, which uploads data to openbravo.

* | **frepple_run**:
  | Runs the frePPLe planning engine.
  | This subcommand is a wrapper around the frepple(.exe) executable.

* | **frepple_loadxml**:
  | Loads an XML file into the database.

* | **frepple_runserver**:
  | Runs a production web server for environments with very few users.
  | For a more scalable solution, deploying frePPLe on Apache with mod_wsgi is required.

* | **help**:
  | Display help on the available subcommands or a specific subcommands.

* | **loaddata**:
  | Installs a dataset in the format of a fixture in the database.

* | **runserver**:
  | Run a development web server. Do not use for actual production.

* | **syncdb**:
  | Obsolete from v3.0 onwards. Please use the migrate command instead.

* | **migrate**:
  | Update the database structure with the latest definitions.
  | This is used to generate the initial database schema.
  | From version 3.0 onwards it is also used to upgrade an existing
    frePPLe database from a previous release to the new release.

* | **frepple_backup**:
  | Backs up the content of the database to a file.

* | **frepple_restore**:
  | Restores the content of the database from a file.

* | **frepple_createbuckets**:
  | Initializes the date bucketization table in the database.

* | **frepple_createmodel**:
  | Generates a sample model in the database. Only useful during testing and demoing.

* | **test**:
  | Run the test suite

Less commonly used:

* **changepassword**
* **cleanup**
* **compilemessages**
* **createcachetable**
* **createsuperuser**
* **dbshell**
* **diffsettings**
* **flush**
* **inspectdb**
* **makemessages**
* **reset**
* **runfcgi**
* **shell**
* **sql**
* **sqlall**
* **sqlclear**
* **sqlcustom**
* **sqlflush**
* **sqlindexes**
* **sqlinitialdata**
* **sqlreset**
* **sqlsequencereset**
* **startapp**
* **testserver**
* **validate**

Options:

* | **-v VERBOSITY, –verbosity=VERBOSITY**:
  | Verbosity level: 0=minimal output, 1=normal output, 2=all output

* | **–settings=SETTINGS**:
  | The Python path to a settings module, normally leave to the default “freppledb.settings”

* | **–pythonpath=PYTHONPATH**:
  | A directory to add to the Python path, e.g. “/home/frepple/myproject”.

* | **–traceback**:
  | Print traceback on exception.

* | **–version**:
  | Show program’s version number and exit.

* | **-h, –help**:
  | Show a help message either showing all commands or help on a specific command.

More detailed information on the commands which frePPLe inherits from the Django
framework can be found at https://docs.djangoproject.com/en/dev/ref/django-admin/
