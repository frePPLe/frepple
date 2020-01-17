Release notes
-------------

6.2.0 (2020/01/17)
==================

.. rubric:: Production planning

- Currentdate parameter now accepts most known formats to represent a date and/or time.

.. rubric:: User interface

- | The last-modified fields and the task execution dates are now shown in the
    local timezone of your browser.
  | For on-premise installations this doesn't change anything. However, our cloud 
    customers across the world will be happy to better recognize the timestamps.  
    
- | Ability to filter on json fields such as the "Demands" field of manufacturing/distribution/purchase 
    orders table.
    
- When exporting Excel files, read-only fields are now visually identifiable in the
  header row. A color and comment distinguish read-only fields from fields that can be
  updated when uploading the data file.  
   
.. rubric:: Integration

- Export of duration fields will not be in seconds anymore but will use same format used
  in the tool: "DD HH:MM:SS". This change is effective for both csv and Excel exports.

.. rubric:: Development

- New mechanism to build Linux packages. The new, docker-based process makes supporting
  multiple linux distributions much easier.

.. rubric:: Security

- | A vulnerability in the django web application framework was identified and corrected.
    The password reset form could be tricked to send the new password to a wrong email address.
  | The same patch can be applied to earlier releases. Contact us if you need help for this.
  | See https://www.djangoproject.com/weblog/2019/dec/18/security-releases/ for full details.
  | By default frePPLe doesn't configure an SMTP mail server. The password reset functionality
    isn't active then, and you are NOT impacted by this issue.
  

6.1.0 (2019/11/29)
==================

.. rubric:: Production planning

- Bug fixes in the solver algorithm when using alternate materials.

- Bug fixes in the solver algorithm when using post-operation times at many 
  places in the supply path.

- The `demand Gantt report <user-guide/user-interface/plan-analysis/demand-gantt-report.html`
  got a long overdue refreshed look and now displays more information.

.. rubric:: User interface

- | Filter arguments are now trimmed to provide a more intuitive filtering. The invisible 
    leading or trailing whitespace lead to confusion and mistakes.
  | On the other hand, if you were filtering on purpose with such whitespace: this is
    no longer possible.  

- Support for user-defined attributes on purchase orders, manufacturing orders and
  distribution orders.
  
- Bug fix: The  user permissions "can copy a scenario" and "can release a scenario" 
  were not working properly. 
  
- Enhancement of the supply path to draw cases where producing operation materials 
  record is missing (produced item declared at operation level) or produced item is only
  declared at routing level.

.. rubric:: Integration

- Renamed the command "create_database" to "createdatabase" for consistency with the other commands.

- Bug fix: remote execution API failure on scenarios

- Various fixes to the connector for Odoo 12.

.. rubric:: Development

- A new screen allows to `execute SQL commands on the database <user-guide/user-interface/executesql.html>`_.
  This new app is only intended to facilitate development and testing, and shouldn't be activated in 
  production environments.

6.0.0 (2019/16/09)
==================

.. rubric:: Production planning

- | The name column in the 
    `buffer table <user-guide/model-reference/buffer.html>`_ is removed. The item and location
    fields are what uniquely defines a buffer.
  | This data model simplification makes data interfaces simpler and more robust. 

- | Data model simplification: The `suboperation table <user-guide/model-reference/suboperations.html>`_ 
    is now deprecated. All data it contained can now be stored in the operation table.
  | This data model simplification makes development of data interfaces easier.

- The default minimum shipment for a demand is changed from "round_down(quantity / 10)"
  to "round_up(quantity / 10)". This provides a better default for planning very slow moving
  forecasts. 
  
- The resource type 'infinite' is now deprecated. It is replaced by a new field 'constrained' on
  resource. This approach allows easier activation and deactivation of certain resources as 
  constraints during planning.
  
- When generating a constrained plan, the material constraint has been removed. It didn't really
  have any impact on the plan algorithm. The constraints actually used by the planning engine are
  capacity, lead time and the operation time fence.  
  
- Improvements to the solver algorithm for bucketized resources and time-per operations.
  The improvements provide a more realistic plan when manufacturing orders span across
  multiple capacity buckets.

- Performance improvements in the evaluation of setup matrices.

- Bug fixes and improved log messages in the propagation of work-in-progress status information.

.. rubric:: User interface

- | Bug fix: When uploading a Purchase/Distribution/Manufacturing orders file with the 
    "First delete all existing records AND ALL RELATED TABLES" selected, all purchase, 
    manufacturing and distribution records were deleted.
    
- Addition of the duration, net duration and setups fields in the manufacturing order screen.

- Addition of Hebrew translations, contributed by https://www.minet.co.il/  Many thanks!

- Give a warning when users try to upload spreadsheets in the (very) old .XLS Excel format
  instead of the new .XLSX spreadsheet format.

- Performance improvement for the "supply path" and "where used" reports for complex and 
  deep bill of materials.
    
.. rubric:: Integration

- | The REST API for manufacturing orders now returns the resources and materials it uses.
  | Updated resources and materials can also written back with API.

- Added support for integration with Odoo 12.

.. rubric:: Third party components

- | The third party components we depend on have been upgraded to new releases. Most
    notably upgrades are postgres 11 and django 2.2.
  | Postgres 10 remains supported, so upgrading your database isn't a must for installing
    this release.
  | When upgrading a linux installation from a previous release, use the following command
    to upgrade the Python packages. On Windows the new packages are part of the installer.
      sudo -H pip install --force-reinstall -r https://raw.githubusercontent.com/frepple/frepple/6.0.0/requirements.txt

- Support for running in Python virtualenv environments.

.. rubric:: Documentation

- Addition of "cookbook" example models on the following functionalities: alternate resources, resource efficiency.

5.3.0 (2019/07/06)
==================

.. rubric:: Production planning

- Bug fix: material shortages can be left in the constrained plan, when solving safety stock
  across multiple stages or in the presence of confirmed supply.

.. rubric:: User interface

- | The modelling wizard that guides new users in loading their first data in frePPLe is completely
    redesigned. It now provides a more complete, more structured and deeper guidance for getting
    started with frePPLe.
  | Currently this new wizard is not available in the Community Edition.
  
- A new guided tour is available. Previous guided tour was a journey around the different pages 
  and features of frePPLe. New guided tour is composed of use case questions, illustrated in
  a short video.

- Filters for a report can now be updated easier. Rather than opening the search dialog
  again you can directly edit the filter description in the title.

- Multiple files can now be imported together in a grid. Opening the import box multiple times
  is a bit boring. Selecting or dragging multiple files is cooler.

- Bug fix. When using the Empty Database feature on either manufacturing or distribution or delivery or purchase orders
  then all orders (manufacturing + distribution + delivery + purchase) were deleted.
  
- Bug fix on backlog calculation of the `demand report <user-guide/user-interface/plan-analysis/demand-report.html>`_

5.2.0 (2019/05/27)
==================

.. rubric:: Production planning

- | Modeling simplication: In the `operation material table <user-guide/modeling-wizard/manufacturing-bom/operation-materials.html>`_
    you had to always insert both the produced material and consumed materials. 
  | In a lot of models an operation always produces 1 unit of the item. In this type
    of model you can now choose to leave out the records for the produced material. 
    We'll automatically add them with makes your modeling and data interfaces easier,
    faster and less error-prone.
  | If an operation produces a quantity different from 1 the producing operation material 
    record remains necessary.

- Performance improvements in the solver algorithm.

- Operations loading multiple bucketized resource now use the effiency of that resources.
  In earlier releases we used the minimum efficiency of all resources that operation loads,
  which is the correct behavior for resources of type default but not for bucketized resources.

- Bug fix to avoid creating excess inventory in models with large operation minimum 
  sizes.
  
.. rubric:: User interface

- Various small styling improvements and usability enhancements.

.. rubric:: Odoo connector

- Bug fixes in the mapping of open and closed sales orders.

5.1.0 (2019/04/22)
==================

.. rubric:: Production planning

- Performance improvements for the bucketized resource solver. 

- Bug fix and improvements in the way that completed and closed manufacturing order status
  is propagated to upstream materials.

.. rubric:: User interface

- | A new filter type is introduced for date fields. You can now easily filter records 
    with a date within a specified time window from today.
  | In earlier versions you had to explicitly change the date argument for the filter every
    day. Which was quite boring, error-prone and not very user friendly. 

- The number format in grid no longer has a fixed number of decimals, but flexibly adapts to
  the size and number of decimals in the number to be shown.

- | The login form now offers the option to remember me the login credentials. This avoids that
    a user has to login every time a browser session on frePPLe is started.
  | The user session information is persisted in a cookie in your browser. The session cookie will
    expire after a period of inactivity (configurable with the setting SESSION_COOKIE_AGE), after
    which the user has to log in again.
  | Security sensitive deployments should set this setting equal to 0, which forces users
    to log in for every browser session.

- When logging in, the user names and email address are now evaluated case-insensitively.
     

5.0.0 (2019/03/16)
==================

.. rubric:: Production planning

- | The identifier of `purchase orders <user-guide/model-reference/purchase-orders.html>`_,
    `distribution orders <user-guide/model-reference/purchase-orders.html>`_ and
    `manufacturing orders <user-guide/model-reference/purchase-orders.html>`_, has been removed. 
  | The reference field is now the primary key, and a required input field.
  | The required reference fields is an API-breaking change.
  
- | A new status "completed" is added on purchase orders, distribution orders and 
    manufacturing orders. It models a status where the order has already completed, but the
    ERP hasn't reflected this yet in its inventory status.
  | When changing the status of a manufacturing order to completed, there is also logic to assure
    that sufficient upstream material is available. If required the status of feeding purchase orders, 
    distribution orders and manufacturing orders is changed to completed.

- | The `resource detail <user-guide/model-reference/operationplan-resources.html>`_ and 
    `inventory detail  <user-guide/model-reference/operationplan-materials.html>`_ tables 
    are now editable. 
  | This allows to import detailed information on allocated resources and consumed materials from 
    the ERP system, and model the current work-in-progress in full detail.
  | In earlier releases these tables only contained output generated by the planning algorithm. 
    From this release onwards they also contain input information for manufacturing orders 
    in the status approved and confirmed. 

- | The default of the parameter `plan.autoFenceOperations <user-guide/model-reference/parameters.html>`_
    is changed from 0 to 999.
  | By default, the planning algorithm now waits for any existing confirmed supply before proposing
    a new replenishment.
  | The new default avoids unnecessary duplicate replenishments and results in more intuitive plans.

- | The search mode to choose among different alternate replenishments can now be controlled by the user.
  | In previous releases this could only be controlled on operations of type 'alternate', and automatically
    generated alternates always used priority as the selection mode. 
  | From this release onwards the field 'operation.search mode' can be used to specify the selection
    mode from among 'priority', 'minimum cost', 'minimum penalty' and 'minimum cost + penalty'.

- The item table gets some read-only fields which capture some key metrics:
  - number of late demands
  - quantity of late demands
  - value of late demands
  - number of unplanned demands
  - quantity of unplanned demands
  - value of unplanned demands
  
- The resource table gets a read-only field to store the number of overloads on the resource.
  
- The weight field for problems of type 'late' is now indicating the quantity being planned late.
  In earlier releases it represented the delivery delay.

- Performance optimizations for various corner cases.

.. rubric:: Odoo connector

- Workcenters assigned manufacturing orders are now also imported.

- Bug fix: Manufacturing orders in the state "ready to produce" were not being sent to
  frePPLe as work-in-progress.

4.5.0 (2019/01/25)
==================

.. rubric:: Production planning

- The default allowed delivery delay of sales orders and forecasts is changed from indefinite 
  to 5 years. This improves the performance of the algorithms in case there are unplannable
  orders.

- A new resource type `time buckets <user-guide/model-reference/resources.html#>`_ is introduced 
  that represents capacity as the number of hours of availability per time bucket.
  
- The capacity consumption from a bucketized resource now also has a constant component
  and considers the resource efficiency.
  
- Addition of the field size maximum to the item supplier and item distribution tables.

- | More detailed modeling of work in progress.
  | The parameters WIP.consume_material and WIP.consume_capacity control whether a confirmed
    manufacturing order consumes material and capacity.

- | More detailed modeling of in transit material.
  | By leaving the origin location empty, no inventory will be consumed at the origin location.
    We assume the material has already left the origin location and is in transit.
  | By leaving the destination location, the distribution order doesn't produce any stock.
    This represents a material transfer outside of our supply chain.

- Ability to use powerful regular expressions in the definition of 
  `setup matrices rules <user-guide/model-reference/setup-matrices.html#>`_ .

- Bug fix: calculation of operation time for 0-duration operations was wrong in some situations.

- Bug fix: incorrect operation duration when different resources in an aggregate pool resource 
  have different working hours.

- Bug fix: corrected corner cases where the solver got into an infinite loop.  

.. rubric:: User interface

- Ability to cancel any running task on the execution screen. Until now only the plan generation
  could be canceled while it was running.
 
- Improved performance and reduced memory footprint when downloading and exporting big reports.
 
- Added field duration to the
  `execution screen <user-guide/user-interface/execute.html>`_

- Added tabs to see the manufacturing orders for a specific item, location or operation.

- Update of the "in progress" fields of the inventory report. Are considered in progress for a given bucket
  all orders starting before the end date of that bucket and ending after the end date of that bucket. 

- Improved display of very small durations. All digits up to 1 microsecond are now visible.

.. rubric:: API

- The `database backup command <user-guide/command-reference.html#backup>`_ and
  `database restore command <user-guide/command-reference.html#restore>`_ now use the 
  faster and smaller compressed binary backup format of PostgreSQL. 

4.4.2 (2018/10/20)
==================

.. rubric:: Production planning

- Performance optimization for models with post-operation times by avoiding
  ineffecient search loops.

- The naming convention for distribution operations is changed from
  'Ship ITEM from ITEM @ SOURCE to ITEM @ DESTINATION' to
  the simpler and shorter 'Ship ITEM from SOURCE to DESTINATION'.

- Bug fix for a specific corner case where material requirements for work in progress
  aren't propagated at all.
  
- New parameter plan.resourceiterationmax allows user control over the number of searches
  for a free capacity slot on a resource. Contributed by Mateusz Knapik.
 
.. rubric:: User interface

- Added field net duration to the
  `resource detail report <user-guide/user-interface/plan-analysis/resource-detail-report.html>`_
  
- Added fields total in progress, work in progress MO, on order PO, in transit DO to the
  `inventory report <user-guide/user-interface/plan-analysis/inventory-report.html>`_
  
- Bug fix: Deleting an object from the edit form in a scenario was incorrectly
  deleting the object in the production instead.
  
- | The `import data files from folder <user-guide/command-reference.html#importfromfolder>`_
    and `import a spreadsheet <user-guide/command-reference.html#importworkbook>`_ functionalities
    now ignores spaces, dashes and underscores in the recognition of the content type from the 
    file or worksheet name.
  | So far, only a worksheet called 'sales order' was recognized as containing sales order data.
    Now "sales-order", "sales_order" and "salesorder" will also be recognized.
    
.. rubric:: Third party components

- | The Ubuntu binaries will be compiled on Ubuntu 18 LTS from now onwards. 
  | Compiling for Ubuntu 16 LTS remains fully supported, but we recommend to upgrade Ubuntu.
  
4.4.1 (2018/09/10)
==================

.. rubric:: Production planning

- Bug fix in the calculation of the lateness/earliness of a manufacturing
  order, purchase order or distribution order. The calculation was incorrectly
  based on the start date rather the end date of the operation in question. 

- A new field "feasible" is now added to the
  `inventory detail report <user-guide/user-interface/plan-analysis/inventory-detail-report.html>`_,
  `resource detail report <user-guide/user-interface/plan-analysis/resource-detail-report.html>`_,
  `operation detail report <user-guide/user-interface/plan-analysis/operation-detail-report.html>`_,
  `purchase order screen <user-guide/model-reference/purchase-orders.html>`_,
  `distribution order screen <user-guide/model-reference/distribution-orders.html>`_ and
  `manufacturing order screen <user-guide/model-reference/manufacturing-orders.html>`_.
  The read-only boolean field indicates whether the order is violating any material, lead time or capacity
  constraints. This is useful in interpreting the results of an unconstrained plan.
  
- | The criterion for `before current problems <user-guide/user-interface/plan-analysis/problem-report.html>`_
    is updated for confirmed orders. The change should result in less problems that are 
    also more meaningful to the users.
  | For orders in the status approved or proposed a before-current problem is created when
    the start date is in the past.
  | For orders in the status confirmed the criterion the problem is now created when the
    end date is in the past, i.e. the order is overdue and should have been finished by now.

- The natural key in the `suboperation table <user-guide/model-reference/suboperations.html>`_
  is changed from operation + suboperation + operation to operation + suboperation +
  effective start date.

.. rubric:: User interface

- Ability to make the data anonymous and obfuscated when 
  `exporting an Excel workbook <user-guide/command-reference.html#exportworkbook>`_. 
  The names of all entities are obfuscated in the resulting spreadsheet. You will still
  need to carefully review the output to clean out any remaining sensitive data.  

- Ability to customize the names for the time buckets used in the reports.
  The `time bucket generation command <user-guide/command-reference.html#createbuckets>`_
  now has extra attributes for setting the name of the daily, weekly, monthly, quarterly
  and yearly buckets.
 
.. rubric:: Third party components

- | Support for Ubuntu 18 LTS. 
  | Ubuntu 16 LTS remains fully supported.
  
- | Windows installer now uses Python 3.6.
  | Python 3.5 remains fully supported.

4.4.0 (2018/08/02)
==================

The Windows installer of this version isn't working correctly due to some packaging mistakes.

.. rubric:: Production planning
  
- Resources can now have an `efficiency percentage <user-guide/model-reference/resources.html>`_. This allows
  the resource to perform an operation faster or slower than the standard operation time.

- The `resource report <user-guide/user-interface/plan-analysis/resource-report.html>`_ now displays the 
  available capacity as a line, replacing the green bar in previous releases to show the free capacity.

- | Performance optimization of the solver algorithm. The solver now passes down the minimum shipment 
    information from the demand to all upstream entities, which allows the algorithm to perform a more
    efficient search.
  | In complex models, the resulting plan may be slightly different - for the better.

- Resource build-ahead penalty calculation now also working for 0-cost resources.

- New rows to the `purchase order summary <user-guide/user-interface/plan-analysis/purchase-order-summary.html>`_ 
  and `distribution order summary <user-guide/user-interface/plan-analysis/distribution-order-summary.html>`_
  reports to show the quantity on order or in transit.

- New rows to the `inventory report <user-guide/user-interface/plan-analysis/inventory-report.html>`_
  to show 1) days of cover of the starting inventory, 2) the safety stock and 3) more details
  on the supply and consumption type.

- | The minimum field on the buffer defines a safety stock. In previous releases this safety stock was
    effective from the horizon start in 1971. Now this safety stock is effective from the current
    date of the plan onwards.
  | This change will give a different result for safety stock replenishments in an unconstrained plan.
    In a lead time constrained plan the results will be identical.  

- Remove buffers of type procurement from the planning engine code. This buffer type was already long
  deprecated and hasn't been accessible to users for quite some time now. 
  
- Simpler and more generic modeling of fixed material consumption and production by operations. 
  The types 'fixed_end' and 'fixed_start' on `operation material <user-guide/model-reference/operation-materials.html>`_
  records are replaced with a field 'fixed_quantity'.

- Renamed the "demand plan detail" report to `delivery orders <user-guide/model-reference/operation-materials.html>`_,
  and enable uploading confirmed or approved shipments to customers as input data.

- | When expanding a confirmed manufacturing order on a routing operation, the automatic creation of the
    child manufacturing orders for each routing step now also considers the post-operation time.
  | Note that such child manufacturing orders are only generated if they aren't provided in the input 
    data yet.   

.. rubric:: User interface

- Bug fix when copying a what-if scenario into another what-if scenario. 

- Bug fix when uploading data files using the Microsoft Edge browser.

.. rubric:: Deprecation

- | Operations of types alternate, routing and split should not load any resources, 
    or consume or produce materials. The suboperations should model all material and capacity 
    usage instead.
  | Note that in the majority of models, the explicit modeling of alternate operations is no
    longer needed. The planning engine detects situations where an item-location can be replenished
    in multiple ways and automatically generates an alternate operation.

4.3.4 (2018/06/08)
==================

.. rubric:: Production planning

- Added new reports `purchase order summary <user-guide/user-interface/plan-analysis/purchase-order-summary.html>`_ 
  and `distribution order summary <user-guide/user-interface/plan-analysis/distribution-order-summary.html>`_
  to summarize the purchase orders or distribution orders per time bucket.

- For consistency with the previous change, the operation report is renamed 
  to `manufacturing order summary <user-guide/user-interface/plan-analysis/manufacturing-order-summary.html>`_.

.. rubric:: Integration

- Extended the `exporttofolder <user-guide/command-reference.html#exporttofolder>`_ 
  command to export additional plan results into CSV or Excel files.

- The data type of all numeric fields is changed from 15 digits with 6 decimals
  to 20 digits with 8 decimals. This allows a larger range of numbers to be
  accurately represented in the database.
  
- The `remote web commands API <integration-guide/remote-commands.html>`_ now 
  supports user authentication with `JSON Web Tokens <https://jwt.io/>`_ to launch tasks,
  download data and upload data. 

4.3.3 (2018/05/03)
==================

.. rubric:: Production planning

- Solver performance optimization where there are availability calendars.
  The plan generation time can be reduced with a factor 3 to 4 in some models.
- Solver enhancements for planning with setup matrices.
- Solver optimization to handle infinite buffers more efficiently.
- Bug fix: Compilation error with Python 3.6

.. rubric:: User interface

- Bug fix for spreadsheet import: more robust handling of empty rows and rows with
  empty fields at the end 
  
.. rubric:: Odoo connector

- Correction to maintain a single root hierarchy.


4.3.2 (2018/03/19)
==================

.. rubric:: Production planning

- | New operationmaterial policy 'transfer_batch' which allows material production
    or consumption in a number of batches of fixed size at various moments during
    the total duration of the operationplan.
  | A new field operationmaterial.transferbatch is introduced.
- A new field 'end items' is added to the manufacturing order, purchase order and
  distribution orders screens. It is similar to the 'demands' which shows the 
  demands 

.. rubric:: API

- Bug fix: backward compatibility after command renaming in 4.3.1

.. rubric:: Third party components

- Upgrade to PostgreSQL 10. 
  PostgreSQL 9.5 and 9.6 remain fully supported.

4.3.1 (2018/02/17)
==================

.. rubric:: Bug fixes

- The autofence now also considers approved supply, and not only confirmed supply.
- Excel files with some non-standard internal structure are now also recognized.
- Work-in-progress operationplans with quantity 0 are no longer rejected.

.. rubric:: Deprecations

- Command frepple_run is renamed to runplan.
- Command frepple_runserver is renamed to runwebserver.
- Command frepple_copy is renamed to scenario_copy.
- Command frepple_importfromfolder is renamed to importfromfolder.
- Command frepple_exporttofolder is renamed to exportfromfolder.
- Command frepple_flush is renamed to empty.
- Command frepple_backup is renamed to backup.
- Command frepple_restore is renamed to restore.
- Command frepple_simulation is renamed to simulation.
- Command frepple_createbuckets is renamed to createbuckets.
- Command frepple_createmodel is renamed to createmodel.
- Command frepple_loadxml is renamed to loadxml.
- Command frepple_runworker is renamed to runworker.
