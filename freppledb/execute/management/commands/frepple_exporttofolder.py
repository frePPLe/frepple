#
# Copyright (C) 2016 by frePPLe bvba
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
import errno
import gzip
import logging

from _datetime import datetime
from time import localtime, strftime
from django.conf import settings
from django.db import connections, DEFAULT_DB_ALIAS
from django.core.management.base import BaseCommand, CommandError
from django.utils.translation import ugettext_lazy as _
from django.template import Template, RequestContext

from freppledb.common.models import User
from freppledb import VERSION
from freppledb.execute.models import Task

logger = logging.getLogger(__name__)


class Command(BaseCommand):

  help = '''
    Exports tables from the frePPLe database to CSV files in a folder
    '''

  requires_system_checks = False

  statements = [
      ("purchaseorder.csv.gz",
       "export",
        '''COPY
        (select source, lastmodified, id, status , reference, quantity,
        to_char(startdate,'YYYY-MM-DD HH24:MI:SS') as startdate,
        to_char(enddate,'YYYY-MM-DD HH24:MI:SS') as enddate,
        criticality, EXTRACT(EPOCH FROM delay) as delay,
        owner_id, item_id, location_id, supplier_id from operationplan
        where status <> 'confirmed' and type='PO')
        TO STDOUT WITH CSV HEADER'''
        ),
      ("distributionorder.csv.gz",
       "export",
        '''COPY
        (select source, lastmodified, id, status, reference, quantity,
        to_char(startdate,'YYYY-MM-DD HH24:MI:SS') as startdate,
        to_char(enddate,'YYYY-MM-DD HH24:MI:SS') as enddate,
        criticality, EXTRACT(EPOCH FROM delay) as delay,
        plan, destination_id, item_id, origin_id from operationplan
        where status <> 'confirmed' and type='DO')
        TO STDOUT WITH CSV HEADER'''
        ),
      ("manufacturingorder.csv.gz",
       "export",
       '''COPY
       (select source, lastmodified, id , status ,reference ,quantity,
       to_char(startdate,'YYYY-MM-DD HH24:MI:SS') as startdate,
       to_char(enddate,'YYYY-MM-DD HH24:MI:SS') as enddate,
       criticality, EXTRACT(EPOCH FROM delay) as delay,
       operation_id, owner_id, plan, item_id
       from operationplan where status <> 'confirmed' and type='MO')
       TO STDOUT WITH CSV HEADER'''
       )
      ]


  def get_version(self):
    return VERSION


  def add_arguments(self, parser):
    parser.add_argument(
      '--user',
      help='User running the command'
      )
    parser.add_argument(
      '--database', default=DEFAULT_DB_ALIAS,
      help='Nominates a specific database to load the data into'
      )
    parser.add_argument(
      '--task', type=int,
      help='Task identifier (generated automatically if not provided)'
      )
    parser.add_argument(
      '--logfile', dest='logfile', action='store_true', default=False,
      help='Define a name for the log file (default = False)'
      )


  def handle(self, *args, **options):
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

    if 'logfile' in options and options['logfile']:
      logfile = re.split(r'/|:|\\', options['logfile'])[-1]
    else:
      timestamp = now.strftime("%Y%m%d%H%M%S")
      if self.database == DEFAULT_DB_ALIAS:
        logfile = 'exporttofolder-%s.log' % timestamp
      else:
        logfile = 'exporttofolder_%s-%s.log' % (self.database, timestamp)

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
        if task.started or task.finished or task.status != "Waiting" or task.name != 'export to folder':
          raise CommandError("Invalid task identifier")
        task.status = '0%'
        task.started = now
        logfile = task.logfile
      else:
        task = Task(name='export to folder', submitted=now, started=now, status='0%', user=self.user, logfile=logfile)
      task.arguments = ' '.join(['"%s"' % i for i in args])
      task.save(using=self.database)

      # Execute
      if os.path.isdir(settings.DATABASES[self.database]['FILEUPLOADFOLDER']):

        # Open the logfile
        # The log file remains in the upload folder as different folders can be specified
        # We do not want t create one log file per folder
        if not os.path.isdir(os.path.join(settings.DATABASES[self.database]['FILEUPLOADFOLDER'], 'export')):
          try:
            os.makedirs(os.path.join(settings.DATABASES[self.database]['FILEUPLOADFOLDER'], 'export'))
          except OSError as exception:
            if exception.errno != errno.EEXIST:
              raise

        self.logfile = open(os.path.join(settings.FREPPLE_LOGDIR, logfile), "a")
        print("%s Started export to folder\n" % datetime.now(), file=self.logfile)

        cursor = connections[self.database].cursor()

        task.status = '0%'
        task.save(using=self.database)

        i = 0
        cnt = len(self.statements)

        for filename, export, sqlquery in self.statements:
          print("%s Started export of %s" % (datetime.now(),filename), file=self.logfile)

          #make sure export folder exists
          exportFolder = os.path.join(settings.DATABASES[self.database]['FILEUPLOADFOLDER'], export)
          if not os.path.isdir(exportFolder):
            os.makedirs(exportFolder)

          try:
            if filename.lower().endswith(".gz"):
              csv_datafile = gzip.open(os.path.join(exportFolder, filename), "w")
            else:
              csv_datafile = open(os.path.join(exportFolder, filename), "w")

            cursor.copy_expert(sqlquery, csv_datafile)

            csv_datafile.close()
            i += 1

          except Exception as e:
            errors += 1
            print("%s Failed to export to %s" % (datetime.now(), filename), file=self.logfile)
            if task:
              task.message = 'Failed to export %s' % filename

          task.status = str(int(i / cnt*100)) + '%'
          task.save(using=self.database)

        print("%s Exported %s file(s)\n" % (datetime.now(), cnt - errors), file=self.logfile)

      else:
        errors += 1
        print("%s Failed, folder does not exist" % datetime.now(), file=self.logfile)
        task.message = "Destination folder does not exist"
        task.save(using=self.database)

    except Exception as e:
      if self.logfile:
        print("%s Failed" % datetime.now(), file=self.logfile)
      errors += 1
      if task:
        task.message = 'Failed to export'
      logger.error("Failed to export: %s" % e)

    finally:
      if task:
        if not errors:
          task.status = '100%'
          task.message = "Exported %s data files" % (cnt)
        else:
          task.status = 'Failed'
          #  task.message = "Exported %s data files, %s failed" % (cnt-errors, errors)
        task.finished = datetime.now()
        task.save(using=self.database)

      if self.logfile:
        print('%s End of export to folder\n' % datetime.now(), file=self.logfile)
        self.logfile.close()

  # accordion template
  title = _('Export plan result to folder')
  index = 1200

  @ staticmethod
  def getHTML(request):

    if 'FILEUPLOADFOLDER' in settings.DATABASES[request.database] and request.user.is_superuser:
      # Function to convert from bytes to human readabl format
      def sizeof_fmt(num):
        for unit in ['','Ki','Mi','Gi','Ti','Pi','Ei','Zi']:
          if abs(num) < 1024.0:
            return "%3.1f%sB" % (num, unit)
          num /= 1024.0
        return "%.1f%sB" % (num, 'Yi')

      # List available data files
      filesexported = []
      if 'FILEUPLOADFOLDER' in settings.DATABASES[request.database]:
        exportfolder = os.path.join(settings.DATABASES[request.database]['FILEUPLOADFOLDER'], 'export')
        if os.path.isdir(exportfolder):
          for file in os.listdir(exportfolder):
            if file.endswith(('.csv', '.csv.gz', '.log')):
              filesexported.append([
                file,
                strftime("%Y-%m-%d %H:%M:%S",localtime(os.stat(os.path.join(exportfolder, file)).st_mtime)),
                sizeof_fmt(os.stat(os.path.join(exportfolder, file)).st_size)
                ])

      javascript = '''
        function deleteExportFile(folder, filename) {
          $.jgrid.hideModal("#searchmodfbox_grid");
          var dialogcontent;
          if (typeof filename === 'object') {
            if (folder === 1) {
              dialogcontent = gettext('You are about to delete all exported files');
            } else {
              dialogcontent = gettext('You are about to delete all uploaded files');
            }
            var oldfilename = filename;
            filename = 'AllFiles';
          } else {
            dialogcontent = interpolate(gettext('You are about to delete file %s'), [filename]);
          }

          $("#popup").html('<div class="modal-dialog">'+
            '<div class="modal-content">'+
              '<div class="modal-header">'+
                '<h4 class="modal-title">'+gettext('Delete file')+'</h4>'+
              '</div>'+
              '<div class="modal-body"><p>'+
              dialogcontent +
              '</p></div>'+
              '<div class="modal-footer">'+
                '<input type="submit" id="confirmbutton" role="button" class="btn btn-danger pull-left" value="'+gettext('Confirm')+'">'+
                '<input type="submit" id="cancelbutton" role="button" class="btn btn-primary pull-right" data-dismiss="modal" value="'+gettext('Cancel')+'">'+
              '</div>'+
            '</div>'+
          '</div>' )
          .modal('show');

          $('#confirmbutton').on('click', function() {
            $.ajax({
              url: "/execute/deletefromfolder/" + folder + "/" + filename + "/",
              type: ("delete").toUpperCase(),
              success: function () {
                if (filename === 'AllFiles') {
                  $("#popup .modal-body>p").text(gettext('All data files were deleted'));
                } else {
                  $("#popup .modal-body>p").text(interpolate(gettext('File %s was deleted'), [filename]));
                }
                $('#confirmbutton').hide();
                $('#cancelbutton').attr('value',gettext('Close'));
                $('#cancelbutton').one('click', function() {$("#popup").hide();});
                $('tr[data-file="'+filename+'"]').remove();
              },
              error: function (result, stat, errorThrown) {
                var filelist = result.responseText.split(' / ');
                var elem = $("#popup .modal-body>p");
                if (filelist.length === 1) {
                  elem.text(interpolate(gettext('File %s was not deleted'), [filename]));
                } else {
                  for (var i = 1; i < filelist.length; i++) {
                    if (i === 1) {
                      elem.text(interpolate(gettext('File %s was not deleted'), [filelist[i]]));
                    } else {
                      elem.parent().append('<p>'+interpolate(gettext("File %s was not deleted"), [filelist[i]])+'</p>');
                    }
                  }
                }
                $("#popup .modal-body>p").addClass('alert alert-danger');
                $('#confirmbutton').hide();
                $('#cancelbutton').attr('value', gettext('Close'));
                $('#cancelbutton').one('click', function() {$("#popup").hide();});
                }
            })
          })
        }
        function downloadExportFile(folder, filename) {
          $.jgrid.hideModal("#searchmodfbox_grid");
          window.open("/execute/downloadfromfolder/" + folder + "/" + filename + '/', '_blank');
        }
        '''
      context = RequestContext(request, {'filesexported': filesexported, 'javascript': javascript})

      template = Template('''
        {% load i18n %}
        <form role="form" method="post" action="{{request.prefix}}/execute/launch/frepple_exporttofolder/">{% csrf_token %}
          <table>
            <tr>
              <td style="vertical-align:top; padding-left: 15px">
                <button type="submit" class="btn btn-primary" id="exporttofolder" value="{% trans "export"|capfirst %}">{% trans "export"|capfirst %}</button>
              </td>
              <td colspan='5' style="padding-left: 15px;">
                <p>{% trans "Exports the plan (purchase orders, distribution orders and manufacturing orders) as a set of CSV files." %}</p>
              </td>
            </tr>
            <tr>
              <td></td>
              <td><strong>{% trans 'file name'|capfirst %}</strong></td>
              <td><strong>{% trans 'size'|capfirst %}</strong></td>
              <td><strong>{% trans 'changed'|capfirst %}</strong></td>
              <td></td>
              <td>
                <div class="btn btn-xs btn-danger deletefile" style="margin-bottom: 5px;" id="allexportfilesdelete" data-toggle="tooltip" data-placement="top" data-original-title="Delete all files from folder" onClick="deleteExportFile(1, {{filesexported}})">
                  <span class="fa fa-close"></span>
                </div>
              </td>
            </tr></form>
            {% for j in filesexported %}
            <tr data-file="{{j.0}}">
              <td></td>
              <td>{{j.0}}</td>
              <td>{{j.2}}</td>
              <td>{{j.1}}</td>
              <td>
                <div class="btn btn-xs btn-primary downloadfile" style="margin-bottom: 5px;" id="filedownload" data-toggle="tooltip" data-placement="top" data-original-title="Download file" onClick="downloadExportFile(1, '{{j.0}}')">
                  <span class="fa fa-arrow-down"></span>
                </div>
              </td>
              <td>
                <div class="btn btn-xs btn-danger deletefile" style="margin-bottom: 5px;" id="filedelete" data-toggle="tooltip" data-placement="top" data-original-title="Delete file from folder" onClick="deleteExportFile(1, '{{j.0}}')">
                  <span class="fa fa-close"></span>
                </div>
              </td>
            </tr>
            {% endfor %}
          </table>
        </form>
        <script>{{ javascript|safe }}</script>
        ''')
      return template.render(context)
    else:
      return None
