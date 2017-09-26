=========================
API from the command line
=========================

Using tools like "curl", "wget" or similar you can use the command line to (depending on your permissions) change/read/add/delete data.

To just get a list of all sales orders in JSON format:

::

   wget --http-user=admin --http-password=admin http://127.0.0.1:8000/api/input/demand/?format=json

   curl -H 'Accept: application/json; indent=4' -u admin:admin http://127.0.0.1:8000/api/input/demand/?format=json

To just get a filtered list of sales orders withe quantity equal or above 200, and with location *factory 2*
(the URL needs escaping, the spaces and & were replaced by ``%20`` and ``\&``) in JSON format:

::

   wget --http-user=admin --http-password=admin http://127.0.0.1:8000/api/input/demand/?quantity__gte=200\&location=factory%202\&format=json

   curl -H 'Accept: application/json; indent=4' -u admin:admin "http://127.0.0.1:8000/api/input/demand/?quantity__gte=200&location=factory%202&format=json"


To just get a list of all sales orders in API format (assuming the user is named "admin" and that the password is also "admin":

::

   wget --http-user=admin --http-password=admin http://127.0.0.1:8000/api/input/demand/?format=api

   curl -H 'Accept: application/json; indent=4; charset=UTF-8' -u admin:admin http://127.0.0.1:8000/api/input/demand/?format=api


To POST a single or multiple records in JSON format it is also straightforward.
For a single record POST request:

::

   curl -X POST -H "Content-Type: application/json; charset=UTF-8" -d "[{\"keyA0\":\"valA0\", \"keyA1\":\"valA1\"}]" -u admin:admin http://127.0.0.1:8000/api/input/demand/?format=json

For a multiple record POST request:

::

   curl -X POST -H "Content-Type: application/json; charset=UTF-8" -d "[{\"keyA0\":\"valA0\", \"keyA1\":\"valA1\"},{\"keyB0\":\"valB0\", \"keyB1\":\"valB1\"}]" -u admin:admin http://127.0.0.1:8000/api/input/demand/?format=json

"key:val" pairs should be separated by a comma, so it is probably easier if you store the data in a file:

::

   curl -X POST -H "Content-Type: application/json; charset=UTF-8" --data @json_records_file.txt -u admin:admin http://127.0.0.1:8000/api/input/demand/?format=json

To PUT/PATCH a single record in JSON format:

::

   curl -X PATCH -H "Content-Type: application/json; charset=UTF-8" -d "{\"key\":\"val\"}" -u admin:admin http://127.0.0.1:8000/api/input/demand/a_demand_id/

::

   curl -X PUT -H "Content-Type: application/json; charset=UTF-8" --data @json_records_file.txt -u admin:admin http://127.0.0.1:8000/api/input/demand/a_demand_id/

PUT requires all fields so "key:val" pairs should be separated by a comma, so it is probably easier if you upload the data from a file like in the POST example.

To PUT/PATCH multiple DEMAND records in JSON format:

::

   curl -X PATCH -H "Content-Type: application/json; charset=UTF-8" -d "[{\"name\":\"a_demand_id1\",\"key\":\"val\"},{\"name\":\"a_demand_id2\",\"key\":\"val\"}]" -u admin:admin http://127.0.0.1:8000/api/input/demand/

::

   curl -X PUT -H "Content-Type: application/json; charset=UTF-8" --data @json_records_file.txt -u admin:admin http://127.0.0.1:8000/api/input/demand/

DEMAND primary key field is ``name``, so for a PATCH request this field must be present in each object.
PUT requires all fields in a  so "key:val" pairs should be separated by a comma, so it is probably easier if you upload the data from a file like in the POST example.


To DELETE records a safeguard is in place that prevents deleting all records in a table.
So the DELETE request requires that the number of records to be deleted is lower than the number of all records in the table.
A DELETE request for one or more records can be done with:

::

   curl -X DELETE -H "Content-Type: application/json; charset=UTF-8" -u admin:admin http://127.0.0.1:8000/api/input/demand/?source=ERP
