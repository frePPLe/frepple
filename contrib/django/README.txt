
This directory contains a sample web application for Frepple.
It is built using the incredible 'Django' web application framework.

The basic steps to set up this environment:
- Install python
- Install django
- Test your installation by starting the development server:
      manage.py runserver
  and then pointing your browser to http://127.0.0.1:8000/
  A welcome page should come up...
- Install your database: postgresql / mysql / sqlite3 / ado_mssql / (oracle)
- Install the python database access library for the database (see django doc for details)
- Create a database schema for frepple
- Edit the file settings.py to point to your database schema
- Edit the file settings.py to point correctly to the template directory
- Initialize the database schema:
      manage.py syncdb        <-- This step will also prompt you to create a django superuser.
      manage.py reset input
      manage.py reset output
      manage.py reset execute
  Verify the database tables are created correctly.
- Create an initial dataset by running the python commands:
      manage.py shell
      >> execfile('execute/create.py')
      >> create_model(10,20,5)
  This creates a model with 10 parallel clusters, 20 demands for each cluster, and a 
  network structure of 5 levels deep.
  You can easily erase and recreate the model:
      manage.py shell
      >> execfile('execute/create.py')
      >> erase_model()
      >> create_model(1000,100,10)     <-- Pretty big model!!!

For more detailed information please look at the django documentation 
on http://www.djangoproject.com  
The tutorial is very good, and doesn't take too much time.
The frepple setup is very simple and doesn't use extensive customization of django at all.

Enjoy!
