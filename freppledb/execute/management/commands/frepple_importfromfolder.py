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

import codecs
from datetime import datetime
import csv
import gzip
from openpyxl import load_workbook
import os

from django.conf import settings
from django.contrib.auth import get_permission_codename
from django.contrib.contenttypes.models import ContentType
from logging import ERROR, WARNING
from django.core.management.base import BaseCommand, CommandError
from django.db import connections, DEFAULT_DB_ALIAS, transaction
from django.utils import translation
from django.utils.formats import get_format

from freppledb.execute.models import Task
from freppledb.common.report import GridReport
from freppledb import VERSION
from freppledb.common.dataload import parseCSVdata, parseExcelWorksheet
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
        print("%s Started import from folder\n" % datetime.now().replace(microsecond=0), file=self.logfile, flush=True)

        all_models = [ (ct.model_class(), ct.pk) for ct in ContentType.objects.all() if ct.model_class() ]
        models = []
        for ifile in os.listdir(settings.DATABASES[self.database]['FILEUPLOADFOLDER']):
          if not ifile.lower().endswith(('.csv', '.csv.gz', '.xslsx')):
            continue
          filename0 = ifile.split('.')[0]

          model = None
          contenttype_id = None
          for m, ct in all_models:
            # Try with translated model names
            if filename0.lower() in (m._meta.model_name.lower(), m._meta.verbose_name.lower(), m._meta.verbose_name_plural.lower()):
              model = m
              contenttype_id = ct
              print("%s Matched a model to file: %s" % (datetime.now().replace(microsecond=0), ifile), file=self.logfile, flush=True)
              break
            # Try with English model names
            with translation.override('en'):
              if filename0.lower() in (m._meta.model_name.lower(), m._meta.verbose_name.lower(), m._meta.verbose_name_plural.lower()):
                model = m
                contenttype_id = ct
                print("%s Matched a model to file: %s" % (datetime.now().replace(microsecond=0), ifile), file=self.logfile, flush=True)
                break

          if not model or model in EXCLUDE_FROM_BULK_OPERATIONS:
            print("%s Ignoring data in file: %s" % (datetime.now().replace(microsecond=0), ifile), file=self.logfile, flush=True)
          elif self.user and not self.user.has_perm('%s.%s' % (model._meta.app_label, get_permission_codename('add', model._meta))):
            # Check permissions
            print("%s You don't have permissions to add: %s" % (datetime.now().replace(microsecond=0), ifile), file=self.logfile, flush=True)
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
          if ifile.endswith('.xlsx'):
            print("%s Started processing data in Excel file: %s" % (datetime.now().replace(microsecond=0), ifile), file=self.logfile, flush=True)
            errors += self.loadExcelfile(model, filetoparse)
            print("%s Finished processing data in file: %s" % (datetime.now().replace(microsecond=0), ifile), file=self.logfile, flush=True)
          else:
            print("%s Started processing data in CSV file: %s" % (datetime.now().replace(microsecond=0), ifile), file=self.logfile, flush=True)
            errors += self.loadCSVfile(model, filetoparse)
            print("%s Finished processing data in CSV file: %s" % (datetime.now().replace(microsecond=0), ifile), file=self.logfile, flush=True)
      else:
        errors += 1
        cnt = 0
        print("%s Failed, folder does not exist" % datetime.now().replace(microsecond=0), file=self.logfile, flush=True)

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
        print('%s Cancelled\n' % datetime.now().replace(microsecond=0), file=self.logfile, flush=True)

    except Exception as e:
      print("%s Failed" % datetime.now().replace(microsecond=0), file=self.logfile, flush=True)
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


  def loadCSVfile(self, model, file):
    errorcount = 0
    datafile = EncodedCSVReader(file, delimiter=self.delimiter)
    try:
      with transaction.atomic(using=self.database):
        for error in parseCSVdata(model, datafile, user=self.user, database=self.database):
          if error[0] == ERROR:
            print('%s Error: %s%s%s%s' % (
              datetime.now().replace(microsecond=0),
              "Row %s: " % error[1] if error[1] else '',
              "field %s: " % error[2] if error[2] else '',
              "%s: " % error[3] if error[3] else '',
              error[4]
              ), file=self.logfile, flush=True)
            errorcount += 1
          elif error[0] == WARNING:
            print('%s Warning: %s%s%s%s' % (
              datetime.now().replace(microsecond=0),
              "Row %s: " % error[1] if error[1] else '',
              "field %s: " % error[2] if error[2] else '',
              "%s: " % error[3] if error[3] else '',
              error[4]
              ), file=self.logfile, flush=True)
          else:
            print('%s %s%s%s%s' % (
              datetime.now().replace(microsecond=0),
              "Row %s: " % error[1] if error[1] else '',
              "field %s: " % error[2] if error[2] else '',
              "%s: " % error[3] if error[3] else '',
              error[4]
              ), file=self.logfile, flush=True)
    except:
      print(
        '%s Error: Invalid data format - skipping the file \n' % datetime.now().replace(microsecond=0),
        file=self.logfile, flush=True
        )
    return errorcount


  def loadExcelfile(self, model, file):
    errorcount = 0
    try:
      with transaction.atomic(using=self.database):
        wb = load_workbook(filename=file, read_only=True, data_only=True)
        for ws_name in wb.get_sheet_names():
          ws = wb.get_sheet_by_name(name=ws_name)
          for error in parseExcelWorksheet(model, ws, user=self.user, database=self.database):
            if error[0] == ERROR:
              print('%s Error: %s%s%s%s' % (
                datetime.now().replace(microsecond=0),
                "Row %s: " % error[1] if error[1] else '',
                "field %s: " % error[2] if error[2] else '',
                "%s: " % error[3] if error[3] else '',
                error[4]
                ), file=self.logfile, flush=True)
              errorcount += 1
            elif error[0] == WARNING:
              print('%s Warning: %s%s%s%s' % (
                datetime.now().replace(microsecond=0),
                "Row %s: " % error[1] if error[1] else '',
                "field %s: " % error[2] if error[2] else '',
                "%s: " % error[3] if error[3] else '',
                error[4]
                ), file=self.logfile, flush=True)
            else:
              print('%s %s%s%s%s' % (
                datetime.now().replace(microsecond=0),
                "Row %s: " % error[1] if error[1] else '',
                "field %s: " % error[2] if error[2] else '',
                "%s: " % error[3] if error[3] else '',
                error[4]
                ), file=self.logfile, flush=True)
    except:
      print(
        '%s Error: Invalid data format - skipping the file \n' % datetime.now().replace(microsecond=0),
        file=self.logfile, flush=True
        )
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
