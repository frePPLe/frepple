=========================
Creating an extension app
=========================

The section describes how you can create a extension app that extends and
customizes the user interface.

The steps outline here are a short and very brief summary of how applications
are developed in the Django web application framework. Check out
https://www.djangoproject.com for more information and an excellent tutorial.

#. | **Create the app folder**:
   | An app is structured as a Python module that needs to follow a specific
     structure.
   | You can create a skeleton structure for your app by unzipping this file.

   :download:`Download zip-file with sample extension <my-app.zip>`

#. | **Register your app**:
   | In the file djangosettings.py your new app needs to be added in the
     section INSTALLED_APPS.
   | It’s best to put your app *before* all standard apps, so you can
     override any of the standard templates and functionality.

#. | **Define the database models**:
   | Edit the file models.py to describe the new database models you require.
   | The database table and its indexes are created with the following two
     commands. The first one generates an incremental database update script.
     The second one executes the migration generated in the first step.

   ::

      frepplectl makemigrations
      frepplectl migrate

#. | **Register the new models in the admin**:
   | You’ll need to edit the file admin.py.
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
