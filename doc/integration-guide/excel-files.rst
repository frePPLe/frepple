===========
Excel files
===========

For small models and prototype models the most convenenient way
of integrating the data will be to work with excel workbooks.

* | Individual data tables can be exported and imported directly
    from the user interface.
  | See :doc:`/user-interface/getting-around/importing-data`
    and :doc:`/user-interface/getting-around/exporting-data`.

  | Some rules of thumbs are used to identify the data to process:

  - Hidden worksheets aren't imported. This can be used to skip
    processing worksheets with lookup data.

  - If a data table is defined on a worksheet, we'll use the range
    of the data table to find the data rows to import. This can be used
    to skip processing header areas.

* | Multiple data tables can be exported and imported in single workbook.
    The workbook contains a separate worksheet for each table.
  | See :doc:`/user-interface/execute`.

  The worksheet name must match the name of the frepple tables.
