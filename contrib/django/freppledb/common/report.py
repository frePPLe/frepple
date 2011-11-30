#
# Copyright (C) 2007-2011 by Johan De Taeye, frePPLe bvba
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
# Foundation Inc., 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301 USA
#

# file : $URL$
# revision : $LastChangedRevision$  $LastChangedBy$
# date : $LastChangedDate$

r'''
This module implements a generic view to presents lists and tables.

It provides the following functionality:
 - Pagination of the results.
 - Ability to filter on fields, using different operators.
 - Ability to sort on a field.
 - Export the results as a CSV file, ready for use in a spreadsheet.
 - Import CSV formatted data files.
 - Show time buckets to show data by time buckets.
   The time buckets and time boundaries can easily be updated.
'''

from datetime import date, datetime
from decimal import Decimal
import csv, cStringIO
import operator

from django.conf import settings
from django.core.paginator import QuerySetPaginator, InvalidPage
from django.views.decorators.csrf import csrf_protect
from django.contrib import messages
from django.contrib.admin.views.decorators import staff_member_required
from django.db import transaction
from django.db import models
from django.db.models.fields import Field
from django.db.models.fields.related import RelatedField, AutoField
from django.http import Http404, HttpResponse, HttpResponseRedirect, HttpResponseForbidden, HttpResponseNotAllowed
from django.forms.models import modelform_factory
from django.shortcuts import render
from django.template import RequestContext, loader
from django.utils import translation
from django.utils.decorators import method_decorator
from django.utils.encoding import smart_str
from django.utils.translation import ugettext as _
from django.utils.formats import get_format, number_format
from django.utils import simplejson as json
from django.utils.text import get_text_list
from django.utils.encoding import iri_to_uri, force_unicode
from django.contrib.admin.models import LogEntry, CHANGE, ADDITION
from django.contrib.contenttypes.models import ContentType
from django.views.generic.base import View

from freppledb.input.models import Parameter, BucketDetail, Bucket


# URL parameters that are not query arguments
reservedParameters = ('o', 'p', 't', 'reporttype', 'pop', 'reportbucket', 'reportstart', 'reportend')


class GridField(object):
  '''
  Base field for columns in grid views.
  '''

  def __init__(self, name, **kwargs):
    self.name = name
    for key in kwargs:
      setattr(self, key, kwargs[key])
    if 'key' in kwargs: self.editable = False
    if not 'title' in kwargs: self.title = _(self.name)
    if not 'field_name' in kwargs: self.field_name = self.name

  def __unicode__(self):
    o = [ "name:'%s',label:'%s',width:%d,align:'%s'," % (self.name, force_unicode(self.title).title().replace("'","\\'"), self.width, self.align), ]
    if self.key: o.append( "key:true," )
    if not self.sortable: o.append("sortable:false,")
    if not self.editable: o.append("editable:false,")
    if self.formatter: o.append("formatter:'%s'," % self.formatter)
    if self.unformat: o.append("unformat:%s," % self.unformat)
    if self.searchrules: o.append("searchrules:{%s}," % self.searchrules)
    if self.extra: o.append(self.extra)
    return ''.join(o)

  name = None
  field_name = None
  formatter = None
  width = 100
  editable = True
  sortable = True
  key = False
  unformat = None
  title = None
  extra = None
  align = 'center'
  searchrules = None


class GridFieldDateTime(GridField):
  formatter = 'date'
  extra = "formatoptions:{srcformat:'Y-m-d H:i:s',newformat:'Y-m-d H:i:s'}"
  width = 140


class GridFieldDate(GridField):
  formatter = 'date'
  extra = "formatoptions:{srcformat:'Y-m-d H:i:s',newformat:'Y-m-d'}"
  width = 140


class GridFieldInteger(GridField):
  formatter = 'integer'
  width = 70
  searchrules = 'integer:true'


class GridFieldNumber(GridField):
  formatter = 'number'
  width = 70
  searchrules = 'number:true'


class GridFieldBool(GridField):
  formatter = 'checkbox'
  width = 60


class GridFieldLastModified(GridField):
  formatter = 'date'
  extra = "formatoptions:{srcformat:'Y-m-d H:i:s',newformat:'Y-m-d H:i:s'}"
  title = _('last modified')
  editable = False
  width = 140


class GridFieldText(GridField):
  width = 200
  align = 'left'


class GridFieldCurrency(GridField):
  formatter = 'currency'
  extra = "formatoptions:{prefix:'$'}"   #TODO make the currency symbol configurable
  width = 80


@staff_member_required
@csrf_protect
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
  global reservedParameters
  reportclass = args['report']
  model = reportclass.model

  # Pick up the list of time buckets
  pref = request.user.get_profile()
  if reportclass.timebuckets:
    (bucket,start,end,bucketlist) = getBuckets(request, pref)
    bucketnames = Bucket.objects.order_by('name').values_list('name', flat=True)
  else:
    bucket = start = end = bucketlist = bucketnames = None
  type = request.GET.get('reporttype','html')  # HTML or CSV (table or list) output

  # Is this a popup window?
  is_popup = request.GET.has_key('pop')

  # Pick up the filter parameters from the url
  counter = reportclass.basequeryset.using(request.database)
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
    if not hasattr(reportclass,'default_sortfield'):
      # Create an attribute to store the index of the default sort
      reportclass.default_sortfield = 0
      for i in reportclass.default_sort:
        if i.isdigit():
          reportclass.default_sortfield = reportclass.default_sortfield * 10 + int(i)
        else:
          break
      reportclass.default_sortdirection = reportclass.default_sort[-1]
    if sortfield<=0 or sortfield > len(reportclass.rows) \
      or (reportclass.rows[sortfield-1][1].has_key('sort') and reportclass.rows[sortfield-1][1]['sort']):
        # Invalid sort
        raise
    # Create sort parameters
    if sortfield == reportclass.default_sortfield:
      if sortdirection == 'd':
        sortparam = '%dd' % sortfield
        counter = counter.order_by('-%s' % (('order_by' in reportclass.rows[sortfield-1][1] and reportclass.rows[sortfield-1][1]['order_by']) or reportclass.rows[sortfield-1][0]))
        sortsql = '%d desc' % sortfield
      else:
        sortparam = '%da' % sortfield
        counter = counter.order_by(('order_by' in reportclass.rows[sortfield-1][1] and reportclass.rows[sortfield-1][1]['order_by']) or reportclass.rows[sortfield-1][0])
        sortsql = '%d asc' % sortfield
    else:
      if sortdirection == 'd':
        sortparam = '%dd' % sortfield
        if reportclass.default_sortdirection == 'a':
          counter = counter.order_by(
            '-%s' % (('order_by' in reportclass.rows[sortfield-1][1] and reportclass.rows[sortfield-1][1]['order_by']) or reportclass.rows[sortfield-1][0]),
            ('order_by' in reportclass.rows[reportclass.default_sortfield-1][1] and reportclass.rows[reportclass.default_sortfield-1][1]['order_by']) or reportclass.rows[reportclass.default_sortfield-1][0]
            )
          sortsql = '%d desc, %d asc' % (sortfield, reportclass.default_sortfield)
        else:
          counter = counter.order_by(
            '-%s' % (('order_by' in reportclass.rows[sortfield-1][1] and reportclass.rows[sortfield-1][1]['order_by']) or reportclass.rows[sortfield-1][0]),
            '-%s' % (('order_by' in reportclass.rows[reportclass.default_sortfield-1][1] and reportclass.rows[reportclass.default_sortfield-1][1]['order_by']) or reportclass.rows[reportclass.default_sortfield-1][0])
            )
          sortsql = '%d desc, %d desc' % (sortfield, reportclass.default_sortfield)
      else:
        sortparam = '%da' % sortfield
        if reportclass.default_sortdirection == 'a':
          counter = counter.order_by(
            ('order_by' in reportclass.rows[sortfield-1][1] and reportclass.rows[sortfield-1][1]['order_by']) or reportclass.rows[sortfield-1][0],
            ('order_by' in reportclass.rows[reportclass.default_sortfield-1][1] and reportclass.rows[reportclass.default_sortfield-1][1]['order_by']) or reportclass.rows[reportclass.default_sortfield-1][0]
            )
          sortsql = '%d asc, %d asc' % (sortfield, reportclass.default_sortfield)
        else:
          counter = counter.order_by(
            ('order_by' in reportclass.rows[sortfield-1][1] and reportclass.rows[sortfield-1][1]['order_by']) or reportclass.rows[sortfield-1][0],
            '-%s' % (('order_by' in reportclass.rows[reportclass.default_sortfield-1][1] and reportclass.rows[reportclass.default_sortfield-1][1]['order_by']) or reportclass.rows[reportclass.default_sortfield-1][0])
            )
          sortsql = '%d asc, %d desc' % (sortfield, reportclass.default_sortfield)
  except:
    # A silent and safe exit in case of any exception
    sortparam = reportclass.default_sort
    sortfield = reportclass.default_sortfield
    sortdirection = reportclass.default_sortdirection
    sortsql = '%d asc' % sortfield
    if sortdirection == 'a':
      counter = counter.order_by(('order_by' in reportclass.rows[sortfield-1][1] and reportclass.rows[sortfield-1][1]['order_by']) or reportclass.rows[sortfield-1][0])
    else:
      counter = counter.order_by('-%s' % (('order_by' in reportclass.rows[sortfield-1][1] and reportclass.rows[sortfield-1][1]['order_by']) or reportclass.rows[sortfield-1][0]))

  # HTML output or CSV output?
  if type[:3] == 'csv':
    # CSV output
    response = HttpResponse(content_type='text/csv; charset=%s' % settings.DEFAULT_CHARSET)
    response['Content-Disposition'] = 'attachment; filename=%s.csv' % iri_to_uri(reportclass.title.lower())
    if hasattr(reportclass,'resultlist2'):
      # SQL override provided of type 2
      response._container = _generate_csv(reportclass, reportclass.resultlist2(request, counter, bucket, start, end, sortsql=sortsql), type, bucketlist, request)
    elif hasattr(reportclass,'resultlist1'):
      # SQL override provided of type 1
      response._container = _generate_csv(reportclass, reportclass.resultlist1(request, counter, bucket, start, end, sortsql=sortsql), type, bucketlist, request)
    else:
      # No SQL override provided
      response._container = _generate_csv(reportclass, counter, type, bucketlist, request)
    response._is_string = False
    return response

  # Build paginator
  page = int(request.GET.get('p', '1'))
  paginator = QuerySetPaginator(counter, reportclass.paginate_by)
  if paginator.page(page).start_index():
    counter = counter[paginator.page(page).start_index()-1:paginator.page(page).end_index()]
  hits = paginator.count

  # Calculate the content of the page
  if hasattr(reportclass,'resultlist1'):
    # SQL override provided
    try:
      objectlist1 = reportclass.resultlist1(request, counter, bucket, start, end, sortsql=sortsql)
    except InvalidPage: raise Http404
  else:
    # No SQL override provided
    objectlist1 = counter
  if hasattr(reportclass,'resultlist2'):
    # SQL override provided
    try:
      objectlist2 = reportclass.resultlist2(request, counter, bucket, start, end, sortsql=sortsql)
    except InvalidPage: raise Http404
  else:
    # No SQL override provided
    objectlist2 = objectlist1

  # Build the path for the complete list.
  # We need to treat URLs for a specific entity a bit differently
  if entity:
    base_request_path = "%s%s/" % (request.prefix, request.path.rstrip("/").rpartition("/")[0])
  else:
    base_request_path = "%s%s" %(request.prefix, request.path)

  # Prepare template context
  head_frozen, head_scroll = _create_rowheader(request, sortfield, sortdirection, reportclass)
  context = {
       'reportclass': reportclass,
       'model': model,
       'hasaddperm': reportclass.editable and model and request.user.has_perm('%s.%s' % (model._meta.app_label, model._meta.get_add_permission())),
       'haschangeperm': reportclass.editable and model and request.user.has_perm('%s.%s' % (model._meta.app_label, model._meta.get_change_permission())),
       'request': request,
       'object': entity or (hits == 1 and reportclass.model and counter[0].pk) or None,
       'objectlist1': objectlist1,
       'objectlist2': objectlist2,
       'reportbucket': bucket,
       'reportstart': start,
       'reportend': end,
       'bucketnames': bucketnames,
       'paginator': paginator,
       'hits' : hits,
       'fullhits': fullhits,
       'is_popup': is_popup,
       'base_request_path': base_request_path,
       # Never reset the breadcrumbs if an argument entity was passed.
       # Otherwise depend on the value in the report class.
       'reset_crumbs': reportclass.reset_crumbs and entity == None,
       'title': (entity and _('%(title)s for %(entity)s') % {'title': force_unicode(reportclass.title), 'entity':force_unicode(entity)}) or reportclass.title,
       'rowheader': head_scroll,
       'rowheaderfrozen': head_frozen,
       'crossheader': issubclass(reportclass, TableReport) and _create_crossheader(request, reportclass),
       'columnheader': issubclass(reportclass, TableReport) and _create_columnheader(request, reportclass, bucketlist),
     }
  if 'extra_context' in args: context.update(args['extra_context'])

  # Render the view, optionally setting the last-modified http header
  return HttpResponse(
    loader.render_to_string(reportclass.template, context, context_instance=RequestContext(request)),
    )


class GridReport(View):
  '''
  The base class for all jqgrid views.
  The parameter values defined here are used as defaults for all reports, but
  can be overwritten.
  '''
  # Points to template to be used
  template = 'admin/base_site_grid.html'
  
  # The title of the report. Used for the window title
  title = ''

  # The resultset that returns a list of entities that are to be
  # included in the report.
  # This query is used to return the number of records.
  # It is also used to generate the actual results, in case no method
  # "resultlist2" is provided on the class.
  basequeryset = None
  
  # Whether or not the breadcrumbs are reset when we open the report
  reset_crumbs = True

  # Extra javascript files to import for running the report
  javascript_imports = []   #TODO not used yet

  # Specifies which column is used for an initial filter
  default_sort = '1a'

  # A model class from which we can inherit information.
  model = None

  # Allow editing in this report or not
  editable = True

  # Number of columns frozen in the report
  frozenColumns = 0

  # A list with required user permissions to view the report
  permissions = []

  @method_decorator(staff_member_required)
  @method_decorator(csrf_protect)
  def dispatch(self, request, *args, **kwargs):    
    # Verify the user is authorized to view the report
    for perm in self.permissions:
      if not request.user.has_perm(perm):
        return HttpResponseForbidden('<h1>%s</h1>' % _('Permission denied'))
    
    # Dispatch to the correct method
    method = request.method.lower()
    if method == 'get':
      return self.get(request, *args, **kwargs)
    elif method == 'post':
      return self.post(request, *args, **kwargs)
    else:
      return HttpResponseNotAllowed(['get','post'])


  @classmethod
  def _generate_csv_data(reportclass, request):
    sf = cStringIO.StringIO()
    encoding = settings.DEFAULT_CHARSET
    if get_format('DECIMAL_SEPARATOR', request.LANGUAGE_CODE, True) == ',':
      writer = csv.writer(sf, quoting=csv.QUOTE_NONNUMERIC, delimiter=';')
    else:
      writer = csv.writer(sf, quoting=csv.QUOTE_NONNUMERIC, delimiter=',')
    if translation.get_language() != request.LANGUAGE_CODE:
      translation.activate(request.LANGUAGE_CODE)

    # Write a header row
    fields = [ force_unicode(f.title).title().encode(encoding,"ignore") for f in reportclass.rows ]
    writer.writerow(fields)
    yield sf.getvalue()

    # Write the report content
    query = reportclass._apply_sort(request, reportclass.filter_items(request, reportclass.basequeryset).using(request.database))
    fields = [ i.field_name for i in reportclass.rows ]
    for row in query.values(*fields):
      # Clear the return string buffer
      sf.truncate(0)
      # Build the return value, encoding all output
      if hasattr(row, "__getitem__"):
        fields = [ row[f.field_name]==None and ' ' or unicode(_localize(row[f.field_name])).encode(encoding,"ignore") for f in reportclass.rows ]
      else:
        fields = [ getattr(row,f.field_name)==None and ' ' or unicode(_localize(getattr(row,f.field_name))).encode(encoding,"ignore") for f in reportclass.rows ]
      # Return string
      writer.writerow(fields)
      yield sf.getvalue()


  @classmethod
  def _apply_sort(reportclass, request, query):
    sort = 'sidx' in request.GET and request.GET['sidx'] or reportclass.rows[0].name
    if 'sord' in request.GET and request.GET['sord'] == 'desc':
      sort = "-%s" % sort
    return reportclass.filter_items(request, query).order_by(sort)


  @classmethod
  def _generate_json_data(reportclass, request):
    page = 'page' in request.GET and int(request.GET['page']) or 1
    recs = reportclass.filter_items(request, reportclass.basequeryset).using(request.database).count()
    total_pages = recs / request.pagesize + 1
    if page > total_pages: page = total_pages
    #if hasattr(reportclass,'resultlist2'):
      # SQL override provided of type 2
    #  query = reportclass._apply_filter_and_sort(request, reportclass.resultlist2(request, counter, bucket, start, end, sortsql=sortsql))
    #elif hasattr(reportclass,'resultlist1'):
      # SQL override provided of type 1
    #  query = reportclass._apply_filter_and_sort(request, reportclass.resultlist1(request, counter, bucket, start, end, sortsql=sortsql))
    #else:
      # No SQL override provided
    query = reportclass._apply_sort(request, reportclass.filter_items(request, reportclass.basequeryset).using(request.database))

    yield '{"total":%d,\n' % total_pages
    yield '"page":%d,\n' % page
    yield '"records":%d,\n' % recs
    yield '"rows":[\n'
    cnt = (page-1)*request.pagesize+1
    first = True

    # # TREEGRID
    #from django.db import connections, DEFAULT_DB_ALIAS
    #cursor = connections[DEFAULT_DB_ALIAS].cursor()
    #cursor.execute('''
    #  select node.name,node.description,node.category,node.subcategory,node.operation_id,node.owner_id,node.price,node.lastmodified,node.level,node.lft,node.rght,node.rght=node.lft+1
    #  from item as node
    #  left outer join item as parent0
    #    on node.lft between parent0.lft and parent0.rght and parent0.level = 0 and node.level >= 0
    #  left outer join item as parent1
    #    on node.lft between parent1.lft and parent1.rght and parent1.level = 1 and node.level >= 1
    #  left outer join item as parent2
    #    on node.lft between parent2.lft and parent2.rght and parent2.level = 2 and node.level >= 2
    #  where node.level = 0
    #  order by parent0.description asc, parent1.description asc, parent2.description asc, node.level, node.description, node.name
    #  ''')
    #for row in cursor.fetchall():
    #  if first:
    #    first = False
    #    yield '{"%s","%s","%s","%s","%s","%s","%s","%s",%d,%d,%d,%s,false]}\n' %(row[0], row[1], row[2], row[3], row[4], row[5], row[6], row[7], row[8], row[9], row[10], row[11] and 'true' or 'false')
    #  else:
    #    yield ',{"%s","%s","%s","%s","%s","%s","%s","%s",%d,%d,%d,%s,false]}\n' %(row[0], row[1], row[2], row[3], row[4], row[5], row[6], row[7], row[8], row[9], row[10], row[11] and 'true' or 'false')
    #yield ']}\n'

    fields = [ i.field_name for i in reportclass.rows ]
    #if False: # TREEGRID
    #  fields.append('level')
    #  fields.append('lft')
    #  fields.append('rght')
    #  fields.append('isLeaf')
    #  fields.append('expanded')
    for i in query[cnt-1:cnt+request.pagesize].values(*fields):
      if first:
        r = [ '{' ]
        first = False
      else:
        r = [ ',\n{' ]
      first2 = True
      for f in reportclass.rows:
        if first2:
          r.append('"%s":"%s"' % (f.name,i[f.field_name]))
          first2 = False
        elif i[f.field_name] != None:
          r.append(', "%s":"%s"' % (f.name,i[f.field_name]))
      #if False:    # TREEGRID
      #  r.append(', %d, %d, %d, %s, %s' % (i['level'],i['lft'],i['rght'], i['isLeaf'] and 'true' or 'false', i['expanded'] and 'true' or 'false' ))
      r.append(',"b1":"y","b2":"z"')
      r.append('}')
      yield ''.join(r)
      cnt = cnt + 1
    yield '\n]}\n'


  @classmethod
  def post(reportclass, request, **args):
    if "csv_file" in request.FILES:
      # Uploading a CSV file
      if not reportclass.model:
        messages.add_message(request, messages.ERROR, _('Invalid upload request'))
        return HttpResponseRedirect(request.prefix + request.get_full_path())
      if not reportclass.editable or not request.user.has_perm('%s.%s' % (reportclass.model._meta.app_label, reportclass.model._meta.get_add_permission())):
        messages.add_message(request, messages.ERROR, _('Not authorized'))
        return HttpResponseRedirect(request.prefix + request.get_full_path())
      (warnings,errors,changed,added) = reportclass.parseUpload(request, request.FILES['csv_file'].read())
      # TODO display errors as a downloadable list in the dialog?
      if len(errors) > 0:
        messages.add_message(request, messages.INFO,
         _('File upload aborted with errors: changed %(changed)d and added %(added)d records') % {'changed': changed, 'added': added}
         )
        for i in errors: messages.add_message(request, messages.INFO, i)
      elif len(warnings) > 0:
        messages.add_message(request, messages.INFO,
          _('Uploaded file processed with warnings: changed %(changed)d and added %(added)d records') % {'changed': changed, 'added': added}
          )
        for i in warnings: messages.add_message(request, messages.INFO, i)
      else:
        messages.add_message(request, messages.INFO,
          _('Uploaded data successfully: changed %(changed)d and added %(added)d records') % {'changed': changed, 'added': added}
          )
      return HttpResponseRedirect(request.prefix + request.get_full_path())      
    else:
      # Inline edit
      d = reportclass.model.objects.get(pk=request.POST['id'])
      for i in request.POST:
        setattr(d, i, request.POST[i])
      d.save()
      resp = HttpResponse()
      resp.content = "OK"
      resp.status_code = 200
      return resp

  @classmethod
  def get(reportclass, request, **args):
    fmt = request.GET.get('format', None)
    if not fmt:
      # Return HTML page
      # Pick up the list of time buckets      
      if issubclass(reportclass, GridPivot):
        pref = request.user.get_profile()
        (bucket,start,end,bucketlist) = getBuckets(request, pref)
        bucketnames = Bucket.objects.order_by('name').values_list('name', flat=True)
      else:
        bucket = start = end = bucketlist = bucketnames = None      
      return render(request, reportclass.template, {
        'reportclass': reportclass,
        'title': reportclass.title,
        'reportbucket': bucket,
        'reportstart': start,
        'reportend': end,
        'is_popup': request.GET.has_key('pop'),
        'bucketnames': bucketnames,
        'bucketlist': bucketlist,
        'model': reportclass.model,
        'reset_crumbs': reportclass.reset_crumbs,
        'hasaddperm': reportclass.editable and reportclass.model and request.user.has_perm('%s.%s' % (reportclass.model._meta.app_label, reportclass.model._meta.get_add_permission())),
        'haschangeperm': reportclass.editable and reportclass.model and request.user.has_perm('%s.%s' % (reportclass.model._meta.app_label, reportclass.model._meta.get_change_permission())),
        })
    elif fmt == 'json':
      # Return JSON data to fill the grid
      return HttpResponse(
         mimetype = 'application/json; charset=%s' % settings.DEFAULT_CHARSET,
         content = reportclass._generate_json_data(request)
         )
    elif fmt == 'csvlist' or fmt == 'csvtable':
      # Return CSV data to export the data
      response = HttpResponse(
         mimetype= 'text/csv; charset=%s' % settings.DEFAULT_CHARSET,
         content = reportclass._generate_csv_data(request)
         )
      response['Content-Disposition'] = 'attachment; filename=%s.csv' % iri_to_uri(reportclass.title.lower())
      return response
    else:
      raise Http404('Unknown format type')

  @classmethod
  def parseUpload(reportclass, request, data):
      '''
      This method reads CSV data from a string (in memory) and creates or updates
      the database records.
      The data must follow the following format:
        - the first row contains a header, listing all field names
        - a first character # marks a comment line
        - empty rows are skipped
  
      Limitation: SQLite doesnt validate the input data appropriately.
      E.g. It is possible to store character strings in a number field. An error
      is generated only when reading the record and trying to convert it to a
      Python number.
      E.g. It is possible to store invalid strings in a Date field.
      '''
      entityclass = reportclass.model
      headers = []
      rownumber = 0
      changed = 0
      added = 0
      warnings = []
      errors = []
      content_type_id = ContentType.objects.get_for_model(entityclass).pk
  
      transaction.enter_transaction_management(using=request.database)
      transaction.managed(True, using=request.database)
      try:
        # Loop through the data records
        has_pk_field = False
        for row in csv.reader(data.splitlines()):
          rownumber += 1
  
          ### Case 1: The first line is read as a header line
          if rownumber == 1:
            for col in row:
              col = col.strip().strip('#').lower()
              if col == "":
                headers.append(False)
                continue
              ok = False
              for i in entityclass._meta.fields:
                if col == i.name.lower() or col == i.verbose_name.lower():
                  if i.editable == True:
                    headers.append(i)
                  else:
                    headers.append(False)
                  ok = True
                  break
              if not ok: errors.append(_('Incorrect field %(column)s') % {'column': col})
              if col == entityclass._meta.pk.name.lower() \
                or col == entityclass._meta.pk.verbose_name.lower():
                  has_pk_field = True
            if not has_pk_field and not isinstance(entityclass._meta.pk, AutoField):
              # The primary key is not an auto-generated id and it is not mapped in the input...
              errors.append(_('Missing primary key field %(key)s') % {'key': entityclass._meta.pk.name})
            # Abort when there are errors
            if len(errors) > 0: return (warnings,errors,0,0)
            # Create a form class that will be used to validate the data
            UploadForm = modelform_factory(entityclass,
              fields = tuple([i.name for i in headers if isinstance(i,Field)]),
              formfield_callback = lambda f: (isinstance(f, RelatedField) and f.formfield(using=request.database)) or f.formfield()
              )
  
          ### Case 2: Skip empty rows and comments rows
          elif len(row) == 0 or row[0].startswith('#'):
            continue
  
          ### Case 3: Process a data row
          else:
            try:
              # Step 1: Build a dictionary with all data fields
              d = {}
              colnum = 0
              for col in row:
                # More fields in data row than headers. Move on to the next row.
                if colnum >= len(headers): break
                if isinstance(headers[colnum],Field): d[headers[colnum].name] = col.strip()
                colnum += 1
  
              # Step 2: Fill the form with data, either updating an existing
              # instance or creating a new one.
              if has_pk_field:
                # A primary key is part of the input fields
                try:
                  # Try to find an existing record with the same primary key
                  it = entityclass.objects.using(request.database).get(pk=d[entityclass._meta.pk.name])
                  form = UploadForm(d, instance=it)
                except entityclass.DoesNotExist:
                  form = UploadForm(d)
                  it = None
              else:
                # No primary key required for this model
                form = UploadForm(d)
                it = None
  
              # Step 3: Validate the data and save to the database
              if form.has_changed():
                try:
                  obj = form.save()
                  LogEntry(
                      user_id         = request.user.pk,
                      content_type_id = content_type_id,
                      object_id       = obj.pk,
                      object_repr     = force_unicode(obj),
                      action_flag     = it and CHANGE or ADDITION,
                      change_message  = _('Changed %s.') % get_text_list(form.changed_data, _('and'))
                  ).save(using=request.database)
                  if it:
                    changed += 1
                  else:
                    added += 1
                except Exception, e:
                  # Validation fails
                  for error in form.non_field_errors():
                    warnings.append(
                      _('Row %(rownum)s: %(message)s') % {
                        'rownum': rownumber, 'message': error
                      })
                  for field in form:
                    for error in field.errors:
                      warnings.append(
                        _('Row %(rownum)s field %(field)s: %(data)s: %(message)s') % {
                          'rownum': rownumber, 'data': d[field.name],
                          'field': field.name, 'message': error
                        })
  
              # Step 4: Commit the database changes from time to time
              if rownumber % 500 == 0: transaction.commit(using=request.database)
            except Exception, e:
              errors.append(_("Exception during upload: %(message)s") % {'message': e,})
      finally:
        transaction.commit(using=request.database)
        transaction.leave_transaction_management(using=request.database)
  
      # Report all failed records
      return (warnings, errors, changed, added)

  @classmethod
  def get_filters(reportclass, request):
    _search = request.GET.get('_search')
    filters = None
  
    if _search == 'true':
        _filters = request.GET.get('filters')
        try:
            filters = _filters and json.loads(_filters)
        except ValueError:
            return None
  
        if filters is None:
            field = request.GET.get('searchField')
            op = request.GET.get('searchOper')
            data = request.GET.get('searchString')
  
            if all([field, op, data]):
                filters = {
                    'groupOp': 'AND',
                    'rules': [{ 'op': op, 'field': field, 'data': data }]
                }
    return filters
  
  
  @classmethod
  def filter_items(reportclass, request, items):
    # TODO: Add option to use case insensitive filters
    # TODO: Add more support for RelatedFields (searching and displaying)
    # FIXME: Validate data types are correct for field being searched.
    filter_map = {
        # jqgrid op: (django_lookup, use_exclude)
        'ne': ('%(field)s__exact', True),
        'bn': ('%(field)s__startswith', True),
        'en': ('%(field)s__endswith',  True),
        'nc': ('%(field)s__contains', True),
        'ni': ('%(field)s__in', True),
        'in': ('%(field)s__in', False),
        'eq': ('%(field)s__exact', False),
        'bw': ('%(field)s__startswith', False),
        'gt': ('%(field)s__gt', False),
        'ge': ('%(field)s__gte', False),
        'lt': ('%(field)s__lt', False),
        'le': ('%(field)s__lte', False),
        'ew': ('%(field)s__endswith', False),
        'cn': ('%(field)s__contains', False)
    }
    _filters = reportclass.get_filters(request)
    if _filters is None:
        return items
  
    q_filters = []
    for rule in _filters['rules']:
        op, field, data = rule['op'], rule['field'], rule['data']
        # FIXME: Restrict what lookups performed against RelatedFields
        field_class = reportclass.model._meta.get_field_by_name(field)[0]
        if isinstance(field_class, models.related.RelatedObject):
            op = 'eq'
        filter_fmt, exclude = filter_map[op]
        filter_str = smart_str(filter_fmt % {'field': field})
        if filter_fmt.endswith('__in'):
            filter_kwargs = {filter_str: data.split(',')}
        else:
            filter_kwargs = {filter_str: smart_str(data)}
  
        if exclude:
            q_filters.append(~models.Q(**filter_kwargs))
        else:
            q_filters.append(models.Q(**filter_kwargs))
  
    if _filters['groupOp'].upper() == 'OR':
        filters = reduce(operator.ior, q_filters)
    else:
        filters = reduce(operator.iand, q_filters)
    return items.filter(filters)

  
class GridPivot(GridReport):

  # Cross definitions.
  # Possible attributes for a cross field are:
  #   - title:
  #     Name of the cross that is displayed to the user.
  #     It defaults to the name of the field.
  #   - editable:
  #     True when the field is editable in the page.
  #     The default value is false.
  crosses = ()

  template = 'admin/base_site_gridpivot.html'


def _localize(value, use_l10n=None):
  '''
  Localize numbers.
  Dates are always represented as YYYY-MM-DD hh:mm:ss since this is
  a format that is understood uniformly across different regions in the
  world.
  '''
  if callable(value):
    value = value()
  if isinstance(value, (Decimal, float, int, long)):
    return number_format(value, use_l10n=use_l10n)
  elif isinstance(value, (list,tuple) ):
    return "|".join([ unicode(_localize(i)) for i in value ])
  else:
    return value


def getBuckets(request, pref=None, bucket=None, start=None, end=None):
  '''
  This function gets passed a name of a bucketization.
  It returns a list of buckets.
  The data are retrieved from the database table dates, and are
  stored in a python variable for performance
  '''
  # Pick up the user preferences
  if pref == None: pref = request.user.get_profile()

  # Select the bucket size (unless it is passed as argument)
  if not bucket:
    bucket = request.GET.get('reportbucket')
    if not bucket:
      try:
        bucket = Bucket.objects.using(request.database).get(name=pref.buckets)
      except:
        try: bucket = Bucket.objects.using(request.database).order_by('name')[0].name
        except: bucket = None
    elif pref.buckets != bucket:
      try: pref.buckets = Bucket.objects.using(request.database).get(name=bucket).name
      except: bucket = None
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
        if not start:
          try: start = datetime.strptime(Parameter.objects.get(name="currentdate").value, "%Y-%m-%d %H:%M:%S").date()
          except: start = datetime.now()
    else:
      try: start = pref.startdate
      except: pass
      if not start:
        try: start = datetime.strptime(Parameter.objects.get(name="currentdate").value, "%Y-%m-%d %H:%M:%S").date()
        except: start = datetime.now()

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
    else:
      try: end = pref.enddate
      except: pass

  # Filter based on the start and end date
  if not bucket:
    return (None, start, end, None)
  else:
    res = BucketDetail.objects.using(request.database).filter(bucket=bucket)
    if start: res = res.filter(startdate__gte=start)
    if end: res = res.filter(startdate__lt=end)
    return (unicode(bucket), start, end, res.values('name','startdate','enddate'))
