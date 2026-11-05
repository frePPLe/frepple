==============================================
PostgreSQL database creation and configuration
==============================================

FrePPLe assumes that the database uses UTF-8 encoding.

FrePPLe needs the following settings for its database connections. If these
values are configured as default for the database (in the file postgresql.conf)
or the database role (using the 'alter role' command), a small performance
optimization is achieved:
::

    client_encoding: 'UTF8',
    default_transaction_isolation: 'read committed',
    timezone: 'Europe/Brussels'  # Value of TIME_ZONE in your djangosettings.py file

FrePPLe can communicate with the PostgreSQL server using either a) Unix
domain sockets ('local' in pg_hba.conf) or b) TCP IP4 or IP6 sockets.

FrePPLe can authenticate on the PostgreSQL database using either a) a
password ('md5' in pg_hba.conf) or b) OS username ('peer' and 'ident'
in pg_hba.conf).

In case of error (while creating the databases) "Postgres PG::Error: ERROR: new encoding (UTF8) is incompatible":
::

    UPDATE pg_database SET datistemplate = FALSE WHERE datname = 'template1';
    DROP DATABASE template1;
    CREATE DATABASE template1 WITH TEMPLATE = template0 ENCODING = 'UNICODE';
    UPDATE pg_database SET datistemplate = TRUE WHERE datname = 'template1';
    \c template1
    VACUUM FREEZE;

#. **Tune the database**

   The default installation of PostgreSQL is not configured right for
   scalable production use.

   We advice using pgtune http://pgtune.leopard.in.ua/ to optimize the configuration
   for your hardware. Use "data warehouse" as application type and also assure the
   max_connection setting is moved from the default 100 to eg 400.

#. **Create the database and database user**

   A database needs to be created for the default database, and one for each of
   the what-if scenarios you want to configure.

   The same user can be used as the owner of these databases. Make sure to grant the
   createrole permissions to the database user.

   The typical SQL statements are shown below. Replace USR, PWD, DB with the suitable
   values.
   ::

       create user USR with password 'PWD' createrole;
       create database DB0 encoding 'utf-8' owner USR;
       create database DB1 encoding 'utf-8' owner USR;
       create database DB2 encoding 'utf-8' owner USR;
       create database DB3 encoding 'utf-8' owner USR;

    To simplify the default instalation settings USR, pwd and DB are all frepple.
