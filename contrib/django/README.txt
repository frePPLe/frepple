
This directory contains the frePPLe web application. 
It is built using the incredible Django web application framework.


The basic steps to set up a development environment:

- Install python 3.2 or higher.
  It is recommended to install the last release.

- Install Django 1.8.x
  Different versions of Django may or may not work with frePPLe...
  (The frePPLe user interface customizes some parts of the Django admin.
  The MultiDBModelAdmin class and the template overrides in the admin folder
  need to be in sync with the version of Django.)

- Some patches are required to Django. To apply the patches, use the commands below
  or merge the updates manually.
    cd [django directory]
    patch -l -p0 < [path to the patch file]/django.patch

- Install and configure the PostgreSQL database.
  For a quick test run, you can also use the SQLite3 database bundled with Python.

- If you're using a PostgreSQL database different from sqlite, you need to install
  install the psycopg2 database access library.

- Create a database schema for frePPle.
  For the Django tests, the user should have sufficient privileges to create a
  new database schema.

- Edit the file settings.py to point to your database schema.

- Initialize the database schema:
      frepplectl.py syncdb
  When the command prompts you to create a django superuser you can choose
  'no', since the inital dataset that is installed will include the users
  "admin", "frepple" and "guest".
  The password for these users is equal to the user name.
  Of course, you can always choose 'yes' and create your own superuser account.
  When the command finishes, verify the database tables are created correctly.

- Test your installation by starting the development web server:
      frepplectl.py runserver
  or the PyCherry web server:
      frepplectl.py frepple_runserver
  and then pointing your browser to http://127.0.0.1:8000/admin
  A login page should come up.
  Use frepple/frepple or admin/admin as the user name and password.

- The "execute" screen in the user interface allows you to erase the data,
  to load a dataset, to generate a random test model and run frePPLe.


For a production environment you should use an apache web server and
the following extra steps are required:

- Install the Apache web server
  
- Install the mod_wsgi module

- Install the Django web application as a Python module
  Either you run the install command in the root directory of the project:
     make install
  Alternatively install the Python module seperately by running this 
  command in the contrib/django directory:
     python setup.py install

- Collect the static files of the web application
     frepplectl.py collectstatic
  The static files are copied in a folder contrib/django/freppledb/static.
  Your web server will need to be configured to serve these static files 
  directly, ie without using the frepple web application.
  
- Edit the file httpd.conf you find in this folder.
  Change the directory name appropriately.
  
- Deploy the web application on apache
  Edit the httpd.conf of the apache server:
     - Assure all modules mentioned in the frepple httpd.conf file are loaded.
     - At the end add an include statement pointing to the frepple httpd.conf file.     

For more detailed information please look at the Django documentation
on http://www.djangoproject.com
The tutorial is very good, and doesn't take too much time.

Enjoy!
