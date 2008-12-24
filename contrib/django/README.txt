
This directory contains a sample web application for frePPLe.
It is built using the incredible Django web application framework.

The basic steps to set up a development environment:

- Install python 2.5
  Lower versions may work, but are not tested...

- Install django
  FREPPLE NEEDS THE VERSION 1.0.2 OF DJANGO.
  Later versions of django may or may not work with frePPLe...

- Some patches are required to django. To apply the patches, use the commands below
  or merge the updates manually.
    cd [django directory]
    patch -l -p0 < [path to the patch file]/django.patch

- Install your database: postgresql / mysql / oracle.
  For a quick test run, you can also use the sqlite3 database bundled with Python.

- If you're using a database different from sqlite, install the python database
  access library for the database (see the django documentation for details).
    - cx_oracle for Oracle
    - psycopg2 for PostgreSQL
    - MySQL-python for MySQL

- Create a database schema for frePPle.
  For the django tests, the user should have sufficient privileges to create a
  new database schema.

- Edit the file settings.py to point to your database schema.

- Initialize the database schema:
      manage.py syncdb
  When the command prompts you to create a django superuser you can choose
  'no', since the inital dataset that is installed will include the users
  "admin", "frepple" and "guest".
  The password for these users is equal to the user name.
  Of course, you can always choose 'yes' and create your own superuser account.
  When the command finishes, verify the database tables are created correctly.

- Test your installation by starting the development server:
      manage.py runserver
  and then pointing your browser to http://127.0.0.1:8000/admin
  A login page should come up.

- The "execute" screen in the user interface allows you to erase the data,
  to load a dataset, to generate a random test model and run frePPLe.

For more detailed information please look at the django documentation
on http://www.djangoproject.com
The tutorial is very good, and doesn't take too much time.

Documentation of the code can be generated with the epydoc package:
- Install epydoc (version >3.0 recommended)
- Run the 'doc' make target:
    make doc
- Point your browser to the file doc/index.html

Enjoy!
