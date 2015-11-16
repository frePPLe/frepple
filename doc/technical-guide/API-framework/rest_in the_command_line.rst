=============
API framework
=============

You are not obliged to use the web browser to work with the REST API framework of frePPLE.

If you install tolls like "curl", "wget" or similar you can use the command line to (depending on your permissions) see/add/delete/modify data.

To just get a list of all sales orders in JSON format:

::

   wget --http-user=admin --http-password=admin http://127.0.0.1:8000/api/input/demand/?format=json

::

   curl -H 'Accept: application/json; indent=4' -u admin:admin http://127.0.0.1:8000/api/input/demand/?format=json


To just get a list of all sales orders in API format (assuming the user is named "admin" and that the password is also "admin":

::

   wget --http-user=admin --http-password=admin http://127.0.0.1:8000/api/input/demand/?format=api

::

   curl -H 'Accept: application/json; indent=4; charset=UTF-8' -u admin:admin http://127.0.0.1:8000/api/input/demand/?format=api


To POST/PATCH/PUT in JSON format it is also straightforward:

::

   curl -X POST -H "Content-Type: application/json; charset=UTF-8" -d '{\"key\":\"val\"}' -u admin:admin http://127.0.0.1:8000/api/input/demand/?format=json

"key:val" pairs should be separated by a comma, so it is probably easier if you store the data in a file:

::

   curl -X POST -H "Content-Type: application/json; charset=UTF-8" --data @json_records_file.txt -u admin:admin http://127.0.0.1:8000/api/input/demand/?format=json

