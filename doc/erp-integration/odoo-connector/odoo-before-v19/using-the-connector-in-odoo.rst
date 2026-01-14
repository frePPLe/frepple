Addition of menus in Odoo
-------------------------

.. important::

   This page applies to Odoo 16, 17 and 18.
   See `this page <../odoo-from-v19/using-the-connector-in-odoo.html>`_ for 19.

After installation, users find the following additional features in odoo:

* | The sales menu has a link to the **frePPLe forecast editor screen**.
  | In this screen users can review and edit the sales forecast at
    different levels in the product, location, customer and time dimensions.

  .. image:: _images/odoo-forecast-editor.png
   :alt: Review and edit sales forecast in odoo

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

  .. image:: _images/odoo-frepple-link.png
   :alt: FrePPLe link in the manufacturing app

Addition of extra views and fields in Odoo
------------------------------------------

.. important::

   This page applies to Odoo 16, 17and 18.
   See `this page <../odoo-from-v19/using-the-connector-in-odoo.html#addition-of-extra-views-and-fields-in-odoo>`_ for 19.

* | Because some manufacturing concepts do not exist in odoo, the manufacturing app
    has been enhanced to include the following objects.

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

  3. Work centers. Owner: A new field *owner* has been added to the work centers (equivalent to the frePPLe :doc:`../../model-reference/resources` owner field). Owner field
     allows the planner to define a parent work center.

     .. image:: _images/work_center.png
      :alt: work center in odoo

  4. Operations: In the Operations view of Odoo, 4 new fields have been added:
     The *Skill*, *Search Mode*, *Priority* and *secondary work center* fields.
     Because it is not uncommom that an operation requires more than one work center to run, the connectors
     off the possibility to configure one or more secondary work centers.
     This table is the equivalent to the frePPLe :doc:`../../model-reference/operation-resources` table.


     .. image:: _images/operations.png
      :alt: Operations in odoo

Quoting capabilities
--------------------

.. important::

   This page applies to Odoo 16, 17and 18.
   See `this page <../odoo-from-v19/using-the-connector-in-odoo.html#quoting-capabilities>`_ for 19.

Starting from Odoo 17, the connectors also allow the planner to use the frePPLe quoting
module from Odoo.

To activate this functionality for an Odoo user, this user needs to be part of the *frePPLe quoting user*
group.

.. image:: _images/frepple-quoting-user.png
    :alt: FrePPLe quoting user group

| Note that the quoting capabilities are only available in the Enterprise Edition of frePPLe.
  When using the frePPLe Community Edition these links will result in a
  page-not-found error message.

* | The quoting capabilities brought by the connectors offer 2 distinct possibilities:

  1. Addtion of a **quote** button at the bottom of the *other info* tab of the quotations in the sales app.

      .. image:: _images/quotations-quote-button.png
        :alt: Extra quote button in the quotations

     If the *Delivery Date* field is empty, clicking on the *Quote* button will fill this field with the
     first possible date to deliver this quotation.

     If the *Delivery Date* field contains a date, clicking on the *Quote* button will check if it is possible to
     deliver the quotation at the delivery date. If it is possible, the *Delivery Date* remains unchanged.
     If it is not possible, the delivery date is updated with the new date (that can only be later than the old one).

     Note that, if the quotation contains multiple lines, the proposed delivery date will be the latest of all
     the lines.

     In the message section, planning information is added for each quotation line:

     .. image:: _images/quotation-message.png
        :alt: Messages contain planning details

  2. Addtion of a *FrePPLe Quotes* view accesible with a menu.

     .. image:: _images/frepple-quotes-menuitem.png
        :alt: An additional menu for the frePPLe quotes

     The *frePPLe Quotes* screen allows the planner to get in a matter of seconds a promised date for
     a product.

     The planner needs to fill the quote information (product, quantity, warehouse...) and hit the *quote*
     button.

     .. image:: _images/quote-promised-date.png
        :alt: A promised date is returned

     From the main screen of the *Frepple Quotes*, a *bulk quote* action is also available to allow the planner
     to compute a promised date for multiple lines at a time.
