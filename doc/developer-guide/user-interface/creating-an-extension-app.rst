=========================
Creating an extension app
=========================

The section describes how you can create a extension app that extends and
customizes the data model and the user interface.

This page outlines the steps involved in creating a custom app and 
explore the capabilities to tailor frePPLe to your business needs and 
process.

:ref:`runplan`

#. | **Prerequisites**:
   | You will need to be familiar with the
     `Python programming language <http://python.org/>`_ to complete this
     tutorial.
   | Knowledge of HTML and SQL is also needed to understand how your app
     works within the frePPLe framework.

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
          "freppledb.input.models.Item",  # Class we are extending
          [
              (
                  "attribute_1",  # Field name in the database
                  _("first attribute"),  # Human readable label of the field
                  "number",  # Type of the field.
                  True,  # Is the field editable?
                  True,  # Should the field be visible by default?
              )
          ],
      )
      ...

   | This file only declares the model structure. The actual database field will be 
     created in a following step.
   
#. | **Define the database models**:
   | The file **models.py** describes new database models.
     It defines the database tables, their fields and indexes.

   .. code-block:: Python
     
      class My_Model(AuditModel):
          # Database fields
          name = models.CharField(_("name"), max_length=300, primary_key=True)
          charfield = models.CharField(
              _("charfield"),
              max_length=300,
              null=True,
              blank=True,
              help_text=_("A sample character field"),
          )
          booleanfield = models.BooleanField(
              _("booleanfield"),
              blank=True,
              default=True,
              help_text=_("A sample boolean field"),
          )
          decimalfield = models.DecimalField(
              _("decimalfield"),
              max_digits=20,
              decimal_places=8,
              default="0.00",
              help_text=_("A sample decimal field"),
          )
      
          class Meta(AuditModel.Meta):
              db_table = "my_model"  # Name of the database table
              verbose_name = _("my model")  # A translatable name for the entity
              verbose_name_plural = _("my models")  # Plural name
              ordering = ["name"]

   | This file only declares the model structure. The actual table will be created in a
     later step.
   
   | You can find all details on models and fields on 
     https://docs.djangoproject.com/en/2.2/ref/models/fields/
        
#. | **Create tables and fields in the database**:
   | In the previous steps all models and attributes were defined. Now we create
     them in the PostgreSQL database. This is done by running the following statement
     on the command line:
   
    .. code-block::

      # Deployment script to apply database schema updates - run by system administrators
      frepplectl migrate

   | This command will incrementally bring the database schema up to date. The database
     schema migration allows upgrading between different versions of frePPLe without
     loss of data and without recreating the database from scratch. The database migrations
     also allow to incrementally update the database with new versions of your app.
    
   | Migration scripts are Python scripts, located in the **migrations** folder. The scripts
     are generated mostly automatic with the command line below. More complex migrations will
     need review and/or coding by developers.
    
   .. code-block::
      
      # Generate a skeleton migration script - run by developers only
      frepplectl makemigrations my_app
    
   .. code-block:: Python
   
      class Migration(AttributeMigration):
      
          # Module owning the extended model
          extends_app_label = "input"
      
          # Defines migrations that are prerequisites for this one
          dependencies = [("my_app", "0001_initial")]
      
          # Defines the migration operation to perform: such as CreateModel, AlterField,
          # DeleteModel, AddIndex, RunSQL, RunPython, etc...
          operations = [
              migrations.AddField(
                  model_name="item",
                  name="attribute_1",
                  field=models.DecimalField(
                      blank=True,
                      db_index=True,
                      decimal_places=8,
                      max_digits=20,
                      null=True,
                      verbose_name="first attribute",
                  ),
              )
          ]

   | You can find all details on migrations on 
     https://docs.djangoproject.com/en/2.2/topics/migrations/

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
   | In the subfolder **fixtures** you can define demo datasets that can
     be loaded with the command "frepplectl loaddata" or `interactively
     in the execution screen <user-guide/command-reference.html#loaddata>`_.

   | Fixtures are text files in JSON format.
   
   .. code-block:: JSON
   
      [
      {"model": "my_app.my_model", "fields": {"name": "sample #1", "charfield": "A", "booleanfield": true, "decimalfield": 999.0}},
      {"model": "my_app.my_model", "fields": {"name": "sample #2", "charfield": "B", "booleanfield": false, "decimalfield": 666.0}}
      ]

      
#. | **Customize the planning script**:
   | The script commands.py is executed by the planning engine to generate a
     plan.
   | You can creating a customized version in your app to add customized
     planning steps.
   | Note that this is not standard Django functionality, but specific to
     frePPLe.
     
#. | **Add custom commands**:
   | Files in the folder **management/commands** define extra commands.
   | You can execute the custom commands from the command line, through a
     web API or interactively from the execution screen.

   ::

      # Run from the command line
      frepplectl my_command
      
   ::
   
      # Web API of the command
      POST /execute/api/my_command/
   
   .. image:: ../_images/my_command.png
      :alt: Custom command in the executio screen
   
   Simplified, the code for a command looks as follows:
   
   .. code-block:: Python

      class Command(BaseCommand):
          # Help text shown when you run "frepplectl help my_command"
          help = "This command does ..."
      
          # Define optional and required arguments
          def add_arguments(self, parser):
              parser.add_argument(
                  "--my_arg",
                  dest="my_arg",
                  type=int,
                  default=0,
                  help="an optional argument for the command",
              )
           
          # The busisness logic of the command goes in this method
          def handle(self, *args, **options):
              print("This command was called with argument %s" % options["my_arg"])
      
          # Label to display on the execution screen
          title = _("My own command")
      
          # Sequence of the command on the execution screen
          index = 1
      
          # This method generates the text to display on the execution screen
          @staticmethod
          def getHTML(request):
              context = RequestContext(request)
              template = Template(
                  """
                  {% load i18n %}
                  <form class="form" role="form" method="post"
                     action="{{request.prefix}}/execute/launch/my_command/">{% csrf_token %}
                  <table>
                  <tr>
                    <td style="padding:15px; vertical-align:top">
                    <button  class="btn btn-primary" id="load" type="submit">{% trans "launch"|capfirst %}</button>
                    </td>
                    <td style="padding:15px">
                    A description of my command
                    </td>
                  </tr>
                  </table>
                  </form>
                  """
              )
              return template.render(context)
              
   | You can find more detailed information on 
     https://docs.djangoproject.com/en/2.2/howto/custom-management-commands/

#. | **Add dashboard widgets**:
   | You can define new widgets in a file **widget.py**. Explore some existing
     widgets to see how the simple structure of such widgets.

#. | **Add unit tests**:
   | Unit tests are defined in the file **tests.py**.
   | They are executed when you run the command:

   ::

      # Run the test
      frepplectl test my_app

   The code for a test looks as follows:
   
   .. code-block:: Python
   
   

#. | **More information!**:
   | FrePPLe is based on django web application framework. You can dig deeper
     by visiting https://www.djangoproject.com, checking out the full documentation
     and follow a tutorial.
   | Another good approach is to study the way the standard apps in frePPLe
     are structured. The full source code of the Community Edition is on 
     https://github.com/frePPLe/frepple/tree/master/freppledb