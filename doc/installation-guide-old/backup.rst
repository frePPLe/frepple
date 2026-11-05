===========================
Backing up your environment
===========================

As any other system your frepple installation will need a backup process
to protect you against that one event-which-can-never-happen.

Here is the list of files you need to back up to be able to fully
restore an environment to its original state:

- The postgres database is the most important one to back up.

- The folder /etc/frepple contains the configuration files.

- The folder /var/log/frepple contains log files, data files,
  and attachment files.

- If you have tailored the apache configuration, you may also include
  the relevant files from the /etc/apache2 folder.

A daily backup of these files is sufficient. The retention policies for
the backup depend on your planning process and IT policies.
