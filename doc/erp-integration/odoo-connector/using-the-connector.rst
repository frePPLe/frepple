Using the connector in Odoo
---------------------------

After installation, users find the following additional features in odoo:

* | The sales menu has a link to the **frePPLe forecast editor screen**.
  | In this screen users can review and edit the sales forecast at
    different levels in the product, location, customer and time dimensions.

  .. image:: _images/odoo-forecast-editor.png
   :alt: Review and edit sales forecast in odoo

  | Note that this screen is only available in the Enterprise Edition of frePPLe.
    When using the frePPLe Community Edition these links will result in a
    page-not-found error message.

* | The inventory menu has a link to the **frePPLe inventory planning screen**.
  | In this screen users can review and edit the stocking policies for
    each item location.

  .. image:: _images/odoo-inventory-planning.png
   :alt: Review and edit safety stock and replenishment policies in odoo

  | Note that this screen is only available in the Enterprise Edition of frePPLe.
    When using the frePPLe Community Edition these links will result in a
    page-not-found error message.

* | The manufacturing menu has a link to the **frePPLe plan editor screen**.
  | In this screen an interactive Gantt chart is shown where users can
    review the plan and adjust where appropriate. Changes to the plan are
    automatically propagated to predecessor and successor production steps.

  .. image:: _images/odoo-plan-editor.png
   :alt: Interactive Gantt chart in odoo

  | Note that this screen is only available in the Enterprise Edition of frePPLe.
    When using the frePPLe Community Edition these links will result in a
    page-not-found error message.

* The manufacturing menu also contains a link to the complete frePPLe
  user interface.

* | Because some manufacturing concepts do not exist in odoo, the manufacturing app
    has been enhanced to include following objects.

  1. Skills: The concept of skill where a work center can have one or more skill has been
     added into odoo. A skill link is visible in the Master Data menu. This table is equivalent
     to the frePPLe :doc:`../../model-reference/skills` table, used to define the available skills.

     .. image:: _images/skill.png
      :alt: Skill view in odoo

  2. Work Center Skill: This table is equivalent to the frePPLe :doc:`../../model-reference/resource-skills` table.
     This table is used to assign skill(s) to a work center.
     A *Work Center Skill* link has been added in the Master Data menu.

     .. image:: _images/work_center_skill.png
      :alt: work center skill view in odoo

  3. Work center owner: A new field *owner* has been added to the work centers (equivalent to the frePPLe :doc:`../../model-reference/resources` owner field). Owner field
     allows the planner to define a parent work center.

     .. image:: _images/work_center.png
      :alt: work center in odoo

  4. Routing Work Center: In the Routing Work Center view of odoo, 3 new fields have been added:
     The *Skill*, *Search Mode* and *Priority* fields.
     This table is the equivalent to the frePPLe :doc:`../../model-reference/operation-resources` table.

     .. image:: _images/routing_work_center.png
      :alt: routing work center in odoo



Using the connector in frePPLe
------------------------------

The odoo integration brings new functionality to the user interface.

* | **Import data from Odoo into frePPLe**
  | The execute screen has an *import data from odoo* accordion menu that
    allows to import the Odoo data in frePPLe database and then generate a plan.

  .. image:: _images/odoo_import.png
   :alt: Import from odoo


  | The plan exported to odoo is a subset of the plan which passes
    certain filter conditions. The remaining part of the plan can
    only be exported manually from frePPLe to Odoo: see below.

  .. image:: _images/odoo_export.png
   :alt: Export to odoo

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

* | An incremental export from the frePPLe user interface for
    individual purchase, manufacturing and distribution
    orders.
  | When selecting a sales order for incremental export a popup window
    is displayed with a list of linked purchase, manufacturing and
    distribution orders.

  | A typical usage is to automatically export the proposed purchase for
    cheap or fast moving items, and let the planner review and approve
    the proposed plan in frePPLe for expensive or slow moving items.

  .. image:: _images/odoo-approve-export.png
   :alt: Exporting individual transactions to odoo

  .. image:: _images/odoo-approve-export-sales-order.png
   :alt: Exporting transactions of a sales order to odoo