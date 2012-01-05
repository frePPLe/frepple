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
import math
import codecs

from django.conf import settings
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
from django.utils import translation
from django.utils.decorators import method_decorator
from django.utils.encoding import smart_str
from django.utils.html import escape
from django.utils.translation import ugettext as _
from django.utils.formats import get_format, number_format
from django.utils import simplejson as json
from django.utils.text import capfirst, get_text_list
from django.utils.encoding import iri_to_uri, force_unicode
from django.contrib.admin.models import LogEntry, CHANGE, ADDITION
from django.contrib.contenttypes.models import ContentType
from django.views.generic.base import View
from freppledb.input.models import Parameter, BucketDetail, Bucket


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
    if self.unformat: o.append("unformat:'%s'," % self.unformat)
    if self.searchrules: o.append("searchrules:{%s}," % self.searchrules)
    if self.extra: o.append("%s," % self.extra)
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

    
def getBOM(encoding):
  if encoding == 'utf_32_be': return codecs.BOM_UTF32_BE
  elif encoding == 'utf_32_le': return codecs.BOM_UTF32_LE
  elif encoding == 'utf_16_be': return codecs.BOM_UTF16_BE
  elif encoding == 'utf_16_le': return codecs.BOM_UTF16_LE
  elif encoding == 'utf-8': return codecs.BOM_UTF8
  else: return ''
  
  
class UTF8Recoder:
  """
  Iterator that reads an encoded data buffer and re-encodes the input to UTF-8.
  """
  def __init__(self, data):
    # Detect the encoding of the data by scanning the BOM. 
    # Skip the BOM header if it is found.
    if data.startswith(codecs.BOM_UTF32_BE): 
      self.reader = codecs.getreader('utf_32_be')(cStringIO.StringIO(data))
      self.reader.read(1)      
    elif data.startswith(codecs.BOM_UTF32_LE): 
      self.reader = codecs.getreader('utf_32_le')(cStringIO.StringIO(data))
      self.reader.read(1)      
    elif data.startswith(codecs.BOM_UTF16_BE): 
      self.reader = codecs.getreader('utf_16_be')(cStringIO.StringIO(data))
      self.reader.read(1)      
    elif data.startswith(codecs.BOM_UTF16_LE): 
      self.reader = codecs.getreader('utf_16_le')(cStringIO.StringIO(data))
      self.reader.read(1)      
    elif data.startswith(codecs.BOM_UTF8): 
      self.reader = codecs.getreader('utf-8')(cStringIO.StringIO(data))
      self.reader.read(1)      
    else:       
      # No BOM header found. We assume the data is encoded in the default CSV character set.
      self.reader = codecs.getreader(settings.CSV_CHARSET)(cStringIO.StringIO(data)) 

  def __iter__(self):
    return self

  def next(self):
    return self.reader.next().encode("utf-8")


class UnicodeReader:
  """
  A CSV reader which will iterate over lines in the CSV data buffer.
  The reader will scan the BOM header in the data to detect the right encoding. 
  """
  def __init__(self, data, **kwds):
    self.reader = csv.reader(UTF8Recoder(data), **kwds)

  def next(self):
    row = self.reader.next()
    return [unicode(s, "utf-8") for s in row]

  def __iter__(self):
    return self

    
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
  # "query" is provided on the class.
  basequeryset = None
  
  # Whether or not the breadcrumbs are reset when we open the report
  reset_crumbs = True

  # Specifies which column is used for an initial filter
  default_sort = '1a'    # TODO "default_sort" not used yet

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
  def _generate_csv_data(reportclass, request, *args, **kwargs):
    sf = cStringIO.StringIO()    
    if get_format('DECIMAL_SEPARATOR', request.LANGUAGE_CODE, True) == ',':
      writer = csv.writer(sf, quoting=csv.QUOTE_NONNUMERIC, delimiter=';')
    else:
      writer = csv.writer(sf, quoting=csv.QUOTE_NONNUMERIC, delimiter=',')
    if translation.get_language() != request.LANGUAGE_CODE:
      translation.activate(request.LANGUAGE_CODE)

    # Write a Unicode Byte Order Mark header, aka BOM (Excel needs it to open UTF-8 file properly)
    encoding = settings.CSV_CHARSET
    sf.write(getBOM(encoding))
      
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
    return query.order_by(sort)


  @classmethod
  def _generate_json_data(reportclass, request, *args, **kwargs):
    page = 'page' in request.GET and int(request.GET['page']) or 1
    query = reportclass.filter_items(request, reportclass.basequeryset).using(request.database)
    recs = query.count()
    total_pages = math.ceil(float(recs) / request.pagesize)
    if page > total_pages: page = total_pages
    query = reportclass._apply_sort(request, query)

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

    # GridReport
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
        s = isinstance(i[f.field_name], basestring) and escape(i[f.field_name]) or i[f.field_name]
        if first2:
          r.append('"%s":"%s"' % (f.name,s))
          first2 = False
        elif i[f.field_name] != None:
          r.append(', "%s":"%s"' % (f.name,s))
      #if False:    # TREEGRID
      #  r.append(', %d, %d, %d, %s, %s' % (i['level'],i['lft'],i['rght'], i['isLeaf'] and 'true' or 'false', i['expanded'] and 'true' or 'false' ))
      r.append('}')
      yield ''.join(r)
    yield '\n]}\n'


  @classmethod
  def post(reportclass, request, *args, **kwargs):
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
  def get(reportclass, request, *args, **kwargs):
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
        'title': (args and args[0] and _('%(title)s for %(entity)s') % {'title': force_unicode(reportclass.title), 'entity':force_unicode(args[0])}) or reportclass.title,
        'reportbucket': bucket,
        'reportstart': start,
        'reportend': end,
        'is_popup': request.GET.has_key('pop'),
        'args': args,
        'filters': reportclass.getQueryString(request),
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
         content = reportclass._generate_json_data(request, *args, **kwargs)
         )
    elif fmt == 'csvlist' or fmt == 'csvtable':
      # Return CSV data to export the data
      response = HttpResponse(
         mimetype= 'text/csv; charset=%s' % settings.DEFAULT_CHARSET,
         content = reportclass._generate_csv_data(request, *args, **kwargs)
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
        for row in UnicodeReader(data):
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
  def _getRowByName(reportclass, name):
    if not hasattr(reportclass,'_rowsByName'):
      reportclass._rowsByName = {}
      for i in reportclass.rows:
        reportclass._rowsByName[i.name] = i
    return reportclass._rowsByName[name]

  
  _filter_map_jqgrid_django = {
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
  

  _filter_map_django_jqgrid = {
      # django lookup: jqgrid op
      'in': 'in',
      'exact': 'eq',
      'startswith': 'bw',
      'gt': 'gt',
      'gte': 'ge',
      'lt': 'lt',
      'lte': 'le',
      'endswith': 'ew',
      'contains': 'cn',
  }
      
      
  @classmethod
  def getQueryString(reportclass, request):
    # Django-style filtering (which uses URL parameters) are converted to a jqgrid filter expression
    filtered = False
    filters = ['{"groupOp":"AND","rules":[']
    for i,j in request.GET.iteritems():
      for r in reportclass.rows:
        if i.startswith(r.field_name):
          filtered = True
          operator = (i==r.field_name) and 'exact' or i[i.rfind('_')+1:]
          filters.append('{"field":"%s","op":"%s","data":"%s"},' % (r.field_name, reportclass._filter_map_django_jqgrid[operator], j))
    if not filtered: return None
    filters.append(']}')
    return ''.join(filters)
        
                
  @classmethod
  def _get_q_filter(reportclass, filterdata):
    q_filters = []
    for rule in filterdata['rules']:
        op, field, data = rule['op'], rule['field'], rule['data']
        filter_fmt, exclude = reportclass._filter_map_jqgrid_django[op]
        filter_str = smart_str(filter_fmt % {'field': reportclass._getRowByName(field).field_name})
        if filter_fmt.endswith('__in'):
            filter_kwargs = {filter_str: data.split(',')}
        else:
            filter_kwargs = {filter_str: smart_str(data)}
        if exclude:
            q_filters.append(~models.Q(**filter_kwargs))
        else:
            q_filters.append(models.Q(**filter_kwargs))    
    if u'groups' in filterdata:
      for group in filterdata['groups']:
        z = reportclass._get_q_filter(group)
        if z: q_filters.append(z)
    if len(q_filters) == 0:
      return None
    elif filterdata['groupOp'].upper() == 'OR':
      return reduce(operator.ior, q_filters)
    else:
      return reduce(operator.iand, q_filters)

      
  @classmethod
  def filter_items(reportclass, request, items):

    filters = None

    # Jqgrid-style filtering
    if request.GET.get('_search') == 'true':     
      # Validate complex search JSON data
      _filters = request.GET.get('filters')
      try:
        filters = _filters and json.loads(_filters)
      except ValueError:
        filters = None
  
      # Single field searching, which is currently not used
      if filters is None:
        field = request.GET.get('searchField')
        op = request.GET.get('searchOper')
        data = request.GET.get('searchString')
        if all([field, op, data]):
          filters = {
              'groupOp': 'AND',
              'rules': [{ 'op': op, 'field': field, 'data': data }]
          }    
    if filters:
      z = reportclass._get_q_filter(filters)
      return z and items.filter(z) or items
    
    # Django-style filtering, using URL parameters
    for i,j in request.GET.iteritems():
      for r in reportclass.rows:
        if i.startswith(r.field_name):
          items = items.filter(**{i:j})
    return items

  
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
  
  
  @classmethod
  def _generate_json_data(reportclass, request, *args, **kwargs):

    # Pick up the list of time buckets      
    pref = request.user.get_profile()
    (bucket,start,end,bucketlist) = getBuckets(request, pref)

    # Prepare the query    
    if args and args[0]:
      page = 1
      recs = 1
      total_pages = 1
      query = reportclass.query(request, reportclass.basequeryset.filter(pk__exact=args[0]), bucket, start, end, sortsql="1 asc")
    else:
      page = 'page' in request.GET and int(request.GET['page']) or 1
      recs = reportclass.filter_items(request, reportclass.basequeryset).using(request.database).count()
      total_pages = math.ceil(float(recs) / request.pagesize)
      if page > total_pages: page = total_pages
      cnt = (page-1)*request.pagesize+1
      query = reportclass.query(request, reportclass.basequeryset[cnt-1:cnt+request.pagesize], bucket, start, end, sortsql="1 asc")

    # Generate header of the output
    yield '{"total":%d,\n' % total_pages
    yield '"page":%d,\n' % page
    yield '"records":%d,\n' % recs
    yield '"rows":[\n'
    
    # Generate output
    currentkey = None
    r = []
    for i in query:
      # We use the first field in the output to recognize new rows.
      if currentkey <> i[reportclass.rows[0].name]:
        # New line
        if currentkey:
          yield ''.join(r)
          r = [ '},\n{' ]
        else:
          r = [ '{' ] 
        currentkey = i[reportclass.rows[0].name]
        first2 = True
        for f in reportclass.rows:
          s = isinstance(i[f.name], basestring) and escape(i[f.name].encode(settings.DEFAULT_CHARSET,"ignore")) or i[f.name]
          if first2:
            r.append('"%s":"%s"' % (f.name,s))
            first2 = False
          else:
            r.append(', "%s":"%s"' % (f.name,s))
      r.append(', "%s":[' % i['bucket'])
      first2 = True
      for f in reportclass.crosses:
        if first2:
          r.append('%s' % i[f[0]])
          first2 = False
        else:
          r.append(', %s' % i[f[0]])
      r.append(']')
    r.append('}')
    r.append('\n]}\n')
    yield ''.join(r)


  @classmethod
  def _generate_csv_data(reportclass, request, *args, **kwargs):  # TODO
    sf = cStringIO.StringIO()    
    if get_format('DECIMAL_SEPARATOR', request.LANGUAGE_CODE, True) == ',':
      writer = csv.writer(sf, quoting=csv.QUOTE_NONNUMERIC, delimiter=';')
    else:
      writer = csv.writer(sf, quoting=csv.QUOTE_NONNUMERIC, delimiter=',')
    if translation.get_language() != request.LANGUAGE_CODE:
      translation.activate(request.LANGUAGE_CODE)
    listformat = (request.GET.get('format','csvlist') == 'csvlist')
      
    # Pick up the list of time buckets      
    pref = request.user.get_profile()
    (bucket,start,end,bucketlist) = getBuckets(request, pref)

    # Prepare the query
    if args and args[0]:
      query = reportclass.query(request, reportclass.basequeryset.filter(pk__exact=args[0]), bucket, start, end, sortsql="1 asc")
    else:
      query = reportclass.query(request, reportclass.basequeryset, bucket, start, end, sortsql="1 asc")

    # Write a Unicode Byte Order Mark header, aka BOM (Excel needs it to open UTF-8 file properly)
    encoding = settings.CSV_CHARSET
    sf.write(getBOM(encoding))

    # Write a header row
    fields = [ force_unicode(f.title).title().encode(encoding,"ignore") for f in reportclass.rows ]
    if listformat:
      fields.extend([ capfirst(force_unicode(_('bucket'))).encode(encoding,"ignore") ])
      fields.extend([ ('title' in s[1] and capfirst(_(s[1]['title'])) or capfirst(_(s[0]))).encode(encoding,"ignore") for s in reportclass.crosses ])
    else:
      fields.extend( [capfirst(_('data field')).encode(encoding,"ignore")])
      fields.extend([ unicode(b['name']).encode(encoding,"ignore") for b in bucketlist])
    writer.writerow(fields)
    yield sf.getvalue()

    # Write the report content
    if listformat:
      for row in query:
        # Clear the return string buffer
        sf.truncate(0)
        # Data for rows
        if hasattr(row, "__getitem__"):
          fields = [ row[f.name]==None and ' ' or unicode(row[f.name]).encode(encoding,"ignore") for f in reportclass.rows ]
          fields.extend([ row['bucket'].encode(encoding,"ignore") ])
          fields.extend([ row[f[0]]==None and ' ' or unicode(_localize(row[f[0]])).encode(encoding,"ignore") for f in reportclass.crosses ])
        else:
          fields = [ getattr(row,f.name)==None and ' ' or unicode(getattr(row,f.name)).encode(encoding,"ignore") for f in reportclass.rows ]
          fields.extend([ getattr(row,'bucket').encode(encoding,"ignore") ])
          fields.extend([ getattr(row,f[0])==None and ' ' or unicode(_localize(getattr(row,f[0]))).encode(encoding,"ignore") for f in reportclass.crosses ])
        # Return string
        writer.writerow(fields)
        yield sf.getvalue()
    else:
      currentkey = None
      for row in query:
        # We use the first field in the output to recognize new rows.
        if not currentkey:
          currentkey = row[reportclass.rows[0].name]
          row_of_buckets = [ row ]
        elif currentkey == row[reportclass.rows[0].name]:
          row_of_buckets.append(row)
        else:
          # Write an entity
          for cross in reportclass.crosses:
            # Clear the return string buffer
            sf.truncate(0)
            fields = [ unicode(row_of_buckets[0][s.name]).encode(encoding,"ignore") for s in reportclass.rows ]
            fields.extend( [('title' in cross[1] and capfirst(_(cross[1]['title']))).encode(encoding,"ignore") or capfirst(_(cross[0])).encode(encoding,"ignore")] )
            fields.extend([ unicode(_localize(bucket[cross[0]])).encode(encoding,"ignore") for bucket in row_of_buckets ])
            # Return string
            writer.writerow(fields)
            yield sf.getvalue()
          currentkey = row[reportclass.rows[0].name]
          row_of_buckets = [row]
      # Write the last entity
      for cross in reportclass.crosses:
        # Clear the return string buffer
        sf.truncate(0)
        fields = [ unicode(row_of_buckets[0][s.name]).encode(encoding,"ignore") for s in reportclass.rows ]
        fields.extend( [('title' in cross[1] and capfirst(_(cross[1]['title']))).encode(encoding,"ignore") or capfirst(_(cross[0])).encode(encoding,"ignore")] )
        fields.extend([ unicode(_localize(bucket[cross[0]])).encode(encoding,"ignore") for bucket in row_of_buckets ])
        # Return string
        writer.writerow(fields)
        yield sf.getvalue()
            

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
