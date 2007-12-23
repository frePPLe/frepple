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

from django.core.paginator import ObjectPaginator, InvalidPage
from django.shortcuts import render_to_response
from django.contrib.admin.views.decorators import staff_member_required
from django.template import RequestContext, loader
from django.db import connection
from django.http import Http404, HttpResponse, HttpResponseForbidden, HttpResponseNotModified
from django.conf import settings
from django.template import Library, Node, resolve_variable, loader
from django.utils.encoding import smart_str
from django.utils.translation import ugettext as _
from django.utils.html import escape
from django.utils.safestring import mark_safe
from django.utils.text import capfirst

from input.models import Plan
from utils.db import python_date
from utils.reportfilter import _create_rowheader, FilterDate

# Parameter settings
ON_EACH_SIDE = 3       # Number of pages show left and right of the current page
ON_ENDS = 2            # Number of pages shown at the start and the end of the page list

# A variable to cache bucket information in memory
datelist = {}


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


class ListReport(Report):
  '''
  Row definitions.

  Supported class methods:
    - lastmodified():
      Returns a datetime object representing the last time the report content
      was updated.

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
  global ON_EACH_SIDE
  global ON_ENDS

  # Pick up the report class
  try: reportclass = args['report']
  except: raise Http404('Missing report parameter in url context')

  # Verify if the page has changed since the previous request
  lastmodifiedrequest = request.META.get('HTTP_IF_MODIFIED_SINCE', None)
  try:
    lastmodifiedresponse = reportclass.lastmodified().replace(microsecond=0)
    lastmodifiedresponse = (formatdate(timegm(lastmodifiedresponse.utctimetuple()))[:26] + 'GMT')
    if lastmodifiedrequest.startswith(lastmodifiedresponse):
      # The report hasn't modified since the previous request
      return HttpResponseNotModified()
  except Exception, e:
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
  type = request.GET.get('type','html')  # HTML or CSV (table or list) output

  # Pick up the filter parameters from the url
  counter = reportclass.basequeryset
  fullhits = counter.count()
  if entity:
    # The url path specifies a single entity.
    # We ignore all other filters.
    counter = counter.filter(pk__exact=entity)
  else:
    # The url doesn't specify a single entity, but may specify filters
    # Convert url parameters into queryset filters.
    # This block of code is copied from the django admin code.
    qs_args = dict(request.GET.items())
    for i in ('o', 'p', 'type'):
      # Remove arguments that aren't filters
      if i in qs_args: del qs_args[i]
    for key, value in qs_args.items():
      # Ignore empty filter values
      if not value or len(value) == 0: del qs_args[key]
      elif not isinstance(key, str):
        # 'key' will be used as a keyword argument later, so Python
        # requires it to be a string.
        del qs_args[key]
        qs_args[smart_str(key)] = value
    counter = counter.filter(**qs_args)

  # Pick up the sort parameter from the url
  sortparam = request.GET.get('o', reportclass.default_sort)
  try:
    if sortparam[0] == '1':
      if sortparam[1] == 'd':
        counter = counter.order_by('-%s' % (('order_by' in reportclass.rows[0][1] and reportclass.rows[0][1]['order_by']) or reportclass.rows[0][0]))
        sortsql = '1 desc'
      else:
        sortparam = '1a'
        counter = counter.order_by(('order_by' in reportclass.rows[0][1] and reportclass.rows[0][1]['order_by']) or reportclass.rows[0][0])
        sortsql = '1 asc'
    else:
      x = int(sortparam[0])
      if x > len(reportclass.rows) or x < 0:
        sortparam = '1a'
        counter = counter.order_by(('order_by' in reportclass.rows[0][1] and reportclass.rows[0][1]['order_by']) or reportclass.rows[0][0])
        sortsql = '1 asc'
      elif sortparam[1] == 'd':
        sortparm = '%dd' % x
        counter = counter.order_by(
          '-%s' % (('order_by' in reportclass.rows[x-1][1] and reportclass.rows[x-1][1]['order_by']) or reportclass.rows[x-1][0]),
          ('order_by' in reportclass.rows[0][1] and reportclass.rows[0][1]['order_by']) or reportclass.rows[0][0]
          )
        sortsql = '%d desc, 1 asc' % x
      else:
        sortparam = '%da' % x
        counter = counter.order_by(
          ('order_by' in reportclass.rows[x-1][1] and reportclass.rows[x-1][1]['order_by']) or reportclass.rows[x-1][0],
          ('order_by' in reportclass.rows[0][1] and reportclass.rows[0][1]['order_by']) or reportclass.rows[0][0]
          )
        sortsql = '%d asc, 1 asc' % x
  except:
    # A silent and safe exit in case of any exception
    sortparam = '1a'
    counter = counter.order_by(('order_by' in reportclass.rows[0][1] and reportclass.rows[0][1]['order_by']) or reportclass.rows[0][0])
    sortsql = '1 asc'

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
    if type == 'csv':
      # Only csv is specified: use the user's preferences to determine whether
      # we want a list or table
      type = type + request.user.get_profile().csvformat
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
  parameters.__setitem__('p', 0)

  # Calculate the content of the page
  if hasattr(reportclass,'resultquery'):
    # SQL override provided
    try:
      results = reportclass.resultquery(sql, sqlargs, bucket, start, end, sortsql=sortsql)
    except InvalidPage: raise Http404
  else:
    # No SQL override provided
    results = counter

  # If there are less than 10 pages, show them all
  page_htmls = []
  if paginator.pages <= 10 and paginator.pages > 1:
    for n in range(0,paginator.pages):
      parameters.__setitem__('p', n)
      if n == page:
        page_htmls.append('<span class="this-page">%d</span>' % (page+1))
      else:
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
            else:
              parameters.__setitem__('p', n)
              page_htmls.append('<a href="%s?%s">%s</a>' % (request.path, escape(parameters.urlencode()),n+1))
          page_htmls.append('...')
          for n in range(paginator.pages - ON_EACH_SIDE, paginator.pages):
              parameters.__setitem__('p', n)
              page_htmls.append('<a href="%s?%s">%s</a>' % (request.path, escape(parameters.urlencode()),n+1))
      elif page >= (paginator.pages - ON_EACH_SIDE - ON_ENDS - 2):
          # 1 2 ... 95 96 97 *98* 99 100
          for n in range(0, ON_ENDS):
              parameters.__setitem__('p', n)
              page_htmls.append('<a href="%s?%s">%s</a>' % (request.path, escape(parameters.urlencode()),n+1))
          page_htmls.append('...')
          for n in range(page - max(ON_EACH_SIDE, ON_ENDS), paginator.pages):
            if n == page:
              page_htmls.append('<span class="this-page">%d</span>' % (page+1))
            else:
              parameters.__setitem__('p', n)
              page_htmls.append('<a href="%s?%s">%d</a>' % (request.path, escape(parameters.urlencode()),n+1))
      else:
          # 1 2 ... 45 46 47 *48* 49 50 51 ... 99 100
          for n in range(0, ON_ENDS):
              parameters.__setitem__('p', n)
              page_htmls.append('<a href="%s?%s">%d</a>' % (request.path, escape(parameters.urlencode()),n+1))
          page_htmls.append('...')
          for n in range(page - ON_EACH_SIDE, page + ON_EACH_SIDE + 1):
            if n == page:
              page_htmls.append('<span class="this-page">%s</span>' % (page+1))
            elif n == '.':
              page_htmls.append('...')
            else:
              parameters.__setitem__('p', n)
              page_htmls.append('<a href="%s?%s">%s</a>' % (request.path, escape(parameters.urlencode()),n+1))
          page_htmls.append('...')
          for n in range(paginator.pages - ON_ENDS - 1, paginator.pages):
              parameters.__setitem__('p', n)
              page_htmls.append('<a href="%s?%s">%d</a>' % (request.path, escape(parameters.urlencode()),n+1))
  page_htmls = mark_safe(' '.join(page_htmls))

  # Prepare template context
  context = {
       'objectlist': results,
       'bucket': bucket,
       'startdate': start,
       'enddate': end,
       'paginator': paginator,
       'hits' : paginator.hits,
       'fullhits': fullhits,
       'paginator_html': mark_safe(page_htmls),
       'javascript_imports': _get_javascript_imports(reportclass),
       # Never reset the breadcrumbs if an argument entity was passed.
       # Otherwise depend on the value in the report class.
       'reset_crumbs': reportclass.reset_crumbs and entity == None,
       'title': (entity and '%s %s %s' % (unicode(reportclass.title),_('for'),entity)) or reportclass.title,
       'rowheader': _create_rowheader(request, sortparam, reportclass),
       'crossheader': issubclass(reportclass, TableReport) and _create_crossheader(request, reportclass),
       'columnheader': issubclass(reportclass, TableReport) and _create_columnheader(request, reportclass, bucketlist),
     }
  if 'extra_context' in args: context.update(args['extra_context'])

  # Render the view, optionally setting the last-modified http header
  response = HttpResponse(
    loader.render_to_string(args['report'].template, context, context_instance=RequestContext(request)),
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


def _get_javascript_imports(reportclass):
  '''
  Put in any necessary JavaScript imports.
  '''
  # Check for the presence of a date filter
  for row in reportclass.rows:
    if 'filter' in row[1] and isinstance(row[1]['filter'], FilterDate):
      return reportclass.javascript_imports + [
          "/admin/jsi18n/",
          "/media/js/core.js",
          "/media/js/calendar.js",
          "/media/js/admin/DateTimeShortcuts.js",
          ]
  return reportclass.javascript_imports


def getBuckets(request, bucket=None, start=None, end=None):
  '''
  This function gets passed a name of a bucketization.
  It returns a list of buckets.
  The data are retrieved from the database table dates, and are
  stored in a python variable for performance
  '''
  global datelist
  # Pick up the arguments
  if not bucket:
    bucket = request.GET.get('bucket')
    if not bucket:
      try: bucket = request.user.get_profile().buckets
      except: bucket = 'default'
  if not start:
    start = request.GET.get('start')
    if start:
      try:
        (y,m,d) = start.split('-')
        start = date(int(y),int(m),int(d))
      except:
        try: start = request.user.get_profile().startdate
        except: pass
        if not start: start = Plan.objects.all()[0].currentdate.date()
    else:
      try: start = request.user.get_profile().startdate
      except: pass
      if not start: start = Plan.objects.all()[0].currentdate.date()
  if not end:
    end = request.GET.get('end')
    if end:
      try:
        (y,m,d) = end.split('-')
        end = date(int(y),int(m),int(d))
      except:
        try: end = request.user.get_profile().enddate
        except: pass
        if not end: end = date(2030,1,1)
    else:
      try: end = request.user.get_profile().enddate
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
