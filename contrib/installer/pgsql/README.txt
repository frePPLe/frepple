
In this folder you find the binary distribution of PostgreSQL 9.5.2 as
obtained from:
  http://www.enterprisedb.com/products-services-training/pgbindownload
We redistribute this product unmodified and in its entirity.

Initialising a database with the provided binaries is easy.
The frePPLe installer runs the following steps for you, but you're 
always free to redo the initialisation to meet your needs:
  initdb --pgdata YOUR_DATA_FOLDER --encoding UTF8
  pg_ctl --pgdata YOUR_DATA_FOLDER --log YOUR_LOG_FILE -w start
  createdb -w -p YOUR_DATABASE_PORT YOUR_DATABASE_NAME

The database server set up by the frePPLe installer has the following
settings:
  - runs port 8002
  - accepts only local connections, and trusts all of them
  - runs with default memory and performance parameters
You can tune these parameters to fit your needs. For performance
tuning the pgtune site http://pgtune.leopard.in.ua/ provides very
useful input.
  
If you want to install PostgreSQL yourself we recommended to use the
installer found at:
  http://www.enterprisedb.com/products-services-training/pgdownload#windows
instead of using the zipped binaries bundled with frePPLe.
