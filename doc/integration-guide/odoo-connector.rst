==============
Odoo connector
==============

.. raw:: html

   <iframe width="640" height="360" src="https://www.youtube.com/embed/6f7pU1NNqNY" frameborder="0" allowfullscreen=""></iframe>

FrePPLe provides an integration with the `Odoo <https://www.odoo.com>`_, a
leading open source business management suite.

Overview
--------

The connector provides the following functionality:

* | Two-way integration.
  | The connector retrieves all master data required for planning from Odoo.
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

* The integration has been developed and tested with v13 (main development
  focus), v12, v11, v10 (support-only) and v9 (outdated).

Here are the slides presented during the Odoo user conference in October 2016.

.. raw:: html

   <iframe src="https://www.slideshare.net/slideshow/embed_code/key/hDESgQ2Xo7spV" width="597" height="486" frameborder="0" marginwidth="0" marginheight="0" scrolling="no" style="border:1px solid #CCC; border-width:1px 1px 0; margin-bottom:5px; max-width: 100%;" allowfullscreen=""> </iframe>

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
     to the frePPLe :doc:`../model-reference/skills` table, used to define the available skills.

     .. image:: _images/skill.png
      :alt: Skill view in odoo

  2. Work Center Skill: This table is equivalent to the frePPLe :doc:`../model-reference/resource-skills` table.
     This table is used to assign skill(s) to a work center.
     A *Work Center Skill* link has been added in the Master Data menu.

     .. image:: _images/work_center_skill.png
      :alt: work center skill view in odoo

  3. Work center owner: A new field *owner* has been added to the work centers (equivalent to the frePPLe :doc:`../model-reference/resources` owner field). Owner field
     allows the planner to define a parent work center.

     .. image:: _images/work_center.png
      :alt: work center in odoo

  4. Routing Work Center: In the Routing Work Center view of odoo, 3 new fields have been added:
     The *Skill*, *Search Mode* and *Priority* fields.
     This table is the equivalent to the frePPLe :doc:`../model-reference/operation-resources` table.

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

Installation and configuration
------------------------------

The connector has 2 components:

* | An odoo addon:
  | All mapping logic between the Odoo and frePPLe data models is in this
    module. The results are accessible on the URL http://odoo_host/frepple/xml
    from which the planning engine will read data in its native XML data format
    and to which it will post the results.

* | A frePPLe addon:
  | This module gives frePPLe the capability to connect to Odoo, read the data
    from it, and publish back the results.
  | It also activates additional menus in the frePPLe user interface.

The section below describes the installation and configuration of these.

* **Configuring the connector - Odoo side**

  * | **Install the Odoo addon**
    | The addon code is found in the github repository https://github.com/frePPLe/odoo.
    | Use the branch from the subfolder matching your Odoo version.

  * | **Configure the Odoo server**
    | FrePPLe needs to be loaded as a server wide module. This is achieved
      by updating an option in the Odoo configuration file odoo.conf:
      "server_wide_modules = base,web,frepple"

  * | **Configure the Odoo addon**
    | The module adds some configuration on the company. You can edit these
      from the company edit form or from the settings.
    | Edit these parameters:

    * | Webtoken key:
      | A secret random string used to sign web tokens for a single signon between
        the Odoo and frePPLe web applications. Choose a string that is long enough,
        random and contains a mix of lower case characters, upper case characters
        and numbers.

    * | Calendar:
      | References a resource.calendar model that is used to define the working
        hours.
      | If left unspecified, we assume 24*7 availability.

    * | Manufacturing warehouse:
      | The connector assumes each company has only a single manufacturing
        location.
      | All bills of materials are modeled there.

    * | Frepple server:
      | URL of your frepple server.
      | Do not include a slash at the end of the URL.

    * | Respect reservations:
      | When this flag is checked, frepple fully respects the material
        reservations of odoo. Frepple only plans with the unreserved materials.
      | When this flag is false, frepple plans with the full material availability
        regardless of any reserved quantities in odoo. The implicit assumption is
        that any reservations will be unreserved in odoo when needed.

    * | Disclose stack trace:
      | To debug the connector and data issues it can be useful to send any connector
        stack traces also to your frepple server.
      | By default this option is not active for security reasons.
      | It is recommended to activate this option only during development or testing.

    .. image:: _images/odoo-settings.png
       :alt: Configuring the Odoo add-on.

  * | **Review time zone setting**
    | The time zone preference of the odoo user utilized by the connector is important.
      Odoo sends all dates to frepple converted to this timezone, and frepple returns dates
      in this timezone.

  * | You can run a **quick test** of the above by opening a web browser to the URL
      http\://<host>:<port>/frepple/xml?database=<db>&language=<language>&company=<company>.
      The parameters db and company determine which odoo database to connect to.
    | After providing the login details, an XML document will be displayed with
      the data that frePPLe will read from Odoo.
    | Note that sometimes, for large odoo dataset, the above link can return an error because of a timeout
      issue. If that is happening, you need to update parameters *limit_time_cpu* and *limit_time_real*
      in the odoo configuration file and increase their value.


* **Configuring the connector - frePPLe side**

  * | **Edit the frePPLe configuration file /etc/frepple/djangosettings.py**

    * | Assure that the "freppledb.odoo" is included in the setting
        INSTALLED_APPS which defines the enabled extensions. By default
        it is disabled.

    * | Update the DATABASE section such that the SECRET_WEBTOKEN_KEY setting of each
        scenario is equal to the web token key configured in Odoo.

    * | Make sure the setting MIDDLEWARE doesn't include the
        "django.middleware.clickjacking.XFrameOptionsMiddleware" class.

    * | If frePPLe and Odoo are installed on 2 different domains (example: https://myfrepple.frepple.com
        and https://myodoo.odoo.com), then following lines need to be added:

        .. code-block:: Python

           CONTENT_SECURITY_POLICY = "frame-ancestors 'self' domain-of-your-odoo-server;"
           X_FRAME_OPTIONS = None
           SESSION_COOKIE_SAMESITE = "none"            # NOTE: "none", not None
           CSRF_COOKIE_SAMESITE = "none"               # NOTE: "none", not None

  * **Configure parameters**

    * | odoo.url: URL of the Odoo server

    * | odoo.db: Odoo database to connect to

    * | odoo.user: Odoo user for the connection

    * | odoo.password: Password for the connection
      | For improved security it is recommended to specify this password in the
        setting ODOO_PASSWORDS in the djangosettings.py file rather then this
        parameter.

    * | odoo.language: Language for the connection.
      | If translated names of products, items, locations, etc they will be used.
      | The default value is en_US.

    * | odoo.company: Company name for which to create purchase quotation and
        manufacturing orders.

    * | odoo.singlecompany:
      | When false (the default) the connector downloads all allowed companies for the odoo integration
        user.
      | When true the connector only downloads the data of the configured odoo.company.

    * | odoo.allowSharedOwnership:
      | By default records read from odoo aren't editable in frepple. You loose your
        edits with every run of the connector.
      | If this flag is set to true you can override the odoo data if the source field
        of the overridden records is also edited.

Data mapping details
--------------------

The connector doesn't cover all possible configurations of Odoo and frePPLe.
The connector will very likely require some customization to fit the particular
setup of the ERP and the planning requirements in frePPLe.

:download:`Download mapping as svg image <_images/odoo-integration.svg>`

:download:`Download mapping as a spreadsheet <_images/odoo-integration.xlsx>`

.. image:: _images/odoo-integration.jpg
   :alt: odoo mapping details
