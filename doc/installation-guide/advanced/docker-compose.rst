==============================
Deployment with docker compose
==============================

Here is a sample docker-compose file that defines 2 containers: 1) a postgres container
to run the database and 2) a frepple web application server.

You access the application with your browser on the URL http://localhost:9000/

The frepple log and configuration files are put in volumes (which allows to reuse
them between different releases of the frepple image).

Note that the postgres database container comes with default settings. For production
use you should update the configuration with the pgtune recommendations from
https://pgtune.leopard.in.ua/ (use "data warehouse" as application type and also assure
the max_connections setting is moved from the default 100 to eg 400).

.. code-block:: none

  services:

    frepple:
      image: "ghcr.io/frepple/frepple-community:latest"
      container_name: frepple-community-webserver
      ports:
        - 9000:80
      depends_on:
        - frepple-community-postgres
      networks:
        - backend
      volumes:
        - log-apache-community:/var/log/apache2
        - log-frepple-community:/var/log/frepple
        - config-frepple-community:/etc/frepple
      environment:
        POSTGRES_HOST: "frepple-community-postgres"
        POSTGRES_PORT: 5432
        POSTGRES_USER: "frepple"
        POSTGRES_PASSWORD: "frepple"
        FREPPLE_DATE_STYLE: "year-month-day"
        FREPPLE_DATE_STYLE_WITH_HOURS: "false"
        FREPPLE_TIME_ZONE: "UTC"
        FREPPLE_THEMES: "earth grass lemon odoo openbravo orange snow strawberry water"
        FREPPLE_DEFAULT_THEME: "earth"
        FREPPLE_EMAIL_USE_TLS: "true"
        FREPPLE_DEFAULT_FROM_EMAIL: "your_email@domain.com"
        FREPPLE_SERVER_EMAIL: "your_email@domain.com"
        FREPPLE_EMAIL_HOST_USER: "your_email@domain.com"
        FREPPLE_EMAIL_HOST_PASSWORD: "frePPLeIsTheBest"
        FREPPLE_EMAIL_HOST: ""
        FREPPLE_EMAIL_PORT: 25
        FREPPLE_CONTENT_SECURITY_POLICY: "frame-ancestors 'self'"
        FREPPLE_X_FRAME_OPTIONS: "SAMEORIGIN"
        FREPPLE_CSRF_TRUSTED_ORIGINS: ""
        FREPPLE_SECURE_PROXY_SSL_HEADER: ""
        FREPPLE_SESSION_COOKIE_SECURE: "false"
        FREPPLE_CSRF_COOKIE_SAMESITE: "lax"
        FREPPLE_FTP_PROTOCOL: "SFTP"
        FREPPLE_FTP_HOST: ""
        FREPPLE_FTP_PORT: 22
        FREPPLE_FTP_USER: ""
        FREPPLE_FTP_PASSWORD: ""

    frepple-community-postgres:
      image: "postgres:16"
      container_name: frepple-community-postgres
      networks:
        - backend
      environment:
        POSTGRES_PASSWORD: frepple
        POSTGRES_DB: frepple
        POSTGRES_USER: frepple
        POSTGRES_DBNAME: frepple

  volumes:
    log-apache-community:
    log-frepple-community:
    config-frepple-community:

  networks:
    backend: