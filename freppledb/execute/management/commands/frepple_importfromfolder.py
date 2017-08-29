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
import csv
import codecs
from datetime import datetime
import gzip

from django.conf import settings
from django.contrib.admin.models import LogEntry, CHANGE, ADDITION
from django.contrib.auth import get_permission_codename
from django.contrib.contenttypes.models import ContentType
from django.core.management.base import BaseCommand, CommandError
from django.db import DEFAULT_DB_ALIAS, transaction, models
from django.db.models.fields import NOT_PROVIDED, AutoField
from django.db.models.fields.related import RelatedField
from django.forms.models import modelform_factory
from django.utils import translation
from django.utils.encoding import force_text
from django.utils.formats import get_format
from django.utils.text import get_text_list

from freppledb.execute.models import Task
from freppledb.common.report import GridReport
from freppledb import VERSION
from freppledb.common.dataload import BulkForeignKeyFormField
from freppledb.common.models import User
from freppledb.common.report import EXCLUDE_FROM_BULK_OPERATIONS


class Command(BaseCommand):

  help = '''
    Loads CSV files from the configured FILEUPLOADFOLDER folder into the frePPLe database.
    The data files should have the extension .csv or .csv.gz, and the file name should
    start with the name of the data model.
    '''

  requires_system_checks = False


  def add_arguments(self, parser):
    parser.add_argument(
      '--user', help='User running the command'
      )
    parser.add_argument(
      '--database', default=DEFAULT_DB_ALIAS,
      help='Nominates a specific database to load the data into'
      )
    parser.add_argument(
      '--task', type=int,
      help='Task identifier (generated automatically if not provided)'
      )


  def get_version(self):
    return VERSION


  def handle(self, **options):
    # Pick up the options
    self.database = options['database']
    if self.database not in settings.DATABASES:
      raise CommandError("No database settings known for '%s'" % self.database )
    if options['user']:
      try:
        self.user = User.objects.all().using(self.database).get(username=options['user'])
      except:
        raise CommandError("User '%s' not found" % options['user'] )
    else:
      try:
        self.user = User.objects.all().using(self.database).filter(is_superuser=True)[0]
      except:
        self.user = None

    now = datetime.now()

    task = None
    self.logfile = None
    errors = 0
    try:
      # Initialize the task
      if options['task']:
        try:
          task = Task.objects.all().using(self.database).get(pk=options['task'])
        except:
          raise CommandError("Task identifier not found")
        if task.started or task.finished or task.status != "Waiting" or task.name != 'import from folder':
          raise CommandError("Invalid task identifier")
        task.status = '0%'
        task.started = now
      else:
        task = Task(name='import from folder', submitted=now, started=now, status='0%', user=self.user)
      task.save(using=self.database)

      # Choose the right self.delimiter and language
      self.delimiter = get_format('DECIMAL_SEPARATOR', settings.LANGUAGE_CODE, True) == ',' and ';' or ','
      translation.activate(settings.LANGUAGE_CODE)

      # Execute
      if os.path.isdir(settings.DATABASES[self.database]['FILEUPLOADFOLDER']):

        # Open the logfile
        self.logfile = open(os.path.join(settings.DATABASES[self.database]['FILEUPLOADFOLDER'], 'importfromfolder.log'), "a")
        print("%s Started import from folder\n" % datetime.now(), file=self.logfile, flush=True)

        all_models = [ (ct.model_class(), ct.pk) for ct in ContentType.objects.all() if ct.model_class() ]
        models = []
        for ifile in os.listdir(settings.DATABASES[self.database]['FILEUPLOADFOLDER']):
          if not ifile.lower().endswith('.csv') and not ifile.lower().endswith('.csv.gz'):
            continue
          filename0 = ifile.split('.')[0]

          model = None
          contenttype_id = None
          for m, ct in all_models:
            if filename0.lower() in (m._meta.model_name.lower(), m._meta.verbose_name.lower(), m._meta.verbose_name_plural.lower()):
              model = m
              contenttype_id = ct
              print("%s Matched a model to file: %s" % (datetime.now(), ifile), file=self.logfile, flush=True)
              break

          if not model or model in EXCLUDE_FROM_BULK_OPERATIONS:
            print("%s Ignoring data in file: %s" % (datetime.now(), ifile), file=self.logfile, flush=True)
          elif self.user and not self.user.has_perm('%s.%s' % (model._meta.app_label, get_permission_codename('add', model._meta))):
            # Check permissions
            print("%s You don't have permissions to add: %s" % (datetime.now(), ifile), file=self.logfile, flush=True)
          else:
            deps = set([model])
            GridReport.dependent_models(model, deps)

            models.append( (ifile, model, contenttype_id, deps) )

        # Sort the list of models, based on dependencies between models
        models = GridReport.sort_models(models)

        i = 0
        cnt = len(models)
        for ifile, model, contenttype_id, dependencies in models:
          task.status = str(int(10 + i / cnt * 80)) + '%'
          task.message = 'Processing data file %s' % ifile
          task.save(using=self.database)
          i += 1
          filetoparse = os.path.join(os.path.abspath(settings.DATABASES[self.database]['FILEUPLOADFOLDER']), ifile)
          print("%s Started processing data in file: %s" % (datetime.now(), ifile), file=self.logfile, flush=True)
          errors += self.parseCSVloadfromfolder(model, filetoparse)


      else:
        errors += 1
        cnt = 0
        print("%s Failed, folder does not exist" % datetime.now(), file=self.logfile, flush=True)

      # Task update
      if errors:
        task.status = 'Failed'
        if not cnt:
          task.message = "Destination folder does not exist"
        else:
          task.message = "Uploaded %s data files with %s errors" % (cnt, errors)
      else:
        task.status = 'Done'
        task.message = "Uploaded %s data files" % cnt
      task.finished = datetime.now()

    except KeyboardInterrupt:
      if task:
        task.status = 'Cancelled'
        task.message = 'Cancelled'
      if self.logfile:
        print('%s Cancelled\n' % datetime.now(), file=self.logfile, flush=True)
    
    except Exception as e:
      print("%s Failed" % datetime.now(), file=self.logfile, flush=True)
      if task:
        task.status = 'Failed'
        task.message = '%s' % e
      raise e

    finally:
      if task:
        if not errors:
          task.status = '100%'
        else:
          task.status = 'Failed'
      task.finished = datetime.now()
      task.save(using=self.database)
      if self.logfile:
        print('%s End of import from folder\n' % datetime.now(), file=self.logfile, flush=True)
        self.logfile.close()


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
    errorcount = 0
    admin_log = []

    # Handle the complete upload as a single database transaction
    with transaction.atomic(using=self.database):
      errors = False
      has_pk_field = False
      for row in self.EncodedCSVReader(file, delimiter=self.delimiter):
        rownumber += 1

        ### Case 1: The first line is read as a header line
        if rownumber == 1:

          # Collect required fields
          required_fields = set()
          for i in model._meta.fields:
            if not i.blank and i.default == NOT_PROVIDED and not isinstance(i, AutoField):
              required_fields.add(i.name)

          # Validate all columns
          for col in row:
            col = col.strip().strip('#').lower()
            if col == "":
              headers.append(None)
              continue
            ok = False
            for i in model._meta.fields:
              if col == i.name.lower() or col == i.verbose_name.lower():
                if i.editable is True:
                  headers.append(i)
                else:
                  headers.append(None)
                required_fields.discard(i.name)
                ok = True
                break
            if not ok:
              headers.append(None)
              print('%s Warning: Skipping field %s' % (datetime.now(), col), file=self.logfile, flush=True)
            if col == model._meta.pk.name.lower() or \
               col == model._meta.pk.verbose_name.lower():
              has_pk_field = True
          if required_fields:
            # We are missing some required fields
            errors = True
            print('%s Error: Some keys were missing: %s' % (datetime.now(), ', '.join(required_fields)), file=self.logfile, flush=True)
            errorcount += 1
          # Abort when there are errors
          if errors:
            break
          header_count = len(headers)

          # Create a form class that will be used to validate the data
          fields = [i.name for i in headers if i]
          UploadForm = modelform_factory(
            model,
            fields=tuple(fields),
            formfield_callback=lambda f: (isinstance(f, RelatedField) and BulkForeignKeyFormField(field=f, using=self.database)) or f.formfield(localize=True)
            )

          # Get natural keys for the class
          natural_key = None
          if hasattr(model.objects, 'get_by_natural_key'):
            if model._meta.unique_together:
              natural_key = model._meta.unique_together[0]
            elif hasattr(model, 'natural_key'):
              natural_key = model.natural_key

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
              if colnum >= header_count:
                break
              if headers[colnum]:
                d[headers[colnum].name] = col.strip()
              colnum += 1

            # Step 2: Fill the form with data, either updating an existing
            # instance or creating a new one.
            if has_pk_field:
              # A primary key is part of the input fields
              try:
                # Try to find an existing record with the same primary key
                it = model.objects.using(self.database).only(*fields).get(pk=d[model._meta.pk.name])
                form = UploadForm(d, instance=it)

              except model.DoesNotExist:
                form = UploadForm(d)
                it = None
            elif natural_key:
              # A natural key exists for this model
              try:
                # Build the natural key
                key = []
                for x in natural_key:
                  key.append(d.get(x, None))
                # Try to find an existing record using the natural key
                it = model.objects.get_by_natural_key(*key)
                form = UploadForm(d, instance=it)
              except model.DoesNotExist:
                form = UploadForm(d)
                it = None
              except model.MultipleObjectsReturned:
                print('%s Error: Row %s: Key fields not unique' % (datetime.now(), rownumber), file=self.logfile, flush=True)
                errorcount += 1
                continue
            else:
              # No primary key required for this model
              form = UploadForm(d)
              it = None
            # Step 3: Validate the form and model, and save to the database
            if form.has_changed():
              if form.is_valid():
                # Save the form
                obj = form.save(commit=False)
                if it:
                  changed += 1
                  obj.save(using=self.database, force_update=True)
                else:
                  added += 1
                  obj.save(using=self.database, force_insert=True)
                if self.user:
                  admin_log.append(
                    LogEntry(
                      user_id=self.user.id,
                      content_type_id=content_type_id,
                      object_id=obj.pk,
                      object_repr=force_text(obj),
                      action_flag=it and CHANGE or ADDITION,
                      #. Translators: Translation included with Django
                      change_message='Changed %s.' % get_text_list(form.changed_data, 'and')
                    ))
              else:
                # Validation fails
                for error in form.non_field_errors():
                  print('%s Error: Row %s: %s' % (datetime.now(), rownumber, error), file=self.logfile, flush=True)
                  errorcount += 1
                for field in form:
                  for error in field.errors:
                    print('%s Error: Row %s field %s: %s' % (datetime.now(), rownumber, field.name, error), file=self.logfile, flush=True)
                    errorcount += 1

          except Exception as e:
            print("%s Error: Exception during upload: %s" % (datetime.now(), e), file=self.logfile, flush=True)
            errorcount += 1

      # Save all admin log entries
      LogEntry.objects.all().using(self.database).bulk_create(admin_log, batch_size=1000)

      # Report all failed records
      if not errors:
        print('%s Uploaded data successfully: changed %d and added %d records' % (datetime.now(), changed, added), file=self.logfile, flush=True)
      else:
        print('%s Error: Invalid data format - skipping the file \n' % datetime.now(), file=self.logfile, flush=True)
      return errorcount


  class EncodedCSVReader:
    '''
    A CSV reader which will iterate over lines in the CSV data buffer.
    The reader will scan the BOM header in the data to detect the right encoding.
    '''
    def __init__(self, datafile, **kwds):
      # Read the file into memory
      # TODO Huge file uploads can overwhelm your system!

      # Detect the encoding of the data by scanning the BOM.
      # Skip the BOM header if it is found.

      if datafile.lower().endswith(".gz"):
        file_open = gzip.open
      else:
        file_open = open
      self.reader = file_open(datafile, 'rb')
      data = self.reader.read(5)
      self.reader.close()
      if data.startswith(codecs.BOM_UTF32_BE):
        self.reader = file_open(datafile, "rt", encoding='utf_32_be')
        self.reader.read(1)
      elif data.startswith(codecs.BOM_UTF32_LE):
        self.reader = file_open(datafile, "rt", encoding='utf_32_le')
        self.reader.read(1)
      elif data.startswith(codecs.BOM_UTF16_BE):
        self.reader = file_open(datafile, "rt", encoding='utf_16_be')
        self.reader.read(1)
      elif data.startswith(codecs.BOM_UTF16_LE):
        self.reader = file_open(datafile, "rt", encoding='utf_16_le')
        self.reader.read(1)
      elif data.startswith(codecs.BOM_UTF8):
        self.reader = file_open(datafile, "rt", encoding='utf_8')
        self.reader.read(1)
      else:
        # No BOM header found. We assume the data is encoded in the default CSV character set.
        self.reader = file_open(datafile, "rt", encoding=settings.CSV_CHARSET)

      # Open the file
      self.csvreader = csv.reader(self.reader, **kwds)

    def __next__(self):
      return next(self.csvreader)

    def __iter__(self):
      return self
