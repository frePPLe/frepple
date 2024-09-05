This Dev-Container was developed in vscode so it uses a base image from microsoft that has some extra vscode stuff.

If you have no PostgresDB installed locally than you may do a "docker-compose up" and start a docker container with Postgres (also creates a freppledata local folder for persistency).
You should also create a "localsettings.py" file (in the project root folder) that will override the "djangosettings.py" file. Here you just need to override the IP address of the DB:
...
"HOST": os.environ.get("POSTGRES_HOST", "host machine IP"),
"PORT": os.environ.get("POSTGRES_PORT", "5432")
...
If the container has IP 172.17.0.2 then the host machine IP should be 172.17.0.1

If the container is "fresh" you must compile the frepple C++ code first.

If the DB is fresh you must run "frepplectl migrate" in the container to create the tables.

After these steps are done you should have a working frePPLe setup.