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
# email : jdetaeye@users.sourceforge.net

from datetime import date, datetime
from xml.sax.saxutils import escape

from django.core.paginator import ObjectPaginator, InvalidPage
from django.shortcuts import render_to_response
from django.contrib.admin.views.decorators import staff_member_required
from django.template import RequestContext, loader
from django.db import connection
from django.http import Http404, HttpResponse
from django.conf import settings
from django.template import Library, Node, resolve_variable

from freppledb.input.models import Plan

# Parameter settings
ON_EACH_SIDE = 3       # Number of pages show left and right of the current page
ON_ENDS = 2            # Number of pages shown at the start and the end of the page list

# A variable to cache bucket information in memory
datelist = {}

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
    if settings.DATABASE_ENGINE == 'sqlite3':
      # Sigh... Poor data type handling in sqlite
      datelist[bucket] = [{
        'name': i,
        'start': datetime.strptime(j,'%Y-%m-%d').date(),
        'end': datetime.strptime(k,'%Y-%m-%d').date()
        } for i,j,k in cursor.fetchall()]
    elif settings.DATABASE_ENGINE == 'oracle':
      # Sigh... Oracle 'date' type converts to a python datetime
      datelist[bucket] = [{'name': i, 'start': j.date(), 'end': k.date()} for i,j,k in cursor.fetchall()]
    else:
      datelist[bucket] = [{'name': i, 'start': j, 'end': k} for i,j,k in cursor.fetchall()]

  # Filter based on the start and end date
  if start and end:
    res = filter(lambda b: b['start'] <= end and b['end'] >= start, datelist[bucket])
  elif end:
    res = filter(lambda b: b['start'] <= end, datelist[bucket])
  elif start:
    res = filter(lambda b: b['end'] >= start, datelist[bucket])
  else:
    res = datelist[bucket]
  return (bucket,start,end,res)


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

  # Row definitions
  # Possible attributes for a row field are:
  #   - filter:
  #     Specifies how a value in the search field affects the base query.
  #   - filter_size:
  #     Specifies the size of the search field.
  #     The default value is 10 characters.
  #   - order_by:
  #     Model field to user for the sorting.
  #     It defaults to the name of the field.
  #   - title:
  #     Name of the row that is displayed to the user.
  #     It defaults to the name of the field.
  rows = ()

  # Cross definitions.
  # Possible attributes for a row field are:
  #   - title:
  #     Name of the cross that is displayed to the user.
  #     It defaults to the name of the field.
  crosses = ()

  # Column definitions
  # Possible attributes for a row field are:
  #   - title:
  #     Name of the cross that is displayed to the user.
  #     It defaults to the name of the field.
  columns = ()


def _generate_csv(rep, qs):
  '''This is a generator function that iterates over the report data and
  returns the data row by row in CSV format.'''
  import csv
  import StringIO
  sf = StringIO.StringIO()
  writer = csv.writer(sf, quoting=csv.QUOTE_NONNUMERIC)

  # Write a header row
  fields = [ ('title' in s[1] and s[1]['title']) or s[0] for s in rep.rows ]
  fields.extend([ ('title' in s[1] and s[1]['title']) or s[0] for s in rep.columns ])
  fields.extend([ ('title' in s[1] and s[1]['title']) or s[0] for s in rep.crosses ])
  writer.writerow(fields)
  yield sf.getvalue()

  # Iterate over all rows and columns
  for row in qs:
    for col in row:
      # Clear the return string buffer
      sf.truncate(0)
      # Build the return value
      fields = [ col[s[0]] for s in rep.rows ]
      fields.extend([ col[s[0]] for s in rep.columns ])
      fields.extend([ col[s[0]] for s in rep.crosses ])
      # Return string
      writer.writerow(fields)
      yield sf.getvalue()


@staff_member_required
def view_report(request, entity=None, **args):
  '''
  This is a generic view for reports having buckets in the time dimension.
  The following arguments can be passed to the view:
    - report:
      Points to a subclass of Report.
      This is a required attribute.
    - extra_context:
      An additional set of records added to the context for rendering the
      view.
    - paginate_by:
      Number of entities to report on a page.
  '''
  global ON_EACH_SIDE
  global ON_ENDS

  # Pick up the report class
  try: reportclass = args['report']
  except: raise Http404('Missing report parameter in url context')

  # Pick up the list of time buckets
  (bucket,start,end,bucketlist) = getBuckets(request)

  # Pick up the filter parameters from the url
  filterargs = [ request.GET.get(f[0]) for f in reportclass.rows ]
  counter = reportclass.basequeryset
  fullhits = counter.count()
  if entity:
    counter = counter.filter(pk__exact=entity)
  else:
    for f in reportclass.rows:
      x = request.GET.get(f[0], None)
      if x and 'filter' in f[1]:
        counter = counter.filter(**{f[1]['filter']:x})

  # Pick up the sort parameter from the url
  sortparam = request.GET.get('o','1a')
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

  # HTML output or CSV output?
  type = request.GET.get('type','html')
  if settings.DATABASE_ENGINE == 'oracle':
    basesql = counter._get_sql_clause(get_full_query=True)
  else:
    basesql = counter._get_sql_clause()
  if type == 'csv':
    # CSV output
    response = HttpResponse(mimetype='text/csv')
    response['Content-Disposition'] = 'attachment; filename=%s.csv' % reportclass.title.lower()
    response._container = _generate_csv(reportclass, reportclass.resultquery('select * %s' % basesql[1], basesql[2], bucket, start, end, sortsql=sortsql))
    response._is_string = False
    return response

  # Create a copy of the request url parameters
  parameters = request.GET.copy()
  parameters.__setitem__('p', 0)

  # Calculate the content of the page
  page = int(request.GET.get('p', '0'))
  paginator = ObjectPaginator(counter, reportclass.paginate_by)
  counter = counter[paginator.first_on_page(page)-1:paginator.first_on_page(page)-1+(reportclass.paginate_by or 0)]
  if settings.DATABASE_ENGINE == 'oracle':
    basesql = counter._get_sql_clause(get_full_query=True)
  else:
    basesql = counter._get_sql_clause()
  try:
    if settings.DATABASE_ENGINE == 'oracle':
      results = reportclass.resultquery(basesql[3], basesql[2], bucket, start, end, sortsql=sortsql)
    else:
      results = reportclass.resultquery('select * %s' % basesql[1], basesql[2], bucket, start, end, sortsql=sortsql)
  except InvalidPage: raise Http404

  # If there are less than 10 pages, show them all
  page_htmls = []
  if paginator.pages <= 10:
    for n in range(0,paginator.pages):
      parameters.__setitem__('p', n)
      if n == page:
        page_htmls.append('<span class="this-page">%d</span>' % (page+1))
      else:
        page_htmls.append('<a href="%s?%s">%s</a>' % (request.path, escape(parameters.urlencode()),n+1))
  else:
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

  # Prepare template context
  context = {
       'objectlist': results,
       'bucket': bucket,
       'startdate': start,
       'enddate': end,
       'bucketlist': bucketlist,
       'paginator': paginator,
       'is_paginated': paginator.pages > 1,
       'has_next': paginator.has_next_page(page - 1),
       'has_previous': paginator.has_previous_page(page - 1),
       'current_page': page,
       'next_page': page + 1,
       'previous_page': page - 1,
       'pages': paginator.pages,
       'hits' : paginator.hits,
       'fullhits': fullhits,
       'page_htmls': page_htmls,
       # Reset the breadcrumbs if no argument entity was passed
       'reset_crumbs': entity == None,
       'title': (entity and '%s for %s' % (reportclass.title,entity)) or reportclass.title,
       'sort': sortparam,
       'class': reportclass,
     }
  if 'extra_context' in args: context.update(args['extra_context'])

  # Uncomment this line to see which sql got executed
  #for i in connection.queries: print i['time'], i['sql']

  # Render the view
  return render_to_response(args['report'].template,
    context, context_instance=RequestContext(request))


class ReportRowHeader(Node):
  def __init__(self, num):
    self.number = int(num)

  def render(self, context):
    req = resolve_variable('request',context)
    sort = resolve_variable('sort',context)
    cls = resolve_variable('class',context)
    x = req.GET.copy()
    if int(sort[0]) == self.number:
      if sort[1] == 'a':
        # Currently sorting in ascending order on this column
        x['o'] = '%dd' % self.number
        y = 'class="sorted ascending"'
      else:
        # Currently sorting in descending order on this column
        x['o'] = '%da' % self.number
        y = 'class="sorted descending"'
    else:
      # Sorted on another column
      x['o'] = '%da' % self.number
      y = ''
    title = (cls.rows[self.number-1][1].has_key('title') and cls.rows[self.number-1][1]['title']) or cls.rows[self.number-1][0]
    if 'filter' in cls.rows[self.number-1][1]:
      return '<th %s><a href="%s?%s">%s%s</a><br/><input type="text" size="%d" value="%s" name="%s" tabindex="%d"/></th>' \
        % (y, req.path, escape(x.urlencode()),
           title[0].upper(), title[1:],
           (cls.rows[self.number-1][1].has_key('filter_size') and cls.rows[self.number-1][1]['filter_size']) or 10,
           x.get(cls.rows[self.number-1][0],''),
           cls.rows[self.number-1][0], self.number+1000,
           )
    else:
      return '<th %s style="vertical-align:top"><a href="%s?%s">%s%s</a></th>' \
        % (y, req.path, escape(x.urlencode()),
           title[0].upper(), title[1:],
          )
