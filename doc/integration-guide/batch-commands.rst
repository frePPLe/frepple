============
Command line
============

:doc:`/command-reference` from the execution screen can also be launched from
the command line with the frepplectl utility.

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

A number of these commands are inherited from the excellent Django web application
framework used by frePPLe. More details on the commands can be found on
https://docs.djangoproject.com/en/3.2/ref/django-admin/