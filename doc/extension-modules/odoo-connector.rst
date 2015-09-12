==============
Odoo connector
==============

.. raw:: html

   <iframe width="640" height="360" src="http://www.youtube.com/embed/XmbF7b34_sc" frameborder="0" allowfullscreen=""></iframe>

FrePPLe provides an integration with the Odoo (formerly known as OpenERP),
a leading open source ERP.

The connector provides the following functionality:

* Two-way integration:

* | Live data integration.
  | The connector reads the data directly from odoo and writes the results
    back. Compared to replicating data to its own database, this provides
    a more native and tighter integration. It is still possible to save a
    copy of the odoo in the frePPLe database to use the frePPLe user
    interface.

* You can still maintain additional data in the frePPLe user interface.
  I.e. Odoo doesn’t need to be the only source of data for your model.

* | Easy to customize.
  | Implemented as an odoo addon module, it is easy to customize the connector
    to your needs.

* | The integration has been developed with Odoo v7.
  | A version for v8 is being worked on.

Here are the slides presented during the `Odoo opendays conference <https://www.odoo.com/event/OpenDays-2014-5/page/website_event.Introduction-OpenDays>`_
in June 2014.

.. raw:: html

   <iframe src="http://www.slideshare.net/slideshow/embed_code/35555795" width="597" height="486" frameborder="0" marginwidth="0" marginheight="0" scrolling="no" style="border:1px solid #CCC; border-width:1px 1px 0; margin-bottom:5px; max-width: 100%;" allowfullscreen=""> </iframe>

**Overview**

The connector has 2 components:

* | An odoo addon:
  | All mapping logic between the Odoo and frePPLe data models is in this
    module. The results are accessible on the URL http://odoo_host/frepple/xml
    from which the planning engine will read data in its native XML data format
    and to which it will post the results.

* | A frePPLe addon:
  | This module gives frePPLe the capability to connect to Odoo, read the data
    from it, and publish back the results.

**Configuring the connector**

* | **Install the Odoo addon**
  | The addon code is found in the folder contrib/odoo, or you can pick up the
    latest version from github https://github.com/frePPLe/frePPLe/tree/master/contrib/odoo.
  | A different version is required for v7 and for v8.

  The module has the following dependencies: ‘procurement’, ‘product’, ‘purchase’,
  ‘sale’, ‘resource’, ‘mrp’, ‘sales_order_date’, and (optional) ‘hr’.

  After installation, you’ll find the following additional features in odoo:

  * A web interface called by the frePPLe planning engine. It is accessible at the
    URL http\://<host>:<port>/frepple/xml?database=<db>&language=<language>&company=<yourcompany>

  * A menu item in the warehouse menu to manually recreate the plan.

  * A scheduler task to recreate the plan as a cron job.

  * Extra configuration options in company editing form, as described below.

* | **Configure the Odoo addon**
  | The module adds some configuration fields on the company model.
  | Edit these parameters:

  * | Calendar:
    | References a resource.calendar model that is used to define the working
      hours.
    | If left unspecified, we assume 24*7 availability.

  * | Manufacturing location:
    | The connector assumes each company has only a single manufacturing
      location.
    | All bills of materials are modelled there.

  * | Cmdline:
    | Command line launched when the plan generation for a company is launched
      interactively from the user interface.
    | Note that when launched from a scheduler cron job, the command line is
      configured on the job directly.

* | **Edit the frePPLe configuration file djangosettings.py**
  | The file is found under /etc/frepple (linux) or <install folder>\bin\custom
    (Windows).
  | Assure that the freppledb.odoo is included in the setting
    INSTALLED_APPS which defines the enabled extensions. By default
    it is enabled.

* **Configure the frePPLe parameters**:

  * odoo.url: URL of the Odoo server

  * odoo.db: Odoo database to connect to

  * odoo.user: Odoo user for the connection

  * | odoo.password: Password for the connection
    | For improved security it is recommended to specify this password in the
      setting ODOO_PASSWORDS in the djangosettings.py file rather then this
      parameter.

  * | odoo.language: Language for the connection.
    | If translated names of products, items, locations, etc they will be used.

  * odoo.company: Company name for which to create purchase quotation and
    manufacturing orders

**Running the connector**

You can run the connector in different ways:

* | **Interactively from the frePPLe user interface**
  | The execute screen has a specific section where you can launch the import
    connector.

.. image:: _images/odoo-import-export.png
   :alt: Import from  and export to odoo

* | **From the command line**
  | The script is especially handy when you want to regenerate the plan
    automatically.
  | Issue the command below.

  ::

     frepplectl frepple_run --env=odoo_read,odoo_write

* | **Interactively from the Odoo menu**
  | Make sure the command line on the company you run for is configured
    correctly.

* | **Automatically with the Odoo cron scheduler**
  | Make sure the command line on the task is configured correctly.

**Mapping details**

The connector doesn’t cover all possible configurations of Odoo and frePPLe.
The connector is very likely to require some customization to fit the particular
setup of the ERP and the planning requirements in frePPLe.

:download:`Download mapping documentation as pdf <_images/odoo-integration.pdf>`

:download:`Download mapping documentation as a spreadsheet <_images/odoo-integration.xlsx>`

.. image:: _images/odoo-integration.jpg
   :alt: odoo mapping details