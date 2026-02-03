Installation and configuration
------------------------------

.. important::

   This page applies to Odoo 19.
   See `this page <../odoo-before-v19/installation-and-configuration.html>`_ for earlier versions.

The connector has 2 components:

* | An Odoo addon:
  | All mapping logic between the Odoo and frePPLe data models is in this
    module. The results are accessible on the URL http://odoo_host/frepple/xml
    from which the planning engine will read data in its native XML data format
    and to which it will post the results.

* | A frePPLe addon:
  | This module gives frePPLe the capability to connect to Odoo, read the data
    from it, and publish back the results.
  | It also activates additional menus in the frePPLe user interface.

The section below describes the installation and configuration of these.

* **Configuring the connector - Odoo side**

  * | **Install the Odoo addon**
    | The addon code is found in the github repository https://github.com/frePPLe/odoo.
      Use the branch from the subfolder matching your Odoo version.
    | The addon is also available from the `odoo app store <https://apps.odoo.com/apps/modules/16.0/frepple/>`_

  * | **Configure the Odoo server**
    | If your Odoo instance is running in multi-database mode you need to
      add the frePPLe addon as a server wide module. This is achieved by updating an
      option in the Odoo configuration file odoo.conf: "server_wide_modules = web,frepple"
    | You can skip this step for single-database Odoo configurations.

  * | **Configure the Odoo addon**
    | The module adds some configuration on the company. You can edit these
      from the company edit form or from the settings.
    | Edit these parameters:

    * | Webtoken key:
      | A secret random string used to sign web tokens for a single signon between
        the Odoo and frePPLe web applications. Choose a string that is long enough,
        random and contains a mix of lower case characters, upper case characters
        and numbers.

    * | Calendar:
      | References a resource.calendar model that is used to define the working
        hours.
      | If left unspecified, we assume 24*7 availability.

    * | Manufacturing warehouse:
      | The connector assumes each company has only a single manufacturing
        location.
      | All bills of materials are modeled there.

    * | Frepple server:
      | URL of your frepple server.
      | Do not include a slash at the end of the URL.

    * | Respect reservations:
      | When this flag is checked, frepple fully respects the material
        reservations of odoo. Frepple only plans with the unreserved materials.
      | When this flag is false, frepple plans with the full material availability
        regardless of any reserved quantities in odoo. The implicit assumption is
        that any reservations will be unreserved in Odoo when needed.

    .. image:: _images/odoo-settings.png
       :alt: Configuring the Odoo add-on.

  * | **Review time zone setting**
    | The time zone preference of the Odoo user utilized by the connector is important.
      Odoo sends all dates to frepple converted to this timezone, and frepple returns dates
      in this timezone.

  * | You can run a **quick test** of the above by opening a web browser to the URL
      http\://<host>:<port>/frepple/xml?database=<db>&language=<language>&company=<company>.
      The parameters db and company determine which Odoo database to connect to.
    | After providing the login details, an XML document will be displayed with
      the data that frePPLe will read from Odoo.
    | Note that sometimes, for large Odoo dataset, the above link can return an error because of a timeout
      issue. If that is happening, you need to update parameters *limit_time_cpu* and *limit_time_real*
      in the Odoo configuration file and increase their value.

  * | **Odoo tuning**
    | The frepple connector is an atypical addon that may require some adjustments on your
      Odoo configuration. It can run for a few minutes and return a large output to the client.
    | To accomodate this traffic, you'll need to review:

    * | Assure the limit_time_cpu and limit_time_real are configured correctly in your Odoo config file.
        If the threshold is too short, Odoo will abort the connector before its done.

    * | When using a nginx proxy in before your Odoo server, assure that the max_response_body_size
        allows big datasets to be returned to the client.

    * | We strongly recommend using a separate PostgreSQL database cluster for frepple. This is 1)
        because Odoo and frepple require different database tuning, and 2) you want both applications
        to be running fully independent.

  * | **Connector development mode**
    | To speed up development of the Odoo connector, you can configure the connector to read
      the inbound and outbound files directly from github.
    | This speeds up your developments, since it skips redeploying the connectors after
      each commit on your Odoo connector github repository.

    | To enable this option, you need to uncomment and edit two sections in the frepplexml.py file.

    * https://github.com/frePPLe/odoo/blob/db24d8b4f882e594b02840f549532e356da4e1dd/frepple/controllers/frepplexml.py#L274
    * https://github.com/frePPLe/odoo/blob/db24d8b4f882e594b02840f549532e356da4e1dd/frepple/controllers/frepplexml.py#L351

    | You should enable this option with github repositories you can trust 100%. Using it with
      repositories you don't control is a big security risk, since it allows anyone to run arbitrary
      code on your Odoo server.

* **Configuring the connector - frePPLe side**

  * | **Edit the frePPLe configuration file /etc/frepple/djangosettings.py**

    * | Assure that the "freppledb.odoo" is included in the setting
        INSTALLED_APPS which defines the enabled extensions. By default
        it is disabled.

    * | Update the DATABASE section such that the SECRET_WEBTOKEN_KEY setting of each
        scenario is equal to the web token key configured in Odoo.

  * **Configure parameters**

    | Some parameters need to be configured in the "admin / parameters" screen. The
      first 5 parameters absolutely need editing, while the remaining parameters optionally
      need modification.
    | To ease deployments and improved security these settings can be configurated in the
      djangosettings.py file or passed as environment environments to the docker container.

    * | odoo.url:
      | URL of the Odoo server.

    * | odoo.db:
      | Odoo database to connect to.
      | The parameter can be left blank for Odoo setups with a single database.

    * | odoo.user:
      | Odoo user for the connection.

    * | odoo.password:
      | Password for the connection (or even better, an API key of the Odoo user).

    * | odoo.company:
      | Company name for which to create purchase quotation and
        manufacturing orders.

    * | odoo.singlecompany:
      | When false (the default) the connector downloads all allowed companies for the Odoo integration
        user.
      | When true the connector only downloads the data of the configured odoo.company.

    * | odoo.allowSharedOwnership:
      | By default records read from Odoo aren't editable in frepple. You loose your
        edits with every run of the connector.
      | If this flag is set to true you can override the Odoo data if the source field
        of the overridden records is also edited.

    * | odoo.delta:
      | Only sales order lines with a write date greater than current date minus odoo.delta days will be pulled.
        Default:999 (Pull entire demand history)
      | For the first import, this parameter should be left to its default value (999) to import all the Odoo
        sales orders into frePPLe.
      | The value of parameter odoo.delta can then be reduced to only import sales orders with a last modified
        date within the last odoo.delta days.
      | The usage of this parameter can significantly shorten the duration of the import Odoo workflow for
        companies with a significant number of sales order records.

* **Configuring access rights**

  Out of the box, the integrated solution will grant only the root and admin users
  access to all frepple functionality. Others users need to be explicitly granted access.

  * | In odoo, you allow people to access frepple by granting the "frepple user" access
      right.
    | The access is not granted by default.
    | You'll need to switch to developer mode to edit this access right.

  * | All Odoo users with the "frepple user" permission are automatically synchronised
      with frepple.
    | Of course, you can add additional users in frepple beyond these Odoo users.

  * | These Odoo users are added to the "odoo users" group in frepple. The members of
      that group get complete permissions in frepple.
    | You can change the default permissions of the group.
    | You can also grant additional priviliges to a user beyond the privileges of the group.
    | The permissions are only synchronized in the default, main scenario in frepple.
