
This directory contains a sample web application for Frepple.
It is built using the incredible 'Django' web application framework.

The basic steps to set up a development environment:
- Install python
- Install django
- Install your database: postgresql / mysql / ado_mssql
  Alternatively, you can use the sqlite3 database included with python.
- Install the python database access library for the database (see django doc for details)
- Create a database schema for frepple
- Edit the file settings.py to point to your database schema
- Edit the file settings.py to point correctly to the template directory
- Test your installation by starting the development server:
      manage.py runserver
  and then pointing your browser to http://127.0.0.1:8000/admin
  A login page should come up. Don't proceed until this is achieved.
- Initialize the database schema:
      manage.py syncdb        <-- This step will also prompt you to create a django superuser.
  Verify the database tables are created correctly.
- Create an initial dataset by running the python commands:
      manage.py shell
      >> execfile('execute/create.py')
      >> create_model(10,20,5)
  This creates a model with 10 parallel clusters, 20 demands for each cluster, and a
  network structure of 5 levels deep.
- You can easily erase and recreate the model later on:
      manage.py shell
      >> execfile('execute/create.py')
      >> erase_model()
      >> create_model(1000,100,10)     <-- Pretty big model!!!

For more detailed information please look at the django documentation
on http://www.djangoproject.com
The tutorial is very good, and doesn't take too much time.
The frepple setup is very simple and doesn't use extensive customization of django at all.

To install a production environment django is deployed in an apache
web server using the mod_python module.
Below are some instructions / notes I took during configuration on my
Fedora Linux machine. I used fedora 5 with mysql database.
It doesn't serve as a complete reference but only as a brief guideline.
- Make sure mysql runs a transactional storage engine as default.
      vi /etc/my.cnf
      >> [mysqld]
      >> ...
      >> default_storage_engine=InnoDB
      >> ...
  Restart mysql after this step.
- Create the mysql user and database
      mysql -u root -p
      >> drop user frepple;
      >> drop database frepple;
      >> create database frepple;
      >> create user frepple identified by 'frepple';
      >> grant all privileges on frepple.* to 'frepple'@'%' identified by 'frepple';
- Mysqldb python module has a bug when dealing with decimal fields in the
  database. This has been fixed in the meantime in the latest releases.
  To work around the problem I updated the following django file:
      vi django/contrib/admin/templatetags/admin_list.py
      >> - result_repr = ('%%.%sf' % f.decimal_places) % field_val     <-- Original
      >> + result_repr = ('%%.%sf' % f.decimal_places) % float(field_val)  <-- Corrected
- Update the django contrib/admin/media/css/base.css stylesheet by commenting out the
  import of a null css sheet.
  It results is request to the web server for a non-existent sheet, giving 404 error.
- Update apache by adding a file /etc/httpd/conf.d/z_frepple.conf with the settings
  shown in the provided httpd.conf file. You will need to carefully review and update
  the settings!
- Update the apache configuration file /etc/httpd/conf/httpd.conf:
     - Run the web server as the same user used for the django development project
     - Switch keepalive on
     - Comment out some redundant modules
     - Choose the appropriate logging level and format
- Link the static django content into your web root directory.
     cd /var/www/html
     ln -s /usr/lib/python2.4/site-packages/django/contrib/admin/media .
Your mileage with the above may vary...

Enjoy!
