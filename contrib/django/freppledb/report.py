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

from django.core.paginator import ObjectPaginator, InvalidPage
from django.shortcuts import render_to_response
from django.contrib.admin.views.decorators import staff_member_required
from django.template import RequestContext, loader
from django.db import connection
from django.http import Http404, HttpResponse
from django.conf import settings

from datetime import date, datetime

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
      except: bucket = 'month'
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
  if bucket not in ('day','week','month','quarter','year'):
    raise Http404, "bucket name %s not valid" % bucket

  # Pick up the buckets
  if not bucket in datelist:
    # Read the buckets from the database if the data isn't available yet
    cursor = connection.cursor()
    cursor.execute('''
      select %s, min(day), max(day)
      from dates
      group by %s
      order by min(day)''' % (bucket,bucket))
    # Compute the data to store in memory
    if settings.DATABASE_ENGINE == 'sqlite3':
      # Sigh... Poor data type handling in sqlite
      datelist[bucket] = [{
        'name': i,
        'start': datetime.strptime(j,'%Y-%m-%d').date(),
        'end': datetime.strptime(k,'%Y-%m-%d').date()
        } for i,j,k in cursor.fetchall()]
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
  # Field definitions
  fields = []


def getSortSQL(param, fields=0):
  try:
    if param[0] == '1':
      if param[1] == 'd': return ('1d','1 desc')
      else: return ('1a','1 asc')
    else:
      x = int(param[0])
      if param[1] == 'd': return ('%dd' % x,'%d desc, 1 asc' % x)
      else: return ('%da' % x,'%d asc, 1 asc' % x)
  except:
    # A silent and safe exit in case of any exception
    return ('1a','1 asc')


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

  # Pick up the sort parameters
  (sortparam,sortsql) = getSortSQL(request.GET.get('o','1a'), len(reportclass.fields))

  # HTML output or CSV output?
  type = request.GET.get('type','html')
  if type == 'csv':
    # CSV output
    c = RequestContext(request, {
       'objectlist': reportclass.resultquery(entity, bucket, start, end, sortsql=sortsql),
       'bucket': bucket,
       'startdate': start,
       'enddate': end,
       'bucketlist': bucketlist,
       })
    response = HttpResponse(mimetype='text/csv')
    response['Content-Disposition'] = 'attachment; filename=%s' % reportclass.template['csv']
    response.write(loader.get_template(reportclass.template['csv']).render(c))
    return response

  # Create a copy of the request url parameters
  parameters = request.GET.copy()
  parameters.__setitem__('p', 0)

  # Calculate the content of the page
  page = int(request.GET.get('p', '0'))
  if not entity and reportclass.countquery:
    paginator = ObjectPaginator(reportclass.countquery, reportclass.paginate_by)
    try: results = reportclass.resultquery(entity, bucket, start, end, offset=paginator.first_on_page(page)-1, limit=reportclass.paginate_by, sortsql=sortsql)
    except InvalidPage: raise Http404
  else:
    paginator = ObjectPaginator(reportclass.resultquery(entity, bucket, start, end, sortsql=sortsql), reportclass.paginate_by)
    try: results = paginator.get_page(page)
    except InvalidPage: raise Http404

  # If there are less than 10 pages, show them all
  page_htmls = []
  if paginator.pages <= 10:
    for n in range(0,paginator.pages):
      parameters.__setitem__('p', n)
      if n == page:
        page_htmls.append('<span class="this-page">%d</span>' % (page+1))
      else:
        page_htmls.append('<a href="%s?%s">%s</a>' % (request.path, parameters.urlencode(),n+1))
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
              page_htmls.append('<a href="%s?%s">%s</a>' % (request.path, parameters.urlencode(),n+1))
          page_htmls.append('...')
          for n in range(paginator.pages - ON_EACH_SIDE, paginator.pages):
              parameters.__setitem__('p', n)
              page_htmls.append('<a href="%s?%s">%s</a>' % (request.path, parameters.urlencode(),n+1))
      elif page >= (paginator.pages - ON_EACH_SIDE - ON_ENDS - 2):
          # 1 2 ... 95 96 97 *98* 99 100
          for n in range(0, ON_ENDS):
              parameters.__setitem__('p', n)
              page_htmls.append('<a href="%s?%s">%s</a>' % (request.path, parameters.urlencode(),n+1))
          page_htmls.append('...')
          for n in range(page - max(ON_EACH_SIDE, ON_ENDS), paginator.pages):
            if n == page:
              page_htmls.append('<span class="this-page">%d</span>' % (page+1))
            else:
              parameters.__setitem__('p', n)
              page_htmls.append('<a href="%s?%s">%d</a>' % (request.path, parameters.urlencode(),n+1))
      else:
          # 1 2 ... 45 46 47 *48* 49 50 51 ... 99 100
          for n in range(0, ON_ENDS):
              parameters.__setitem__('p', n)
              page_htmls.append('<a href="%s?%s">%d</a>' % (request.path, parameters.urlencode(),n+1))
          page_htmls.append('...')
          for n in range(page - ON_EACH_SIDE, page + ON_EACH_SIDE + 1):
            if n == page:
              page_htmls.append('<span class="this-page">%s</span>' % (page+1))
            elif n == '.':
              page_htmls.append('...')
            else:
              parameters.__setitem__('p', n)
              page_htmls.append('<a href="%s?%s">%s</a>' % (request.path, parameters.urlencode(),n+1))
          page_htmls.append('...')
          for n in range(paginator.pages - ON_ENDS - 1, paginator.pages):
              parameters.__setitem__('p', n)
              page_htmls.append('<a href="%s?%s">%d</a>' % (request.path, parameters.urlencode(),n+1))

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
       'page_htmls': page_htmls,
       # Reset the breadcrumbs if no argument entity was passed
       'reset_crumbs': entity == None,
       'title': (entity and '%s for %s' % (reportclass.title,entity)) or reportclass.title,
       'sort': sortparam,
     }
  if 'extra_context' in args: context.update(args['extra_context'])

  # Uncomment this line to see which sql got executed
  #for i in connection.queries: print i['time'], i['sql']

  # Render the view
  return render_to_response(args['report'].template['html'],  context, context_instance=RequestContext(request))
