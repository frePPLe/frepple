
This directory contains the frePPLe web application.
It is built using the incredible Django web application framework.


The basic steps to set up a development environment:

- Install python 3.2 or higher.
  It is recommended to install the last release.

- FrePPLe needs a patched version of django.
  The patch is maintained on github in this fork: https://github.com/frePPLe/django/
  Install the patched version of django from the branch that matches your frePPLe release.

  The shell commands for these steps are (replace 3.0 with the correct frePPLe version)
      wget https://github.com/frePPLe/django/archive/frepple_3.0.tar.gz
      tar xvfz frepple_3.0.tar.gz
      cd django-frepple_3.0
      python3 setup.py install

- Install and configure the PostgreSQL database.

- Install the psycopg2 package to access PostgreSQL databases from Python.

- Create a database for frePPle.
  For the Django tests, the user should have sufficient privileges to create a
  new database schema.

- Edit the file settings.py to point to your database schema.

- Initialize the database schema:
      frepplectl.py migrate
  When the command prompts you to create a django superuser you can choose
  'no', since the inital dataset that is installed will include the users
  "admin" with password "admin".
  Of course, you can always choose 'yes' and create your own superuser account.
  When the command finishes, verify the database tables are created correctly.

- Test your installation by starting the development web server:
      frepplectl.py runserver
  and then pointing your browser to http://127.0.0.1:8000/
  A login page should come up.
  Use admin/admin as the user name and password.

- The "execute" screen in the user interface allows you to erase the data,
  to load a dataset, to generate a random test model and run frePPLe.




For more detailed information please look at the Django documentation
on http://www.djangoproject.com
The tutorial is very good, and doesn't take too much time.

Enjoy!
