===========
Maintenance
===========

The commands on this page assume the service names and deployment directory
from :doc:`quick-start`. Run them from the directory containing ``compose.yml``
and ``.env``. For an external database, use your database administrator's
equivalent backup and restore procedures.

* :ref:`start-and-stop`
* :ref:`check-status`
* :ref:`container-shell`
* :ref:`backup`
* :ref:`upgrade`
* :ref:`upgrade-v10`
* :ref:`upgrade-postgresql`
* :ref:`contacting-support`

.. _start-and-stop:

Start and stop
--------------

Here are the commands to start and stop the application.

.. code-block:: bash

   # Stop without losing data
   docker compose stop

   # Restart without losing data
   docker compose start


.. _check-status:

Check status
------------

Wondering what the container is doing?

.. code-block:: bash

   # Service status and recent application output
   docker compose ps
   docker compose logs --tail=100 frepple

   # Follow application output
   docker compose logs -f frepple


.. _container-shell:

Running a command or shell in the container
-------------------------------------------

Occasionally you may need to run a command or open a shell in the running container.

.. code-block:: bash

   # Run a management command against the running application
   # Add the -T argument for non-interactive use in unattended scripts
   docker compose exec frepple frepplectl help
   docker compose exec frepple frepplectl importfromfolder --database=default

   # Open an interactive shell in the running container
   docker compose exec frepple /bin/bash


.. _maintenance-backup:

Back up the environment
-----------------------

Frepple stores data in several locations. You'll want a backup strategy that covers each of them.

* | The majority of the data is stored in the PostgreSQL databases.
  | It's recommended to set up a process for regular database backups.
* | The ``frepple_config /etc/frepple`` docker volume contains a number of configuration files,
    together with the license file.
  | It's a small amount of data, but critical to preserve and manage well.
* | The ``frepple_log /var/log/frepple`` docker volume contains log files of tasks, data files,
    attachments and interface files.
* | The ``frepple_data /usr/share/frepple/python_packages`` docker volume contains
    custom code.
  | Your development process hopefully has a strategy for managing this custom code.

Choose backup frequency and retention from your acceptable data loss and
recovery time. The database backup is the most important part of your backup strategy.

Here is an example of a coordinated backup. It is intended only as an illustration
and should be adapted to your specific environment and requirements.

.. code-block:: bash

   backup_dir="backup-$(date +%Y-%m-%d_%H-%M-%S)"
   mkdir -m 700 "$backup_dir"

   # Backing up PostgreSQL databases
   docker compose exec -T postgres pg_dump -U frepple -Fc frepple0 \
     > "$backup_dir/default.dump"
   docker compose exec -T postgres pg_dump -U frepple -Fc frepple1 \
     > "$backup_dir/scenario1.dump"
   docker compose exec -T postgres pg_dump -U frepple -Fc frepple2 \
     > "$backup_dir/scenario2.dump"

   # Backing up configuration, logs, and custom code from the frepple container
   docker compose cp frepple:/etc/frepple "$backup_dir/config"
   docker compose cp frepple:/var/log/frepple "$backup_dir/logs"
   docker compose cp frepple:/usr/share/frepple/python_packages "$backup_dir/python_packages"


.. _upgrade:

Upgrade frePPLe
---------------

Frepple release are smooth and easy to apply. You have no excuse not to upgrade
frequently to benefit from the latest features and fixes.

Important: Frepple upgrades are roll-forward only. You can upgrade to a newer
release, you cannot easily revert to a previous release. In the unfortunate event you
need to go back, please seek assistance from the frepple support team.

#. Read the :doc:`../release-notes`, including required intermediate upgrades

#. Backup the environment as shown above.

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

   The entrypoint automatically will upgrade the database schema to the new
   release. Review the output for errors.

#. The migration will finish in less than a minute.


.. _upgrade-v10:

Upgrade to frepple 10
~~~~~~~~~~~~~~~~~~~~~

With frepple 10, the upgrade process is slightly different from other upgrades.
That's becasue the configuration files have been reorganized, and your setup needs to be upgraded.

Here is the recommended procedure to upgrade to frepple 10:

#. Create a backup your back of your database and the folders /etc/frepple and /var/log/frepple.

#. Extract the default configuration files of the v10 release.

   .. code-block:: bash

   mkdir -p ./frepple-defaults
   docker run --rm frepple-community:10.0.0 tar -cf - -C /etc/frepple . | tar -xf - -C ./frepple-defaults

#. The files in ``./frepple-defaults`` now contain the default configuration for frepple 10.
   The files nginx.conf, entrypoint.sh and supervisord.conf you can very likely copy straight into your
   old configuration volume. Most implementation never needed to modify these files.

#. The file djangosettings.py on the other hand needs to migrated. You'll start from the new default
   content of the file and bring your modifications across from your old configuration.

   In particular the following settings should be carefully reviewed and merged:

   -  TODO

#. With all configuration files now updated to the new format, the upgrade process
   can proceed as usual. Restart the frepple container, and it will automatically upgrade
   the database schema.

#. If you're stuck or feel unsure about the upgrade process, reach out to the frepple team for assistance.


.. _upgrade-postgresql:

Upgrade PostgreSQL
~~~~~~~~~~~~~~~~~~

Frepple supports multiple PostgreSQL versions. This means you can upgrade each completely independently.

Follow PostgreSQL's supported ``pg_upgrade`` or dump/restore procedure to upgrade your
PostgreSQL server without losing any data.

Don't forget to retune your PostgreSQL configuration after the upgrade with
`PGTune <https://pgtune.leopard.in.ua/>`_.


.. _contacting-support:

Contacting frepple support
--------------------------

If you want to send a dataset to the frepple team for support or debugging, you can generate and
download a database dump with the data. See :ref:`contacting support <contacting_support>`.
