============
Command line
============

The frepplectl utility allows a wide range of different operations
to be launched from the command line.

Usage::

   frepplectl subcommand [options] [args]

Type 'frepplectl.py help <subcommand>' for help on a specific subcommand.

Commonly used subcommands are:

* | **runplan** (formerly called frepple_run):
  | Run the solver algorithm to generate a plan.

* | **migrate**:
  | Update the database structure with the latest definitions.
  | This is used to generate the initial database schema.

* | **scenario_copy** (formerly called frepple_copy):
  | Creates a copy of a database into a scenario.

* | **backup** (formerly called frepple_backup):
  | Backs up the content of the database to a file.

* | **restore** (formerly called frepple_restore):
  | Restores the content of the database from a file.

* | **dumpdata**:
  | Output the contents of the database as a fixture of the given format.

* | **empty** (formerly called frepple_flush):
  | Deletes the data from the frePPLe database.

* | **importfromfolder** (formerly called frepple_importfromfolder):
  | Load CSV-formatted data files from a configured data folder into the
    frePPLe database.

* | **exporttofolder** (formerly called frepple_exporttofolder):
  | Dump planning results in CSV-formatted data files into a configured
    data folder.

* | **forecastsimulation** (formerly called frepple_forecastsimulation):
  | Estimates the forecast accuracy over the recent history by turning back the clock.

* | **simulation** (formerly called frepple_simulation):
  | Simulates the execution of the plan. Used for research purposes on
    plan stability and robustness in case of disturbances.

* | **openbravo_import**:
  | Execute the openbravo import connector, which downloads data from openbravo.

* | **openbravo_export**:
  | Execute the openbravo export connector, which uploads data to openbravo.

* | **loadxml** (formerly called frepple_loadxml):
  | Loads an XML file into the database.

* | **runwebserver** (formerly called frepple_runserver):
  | Runs a production web server for environments with very few users.
  | For a more scalable solution, deploying frePPLe on Apache with mod_wsgi is required.

* | **help**:
  | Display help on the available subcommands or a specific subcommands.

* | **loaddata**:
  | Installs a dataset in the format of a fixture in the database.

* | **runserver**:
  | Run a development web server. Do not use for actual production.

* | **createbuckets** (formerly called frepple_createbuckets):
  | Initializes the date bucketization table in the database.

* | **createmodel** (formerly called frepple_createmodel):
  | Generates a sample model in the database. Only useful during testing and demoing.

* | **test**:
  | Run the test suite

* | **createsuperuser**:
  | Create a new superuser.

* | **dbshell**:
  | Run an interactive SQL session on the PostgreSQL database.

* | **shell**:
  | Run an interactive Python interpreter session.

Less commonly used:

* **changepassword**
* **cleanup**
* **compilemessages**
* **dbshell**
* **diffsettings**
* **flush**
* **inspectdb**
* **makemessages**
* **reset**
* **sql**
* **sqlall**
* **sqlclear**
* **sqlcustom**
* **sqlflush**
* **sqlindexes**
* **sqlinitialdata**
* **sqlreset**
* **sqlsequencereset**
* **validate**

Options:

* | **--database=DATABASE**:
  | Specifies which database to run the command for. The database names are defined in the
    djangosettings.py.

* | **-v VERBOSITY, --verbosity=VERBOSITY**:
  | Verbosity level: 0=minimal output, 1=normal output, 2=all output.

* | **--settings=SETTINGS**:
  | The Python path to a settings module, normally leave to the default "freppledb.settings".

* | **--pythonpath=PYTHONPATH**:
  | A directory to add to the Python path, e.g. "/home/frepple/myproject".

* | **--traceback**:
  | Print traceback on exception.

* | **--version**:
  | Show program's version number and exit.

* | **-h, --help**:
  | Show a help message either showing all commands or help on a specific command.

More detailed information on the commands which frePPLe inherits from the Django
framework can be found at https://docs.djangoproject.com/en/dev/ref/django-admin/
