Release notes
-------------

4.4 (Upcoming release)
======================

.. rubric:: Production planning

- The `resource report <user-guide/user-interface/plan-analysis/resource-report.html>`_ now displays the 
  available capacity as a line, replacing the green bar in previous releases to show the free capacity.

- | Performance optimization of the solver algorithm. The solver now passes down the minimum shipment 
    information from the demand to all upstream entities, which allows the algorithm to perform a more
    efficient search.
  | In complex models, the resulting plan may be slightly different - for the better.

- Resource build-ahead penalty calculation now also working for 0-cost resources.

- New rows to `purchase order summary <user-guide/user-interface/plan-analysis/purchase-order-summary.html>`_ 
  and `distribution order summary <user-guide/user-interface/plan-analysis/distribution-order-summary.html>`_
  reports to show the quantity on order or in transit.
  
- Resources can now have an `efficiency percentage <user-guide/model-reference/resources.html>`_. This allows
  the resource to perform an operation faster or slower than the standard operation time.

.. rubric:: Inventory planning

- The safety stock and ROQ minimum/maximum period of cover are now expressed in days. It was before entered
  as the number of period buckets, the period bucket being the value of the inventoryplanning.calendar parameter.


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
