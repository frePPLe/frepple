Using the connector in frePPLe
------------------------------

.. important::

   This page applies to odoo v16, v17and v18.
   See `this page <../odoo-from-v19/using-the-connector-in-frepple.html>`_ for v19.

The odoo integration brings new functionality to the user interface.

* | **Task "Import data from Odoo"**
  | The execute screen has an *import data from odoo* command that
    allows to import the Odoo data in frePPLe database and then generate a plan.

  .. image:: _images/odoo_import.png
   :alt: Import data from odoo

  | The connector distinguishes different modes to retrieve data from Odoo. This
    allows us to schedule the interfacing of larger and/or slowly changing data
    volumes (eg sales order history over the last few years as required for the
    forecast calculation) from the extraction of data elements that need to be
    retrieved whenever the plan is generated (eg open sales orders, current
    inventory).
  | Using the argument odoo_read_1 or odoo_read_2 specific the requested data
    extraction mode. By default all data elements are extracted in mode 1.
    It requires customization of the Odoo addon to define for which
    data elements you want to use mode 2.

* | **Task "Pull all demand history from Odoo"**
  | The execute screen has a *pull all demand history from odoo* command that
    allows to import all the demand history from Odoo. This command uses the
    XML RPC API of Odoo and is a one-off command
    that can be used from a fresh frepple database to pull all the demand history
    from Odoo. Note that the above *Import data from Odoo* command will also pull all
    the demand history among all other master and transactional data. As the demand
    history can be a very large dataset, it could be convinient to first use the
    *Pull all demand history from Odoo* command and then use the *odoo.delta* parameter
    with the regular *Import data from Odoo* command.

  .. image:: _images/odoo_pull_so_history.png
   :alt: Pull all demand history from Odoo


* | **Task "Export data to Odoo"**

  | The plan exported to odoo is a subset of the plan which passes
    certain filter conditions. The remaining part of the plan can
    only be exported manually from frePPLe to Odoo: see below.

  .. image:: _images/odoo_export.png
   :alt: Export data to odoo

  | The default command will export the following parts of the plan to odoo:

  - proposed purchase orders starting within the next 7 days

  - proposed distribution orders starting within the next 7 days

  - proposed manufacturing orders starting within the next 7 days

  - rescheduled new dates for approved work orders

  | In practice we have seen that implementation projects have different requirements,
    and this command very often needs to be customized.

* | **An incremental export from the frePPLe user interface for
    individual purchase, manufacturing and distribution
    orders.**

  | Users select a number of proposed tranactions, and click the "export to odoo"
    button. This immediately creates the matching transaction in odoo.

  | A typical usage is to automatically export the proposed purchase for
    cheap or fast moving items, and let the planner review and approve
    the proposed plan in frePPLe for expensive or slow moving items.

  .. image:: _images/odoo-approve-export.png
   :alt: Exporting individual transactions to odoo
