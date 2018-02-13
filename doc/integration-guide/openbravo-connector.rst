===================
Openbravo connector
===================

.. raw:: html

   <iframe width="640" height="360" src="https://www.youtube.com/embed/CBDaY4RUH58" frameborder="0" allowfullscreen=""></iframe>

FrePPLe provides an integration with `Openbravo <http://www.openbravo.com>`_, a
leading open source agile ERP system.

Overview
--------

The connector provides the following functionality:

* Two-way integration:

  * Synchronizes the frePPLe database with items, locations, bill of materials,
    routings, resources, sales orders, customers, inventory, production orders,
    purchase orders from Openbravo.

  * Uploads new production requirements, purchase requisitions and expected
    delivery date of sales orders from frePPLe to Openbravo.

* Uses the standard web services API to access Openbravo.
  No changes are required on Openbravo side.

* For optimal performance the connector allows net-change download. Only the
  objects that have been created or changed in Openbravo within a certain time
  frame are extracted.

* You can still maintain additional data in the frePPLe user interface. I.e.
  Openbravo doesn't need to be the only source of data for your frePPLe model.

* | Easy to customize.
  | The connector uses the standard Openbravo web services (see 
    http://wiki.openbravo.com/wiki/XML_REST_Web_Services ) to read and write 
    data.
  | Coded in Python, the connector can easily be updated to match the
    customizations done in your Openbravo deployment.

* | The connector has been validated with Openbravo 16Q3.3. 
  | For integration of work requirements the Advanced Warehousing Operations
    (see http://wiki.openbravo.com/wiki/Modules:Advanced_Warehouse_Operations )
    is recommended, as it provides an additional web service that provides
    a better workflow for the end users.


.. _openbravo_import:

Importing data from Openbravo into frePPLe
------------------------------------------

You can run the import interface in 3 ways:

* | **Interactively from the frePPLe user interface.**
  | The execute screen has a specific section where you can launch the import
    connector.
  | You can specify the number of days of recent changes you want to extract
    from Openbravo.

  .. image:: _images/openbravo-import.png
	 :alt: Import from openbravo

* | **From the command line.**
  | The frepplectl command is useful when you want to run the interface
    automatically, e.g. with a cron job.
  | Issue one of the commands below. The second command runs an incremental
    import of the Openbravo objects that have been changed in the last 7 days.

  ::

    frepplectl openbravo_import
    frepplectl openbravo_import --delta=7
    
* | **Through a web API.**
  | The web API is the proper method to automate the integration on the frePPLe
    cloud servers.
  
  ::
  
    POST /execute/api/openbravo_import/?delta=7

    
.. _openbravo_export:

Exporting data from frePPLe to Openbravo
----------------------------------------

You can bring the planning results to Openbravo in 4 ways:

* | **Incremental export from the frePPLe user interface**
  | User can select proposed purchase orders, distribution orders or manufacturing
    orders in the frePPLe screens, and then use the action menu to bring them
    immediately to Openbravo.

  .. image:: _images/openbravo-export-incremental.png
     :alt: Export to openbravo

* | **Bulk export from the frePPLe user interface.**
  | The execute screen has a specific section where you can launch the export
    connector. This allows to export all proposed transactions meeting certain
    criteria to Openbravo.
  | Three parameters define a filter criterion to select which transactions
    will be included in the bulk exports.

  .. image:: _images/openbravo-export.png
     :alt: Export to openbravo

* | **Bulk export from the command line.**
  | Issue the command below. The script is especially handy when you want to
    run the interface automatically.

  ::

     frepplectl openbravo_export

* | **Bulk export through a web API.**
  | The web API is the proper method to automate the integration on the frePPLe
    cloud servers.
  
  ::
  
    POST /execute/api/openbravo_export/

It is possible to combine both the incremental and bulk export in the same frePPLe
instance. For instance, proposed purchase orders for a total value less than a certain 
dollar threshold can be exported automatically to Openbravo. Proposed purchase orders
above the threshold are then reviewed in frePPLe by the planner, and export 
incrementally upon the planners' approval.

Installation and configuration
------------------------------

Most of the configuration is happening on frePPLe side.

* **Configuring the connector - Openbravo side**

  * | The connector doesn't require any extra installation on Openbravo side.

  * | The connector uses the `standard XML REST web services <http://wiki.openbravo.com/wiki/XML_REST_Web_Services>`_
      and a user that has correct access rights to the organization you want to
      integrate into frePPLe.

* **Configuring the connector - frePPLe side**

  * | **Edit the configuration file djangosettings.py**
    | The file is found under /etc/frepple (linux) or <install folder>\bin\custom
      (Windows).
    | Assure that the freppledb.openbravo is included in the setting
      INSTALLED_APPS which defines the enabled extensions. By default
      it is not enabled.

  * | **Migrate your frePPLe database**
    | Run the migrate command to add some extra fields in the database, and load the 
      connector parameters.
    
    ::

       frepplectl migrate

  * | **Configure the following parameters**
    | In the frePPLe user interface, the menu item 'admin/parameters' opens a
      data table to edit these.
  
    * openbravo.host: host where the Openbravo web service is running
  
    * openbravo.user: Openbravo user used to for the connection
  
    * | openbravo.password: Password for the connection
      | For improved security it is recommended to specify this password in the
        setting OPENBRAVO_PASSWORDS in the djangosettings.py file rather then 
        using this parameter.
  
    * | openbravo.date_format: Date format for openbravo webservice filter
      | Date format defaults to  %Y-%m-%d (i.e. YYYY-MM-DD) but can here be changed
        to other formats like %m-%d-%Y (i.e. MM-DD-YYYY).
  
    * | openbravo.exportPurchasingPlan 
      | By default we export purchase requisitions and manufacturing work orders. 
      | By switching this flag to true, we will export to the purchaseplan object instead, 
        which is where the Openbravo MRP run normally stores its results. Switch this 
        flag to true only if you have specific customizations using the purchaseplan table.
  
    * | openbravo.filter_export_purchase_order
      | Filter expression purchase orders for bulk export of purchase orders.
    
    * | openbravo.filter_export_manufacturing_orderfilter:
      | Filter expression for bulk export of manufacturing orders.
    
    * | openbravo.filter_export_distribution_order
      | Filter expression for bulk export of distribution orders.

Data mapping details
--------------------

The connector doesn't cover all possible configurations of Openbravo and
frePPLe. The connector is quite likely to require some customization to fit
the particular setup of the Openbravo and the planning requirements in frePPLe.

:download:`Download mapping documentation as SVG <_images/openbravo-integration.svg>`

.. image:: _images/openbravo-integration.svg
   :alt: openbravo mapping details
