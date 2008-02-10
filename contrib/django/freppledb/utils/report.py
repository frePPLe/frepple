#
# Copyright (C) 2007 by Johan De Taeye
#
# This library is free software; you can redistribute it and/or modify it
# under the terms of the GNU Lesser General Public License as published
# by the Free Software Foundation; either version 2.1 of the License, or
# (at your option) any later version.
#
# This library is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU Lesser
# General Public License for more details.
#
# You should have received a copy of the GNU Lesser General Public
# License along with this library; if not, write to the Free Software
# Foundation Inc., 59 Temple Place, Suite 330, Boston, MA 02111-1307, USA
#

# file : $URL$
# revision : $LastChangedRevision$  $LastChangedBy$
# date : $LastChangedDate$

from datetime import date, datetime
from email.Utils import formatdate
from calendar import timegm
import csv

from django.core.paginator import ObjectPaginator, InvalidPage
from django.shortcuts import render_to_response
from django.contrib.admin.views.decorators import staff_member_required
from django.template import RequestContext, loader
from django.db import models, transaction, connection
from django.db.models.fields.related import ForeignKey, AutoField
from django.http import Http404, HttpResponse, HttpResponseRedirect, HttpResponseForbidden, HttpResponseNotModified
from django.conf import settings
from django.utils.encoding import smart_str
from django.utils.translation import ugettext as _
from django.utils.html import escape
from django.utils.safestring import mark_safe
from django.utils.text import capfirst

from input.models import Plan
from utils.db import python_date


# Parameter settings
ON_EACH_SIDE = 3       # Number of pages show left and right of the current page
ON_ENDS = 2            # Number of pages shown at the start and the end of the page list

# A variable to cache bucket information in memory
datelist = {}

# Operators used for the date and number filtering in the reports
IntegerOperator = {
  'lte': '&lt;=',
  'gte': '&gt;=',
  'lt': '&lt;&nbsp;',
  'gt': '&gt;&nbsp;',
  'exact': '==',
  }

# Operators used for the text filtering in the reports
TextOperator = {
  'icontains': 'i in',
  'contains': 'in',
  'istartswith': 'i starts',
  'startswith': 'starts',
  'iendswith': 'i ends',
  'endswith': 'ends',
  'iexact': 'i is',
  'exact': 'is',
  }

# URL parameters that are not query arguments
reservedParameters = ('o', 'p', 'reporttype', 'pop', 'reportbucket', 'reportstart', 'reportend')

class Report(object):
  '''
  The base class for all reports.
  The parameter values defined here are used as defaults for all reports, but
  can be overwritten.
  '''
  # Points to templates to be used for different output formats
  template = {}
  # The title of the report. Used for the window title
  title = ''
  # The default number of entities to put on a page
  paginate_by = 25

  # The resultset that returns a list of entities that are to be
  # included in the report.
  basequeryset = None

  # Whether or not the breadcrumbs are reset when we open the report
  reset_crumbs = True

  # Extra javascript files to import for running the report
  javascript_imports = []

  # Specifies which column is used for an initial filter
  default_sort = '1a'

  # A model class from which we can inherit information.
  model = None

  # Allow editing in this report or not
  editable = True


class ListReport(Report):
  '''
  Row definitions.

  Supported class methods:
    - lastmodified():
      Returns a datetime object representing the last time the report content
      was updated.
    - resultquery():
      Returns an iterable that returns the data to be displayed.
      If not specified, the basequeryset is used.

  Possible attributes for a row field are:
    - filter:
      Specifies a widget for filtering the data.
    - order_by:
      Model field to user for the sorting.
      It defaults to the name of the field.
    - title:
      Name of the row that is displayed to the user.
      It defaults to the name of the field.
    - sort:
      Whether or not this column can be used for sorting or not.
      The default is true.
    - javascript_imports:
      Extra javascript files to import for running the report
  '''
  rows = ()

  # A list with required user permissions to view the report
  permissions = []


class TableReport(Report):
  '''
  Row definitions.

  Supported class methods:
    - lastmodified():
      Returns a datetime object representing the last time the report content
      was updated.
    - resultquery():
      Returns an iterable that returns the data to be displayed.
      If not specified, the basequeryset is used.

  Possible attributes for a row field are:
    - filter:
      Specifies a widget for filtering the data.
    - order_by:
      Model field to user for the sorting.
      It defaults to the name of the field.
    - title:
      Name of the row that is displayed to the user.
      It defaults to the name of the field.
    - sort:
      Whether or not this column can be used for sorting or not.
      The default is true.
    - javascript_imports:
      Extra javascript files to import for running the report
  '''
  rows = ()

  # Cross definitions.
  # Possible attributes for a row field are:
  #   - title:
  #     Name of the cross that is displayed to the user.
  #     It defaults to the name of the field.
  #   - editable:
  #     True when the field is editable in the page.
  #     The default value is false.
  crosses = ()

  # Column definitions
  # Possible attributes for a row field are:
  #   - title:
  #     Name of the cross that is displayed to the user.
  #     It defaults to the name of the field.
  columns = ()

  # A list with required user permissions to view the report
  permissions = []


@staff_member_required
def view_report(request, entity=None, **args):
  '''
  This is a generic view for two types of reports:
    - List reports, showing a list of values are rows
    - Table reports, showing in addition values per time buckets as columns
  The following arguments can be passed to the view:
    - report:
      Points to a subclass of Report.
      This is a required attribute.
    - extra_context:
      An additional set of records added to the context for rendering the
      view.
  '''

  # Pick up the report class
  global reservedParameters;
  reportclass = args['report']
  model = reportclass.model

  # Process uploaded data files
  if request.method == 'POST':
    if not reportclass.model or "csv_file" not in request.FILES:
      request.user.message_set.create(message=_('Invalid upload request'))
      return HttpResponseRedirect(request.get_full_path())
    if not reportclass.editable or not request.user.has_perm('%s.%s' % (model._meta.app_label, model._meta.get_add_permission())):
      request.user.message_set.create(message=_('Not authorized'))
      return HttpResponseRedirect(request.get_full_path())
    (warnings,errors) = parseUpload(request, reportclass, request.FILES['csv_file']['content'])
    if len(errors) > 0:
      request.user.message_set.create(message=_('File upload aborted with errors'))
      for i in errors: request.user.message_set.create(message=i)
    elif len(warnings) > 0:
      request.user.message_set.create(message=_('Uploaded file processed with warnings'))
      for i in warnings: request.user.message_set.create(message=i)
    else:
      request.user.message_set.create(message=_('Uploaded data successfully'))
    return HttpResponseRedirect(request.get_full_path())

  # Verify if the page has changed since the previous request
  lastmodifiedrequest = request.META.get('HTTP_IF_MODIFIED_SINCE', None)
  try:
    lastmodifiedresponse = reportclass.lastmodified().replace(microsecond=0)
    lastmodifieduser = request.user.get_profile().lastmodified.replace(microsecond=0)
    if lastmodifieduser and lastmodifieduser > lastmodifiedresponse:
      # A change of user or user preferences must trigger recomputation
      lastmodifiedresponse = lastmodifieduser
    lastmodifiedresponse = (formatdate(timegm(lastmodifiedresponse.utctimetuple()))[:26] + 'GMT')
    if lastmodifiedrequest and lastmodifiedrequest.startswith(lastmodifiedresponse):
      # The report hasn't modified since the previous request
      return HttpResponseNotModified()
  except:
    lastmodifiedresponse = None

  # Verify the user is authorirzed to view the report
  for perm in reportclass.permissions:
    if not request.user.has_perm(perm):
      return HttpResponseForbidden('<h1>%s</h1>' % _('Permission denied'))

  # Pick up the list of time buckets
  if issubclass(reportclass, TableReport):
    (bucket,start,end,bucketlist) = getBuckets(request)
  else:
    bucket = start = end = bucketlist = None
  type = request.GET.get('reporttype','html')  # HTML or CSV (table or list) output

  # Is this a popup window?
  is_popup = request.GET.has_key('pop')

  # Pick up the filter parameters from the url
  counter = reportclass.basequeryset
  fullhits = counter.count()
  if entity:
    # The url path specifies a single entity.
    # We ignore all other filters.
    counter = counter.filter(pk__exact=entity)
  else:
    # The url doesn't specify a single entity, but may specify filters
    # Convert URL parameters into queryset filters.
    for key, valuelist in request.GET.lists():
       # Ignore arguments that aren't filters
       if key not in reservedParameters:
         # Loop over all values, since the same filter key can be
         # used multiple times!
         for value in valuelist:
           if len(value)>0:
             counter = counter.filter( **{smart_str(key): value} )

  # Pick up the sort parameter from the url
  sortparam = request.GET.get('o', reportclass.default_sort)
  try:
    # Pick up the sorting arguments
    sortfield = 0
    for i in sortparam:
      if i.isdigit():
        sortfield = sortfield * 10 + int(i)
      else:
        break
    sortdirection = sortparam[-1]
    # Create sort parameters
    if sortfield == '1':
      if sortdirection == 'd':
        counter = counter.order_by('-%s' % (('order_by' in reportclass.rows[0][1] and reportclass.rows[0][1]['order_by']) or reportclass.rows[0][0]))
        sortsql = '1 desc'
      else:
        sortparam = '1a'
        counter = counter.order_by(('order_by' in reportclass.rows[0][1] and reportclass.rows[0][1]['order_by']) or reportclass.rows[0][0])
        sortsql = '1 asc'
    else:
      if sortfield > len(reportclass.rows) or sortfield < 0:
        sortparam = '1a'
        counter = counter.order_by(('order_by' in reportclass.rows[0][1] and reportclass.rows[0][1]['order_by']) or reportclass.rows[0][0])
        sortsql = '1 asc'
      elif sortdirection == 'd':
        sortparm = '%dd' % sortfield
        counter = counter.order_by(
          '-%s' % (('order_by' in reportclass.rows[sortfield-1][1] and reportclass.rows[sortfield-1][1]['order_by']) or reportclass.rows[sortfield-1][0]),
          ('order_by' in reportclass.rows[0][1] and reportclass.rows[0][1]['order_by']) or reportclass.rows[0][0]
          )
        sortsql = '%d desc, 1 asc' % sortfield
      else:
        sortparam = '%da' % sortfield
        counter = counter.order_by(
          ('order_by' in reportclass.rows[sortfield-1][1] and reportclass.rows[sortfield-1][1]['order_by']) or reportclass.rows[sortfield-1][0],
          ('order_by' in reportclass.rows[0][1] and reportclass.rows[0][1]['order_by']) or reportclass.rows[0][0]
          )
        sortsql = '%d asc, 1 asc' % sortfield
  except:
    # A silent and safe exit in case of any exception
    sortparam = '1a'
    counter = counter.order_by(('order_by' in reportclass.rows[0][1] and reportclass.rows[0][1]['order_by']) or reportclass.rows[0][0])
    sortsql = '1 asc'
    sortfield = 1
    sortdirection = 'a'

  # Build paginator
  if type[:3] != 'csv':
    page = int(request.GET.get('p', '0'))
    paginator = ObjectPaginator(counter, reportclass.paginate_by)
    counter = counter[paginator.first_on_page(page)-1:paginator.first_on_page(page)-1+(reportclass.paginate_by or 0)]

  # Construct SQL statement, if the report has an SQL override method
  if hasattr(reportclass,'resultquery'):
    if settings.DATABASE_ENGINE == 'oracle':
      # Oracle
      basesql = counter._get_sql_clause(get_full_query=True)
      sql = basesql[3] or 'select %s %s' % (",".join(basesql[0]), basesql[1])
    elif settings.DATABASE_ENGINE == 'sqlite3':
      # SQLite
      basesql = counter._get_sql_clause()
      sql = 'select * %s' % basesql[1]
    else:
      # PostgreSQL and mySQL
      basesql = counter._get_sql_clause()
      sql = 'select %s %s' % (",".join(basesql[0]), basesql[1])
    sqlargs = basesql[2]

  # HTML output or CSV output?
  if type[:3] == 'csv':
    # CSV output
    response = HttpResponse(mimetype='text/csv')
    response['Content-Disposition'] = 'attachment; filename=%s.csv' % reportclass.title.lower()
    if hasattr(reportclass,'resultquery'):
      # SQL override provided
      response._container = _generate_csv(reportclass, reportclass.resultquery(sql, sqlargs, bucket, start, end, sortsql=sortsql), type, bucketlist)
    else:
      # No SQL override provided
      response._container = _generate_csv(reportclass, counter, type, bucketlist)
    response._is_string = False
    return response

  # Create a copy of the request url parameters
  parameters = request.GET.copy()
  for x in reservedParameters:
    if x in parameters: parameters.__delitem__(x)

  # Calculate the content of the page
  if hasattr(reportclass,'resultquery'):
    # SQL override provided
    try:
      results = reportclass.resultquery(sql, sqlargs, bucket, start, end, sortsql=sortsql)
    except InvalidPage: raise Http404
  else:
    # No SQL override provided
    results = counter

  # Build the paginator html
  page_htmls = _get_paginator_html(request, paginator, page, parameters)

  # Prepare template context
  context = {
       'reportclass': reportclass,
       'model': model,
       'hasaddperm': reportclass.editable and model and request.user.has_perm('%s.%s' % (model._meta.app_label, model._meta.get_add_permission())),
       'haschangeperm': reportclass.editable and model and request.user.has_perm('%s.%s' % (model._meta.app_label, model._meta.get_change_permission())),
       'request': request,
       'objectlist': results,
       'reportbucket': bucket,
       'reportstart': start,
       'reportend': end,
       'paginator': paginator,
       'hits' : paginator.hits,
       'fullhits': fullhits,
       'is_popup': is_popup,
       'paginator_html': mark_safe(page_htmls),
       'javascript_imports': _get_javascript_imports(reportclass),
       # Never reset the breadcrumbs if an argument entity was passed.
       # Otherwise depend on the value in the report class.
       'reset_crumbs': reportclass.reset_crumbs and entity == None,
       'title': (entity and '%s %s %s' % (unicode(reportclass.title),_('for'),entity)) or reportclass.title,
       'rowheader': _create_rowheader(request, sortfield, sortdirection, reportclass),
       'crossheader': issubclass(reportclass, TableReport) and _create_crossheader(request, reportclass),
       'columnheader': issubclass(reportclass, TableReport) and _create_columnheader(request, reportclass, bucketlist),
     }
  if 'extra_context' in args: context.update(args['extra_context'])

  # Render the view, optionally setting the last-modified http header
  response = HttpResponse(
    loader.render_to_string(reportclass.template, context, context_instance=RequestContext(request)),
    )
  if lastmodifiedresponse: response['Last-Modified'] = lastmodifiedresponse
  return response


def _create_columnheader(req, cls, bucketlist):
  '''
  Generate html header row for the columns of a table report.
  '''
  # @todo not very clean and consistent with cross and row
  return mark_safe(' '.join(['<th>%s</th>' % j['name'] for j in bucketlist]))


def _create_crossheader(req, cls):
  '''
  Generate html for the crosses of a table report.
  '''
  res = []
  for crs in cls.crosses:
    title = capfirst((crs[1].has_key('title') and crs[1]['title']) or crs[0]).replace(' ','&nbsp;')
    # Editable crosses need to be a bit higher...
    if crs[1].has_key('editable'):
      if (callable(crs[1]['editable']) and crs[1]['editable'](req)) \
      or (not callable(crs[1]['editable']) and crs[1]['editable']):
        title = '<span style="line-height:18pt;">' + title + '</span>'
    res.append(title)
  return mark_safe('<br/>'.join(res))


def _get_paginator_html(request, paginator, page, parameters):
  # Django has standard some very similar code in the tags 'paginator_number'
  # and 'pagination' in the file django\contrib\admin\templatetags\admin_list.py.
  # Functionally there is no real difference. The implementation below relies
  # less on the template engine.
  global ON_EACH_SIDE
  global ON_ENDS
  page_htmls = []
  if paginator.pages <= 10 and paginator.pages > 1:
    # If there are less than 10 pages, show them all
    for n in range(0,paginator.pages):
      if n == page:
        page_htmls.append('<span class="this-page">%d</span>' % (page+1))
      elif n == 0 and len(parameters) == 0:
        page_htmls.append('<a href="%s">1</a>' % request.path)
      else:
        if n: parameters.__setitem__('p', n)
        page_htmls.append('<a href="%s?%s">%s</a>' % (request.path, escape(parameters.urlencode()),n+1))
  elif paginator.pages > 1:
      # Insert "smart" pagination links, so that there are always ON_ENDS
      # links at either end of the list of pages, and there are always
      # ON_EACH_SIDE links at either end of the "current page" link.
      if page <= (ON_ENDS + ON_EACH_SIDE):
          # 1 2 *3* 4 5 6 ... 99 100
          for n in range(0, page + max(ON_EACH_SIDE, ON_ENDS)+1):
            if n == page:
              page_htmls.append('<span class="this-page">%d</span>' % (page+1))
            elif n == 0 and len(parameters) == 0:
              page_htmls.append('<a href="%s">1</a>' % request.path)
            else:
              if n: parameters.__setitem__('p', n)
              page_htmls.append('<a href="%s?%s">%s</a>' % (request.path, escape(parameters.urlencode()),n+1))
          page_htmls.append('...')
          for n in range(paginator.pages - ON_ENDS, paginator.pages):
            parameters.__setitem__('p', n)
            page_htmls.append('<a href="%s?%s">%s</a>' % (request.path, escape(parameters.urlencode()),n+1))
      elif page >= (paginator.pages - ON_EACH_SIDE - ON_ENDS - 1):
          # 1 2 ... 95 96 97 *98* 99 100
          for n in range(0, ON_ENDS):
            if n == 0 and len(parameters) == 0:
              page_htmls.append('<a href="%s">1</a>' % request.path)
            else:
              if n: parameters.__setitem__('p', n)
              page_htmls.append('<a href="%s?%s">%s</a>' % (request.path, escape(parameters.urlencode()),n+1))
          page_htmls.append('...')
          for n in range(page - max(ON_EACH_SIDE, ON_ENDS), paginator.pages):
            if n == page:
              page_htmls.append('<span class="this-page">%d</span>' % (page+1))
            else:
              if n: parameters.__setitem__('p', n)
              page_htmls.append('<a href="%s?%s">%d</a>' % (request.path, escape(parameters.urlencode()),n+1))
      else:
          # 1 2 ... 45 46 47 *48* 49 50 51 ... 99 100
          for n in range(0, ON_ENDS):
            if n == 0 and len(parameters) == 0:
              page_htmls.append('<a href="%s">1</a>' % request.path)
            else:
              if n: parameters.__setitem__('p', n)
              page_htmls.append('<a href="%s?%s">%d</a>' % (request.path, escape(parameters.urlencode()),n+1))
          page_htmls.append('...')
          for n in range(page - ON_EACH_SIDE, page + ON_EACH_SIDE + 1):
            if n == page:
              page_htmls.append('<span class="this-page">%s</span>' % (page+1))
            elif n == '.':
              page_htmls.append('...')
            else:
              if n: parameters.__setitem__('p', n)
              page_htmls.append('<a href="%s?%s">%s</a>' % (request.path, escape(parameters.urlencode()),n+1))
          page_htmls.append('...')
          for n in range(paginator.pages - ON_ENDS, paginator.pages):
              if n: parameters.__setitem__('p', n)
              page_htmls.append('<a href="%s?%s">%d</a>' % (request.path, escape(parameters.urlencode()),n+1))
  return mark_safe(' '.join(page_htmls))


def _get_javascript_imports(reportclass):
  '''
  Put in any necessary JavaScript imports.
  '''
  # Check for the presence of a date filter
  if issubclass(reportclass, TableReport):
    add = True
  else:
    add = False
    for row in reportclass.rows:
      if 'filter' in row[1] and isinstance(row[1]['filter'], FilterDate):
        add = True
  if add:
    return reportclass.javascript_imports + [
      "/admin/jsi18n/",
      "/media/js/core.js",
      "/media/js/calendar.js",
      "/media/js/admin/DateTimeShortcuts.js",
      ]
  else:
    return reportclass.javascript_imports


def _generate_csv(rep, qs, format, bucketlist):
  '''
  This is a generator function that iterates over the report data and
  returns the data row by row in CSV format.
  '''
  import csv
  import StringIO
  sf = StringIO.StringIO()
  writer = csv.writer(sf, quoting=csv.QUOTE_NONNUMERIC)

  # Write a header row
  fields = [ ('title' in s[1] and capfirst(_(s[1]['title']))) or capfirst(_(s[0])) for s in rep.rows ]
  if issubclass(rep,TableReport):
    if format == 'csvlist':
      fields.extend([ ('title' in s[1] and capfirst(_(s[1]['title']))) or capfirst(_(s[0])) for s in rep.columns ])
      fields.extend([ ('title' in s[1] and capfirst(_(s[1]['title']))) or capfirst(_(s[0])) for s in rep.crosses ])
    else:
      fields.extend( [capfirst(_('data field'))])
      fields.extend([ b['name'] for b in bucketlist])
  writer.writerow(fields)
  yield sf.getvalue()

  if issubclass(rep,ListReport):
    # Type 1: A "list report"
    # Iterate over all rows
    for row in qs:
      # Clear the return string buffer
      sf.truncate(0)
      # Build the return value
      try: fields = [ getattr(row,s[0]) for s in rep.rows ]
      except: fields = [ row[s[0]] for s in rep.rows ]
      # Return string
      writer.writerow(fields)
      yield sf.getvalue()
  elif issubclass(rep,TableReport):
    if format == 'csvlist':
      # Type 2: "table report in list format"
      # Iterate over all rows and columns
      for row in qs:
        # Clear the return string buffer
        sf.truncate(0)
        # Build the return value
        fields = [ row[s[0]] for s in rep.rows ]
        fields.extend([ row[s[0]] for s in rep.columns ])
        fields.extend([ row[s[0]] for s in rep.crosses ])
        # Return string
        writer.writerow(fields)
        yield sf.getvalue()
    else:
      # Type 3: A "table report in table formtat"
      # Iterate over all rows, crosses and columns
      prev_row = None
      for row in qs:
        if not prev_row:
          prev_row = row[rep.rows[0][0]]
          row_of_buckets = [row]
        elif prev_row == row[rep.rows[0][0]]:
          row_of_buckets.append(row)
        else:
          # Write an entity
          for cross in rep.crosses:
            # Clear the return string buffer
            sf.truncate(0)
            fields = [ row_of_buckets[0][s[0]] for s in rep.rows ]
            fields.extend( [('title' in cross[1] and capfirst(_(cross[1]['title']))) or capfirst(_(cross[0]))] )
            fields.extend([ bucket[cross[0]] for bucket in row_of_buckets ])
            # Return string
            writer.writerow(fields)
            yield sf.getvalue()
          prev_row = row[rep.rows[0][0]]
          row_of_buckets = [row]
      # Write the last entity
      for cross in rep.crosses:
        # Clear the return string buffer
        sf.truncate(0)
        fields = [ row_of_buckets[0][s[0]] for s in rep.rows ]
        fields.extend( [('title' in cross[1] and capfirst(_(cross[1]['title']))) or capfirst(_(cross[0]))] )
        fields.extend([ bucket[cross[0]] for bucket in row_of_buckets ])
        # Return string
        writer.writerow(fields)
        yield sf.getvalue()
  else:
    raise Http404('Unknown report type')


def getBuckets(request, bucket=None, start=None, end=None):
  '''
  This function gets passed a name of a bucketization.
  It returns a list of buckets.
  The data are retrieved from the database table dates, and are
  stored in a python variable for performance
  '''
  global datelist
  pref = request.user.get_profile()

  # Select the bucket size (unless it is passed as argument)
  if not bucket:
    bucket = request.GET.get('reportbucket')
    if not bucket:
      try: bucket = pref.buckets
      except: bucket = 'default'
    elif pref.buckets != bucket:
      pref.buckets = bucket
      pref.save()

  # Select the start date (unless it is passed as argument)
  if not start:
    start = request.GET.get('reportstart')
    if start:
      try:
        (y,m,d) = start.split('-')
        start = date(int(y),int(m),int(d))
        if pref.startdate != start:
          pref.startdate = start
          pref.save()
      except:
        try: start = pref.startdate
        except: pass
        if not start: start = Plan.objects.all()[0].currentdate.date()
    else:
      try: start = pref.startdate
      except: pass
      if not start: start = Plan.objects.all()[0].currentdate.date()

  # Select the end date (unless it is passed as argument)
  if not end:
    end = request.GET.get('reportend')
    if end:
      try:
        (y,m,d) = end.split('-')
        end = date(int(y),int(m),int(d))
        if pref.enddate != end:
          pref.enddate = end
          pref.save()
      except:
        try: end = pref.enddate
        except: pass
        if not end: end = date(2030,1,1)
    else:
      try: end = pref.enddate
      except: pass
      if not end: end = date(2030,1,1)

  # Check if the argument is valid
  if bucket not in ('default','day','week','month','quarter','year'):
    raise Http404, "bucket name %s not valid" % bucket

  # Pick up the buckets
  if not bucket in datelist:
    # Read the buckets from the database if the data isn't available yet
    cursor = connection.cursor()
    field = (bucket=='day' and 'day_start') or bucket
    cursor.execute('''
      select %s, min(day_start), max(day_start)
      from dates
      group by %s
      order by min(day_start)''' \
      % (connection.ops.quote_name(field),connection.ops.quote_name(field)))
    # Compute the data to store in memory
    datelist[bucket] = [{'name': i, 'start': python_date(j), 'end': python_date(k)} for i,j,k in cursor.fetchall()]

  # Filter based on the start and end date
  if start and end:
    res = filter(lambda b: b['start'] < end and b['end'] >= start, datelist[bucket])
  elif end:
    res = filter(lambda b: b['start'] < end, datelist[bucket])
  elif start:
    res = filter(lambda b: b['end'] >= start, datelist[bucket])
  else:
    res = datelist[bucket]
  return (bucket,start,end,res)


def _create_rowheader(req, sortfield, sortdirection, cls):
  '''
  Generate html header row for the columns of a table or list report.
  '''
  # @todo This filter form is NOT valid HTML code! Forms are not allowed to
  # be nested in a table.
  # It somehow works anyway. Only drawback is that the DOM tree in standard
  # complying browsers (eg firefox and opera) is broken.
  result = ['<form action="javascript:filterform()">']
  number = 0
  args = req.GET.copy()
  args2 = req.GET.copy()
  sortable = False

  # When we update the filter, we always want to see page 1 again
  if 'p' in args2: del args2['p']

  # A header cell for each row
  for row in cls.rows:
    number = number + 1
    title = capfirst(escape((row[1].has_key('title') and row[1]['title']) or row[0]))
    if not row[1].has_key('sort') or row[1]['sort']:
      # Sorting is allowed
      sortable = True
      if sortfield == number:
        if sortdirection == 'a':
          # Currently sorting in ascending order on this column
          args['o'] = '%dd' % number
          y = 'class="sorted ascending"'
        else:
          # Currently sorting in descending order on this column
          args['o'] = '%da' % number
          y = 'class="sorted descending"'
      else:
        # Sorted on another column
        args['o'] = '%da' % number
        y = ''
      # Which widget to use
      if 'filter' in row[1]:
        # Filtering allowed
        result.append( u'<th %s><a href="%s?%s">%s</a><br/>%s</th>' \
          % (y, escape(req.path), escape(args.urlencode()),
             title, row[1]['filter'].output(row, number, args)
             ) )
        rowfield = row[1]['filter'].field or row[0]
      else:
        # No filtering allowed
        result.append( u'<th %s><a href="%s?%s">%s</a></th>' \
          % (y, escape(req.path), escape(args.urlencode()), title) )
        rowfield = row[0]
      for i in args:
        field, sep, operator = i.rpartition('__')
        if (field or operator) == rowfield and i in args2: del args2[i]
    else:
      # No sorting is allowed on this field
      # If there is no sorting allowed, then there is also no filtering
      result.append( u'<th>%s</th>' % title )

  # Extra hidden fields for query parameters that aren't rows
  for key in args2:
    result.append(u'<input type="hidden" name="%s" value="%s"/>' % (key, args2[key]))

  # 'Go' button
  if sortable:
    result.append( u'<th><input type="submit" value="Go" tabindex="1100"/></th></form>' )
  else:
    result.append( u'</form>' )
  return mark_safe(u'\n'.join(result))


class FilterText(object):
  def __init__(self, operator="icontains", field=None, size=10):
    self.operator = operator
    self.field = field
    self.size = size

  def output(self, row, number, args):
    global TextOperator
    rowfield = self.field or row[0]
    res = []
    counter = number*10
    for i in args:
      try:
        field, sep, operator = i.rpartition('__')
        if field == '':
          field = operator
          operator = 'exact'
        if field == rowfield:
          for value in args.getlist(i):
            res.append('<span class="textfilteroper" id="operator%d">%s</span><input class="filter" id="filter%d" type="text" size="%d" value="%s" name="%s__%s" tabindex="%d"/>' \
              % (counter, TextOperator[operator], counter, self.size,
                 escape(value),
                 rowfield, operator, number+1000,
                 ))
      except:
        # Silently ignore invalid filters
        pass
      counter = counter + 1
    if len(res) > 0:
      return '<br/>'.join(res)
    else:
      return '<span class="textfilteroper" id="operator%d">%s</span><input class="filter" id="filter%d" type="text" size="%d" value="%s" name="%s__%s" tabindex="%d"/>' \
          % (number*10, TextOperator[self.operator], number*10, self.size,
             escape(args.get("%s__%s" % (rowfield,self.operator),'')),
             rowfield, self.operator, number+1000,
             )


class FilterNumber(object):
  def __init__(self, operator="lt", field=None, size=9):
    self.operator = operator
    self.field = field
    self.size = size

  def output(self, row, number, args):
    global IntegerOperator
    res = []
    rowfield = self.field or row[0]
    counter = number*10
    for i in args:
      try:
        # Skip empty filters
        if args.get(i) == '': continue
        # Determine field and operator
        field, sep, operator = i.rpartition('__')
        if field == '':
          field = operator
          operator = 'exact'
        if field == rowfield:
          for value in args.getlist(i):
            res.append('<span class="numfilteroper" id="operator%d">%s</span><input class="filter" id="filter%d" type="text" size="%d" value="%s" name="%s__%s" tabindex="%d"/>' \
              % (counter, IntegerOperator[operator], counter, self.size,
                 escape(value),
                 rowfield, operator, number+1000,
                 ))
      except:
        # Silently ignore invalid filters
        pass
      counter = counter + 1
    if len(res) > 0:
      return '<br/>'.join(res)
    else:
      return '<span class="numfilteroper" id="operator%d">%s</span><input class="filter" id="filter%d" type="text" size="%d" value="%s" name="%s__%s" tabindex="%d"/>' \
          % (number*10, IntegerOperator[self.operator], number*10, self.size,
             escape(args.get("%s__%s" % (rowfield,self.operator),'')),
             rowfield, self.operator, number+1000,
             )


class FilterDate(object):
  def __init__(self, operator="lt", field=None, size=9):
    self.operator = operator
    self.field = field
    self.size = size

  def output(self, row, number, args):
    global IntegerOperator
    res = []
    rowfield = self.field or row[0]
    counter = number*10
    for i in args:
      try:
        # Skip empty filters
        if args.get(i) == '': continue
        # Determine field and operator
        field, sep, operator = i.rpartition('__')
        if field == '':
          field = operator
          operator = 'exact'
        if field == rowfield:
          for value in args.getlist(i):
            res.append('<span class="datefilteroper" id="operator%d">%s</span><input class="vDateField filter" id="filter%d" type="text" size="%d" value="%s" name="%s__%s" tabindex="%d"/>' \
              % (counter, IntegerOperator[operator], counter, self.size,
                 escape(value),
                 rowfield, operator, number+1000,
                 ))
      except:
        # Silently ignore invalid filters
        pass
      counter = counter + 1
    if len(res) > 0:
      return '<br/>'.join(res)
    else:
      return '<span class="datefilteroper" id="operator%d">%s</span><input class="vDateField filter" id="filter%d" type="text" size="%d" value="%s" name="%s__%s" tabindex="%d"/>' \
          % (number*10, IntegerOperator[self.operator], number*10, self.size,
             escape(args.get("%s__%s" % (rowfield,self.operator),'')),
             rowfield, self.operator, number+1000,
             )


class FilterChoice(object):
  def __init__(self, field=None, choices=None):
    self.field = field
    self.choices = choices

  def output(self, row, number, args):
    rowfield = self.field or row[0]
    value = args.get(rowfield, None)
    result = ['<select name="%s" class="filter"> <option value="">%s</option>' \
      % (rowfield, _('All')) ]
    for code, label in self.choices:
      if code != '':
        if (code == value):
          result.append('<option value="%s" selected="yes">%s</option>' % (code, unicode(label)))
        else:
          result.append('<option value="%s">%s</option>' % (code, unicode(label)))
    result.append('</select>')
    return ' '.join(result)


class FilterBool(FilterChoice):
  '''
  A boolean filter is a special case of the choice filter: the choices
  are limited to 0/false and 1/true.
  '''
  def __init__(self, field=None):
    super(FilterBool, self).__init__(
      field=field,
      choices=( ('0',_('False')), ('1',_('True')), ),
      )


@transaction.commit_manually
def parseUpload(request, reportclass, data):
    '''
    This method reads CSV data from a string (in memory) and creates or updates
    the database records.
    The data must follow the following format:
      - the first row contains a header, listing all field names
      - a first character # marks a comment line
      - empty rows are skipped
    '''
    entityclass = reportclass.model
    headers = []
    rownumber = 0
    warnings = []
    errors = []

    # Loop through the data records
    has_pk_field = False
    for row in csv.reader(data.splitlines()):
      rownumber += 1
      # The first line is read as a header line
      if rownumber == 1:
        for col in row:
          col = col.strip().strip('#').lower()
          ok = False
          for i in entityclass._meta.fields:
            if i.name == col:
              headers.append(i)
              ok = True
              break
          if not ok: errors.append(_('Incorrect field ') + col)
          if col == entityclass._meta.pk.name: has_pk_field = True
        if not has_pk_field and not isinstance(entityclass._meta.pk, AutoField):
          # The primary key is not an auto-generated id and it is not mapped in the input...
          errors.append(_('Missing primary key field ') + entityclass._meta.pk.name)
        if len(errors) > 0:
          return (warnings,errors)

      # Skip empty rows and comments rows
      elif len(row) == 0 or row[0].startswith('#'):
        continue

      # Process a data row
      else:
        cnt = 0
        d = {}
        try:
          for col in row:
            # More fields in data row than headers. Move on to the next row
            if cnt >= len(headers): break
            if isinstance(headers[cnt], ForeignKey):
              try: d[headers[cnt].name] = headers[cnt].rel.to.objects.get(pk=col)
              except Exception, e: warnings.append('%s %d: %s' % (_('Row'), rownumber, e))
            else:
              d[headers[cnt].name] = col
            cnt += 1
          if has_pk_field:
            # A primary key is part of the input fields
            try:
              it = entityclass.objects.get(pk=d[entityclass._meta.pk.name])
              del d[entityclass._meta.pk.name]
              for x in d: it.__setattr__ (x,d[x])
            except:
              it = entityclass(**d)
          else:
            # The primary key is autogenerated
            it = entityclass(**d)
          it.save()
          transaction.commit()    # @todo Too many commits && slow performance
        except Exception, e:
          warnings.append('%s %d: %s' % (_('Row'), rownumber, e))
          transaction.rollback()

    # Report all failed records
    return (warnings,errors)