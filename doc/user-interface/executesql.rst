====================
SQL execution screen
====================

.. Important::

   The SQL queries are run in a database role that is configurable with the setting
   DATABASES / SQL_ROLE. By default this role has only read permissions
   to a subset of the database tables.
   
   Database administrators can grant additional permissions, if required.
   
This screen allows you to run SQL statements on the frePPLe database.

.. image:: _images/executesql.png
   :alt: SQL execution screen

The menu is shown when all the following conditions are met:

- The executesql app is activated in INSTALLED_APPS section of 
  the djangosettings.py file.
  
- You have superuser privileges.
