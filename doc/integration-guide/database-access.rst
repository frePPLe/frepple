===============
Database access
===============

For large data volumes a data integration with an `ETL tool`_
to directly connect to the PostgreSQL database will be the most
efficient.

The frePPLe database schema is very transparent and straightforward
to allow this type of integration.

Keep in mind however:

* Your ETL-interface will need to capture and handle all types of
  invalid data. With all other integration methods the frePPLe API 
  layer catches and reports such errors, but not in this integration
  mode. 

* The database schema can change between releases. We provide no guarantuee
  that your ETL-interface will be future-proof.

.. _`ETL tool`: https://en.wikipedia.org/wiki/Extract,_transform,_load