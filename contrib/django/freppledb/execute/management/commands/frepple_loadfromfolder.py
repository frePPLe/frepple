#
# Copyright (C) 2011-2016 by frePPLe bvba
#
# This library is free software; you can redistribute it and/or modify it
# under the terms of the GNU Affero General Public License as published
# by the Free Software Foundation; either version 3 of the License, or
# (at your option) any later version.
#
# This library is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU Affero
# General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public
# License along with this program.  If not, see <http://www.gnu.org/licenses/>.
#

import os
import sys
import csv
import codecs
import collections
from datetime import datetime
from io import StringIO, BytesIO

from django.core.management.base import BaseCommand, CommandError

from django.contrib.auth import get_permission_codename
from django.contrib.auth.models import Group
from django.contrib.contenttypes.models import ContentType
from django.db import DEFAULT_DB_ALIAS
from django.db import connections, transaction, models
from django.conf import settings
from django.utils.formats import get_format
from django.utils import translation
from django.db.models.fields import Field, CharField, IntegerField, AutoField
from django.forms.models import modelform_factory
from django.db.models.fields.related import RelatedField
from django.contrib.admin.models import LogEntry, CHANGE, ADDITION, DELETION
from django.utils.text import capfirst, get_text_list
from django.utils.encoding import force_text

from optparse import make_option
from django.db.models.loading import get_model
from time import localtime, strftime

from freppledb.execute.models import Task
from freppledb.common.report import GridReport
from freppledb import VERSION
from freppledb.common.models import User, Comment, Parameter, BucketDetail, Bucket, HierarchyModel
#from builtins import None
EXCLUDE_FROM_BULK_OPERATIONS = (Group, User, Comment)


class Command(BaseCommand):
  help = "Loads CSV files from a specified folder into the frePPLe database"
  option_list = BaseCommand.option_list + (
    make_option(
      '--user', dest='user', type='string',
      help='User running the command'
      ),
    make_option(
      '--database', action='store', dest='database', default=DEFAULT_DB_ALIAS,
      help='Nominates a specific database to load data from and export results into'
      ),
    make_option(
      '--task', dest='task', type='int',
      help='Task identifier (generated automatically if not provided)'
      ),
  )
  args = 'CSV file(s)'
  
  requires_system_checks = False

  def get_version(self):
    return VERSION

  def handle(self, *args, **options):
    # Pick up the options
    if 'database' in options:
      self.database = options['database'] or DEFAULT_DB_ALIAS
    else:
      self.database = DEFAULT_DB_ALIAS
    if self.database not in settings.DATABASES:
      raise CommandError("No database settings known for '%s'" % self.database )
    if 'user' in options and options['user']:
      try:
        self.user = User.objects.all().using(self.database).get(username=options['user'])
      except:
        raise CommandError("User '%s' not found" % options['user'] )
    else:
      self.user = None

    now = datetime.now()

    task = None
    try:
      # Initialize the task
      if 'task' in options and options['task']:
        try:
          task = Task.objects.all().using(self.database).get(pk=options['task'])
        except:
          raise CommandError("Task identifier not found")
        if task.started or task.finished or task.status != "Waiting" or task.name != 'load from folder':
          raise CommandError("Invalid task identifier")
        task.status = '0%'
        task.started = now
      else:
        task = Task(name='load from folder', submitted=now, started=now, status='0%', user=self.user)
      task.arguments = ' '.join(['"%s"' % i for i in args])
      task.save(using=self.database)
      
      # Choose the right self.delimiter and language
      self.delimiter = get_format('DECIMAL_SEPARATOR', settings.LANGUAGE_CODE, True) == ',' and ';' or ','
      translation.activate(settings.LANGUAGE_CODE)
      
      # Execute        
      filestoupload = list()
      if os.path.isdir(settings.DATABASES[self.database]['FILEUPLOADFOLDER']):
        thisfolder = settings.DATABASES[self.database]['FILEUPLOADFOLDER']
        for fileindir in os.listdir(settings.DATABASES[self.database]['FILEUPLOADFOLDER']):
          if fileindir.endswith('.csv'):
            filestoupload.append(fileindir)
            #filestoupload.append([file,strftime("%Y-%m-%d %H:%M:%S",localtime(os.stat(os.path.join(thisfolder, file)).st_mtime)),sizeof_fmt(os.stat(os.path.join(thisfolder, file)).st_size, 'B')])
        
        all_models = [ (ct.model_class(), ct.pk) for ct in ContentType.objects.all() if ct.model_class() ]
        models = []
        for ifile in filestoupload:
          
          filename0 = ifile.split('.')[0]
          
          model = None
          contenttype_id = None
          for m, ct in all_models:
            if filename0.lower() in (m._meta.model_name.lower(), m._meta.verbose_name.lower(), m._meta.verbose_name_plural.lower()):
              model = m
              contenttype_id = ct
              break
            
          if not model or model in EXCLUDE_FROM_BULK_OPERATIONS:
            print("Ignoring data in file: %s" % ifile)
          elif not self.user==None and not self.user.has_perm('%s.%s' % (model._meta.app_label, get_permission_codename('add', model._meta))):
            # Check permissions
            print("You don't permissions to add: %s" % ifile)
          else:
            deps = set([model])
            GridReport.dependent_models(model, deps)
            models.append( (ifile, model, contenttype_id, deps) )

    # Sort the list of models, based on dependencies between models
        cnt = len(models)
        ok = False
        while not ok:
          ok = True
          for i in range(cnt):
            for j in range(i + 1, cnt):
              if models[i][1] in models[j][3]:
                # A subsequent model i depends on model i. The list ordering is
                # thus not ok yet. We move this element to the end of the list.
                models.append(models.pop(i))
                ok = False

        for ifile, model, contenttype_id, dependencies in models:
          
          print("Processing data in file: %s" % ifile)
          rownum = 0
          has_pk_field = False
          headers = []
          uploadform = None
          changed = 0
          added = 0
          numerrors = 0
          
          #Will the permissions have to be checked table by table?
          permname = get_permission_codename('add', model._meta)
          if not self.user == None and not self.user.has_perm('%s.%s' % (model._meta.app_label, permname)):
            print('Permission denied')
            return
          

          filetoparse=os.path.join(os.path.abspath(thisfolder), ifile)
          self.parseCSVloadfromfolder(model, filetoparse)
            
      # Task update
      task.status = 'Done'
      task.finished = datetime.now()

    except Exception as e:
      if task:
        task.status = 'Failed'
        task.message = '%s' % e
        task.finished = datetime.now()
      raise e

    finally:
      if task:
        task.save(using=self.database)

  def parseCSVloadfromfolder(self, model, file):
    '''
    This method reads CSV data from a file and creates or updates
    the database records.
    The data must follow the following format:
      - the first row contains a header, listing all field names
      - a first character # marks a comment line
      - empty rows are skipped
    '''
    # Init
    headers = []
    rownumber = 0
    changed = 0
    added = 0
    content_type_id = ContentType.objects.get_for_model(model).pk
    
    # Handle the complete upload as a single database transaction
    with transaction.atomic(using=self.database):
      errors = False
      has_pk_field = False
      for row in self.EncodedCSVReader(file, delimiter=self.delimiter):
        rownumber += 1
  
        ### Case 1: The first line is read as a header line
        if rownumber == 1:
  
          for col in row:
            col = col.strip().strip('#').lower()
            if col == "":
              headers.append(False)
              continue
            ok = False
            for i in model._meta.fields:
              if col == i.name.lower() or col == i.verbose_name.lower():
                if i.editable is True:
                  headers.append(i)
                else:
                  headers.append(False)
                ok = True
                break
            if not ok:
              headers.append(False)
              print('Skipping field %s' % col)
            if col == model._meta.pk.name.lower() or \
               col == model._meta.pk.verbose_name.lower():
              has_pk_field = True
          if not has_pk_field and not isinstance(model._meta.pk, AutoField):
            # The primary key is not an auto-generated id and it is not mapped in the input...
            errors = True
            # Translators: Translation included with Django
            print('Some keys were missing: %s' % model._meta.pk.name)
          # Abort when there are errors
          if errors:
            break

          # Create a form class that will be used to validate the data
          UploadForm = modelform_factory(
            model,
            fields=tuple([i.name for i in headers if isinstance(i, Field)]),
            formfield_callback=lambda f: (isinstance(f, RelatedField) and f.formfield(using=self.database, localize=True)) or f.formfield(localize=True)
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
              if colnum >= len(headers):
                break
              if isinstance(headers[colnum], Field):
                d[headers[colnum].name] = col
              colnum += 1

            # Step 2: Fill the form with data, either updating an existing
            # instance or creating a new one.
            if has_pk_field:
              # A primary key is part of the input fields
              try:
                # Try to find an existing record with the same primary key
                it = model.objects.using(self.database).get(pk=d[model._meta.pk.name])
                form = UploadForm(d, instance=it)

              except model.DoesNotExist:
                form = UploadForm(d)
                it = None
            else:
              # No primary key required for this model
              form = UploadForm(d)
              it = None
              
            # Step 3: Validate the data and save to the database
            if form.has_changed():
              try:
                with transaction.atomic(using=self.database):
                  obj = form.save(commit=False)
                  obj.save(using=self.database)
                  LogEntry(
                    user_id=0,   # To change in the near future !!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!
                    content_type_id=content_type_id,
                    object_id=obj.pk,
                    object_repr=force_text(obj),
                    action_flag=it and CHANGE or ADDITION,
                    #. Translators: Translation included with Django
                    change_message='Changed %s.' % get_text_list(form.changed_data, 'and')
                  ).save(using=self.database)
                  if it:
                    changed += 1
                  else:
                    added += 1
              except Exception as e:
                # Validation fails
                for error in form.non_field_errors():
                  print('Row %s: %s' % (rownumber, error))
                for field in form:
                  for error in field.errors:
                    print('Row %s field %s: %s' % (rownumber, field.name, error))
          except Exception as e:
            print("Exception during upload: %s" % e )
  
      # Report all failed records
      print('Uploaded data successfully: changed %d and added %d records' % (changed, added))
         
  class EncodedCSVReader:
    '''
    A CSV reader which will iterate over lines in the CSV data buffer.
    The reader will scan the BOM header in the data to detect the right encoding.
    '''
    def __init__(self, datafile, **kwds):
      # Read the file into memory
      # TODO Huge file uploads can overwhelm your system!

      self.reader = open(datafile,'rb')
      data = self.reader.read(5)
      self.reader.close()
      # Detect the encoding of the data by scanning the BOM.
      # Skip the BOM header if it is found.
      
      if data.startswith(codecs.BOM_UTF32_BE):
        self.reader = open(datafile, "rt", encoding='utf_32_be')
        self.reader.read(1)
      elif data.startswith(codecs.BOM_UTF32_LE):
        self.reader = open(datafile, "rt", encoding='utf_32_le')
        self.reader.read(1)
      elif data.startswith(codecs.BOM_UTF16_BE):
        self.reader = open(datafile, "rt", encoding='utf_16_be')
        self.reader.read(1)
      elif data.startswith(codecs.BOM_UTF16_LE):
        self.reader = open(datafile, "rt", encoding='utf_16_le')
        self.reader.read(1)
      elif data.startswith(codecs.BOM_UTF8):
        self.reader = open(datafile, "rt", encoding='utf_8')
        self.reader.read(1)
      else:
        # No BOM header found. We assume the data is encoded in the default CSV character set.
        self.reader = open(datafile, "rt", encoding=settings.CSV_CHARSET)
      self.csvreader = csv.reader(self.reader, **kwds)
  
    def __next__(self):
      return next(self.csvreader)
  
    def __iter__(self):
      return self
