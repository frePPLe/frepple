Installation and configuration
------------------------------

* | **Installation**

The connector can be downloaded from the `Odoo apps store <https://apps.odoo.com/apps/modules/19.0/frepple>`_.
The connector is available for free and can be installed directly from the Odoo interface.
The connector is available for the last 3 versions of Odoo (currently the 17, 18 and 19).
With each new Odoo version, we update the connector to ensure it works with the latest Odoo version.

Once installed, the connector will add menus, tables and fields to your Odoo instance.
The frepple settings should be correctly configured to ensure the connector works correctly with the
Advanced Planning and Scheduling Service.

* | **Configuration**
  | By default, the frePPLe settings in Odoo are set to the following parameters:

    * **frePPLe server**: ``https://odoo.frepple.com``
    * **Webtoken key**: ``advanced_planning_and_scheduling_service``

    Your Odoo instance must also be accessible from the internet. The advanced planning and scheduling service needs to
    reach your Odoo instance to send the recommendations back. Local or private network
    installations that are not exposed to the internet will not work with this feature.


* **Configuring access rights**

  Out of the box, the connector will grant only the root and admin users
  access to the recommendations. Others users need to be explicitly granted access.

  * | In odoo, you allow people to access frepple by granting the "frepple user" access
      right.
    | The access is not granted by default.
    | You'll need to switch to developer mode to edit this access right.

  * | All Odoo users with the "frepple user" permission are automatically synchronised
      with frepple.

