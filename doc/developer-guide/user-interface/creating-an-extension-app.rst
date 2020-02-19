=========================
Creating an extension app
=========================

The section describes how you can create a extension app that extends and
customizes the data model and the user interface.

This page outlines the steps involved in creating a custom app and 
explore the capabilities to tailor frePPLe to your business needs and 
process.

#. You will need to be familiar with the 
   `Python programming language <http://python.org/>`_ to complete this
   tutorial.
   
#. | **Create the app folder**:
   | An app is structured as a Python module that needs to follow a specific
     structure.
   | You can create a skeleton structure for your app by unzipping this file.
     and place its contents under the freppledb folder.

   :download:`Download zip-file with sample extension <my-app.zip>`

   .. code-block::

      my-app
         |- __init__.py
         |- models.py
         |- admin.py
         |- attributes.py
         |- migrations
         |   |- __init__.py
         |   |- 0001-initial.py
         |   |- 0002-attributes.py
         |- urls.py
         |- views.py
         |- menu.py
         |- commands.py
         |- tests.py
         |- templates
         |   |- ...
         |- management
             |- __init__.py
             |- commands
                 |- __init__.py
                 |- mycommand.py

#. | **Register your app**:
   | In the file **djangosettings.py** your new app needs to be added in the
     section INSTALLED_APPS.
   | The ordering of the apps is important - apps higher in the list can
     override functionality of apps lower in the list. Insert your app
     at the location indicated in the file.

   .. code-block:: Python
     
      INSTALLED_APPS = (
          "django.contrib.auth",
          "django.contrib.contenttypes",
          "django.contrib.messages",
          "django.contrib.staticfiles",
          "bootstrap3",
          "freppledb.boot",
          # Add any project specific apps here
          "freppledb.myapp",  # <<<< HERE'S OUR APP
          # "freppledb.odoo",
          # "freppledb.erpconnection",
          "freppledb.input",
          "freppledb.output",
          "freppledb.metrics",
          "freppledb.execute",
          "freppledb.common",
          "django_filters",
          "rest_framework",
          "django_admin_bootstrapped",
          "django.contrib.admin",
          # The next two apps allow users to run their own SQL statements on
          # the database, using the SQL_ROLE configured above.
          "freppledb.reportmanager",
          # "freppledb.executesql",
      )

#. | **Extend existing models.**:
   | The file **attributes.py** defines new fields that extend the standard
     data model. For instance, pretty much every implementation has some
     specifi item characteristics which the planner would like to see. 
   
   .. code-block:: Python
   
      ...
      registerAttribute(    
          "freppledb.input.models.Item", # Class we are extending
          [
              (
                  "attribute_1",         # Field name in the database
                  _("first attribute"),  # Human readable label of the field
                  "number",              # Type of the field.
                  True,                  # Is the field editable?
                  True,                  # Should the field be visible by default?
              ),
          ],
      )   
      ...

   | This file only declares the model structure. The actual table will be created in a
     later step.
   
#. | **Define the database models**:
   | The file **models.py** describes new database models.
     It defines the database tables, their fields and indexes.

   .. code-block:: Python
     
      class My_Model(AuditModel):
        # Database fields
        name = models.CharField(_('name'), max_length=settings.NAMESIZE, primary_key=True)
        charfield = models.CharField(_('charfield'), max_length=settings.DESCRIPTIONSIZE, null=True,
          blank=True, help_text= _('A sample character field'))
        booleanfield = models.BooleanField(_('booleanfield'), blank=True, default=True,
          help_text= _('A sample boolean field'))
        decimalfield = models.DecimalField(_('decimalfield'), max_digits=settings.MAX_DIGITS,
          decimal_places=settings.DECIMAL_PLACES, default='0.00',
          help_text= _('A sample decimal field')
          ) 
      
        class Meta(AuditModel.Meta):
          db_table = 'my_model'                 # Name of the database table
          verbose_name = _('my model')          # A translatable name for the entity
          verbose_name_plural = _('my models')  # Plural name
          ordering = ['name']

   | This file only declares the model structure. The actual table will be created in a
     later step.
   
   | You can find all details on models and fields on 
     https://docs.djangoproject.com/en/2.2/ref/models/fields/
        
#. | **Create the fields in the database**:
   | In the previous steps all models and attributes were defined. In this step we create
     them in the PostgreSQL database.   
   | The database table and its indexes are created with the following two
     commands. The first one generates an incremental database update script.
     The second one executes the migration generated in the first step.

   | You can find all details on migrations on 
     https://docs.djangoproject.com/en/2.2/topics/migrations/
   ::

      frepplectl makemigrations
      frepplectl migrate

#. | **Register the new models in the admin**:
   | You'll need to edit the file admin.py.
   | FrePPLe uses 2 admin sites by default: freppledb.admin.data_admin for
     model input data, and freppledb.admin.admin_site for models that are
     normally used only by system administrators.

#. | **Create or override HTML template pages**:
   | The web pages are rendered from a set of HTML templates. Create a
     template folder in your new app to store your templates. In the file
     djangosettings.py this folder needs to be added *before* the other
     entries (in this way your override is used instead of the standard file).

   | For instance, you can copy the file admin/base_site.html into your
     template folder, and edit the line shown below with the name and logo
     of your company.

   ::

     {% block branding %}frePPLe {% version %}{% endblock %}

#. | **Define new reports**:
   | New reports are normally defined in a file views.py or as files in a
     folder called views.
   | See :doc:`this page <adding-or-customizing-a-report>` for more details
     on the structure of the report code.

#. | **Register the URLs of the new reports**:
   | The url where the report is published is defined in the file urls.py.

#. | **Add the reports to the menu**:
   | The menu is a defined in the file menu.py.
   | Note that the models registered in the admin automatically get added
     already in the menu.
   | Note that this menu structure is not standard Django functionality,
     but specific to frePPLe.

#. | **Add demo data**:
   | In a subfolder called fixtures you can define demo datasets that can
     be loaded with the command "frepplectl loaddata" or interactively
     in the execution screen.

#. | **Add custom commands**:
   | By creating files in the folder management/commands you can define extra
     commands.
   | You can execute the custom commands with:

   ::

      frepplectl my_command

#. | **Add dashboard widgets**:
   | You can define new widgets in a file widget.py. Explore some existing
     widgets to see how the simple structure of such widgets.
   | In the Enterprise Edition each user can create his/her own dashboard,
     by selecting the desired widgets from the available list.
   | In the Community Edition the dashboard is configuration with the setting
     DEFAULT_DASHBOARD in the file djangosettings.py.

#. | **Add unit tests**:
   | Unit tests are defined in the file tests.py.
   | They are executed when you run the command:

   ::

      frepplectl test my_app

#. | **Customize the planning script**:
   | The script commands.py is executed by the planning engine to generate a
     plan.
   | You can creating a customized version in your app to add customized
     planning steps.
   | Note that this is not standard Django functionality, but specific to
     frePPLe.

#. | **More information!**:
   | FrePPLe is based on django web application framework. You can dig deeper
     by visiting https://www.djangoproject.com, checking out the full documentation
     and follow a tutorial.
   | Another good approach is to study the way the standard apps in frePPLe
     are structured. The full source code of the Community Edition is on 
     https://github.com/frePPLe/frepple/tree/master/freppledb