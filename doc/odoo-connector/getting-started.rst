===============
Getting started
===============

- **STEP 1:Installation of the connector addon in Odoo**

  | The connector can be downloaded from the `Odoo apps store <https://apps.odoo.com/apps/modules/19.0/frepple>`_.
    or its `GitHub repository <https://github.com/frepple/odoo>`_.  Only the install the freppe app from this
    repository, the other apps are for testing and development purposes only.

  | Make sure to install the branch corresponding to your Odoo version.

- **STEP 2: Choose how you will run frepple**

  .. image:: _images/options_to_run_frepple.png
    :alt: Options to run frepple.

  We have 3 options to install and configure frepple. In increasing order of complexity, these are:

  #. **Don't install frepple, but use the frepple cloud service.**

     This is the easiest way to get started. After installing the addon, you can immediately send
     your odoo data to the frepple cloud service. The service sends the key actions in your plan
     back to your odoo instance.

     This setup is recommended for a trial, and for companies with simple planning needs.
     The main limitation of this setup is that you don't have the frepple user interface to review
     and analyze the planning results.

     This option is plug-and-plan, and gets you up and running in minutes.

  #. **Use a frepple instance on the frepple cloud.**

     You can register for a 15-day free trial on the `frepple cloud <https://cloud.frepple.com>`_ and
     connect your Odoo instance to it.

     In this option you have access to the frepple user interface with all its features, without
     having to install and configure frepple.

     This setup is recommended for trials. Many companies continue to use the frepple cloud after
     a successful trial since it removes the learning curve and maintenance overhead of a local installation.

  #. **Install and configure your own frepple instance.**

     For techy die-hards or companies with strict security policies, there is the option to install
     a frepple instance on your own servers.

- **STEP 3: Follow the instructions for your chosen option**

- **Option 1: Using the frepple APS cloud service**

  - After installing the connector addon in Odoo, you can immediately send your odoo data to the frepple
    cloud service.
    Use the "generate recommendations" button in the Odoo interface to send your data to the
    frepple cloud service.

    .. image:: _images/odoo-menu-bar.png
      :alt: Frepple in the odoo menu bar.

  - Collecting all odoo data, sending them to the frepple cloud service, and letting frepple process the data
    can take 5 to 10 minutes.
    Once it's finished you get a set of actions to take in odoo.

    .. image:: _images/recommendations.png
      :alt: Frepple recommended actions in Odoo.

    You can directly take actions on these recommendations:

      - Draft a new purchase order
      - Draft a new manufacturing order
      - Reschedule an existing manufacturing order

- **Option 2: Using the frepple cloud with a trial account**

  - Register for a 15-day free trial on the `frepple cloud <https://cloud.frepple.com>`_.
    It takes only a minute to fill out the form and wait for the confirmation email that your
    environment is ready.

  - Next, login to your frepple instance. And use the "connect to Odoo" button
    on the home screen to link your odoo and frepple instances.

- **Option 3: Installing frePPLe on your own infrastructure**

    - You will need knowledge of Linux, Docker and PostgreSQL to complete the installation.

    - Follow the instructions in the `frepple installation guide <https://docs.frepple.com/installation/>`_ to
      install and configure your own frepple instance.

    - Next, login to your frepple instance. And use the "connect to Odoo" button
      on the home screen to link your odoo and frepple instances.

