===========
Maintenance
===========

The commands on this page assume the service names and deployment directory
from :doc:`quick-start`. Run them from the directory containing ``compose.yml``
and ``.env``. For an external database, use your database administrator's
equivalent backup and restore procedures.

Routine administration
----------------------

.. code-block:: bash

   # Service status and recent application output
   docker compose ps
   docker compose logs --tail=100 frepple

   # Follow application output
   docker compose logs -f frepple

   # Run a management command against the running application
   docker compose exec frepple frepplectl help
   docker compose exec frepple frepplectl importfromfolder --database=default

   # Open a shell in the running container
   docker compose exec frepple /bin/bash

   # Stop and restart without removing containers or volumes
   docker compose stop
   docker compose start

See :doc:`../command-reference` for management commands and their arguments.
Many data-management tasks are also available from the execution screen.

Use ``docker compose exec -T`` instead of ``exec`` in unattended scripts.
Check the command's exit status and application task logs. Run imports and
planning jobs only when they won't conflict with scheduled jobs.

Monitoring
----------

Monitor more than container uptime:

* Check the login page through the public HTTPS endpoint.
* Inspect application, scheduler and nginx output with ``docker compose logs``.
* Check task failures, planning runtimes and scheduled job completion.
* Monitor CPU, memory, container restarts and host disk space.
* Monitor PostgreSQL connections, storage, slow queries and backup success.
* Check TLS certificate and Enterprise license expiration.
* Alert on failed backups, and periodically test a restoration.

The example Compose file rotates Docker's JSON logs. Task logs and other
application files in ``/var/log/frepple`` need their own retention policy.
That directory also contains interface files and attachments; don't treat
everything in it as disposable logging.

.. _maintenance-backup:

Back up the environment
-----------------------

A complete recovery requires:

* All model databases, including ``default`` and every scenario you need to
  retain, plus database role definitions and grants.
* ``/etc/frepple``, including deployment settings, nginx and supervisor
  configuration, startup hooks and the Enterprise license.
* ``/var/log/frepple``, including uploads, attachments, interface files and
  any database dumps you intend to retain.
* ``compose.yml``, protected environment/secrets, custom image sources,
  dependency pins and a record of the deployed image version or digest.
* Any custom Python packages or other persistent files maintained outside
  the image, including ``/usr/share/frepple/python_packages`` if used.

Choose backup frequency and retention from your acceptable data loss and
recovery time. A daily backup may suit some planning processes, but it is
not a universal guarantee. Encrypt backups, restrict access and store a copy
outside the Docker host. A volume on the same host is not a disaster-recovery
backup.

Example: a coordinated backup
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

For the bundled PostgreSQL service, the following example pauses the
application, dumps the three initial databases and copies the persistent
files. Block incoming traffic and let active tasks finish first. Stopping
the application also stops its scheduler.

Use a new backup directory for each run. Extend the database list for any
additional scenarios and adapt the names if you changed the prefix.

.. code-block:: bash

   mkdir -p backups
   mkdir -m 700 backups/pre-upgrade
   docker compose stop frepple

   docker compose exec -T postgres pg_dumpall -U frepple --roles-only \
     > backups/pre-upgrade/roles.sql
   docker compose exec -T postgres pg_dump -U frepple -Fc frepple0 \
     > backups/pre-upgrade/default.dump
   docker compose exec -T postgres pg_dump -U frepple -Fc frepple1 \
     > backups/pre-upgrade/scenario1.dump
   docker compose exec -T postgres pg_dump -U frepple -Fc frepple2 \
     > backups/pre-upgrade/scenario2.dump

   docker compose cp frepple:/etc/frepple backups/pre-upgrade/config
   docker compose cp frepple:/var/log/frepple backups/pre-upgrade/files
   docker compose cp frepple:/usr/share/frepple/python_packages backups/pre-upgrade/python_packages
   cp compose.yml .env backups/pre-upgrade/

   docker compose start frepple

Check each command for errors before proceeding. ``roles.sql`` and ``.env``
contain sensitive information. Record the image versions alongside these
files, inspect the dump inventories with ``pg_restore --list``, and copy the
backup to your protected external backup destination.

For an external database, use a PostgreSQL client compatible with the server.
Don't copy the live PostgreSQL data directory as a substitute for a consistent
database backup.

FrePPLe also provides a per-scenario backup command:

.. code-block:: bash

   docker compose exec frepple frepplectl backup --database=default

This writes a dump under ``/var/log/frepple``. Repeat it for each required
scenario. The command removes old dumps after about a month; copy dumps
elsewhere if you need longer retention. It does not replace a complete
environment backup.

.. _maintenance-restore:
.. _moveserver:

Restore or move to another server
---------------------------------

Test recovery on an isolated host or Compose project before depending on it.
Keep outbound integrations and scheduled jobs disabled during a test restore.

#. Install Docker and retrieve the exact frePPLe image version, custom image
   and PostgreSQL major version used for the backup.
#. Restore the Compose configuration and secrets. Create the required
   storage, but don't start the frePPLe application yet: its entrypoint
   creates and migrates databases automatically.
#. Start PostgreSQL only:

   .. code-block:: bash

      docker compose up -d postgres

#. Have the database administrator restore or recreate the database roles,
   passwords, memberships and ownership. Review ``roles.sql`` before using
   it: the target server may already have some roles, and managed services
   may restrict role restoration.
#. Create the target databases with the application role as owner, then
   restore every dump to the matching database. For example, on a fresh
   target using the bundled service:

   .. code-block:: bash

      docker compose exec -T postgres createdb -U frepple -O frepple -T template0 -E UTF8 frepple0
      docker compose exec -T postgres pg_restore -U frepple -d frepple0 \
        --exit-on-error < backups/pre-upgrade/default.dump

   Repeat for each scenario. If a target database already contains data,
   don't restore on top of it without an explicit replacement plan.
#. Create, but don't start, the application container:

   .. code-block:: bash

      docker compose create frepple
      docker compose cp backups/pre-upgrade/config/. frepple:/etc/frepple
      docker compose cp backups/pre-upgrade/files/. frepple:/var/log/frepple
      docker compose cp backups/pre-upgrade/python_packages/. frepple:/usr/share/frepple/python_packages

   Restore separately mounted licenses and custom files as well. Check that
   the container's ``frepple`` user can read and write the restored files.
#. Adjust database hostnames, public hostname, proxy settings and credentials
   for the new environment. Start the application and inspect initialization
   and migration output.
#. Verify login, all scenarios, attachments, reports, a planning run, custom
   applications and integrations. Confirm reporting-role permissions. Enable
   scheduled jobs and route users to the restored environment only after
   these checks pass.

.. warning::

   Restoring a database replaces its business data. The
   ``frepplectl restore`` command also drops and recreates its target
   database. Don't run a restore against a live environment without a
   maintenance window, a current backup and a verified target.

.. _maintenance-upgrade:

Upgrade frePPLe
---------------

#. Read the :doc:`../release-notes`, including required intermediate upgrades,
   dependency changes and custom-app compatibility.
#. Rehearse the upgrade against a restored copy of production. Measure
   migration time and verify all scenarios.
#. Schedule downtime, stop integrations and allow running tasks to finish.
   Make a complete backup as described above.
#. Pull the selected new image without starting the application. For example,
   after updating ``FREPPLE_VERSION`` in ``.env``:

   .. code-block:: bash

      docker compose pull frepple

   For a custom image, rebuild and test it against the new base release,
   then update the image tag in Compose.
#. Compare the new image's configuration with the persisted configuration.
   To extract the new defaults without running its entrypoint:

   .. code-block:: bash

      docker create --name frepple-upgrade-defaults \
        --entrypoint /bin/true ghcr.io/frepple/frepple-community:10.0.0
      docker cp frepple-upgrade-defaults:/etc/frepple ./new-release-config
      docker rm -v frepple-upgrade-defaults

   Substitute the actual target image and use an unused temporary container
   name and destination directory. Reapply your deliberate customizations
   to the new defaults. In particular, review ``djangosettings.py``,
   ``entrypoint.sh``, ``nginx.conf`` and ``supervisord.conf``.
   Preserve the deployment's secret keys and license. Never blindly keep
   the entire old configuration or replace it without reviewing local edits.
#. While the application is stopped, update the configuration volume and
   recreate the service:

   .. code-block:: bash

      docker compose up -d --no-deps frepple
      docker compose logs -f frepple

   The entrypoint runs migrations automatically. Review the output for
   errors for every active scenario, not just successful container startup.
#. Verify login, scenario access, reports, planning runs, APIs, custom apps
   and scheduled tasks. Then reopen access and resume integrations.

.. important::

   Switching back to an older container image does not undo database
   migrations. Recovery may require restoring both the pre-upgrade databases
   and files with the old image and configuration. Writes made after the
   backup will be lost on restore; decide the recovery point before reopening
   the application.

Upgrade PostgreSQL separately
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Don't change the PostgreSQL major-version tag and point it at an existing
data volume. Follow PostgreSQL's supported ``pg_upgrade`` or dump/restore
procedure, check the selected image's storage layout, and test role grants
and ownership. Keep the application upgrade and PostgreSQL major upgrade
as separate, recoverable operations.

Migrate a native installation to containers
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

#. Back up the old environment and record its frePPLe version, database
   names, scenario identifiers, settings, custom applications and license.
#. Test the migration separately. Where possible, first move to a container
   of the same version; otherwise follow the release's supported upgrade
   path.
#. Provision the container deployment without starting the application.
   Restore the main and scenario databases to the numbered names expected
   by ``POSTGRES_DB_PREFIX``. Map the old ``default`` to suffix ``0`` and
   the old scenarios to their corresponding numbered slots.
#. Restore attachments and interface files from ``/var/log/frepple``.
   Reapply configuration changes to the new image's defaults. Don't copy
   the old ``DATABASES`` dictionary or Apache configuration into the new
   nginx-based deployment.
#. Add custom code through a derived image, mount the Enterprise license
   if applicable, and verify database roles and grants.
#. Start the container in a maintenance window, inspect migrations and
   complete the same checks as a full restore. Ensure the old scheduler
   and integrations are stopped before activating their replacements.

.. _maintenance-storage:

Manage disk usage and quotas
----------------------------

FrePPLe's storage quota counts active scenario databases and application
files such as task logs, interface files, plan exports and database dumps.
It is not a host or Docker filesystem quota.

Set ``MAXSTORAGE`` in ``localsettings.py`` to a limit in MB, or ``None`` for
unlimited usage (the on-premise default). *Help / About frePPLe* shows usage
and the allocated quota.

When the quota is exceeded, file imports, scenario copies and import/export
folder tasks are blocked. To reclaim space:

* Release scenarios that are no longer required.
* Review forecasting horizons and archive retention.
* Remove business data no longer needed for planning, following your
  organization's retention requirements.
* Remove obsolete interface files, plan exports and database dumps after
  confirming they are no longer needed.

``MAXTOTALLOGFILESIZE`` limits total task-log storage in MB (default 200).
Older task logs are automatically removed when that limit is exceeded.
This doesn't limit database, Docker-log or attachment storage. Monitor free
disk space independently.

.. _maintenance-troubleshooting:

Troubleshooting
---------------

.. list-table::
   :header-rows: 1
   :widths: 30 70

   * - Symptom
     - Checks
   * - Image download denied
     - Check image name, tag and edition. Authenticate to ``ghcr.io`` with
       an account/token authorized to read that package.
   * - Database unavailable at startup
     - Check service health, ``POSTGRES_HOST``, port, DNS, firewall and
       ``pg_hba.conf``. ``localhost`` doesn't refer to another container.
       The entrypoint waits only a limited time for PostgreSQL.
   * - Password authentication failed
     - Confirm the actual database role password. Changing ``.env`` does
       not change a password in an initialized PostgreSQL volume.
   * - Database or reporting-role permission error
     - Check database ownership, database/role creation privileges and
       reporting-role grants. Inspect migration output for each scenario.
   * - Login page unavailable or gateway error
     - Check ``docker compose ps`` and logs for nginx, application-server,
       configuration and migration errors. Test the backend separately
       from the public reverse proxy.
   * - CSRF failure, incorrect redirects or insecure cookies
     - Review public hostname, trusted origins and the forwarded-protocol
       handling at both proxy layers; see :ref:`installation-https`.
   * - Plan editor can't connect
     - Check WebSocket support on proxies/firewalls and the scenario's
       planning web service; see :ref:`websocket`.
   * - Files or configuration aren't writable
     - Check volume mounts and ownership for the container's unprivileged
       ``frepple`` user. An empty bind mount can hide supplied configuration.
   * - Environment change has no effect
     - Recreate with ``docker compose up -d``. Check whether a Python
       setting or database parameter overrides the environment value.
   * - Upgrade still uses old configuration
     - Check persisted ``/etc/frepple`` contents against the target image.
       The image doesn't overwrite existing volume contents.

Before contacting support, record the image tag/digest, edition, Docker and
PostgreSQL versions, scenario, failing command or request, timestamps and
relevant logs. Remove credentials, tokens, licenses and business data before
sharing configuration or diagnostics.
