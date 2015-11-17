============================
Detail API from your browser
============================

In the "Detail API for [model name]",
you will see the request that was made to the rest framework
(for a single record of the database table),

the headers from the HTTP response,

and a text box with the record HTTP response content.

In the bottom, depending on your permissions, you will see a menu with different options.

In this menu you may issue a new GET request on JSON or API formats.

You may also also issue a OPTIONS request to see what values are accepted on the fields.

If you have permissions you to add records you will also see three more menu options.

The third option will show an HTML form that you can send in a PUT request in the case of changing a single record in the database.

The fourth will allow you to send either PUT or PATCH requests to the database by changing the information in the text area.
Here you can also select the format "application/json", "application/x-www-form-urlencoded" or "multipart/form-data".

The fifth and last option is to delete the record from the database.

.. image:: ../_images/api_detail.png
   :alt: REST detail API
