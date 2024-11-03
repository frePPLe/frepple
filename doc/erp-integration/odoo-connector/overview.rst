Overview
--------

Before going into the technical details, you might want to take one step back and understand
`what Odoo cannot do for planners <https://frepple.com/blog/five_things_odoo_mrp_doesnt_do/>`_
and why advanced planning is required for complex environments.

.. image:: _images/odoo_planning_complexity.png
   :alt: Import data from odoo
   :scale: 50%


The connector provides the following functionality:

* | Two-way integration.
  | The connector retrieves all master and transactional data required for planning from Odoo.
  | The connector publishes the resulting plan back to Odoo. The planner can
    trigger the export of the plan to Odoo either after the plan is finished
    or after a manual review and approval.

* | Live data integration.
  | The connector reads the data directly from Odoo and writes master and
    transactional data in frePPLe database. The planner can then run a plan in frePPLe
    and either export all the plan in Odoo or selects which data to export.

* | User interface integration.
  | Users can access frePPLe screens from the Odoo interface, without
    logging in a second application.

* | Easy to customize.
  | Implemented as an odoo addon module, it is easy to customize the connector
    to your needs.

* | The integration has been developed and tested with the latest versions of Odoo.
  | We support the last 3 versions of Odoo connectors (currently the v15, v16, v17 and v18).

Below are the slides presented during the Odoo user conference in October 2022 where we describe how frePPLe
solves Odoo customer business cases.

.. raw:: html

   <iframe src="https://www.slideshare.net/slideshow/embed_code/key/LJvg4KnDyJlmYl?hostedIn=slideshare&page=upload" width="597" height="486" frameborder="0" marginwidth="0" marginheight="0" scrolling="no" style="border:1px solid #CCC; border-width:1px 1px 0; margin-bottom:5px; max-width: 100%;" allowfullscreen=""></iframe>


Below are the slides presented during the Odoo user conference in October 2016:

.. raw:: html

   <iframe src="https://www.slideshare.net/slideshow/embed_code/key/hDESgQ2Xo7spV" width="597" height="486" frameborder="0" marginwidth="0" marginheight="0" scrolling="no" style="border:1px solid #CCC; border-width:1px 1px 0; margin-bottom:5px; max-width: 100%;" allowfullscreen=""> </iframe>