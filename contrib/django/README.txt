
This directory contains the frePPLe web application.
It is built using the incredible Django web application framework.


The basic steps to set up a development environment:

- Install python 3.5 or higher from https://www.python.org/downloads/

- Install and configure the PostgreSQL database.

- Install the psycopg2 package to access PostgreSQL databases from Python.

- Install the Python packages using the pip package manager.
    pip install -r requirements.txt

- Install nodes.js from https://nodejs.org/en/download/

- Install the javascript dependencies.
    npm install

- Create a database for frePPle.
  For the Django tests, the user should have sufficient privileges to create a
  new database schema.

- Edit the file djangosettings.py to point to your database schema.

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

Enjoy!
