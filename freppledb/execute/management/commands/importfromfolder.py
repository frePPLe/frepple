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
from time import localtime, strftime
import csv
import gzip
from openpyxl import load_workbook
import os
import logging

from django.conf import settings
from django.contrib.auth import get_permission_codename
from django.contrib.contenttypes.models import ContentType
from logging import ERROR, WARNING
from django.core.management.base import BaseCommand, CommandError
from django.db import connections, DEFAULT_DB_ALIAS, transaction
from django.utils import translation
from django.utils.formats import get_format
from django.utils.translation import ugettext_lazy as _
from django.template import Template, RequestContext

from freppledb.execute.models import Task
from freppledb.common.middleware import _thread_locals
from freppledb.common.report import GridReport, matchesModelName
from freppledb import VERSION
from freppledb.common.dataload import parseCSVdata, parseExcelWorksheet
from freppledb.common.models import User
from freppledb.common.report import EXCLUDE_FROM_BULK_OPERATIONS

logger = logging.getLogger(__name__)


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
    now = datetime.now()
    self.database = options['database']
    if self.database not in settings.DATABASES:
      raise CommandError("No database settings known for '%s'" % self.database )
    if options['user']:
      try:
        self.user = User.objects.all().using(self.database).get(username=options['user'])
      except:
        raise CommandError("User '%s' not found" % options['user'] )
    else:
      self.user = None
    timestamp = now.strftime("%Y%m%d%H%M%S")
    if self.database == DEFAULT_DB_ALIAS:
      logfile = 'importfromfolder-%s.log' % timestamp
    else:
      logfile = 'importfromfolder_%s-%s.log' % (self.database, timestamp)

    try:
      handler = logging.FileHandler(os.path.join(settings.FREPPLE_LOGDIR, logfile), encoding='utf-8')
      # handler.setFormatter(logging.Formatter(settings.LOGGING['formatters']['simple']['format']))
      logger.addHandler(handler)
      logger.propagate = False
    except Exception as e:
      print("%s Failed to open logfile %s: %s" % (datetime.now(), logfile, e))

    task = None
    errors = [0, 0]
    returnederrors = [0, 0]
    try:
      setattr(_thread_locals, 'database', self.database)
      # Initialize the task
      if options['task']:
        try:
          task = Task.objects.all().using(self.database).get(pk=options['task'])
        except:
          raise CommandError("Task identifier not found")
        if task.started or task.finished or task.status != "Waiting" or task.name not in ('frepple_importfromfolder', 'importfromfolder'):
          raise CommandError("Invalid task identifier")
        task.status = '0%'
        task.started = now
        task.logfile = logfile
      else:
        task = Task(name='importfromfolder', submitted=now, started=now, status='0%', user=self.user, logfile=logfile)
      task.save(using=self.database)

      # Choose the right self.delimiter and language
      self.delimiter = get_format('DECIMAL_SEPARATOR', settings.LANGUAGE_CODE, True) == ',' and ';' or ','
      translation.activate(settings.LANGUAGE_CODE)

      # Execute
      if 'FILEUPLOADFOLDER' in settings.DATABASES[self.database] \
        and os.path.isdir(settings.DATABASES[self.database]['FILEUPLOADFOLDER']):

        # Open the logfile
        logger.info("%s Started importfromfolder\n" % datetime.now().replace(microsecond=0))

        all_models = [ (ct.model_class(), ct.pk) for ct in ContentType.objects.all() if ct.model_class() ]
        models = []
        for ifile in os.listdir(settings.DATABASES[self.database]['FILEUPLOADFOLDER']):
          if not ifile.lower().endswith(('.csv', '.csv.gz', '.xlsx')):
            continue
          filename0 = ifile.split('.')[0]

          model = None
          contenttype_id = None
          for m, ct in all_models:
            if matchesModelName(filename0, m):
              model = m
              contenttype_id = ct
              logger.info("%s Matched a model to file: %s" % (datetime.now().replace(microsecond=0), ifile))
              break

          if not model or model in EXCLUDE_FROM_BULK_OPERATIONS:
            logger.info("%s Ignoring data in file: %s" % (datetime.now().replace(microsecond=0), ifile))
          elif self.user and not self.user.has_perm('%s.%s' % (model._meta.app_label, get_permission_codename('add', model._meta))):
            # Check permissions
            logger.info("%s You don't have permissions to add: %s" % (datetime.now().replace(microsecond=0), ifile))
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
          if ifile.lower().endswith('.xlsx'):
            logger.info("%s Started processing data in Excel file: %s" % (datetime.now().replace(microsecond=0), ifile))
            returnederrors = self.loadExcelfile(model, filetoparse)
            errors[0] += returnederrors[0]
            errors[1] += returnederrors[1]
            logger.info("%s Finished processing data in file: %s" % (datetime.now().replace(microsecond=0), ifile))
          else:
            logger.info("%s Started processing data in CSV file: %s" % (datetime.now().replace(microsecond=0), ifile))
            returnederrors = self.loadCSVfile(model, filetoparse)
            errors[0] += returnederrors[0]
            errors[1] += returnederrors[1]
            logger.info("%s Finished processing data in CSV file: %s" % (datetime.now().replace(microsecond=0), ifile))
      else:
        errors[0] += 1
        cnt = 0
        logger.error("%s Failed, folder does not exist" % datetime.now().replace(microsecond=0))

      # Task update
      if errors[0] > 0:
        task.status = 'Failed'
        if not cnt:
          task.message = "Destination folder does not exist"
        else:
          task.message = "Uploaded %s data files with %s errors and %s warnings" % (cnt, errors[0], errors[1])
      else:
        task.status = 'Done'
        task.message = "Uploaded %s data files with %s warnings" % (cnt, errors[1])
      task.finished = datetime.now()

    except KeyboardInterrupt:
      if task:
        task.status = 'Cancelled'
        task.message = 'Cancelled'
      logger.info('%s Cancelled\n' % datetime.now().replace(microsecond=0))

    except Exception as e:
      logger.error("%s Failed" % datetime.now().replace(microsecond=0))
      if task:
        task.status = 'Failed'
        task.message = '%s' % e
      raise e

    finally:
      setattr(_thread_locals, 'database', None)
      if task:
        if errors[0] == 0:
          task.status = 'Done'
        else:
          task.status = 'Failed'
      task.finished = datetime.now()
      task.save(using=self.database)
      logger.info('%s End of importfromfolder\n' % datetime.now().replace(microsecond=0))



  def loadCSVfile(self, model, file):
    errorcount = 0
    warningcount = 0
    datafile = EncodedCSVReader(file, delimiter=self.delimiter)
    try:
      with transaction.atomic(using=self.database):
        for error in parseCSVdata(model, datafile, user=self.user, database=self.database):
          if error[0] == ERROR:
            logger.error('%s Error: %s%s%s%s' % (
              datetime.now().replace(microsecond=0),
              "Row %s: " % error[1] if error[1] else '',
              "field %s: " % error[2] if error[2] else '',
              "%s: " % error[3] if error[3] else '',
              error[4]
              ))
            errorcount += 1
          elif error[0] == WARNING:
            logger.warning('%s Warning: %s%s%s%s' % (
              datetime.now().replace(microsecond=0),
              "Row %s: " % error[1] if error[1] else '',
              "field %s: " % error[2] if error[2] else '',
              "%s: " % error[3] if error[3] else '',
              error[4]
              ))
            warningcount += 1
          else:
            logger.info('%s %s%s%s%s' % (
              datetime.now().replace(microsecond=0),
              "Row %s: " % error[1] if error[1] else '',
              "field %s: " % error[2] if error[2] else '',
              "%s: " % error[3] if error[3] else '',
              error[4]
              ))
    except:
      logger.error('%s Error: Invalid data format - skipping the file \n' % datetime.now().replace(microsecond=0))
    return [errorcount, warningcount]


  def loadExcelfile(self, model, file):
    errorcount = 0
    warningcount = 0
    try:
      with transaction.atomic(using=self.database):
        wb = load_workbook(filename=file, read_only=True, data_only=True)
        for ws_name in wb.sheetnames:
          ws = wb[ws_name]
          for error in parseExcelWorksheet(model, ws, user=self.user, database=self.database):
            if error[0] == ERROR:
              logger.error('%s Error: %s%s%s%s' % (
                datetime.now().replace(microsecond=0),
                "Row %s: " % error[1] if error[1] else '',
                "field %s: " % error[2] if error[2] else '',
                "%s: " % error[3] if error[3] else '',
                error[4]
                ))
              errorcount += 1
            elif error[0] == WARNING:
              logger.warning('%s Warning: %s%s%s%s' % (
                datetime.now().replace(microsecond=0),
                "Row %s: " % error[1] if error[1] else '',
                "field %s: " % error[2] if error[2] else '',
                "%s: " % error[3] if error[3] else '',
                error[4]
                ))
              warningcount += 1
            else:
              logger.info('%s %s%s%s%s' % (
                datetime.now().replace(microsecond=0),
                "Row %s: " % error[1] if error[1] else '',
                "field %s: " % error[2] if error[2] else '',
                "%s: " % error[3] if error[3] else '',
                error[4]
                ))
    except:
      logger.error('%s Error: Invalid data format - skipping the file \n' % datetime.now().replace(microsecond=0))
    return [errorcount, warningcount]

  # accordion template
  title = _('Import data files from folder')
  index = 1300
  help_url = 'user-guide/command-reference.html#importfromfolder'

  @ staticmethod
  def getHTML(request):

    if 'FILEUPLOADFOLDER' in settings.DATABASES[request.database] and request.user.is_superuser:
      # Function to convert from bytes to human readabl format
      def sizeof_fmt(num):
        for unit in ['', 'Ki', 'Mi', 'Gi', 'Ti', 'Pi', 'Ei', 'Zi']:
          if abs(num) < 1024.0:
            return "%3.1f%sB" % (num, unit)
          num /= 1024.0
        return "%.1f%sB" % (num, 'Yi')

      filestoupload = []
      if 'FILEUPLOADFOLDER' in settings.DATABASES[request.database]:
        uploadfolder = settings.DATABASES[request.database]['FILEUPLOADFOLDER']
        if os.path.isdir(uploadfolder):
          for file in os.listdir(uploadfolder):
            if file.endswith(('.csv', '.csv.gz', '.log', '.xlsx')):
              filestoupload.append([
                file,
                strftime("%Y-%m-%d %H:%M:%S",localtime(os.stat(os.path.join(uploadfolder, file)).st_mtime)),
                sizeof_fmt(os.stat(os.path.join(uploadfolder, file)).st_size)
                ])

      context = RequestContext(request, {'filestoupload': filestoupload})

      template = Template('''
        {% load i18n %}
        <form role="form" method="post" action="{{request.prefix}}/execute/launch/importfromfolder/">{% csrf_token %}
          <table>
            <tr>
              <td style="vertical-align:top; padding-left: 15px">
                <button type="submit" class="btn btn-primary" id="importfromfolder" value="{% trans "import"|capfirst %}">{% trans "import"|capfirst %}</button>
              </td>
              <td colspan='5' style="padding-left: 15px;">
                <p>{% trans "Import CSV or Excel files from the data folder. The file names must match the names of data objects and the first line in the file must contain the field names." %}</p>
              </td>
            </tr>
            <tr>
              <td></td>
              <td><strong>{% trans 'file name'|capfirst %}</strong></td>
              <td><strong>{% trans 'size'|capfirst %}</strong></td>
              <td><strong>{% trans 'changed'|capfirst %}</strong></td>
              <td>
                <span class="btn btn-xs btn-primary" id="filescopy" style="margin-bottom: 5px;" data-toggle="tooltip" data-placement="top" data-original-title="{% trans 'Upload data files' %}"
                  onclick="import_show('{% trans 'Copy files to folder' %}',null,true,uploadfilesajax)">
                  <span class="fa fa-arrow-up"></span>
                </span>
              </td>
              <td>
                <div class="btn btn-xs btn-danger deletefile" style="margin-bottom: 5px;" id="allimportfilesdelete" data-toggle="tooltip" data-placement="top" data-original-title="{% trans 'Delete all files' %}" onClick="deleteImportFile(0, {{filestoupload}})">
                  <span class="fa fa-close"></span>
                </div>
              </td>
            </tr></form>
            {% for j in filestoupload %}
            <tr data-file="{{j.0}}">
              <td></td>
              <td>{{j.0}}</td>
              <td>{{j.2}}</td>
              <td>{{j.1}}</td>
              <td>
                <div class="btn btn-xs btn-primary downloadfile" style="margin-bottom: 5px;" id="filedownload" data-toggle="tooltip" data-placement="top" data-original-title="{% trans "Download file" %}" onClick="downloadImportFile(0, '{{j.0}}')">
                  <span class="fa fa-arrow-down"></span>
                </div>
              </td>
              <td>
                <div class="btn btn-xs btn-danger deletefile" style="margin-bottom: 5px;" id="filedelete" data-toggle="tooltip" data-placement="top" data-original-title="{% trans "Delete file" %}" onClick="deleteImportFile(0, '{{j.0}}')">
                  <span class="fa fa-close"></span>
                </div>
              </td>
            </tr>
            {% endfor %}
          </table>
        </form>
        <script>
        var xhr = {abort: function () {}};
        var uploadfilesajax = {
          url: '{{request.prefix}}/execute/uploadtofolder/0/',
          success: function (data) {
            var el = $('#uploadResponse');
            el.empty();
            $("#animatedcog").css('visibility','hidden');
            var lines = data.split('\\n');
            for (var i = 0; i < lines.length; i++) {
              el.append(lines[i] + '<br>');
            }
            if (el.attr('data-scrolled')!== "true") {
              el.attr('data-scrolled', el[0].scrollHeight - el.height());
              el.scrollTop(el[0].scrollHeight - el.height());
            }
            if (document.queryCommandSupported('copy'))
              $('#copytoclipboard').show();
            $('#canceluploadbutton').hide();
            $('#cancelimportbutton').hide();
            $('#cancelbutton').one('click', function() {location.reload();});
          },
          error: function (result, stat, errorThrown) {
            var el = $('#uploadResponse');
            el.empty();
            $("#animatedcog").css('visibility','hidden');
            var lines = result.responseText.split('\\n');
            for (var i = 0; i < lines.length; i++) {
              el.append(lines[i] + '<br>');
            }
            if (el.attr('data-scrolled')!== "true") {
              el.attr('data-scrolled', el[0].scrollHeight - el.height());
              el.scrollTop(el[0].scrollHeight - el.height());
            }
            if (document.queryCommandSupported('copy'))
              $('#copytoclipboard').show();
            $('#canceluploadbutton').hide();
            $('#cancelimportbutton').hide();
            }
        };

        function deleteImportFile(folder, filename) {
          $.jgrid.hideModal("#searchmodfbox_grid");
          var dialogcontent;
          if (typeof filename === 'object') {
            dialogcontent = "{% trans 'You are about to delete all files' %}";           
            var oldfilename = filename;
            filename = 'AllFiles';
          } else {
            dialogcontent = interpolate("{% trans 'You are about to delete file %s' %}", [filename]);
          }

          $("#popup").html('<div class="modal-dialog">'+
            '<div class="modal-content">'+
              '<div class="modal-header">'+
                '<h4 class="modal-title">{% trans 'Delete file' %}</h4>'+
              '</div>'+
              '<div class="modal-body"><p>'+
              dialogcontent +
              '</p></div>'+
              '<div class="modal-footer">'+
                '<input type="submit" id="confirmbutton" role="button" class="btn btn-danger pull-left" value="{% trans 'Confirm' %}">'+
                '<input type="submit" id="cancelbutton" role="button" class="btn btn-primary pull-right" data-dismiss="modal" value="{% trans 'Cancel' %}">'+
              '</div>'+
            '</div>'+
          '</div>' )
          .modal('show');

          $('#confirmbutton').on('click', function() {
            $.ajax({
              url: "{{request.prefix}}/execute/deletefromfolder/" + folder + "/" + filename + "/",
              type:  ("delete").toUpperCase(),
              success: function () {
                if (filename === 'AllFiles') {
                  $("#popup .modal-body>p").text("{% trans 'All data files were deleted' %}");
                } else {
                  $("#popup .modal-body>p").text(interpolate("{% trans 'File %s was deleted' %}", [filename]));
                }
                $('#confirmbutton').hide();
                $('#cancelbutton').attr('value', "{% trans 'Close' %}");
                $('#cancelbutton').one('click', function() {$("#popup").hide();});
                location.reload();
              },
              error: function (result, stat, errorThrown) {
                var filelist = result.responseText.split(' / ');
                var elem = $("#popup .modal-body>p");
                if (filelist.length === 1) {
                  elem.text(interpolate("{% trans 'File %s was not deleted' %}", [filename]));
                } else {
                  for (var i = 1; i < filelist.length; i++) {
                    if (i === 1) {
                      elem.text(interpolate("{% trans 'File %s was not deleted' %}", [filelist[i]]));
                    } else {
                      elem.parent().append('<p>'+interpolate("{% trans "File %s was not deleted" %}", [filelist[i]])+'</p>');
                    }
                  }
                }
                $("#popup .modal-body>p").addClass('alert alert-danger');
                $('#confirmbutton').hide();
                $('#cancelbutton').attr('value', "{% trans 'Close' %}");
                $('#cancelbutton').one('click', function() {$("#popup").hide();});
                }
            })
          })
        }
        function downloadImportFile(folder, filename) {
          $.jgrid.hideModal("#searchmodfbox_grid");
          window.open("{{request.prefix}}/execute/downloadfromfolder/" + folder + "/" + filename + '/', '_blank');
        }
        </script>
        ''')
      return template.render(context)
      # A list of translation strings from the above
      translated = (
        _("export"), _("file name"), _("size"), _("changed"), _("Delete all files"),
        _("Delete file"), _("Upload data files"), _("Download file"),
        _("Import CSV or Excel files from the data folder. The file names must match the names of data objects and the first line in the file must contain the field names."),
        _("File %s was not deleted"), _('Close'), _("File %s was deleted"), _("All data files were deleted"),
        _("You are about to delete all files"), _("You are about to delete file %s"),
        _("Delete file"), _("Confirm"), _("Cancel")
        )
    else:
      return None


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
