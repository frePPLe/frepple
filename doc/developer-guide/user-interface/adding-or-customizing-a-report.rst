==============================
Adding or customizing a report
==============================

This section describes the different steps to add a new report (or update an
existing one) in the user interface. We’ll describe both the general case
as well as the generic view provided by frePPLe.

The steps outline here are a short and very brief summary of how screens
are developed in the Django web application framework. Check out
https://www.djangoproject.com for more information and an excellent tutorial.

For clarity and ease of maintenance it is recommended to always add your
reports in :doc:`a custom extension app <creating-an-extension-app>`.

General case
------------

As an example we’ll create a report to display some statistics on the size
of your model. It will simply display the total number of buffers and operations
in your model.

#. | **Create a view to generate the data**.
   | A view function retrieves the report data from the database (or computes
     it from another source) and passes a data dictionary with the data to
     the report template.
   | A view is a Python function. Here’s the view required for our example,
     which you can put in a file statistics.py:

   ::

      from freppledb.input.models import *
      from django.shortcuts import render_to_response
      from django.template import RequestContext
      from django.contrib.admin.views.decorators import staff_member_required

      @staff_member_required
      def MyStatisticsReport(request):
        countOperations = Operation.objects.using(request.database).count()
        countBuffers = Buffer.objects.using(request.database).count()
        return render_to_response('statistics.html',
          RequestContext(request, {
            'numOperations': countOperations,
            'numBuffers': countBuffers,
            'title': 'Model statistics',
          }))

   | The function decorator staff_member_required is used to assure users
     are authenticated properly.
   | Notice how the first 2 statements in the function use the Django
     relational mapping to pick the data from the database. This code
     is translated by the framework in SQL queries on the database.
   | The last line in the function passes the data in a dictionary to the
     Django template engine. The template engine will generate the HTML
     code returned to the user's browser.

#. | **Create a template to visualize the data**.
   | The template file statistics.html will define all aspects of the
     visualizing the results.
   | The file templates/statistics.html for our example looks like this:

   ::

       {% extends "admin/base_site_nav.html" %}
       {% load i18n %}
       {% block content %}
       <div id="content-main">
       {% trans 'Number of operations:' %} {{numOperations}}<br>
       {% trans 'Number of buffers:' %} {{numBuffers}}<br>
       </div>
       {% endblock %}

   Templates are inheriting from each other. In this example we inherit
   from the base template which already contains the navigation toolbar
   and the breadcrumbs trail. We only override the block which contains
   the div-element with the main content.

   Templates use special tags to pick up data elements or to call special
   functions. The {{ }} tag is used to refer to the data elements provided
   by the view function. The {% trans %} tag is used to mark text that
   should be translated into the different languages for the user interface.

#. | **Map the view as a URL**.
   | To expose the view as a URL to the users you’ll need to map it to a
     URL pattern.

   Edit the definition of the urlpatterns variable in the file urls.py to
   set up a URL for this example:

   ::

      urlpatterns = patterns('',
       ...
       (r'^statistics.html$', 'statistics.MyStatisticsReport'),
       )

#. | **Update the menu structure**.
   | You’ll want to add the report also to a menu.

   The following lines in this file menu.py will do this:

   ::

      from django.utils.translation import ugettext as _
      from freppledb.menu import menu
      menu.addItem("admin", "statistics", url="/statistics.html",
        label=_('Model statistics'), index=900)

Using the frePPLe generic report
--------------------------------

FrePPLe uses a standard view for displaying data in a list or grid layout,
respectively called ListReport and TableReport. With these views you can add
new reports with with less code and more functionality (such as sorting,
filtering, pagination, export and import).

The steps for adding the view are slightly different from the generic case.

#. | **Define a report class**
   | Instead of defining a view function we define a class with the report
     metadata. See the definition of the report base classes in the file
     common/report.py to see all available options for the metadata classes.

   | For a list report this class has the following structure:

   ::

      from freppledb.common.report import *

       class myReportClass(ListReport):
         template = 'myreporttemplate.html'
         title = 'title of my report'
         basequeryset = ... # A query returning the data to display
         frozenColumns = 1
         rows = (
           ('field1', {
             'filter': FilterNumber(operator='exact', ),
             'title': _('field1'),
             }),
           ('field2', {
             'filter': FilterText(size=15),
             'title': _('field2')}),
           ('field3', {
             'title': _('field3'),
             'filter': FilterDate(),
             }),
           )

   | For a table report this class has the following structure:

   ::

      from freppledb.common.report import *

      class myReportClass(TableReport):
        template = 'myreporttemplate.html'
        title = 'title of my report'
        basequeryset = ... # A query returning the data to display
        model = Operation
        rows = (
          ('field1',{
            'filter': FilterNumber(operator='exact', ),
            'title': _('field1'),
            }),
          )
        crosses = (
          ('field2', {'title': 'field2',}),
          ('field3', {'title': 'field3',}),
          )
        columns = (
          ('bucket',{'title': _('bucket')}),
          )

        @staticmethod
        def resultlist1(request, basequery, bucket, startdate, enddate, sortsql='1 asc'):
          ... # A query returning the data to display as fixed columns on the left hand side.

        @staticmethod
        def resultlist2(request, basequery, bucket, startdate, enddate, sortsql='1 asc'):
          ... # A query returning the data to display for all cells in the grid.

#. | **Create a template to visualize the data**.

   | For a list report the template has the following structure:

   ::

      {% extends "admin/base_site_list.html" %}
      {% load i18n %}

      {% block frozendata %}
      {% for i in objectlist1 %}
      <tr>
      <td>{{i.field1}}</td>
      </tr>{% endfor %}
      {% endblock %}

      {% block data %}
      {% for i in objectlist1 %}
      <tr>
      <td>{{i.field2}}</td>
      <td>{{i.field3}}</td>
      </tr>{% endfor %}
      {% endblock %}

   For a grid report the template is identical, except that you need to inherit
   from the admin/base_site_table.html template.

#. | **Map the view as a URL**.
   | The syntax for adding a report now refers to the generic view, and we pass
     the report class as an argument

   ::

      urlpatterns = patterns('',
       ...
       (r'^myreport/([^/]+)/$', 'freppledb.common.report.view_report',
         {'report': myReportClass,}),
       ...
       )

#. | **Update the menu structure**.
   | This step is identical to the general case.
