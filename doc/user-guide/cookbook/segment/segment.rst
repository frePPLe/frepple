========
Segments
========

Segments is a collection of SKU used either for filtering purpose or for inventory planning when combined with a business rule.
To define a segment, a unique name for that segment and a query are required, an optional description can also be provided.
The query is an SQL-like query that can use fields from both item and location objects.
Note that segment are dynamic in the sense that whether an SKU belongs to a segment or not is automatically recomputed during a plan execution.
Therefore SKU can get in (and out) of a segment if it matches (or no more matches) the segment query.

Available fields for item table are :

* | name 
  | category
  | subcategory
  | description
  | cost
  | owner_id : *owner_id* should be used though *owner* keyword is displayed in frePPLe.

Available fields for location table are :

* | name 
  | category
  | subcategory
  | description
  | owner_id : *owner_id* should be used though *owner* keyword is displayed in frePPLe.

:download:`Excel spreadsheet segment <segment.xlsx>`
  
  In this example, we have defined four segments :

* | All parts in RDC : This segment is composed of all SKUs in RDC.
  | The query to define the segment is the following : 
  | *location.name = 'RDC'*


* | Cheap parts in Paris : This segment is composed of parts having a cost less than 20 in the Tennis shop Paris location.
  | The query to define the segment is the following : 
  | *item.cost <= 20 and location.name = 'Tennis shop Paris'*

* | Expensive parts in Brussels : This segment is composed of parts with a price higher than 50 in Tennis shop Brussels location.
  | The query to define the segment is the following : 
  | *item.cost > 50 and location.name = 'Tennis shop Brussels'*
  
* | All parts in shops : This segment is composed of all parts in both Tennis shop Brussels and Tennis shop Paris.
  | The query to define the segment is the following (Note that the % character should be used as wildcard) : 
  | *location.name like '%shop%'*
  
Any of the segments can be used for filtering purpose. For instance, in the *Inventory Planning* screen, 
a drop-down menu appears with the list of the defined segments to only display the collection of SKU belonging to that segment.

