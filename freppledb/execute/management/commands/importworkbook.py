#
# Copyright (C) 2011-2013 by frePPLe bvba
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
from datetime import datetime
import subprocess
import re
from logging import ERROR, WARNING, DEBUG

from openpyxl import load_workbook, Workbook
from openpyxl.utils import get_column_letter
from openpyxl.writer.write_only import WriteOnlyCell

from django.core.management.base import BaseCommand, CommandError
from django.core.files import File
from django.contrib.auth import get_permission_codename
from django.contrib.auth.models import Group
from django.contrib.contenttypes.models import ContentType
from django.db import DEFAULT_DB_ALIAS
from django.db import connections, transaction, models
from django.conf import settings
from django.utils import translation, six
from django.utils.translation import ugettext_lazy as _
from django.utils.encoding import smart_str, force_text, force_str
from django.template import Template, RequestContext
from django.http import HttpRequest

from freppledb import VERSION
from freppledb.common.middleware import _thread_locals
from freppledb.common.models import User, Comment
from freppledb.common.report import importWorkbook, GridReport, matchesModelName
from freppledb.common.dataload import parseExcelWorksheet
from freppledb.execute.models import Task

import logging
logger = logging.getLogger(__name__)

# A list of models with some special, administrative purpose.
# They should be excluded from bulk import, export and erasing actions.
EXCLUDE_FROM_BULK_OPERATIONS = (Group, User, Comment)


class Command(BaseCommand):

  # help = "Loads XLS workbook file into the frePPLe database"
  help = "command not implemented yet"

  requires_system_checks = False

  def add_arguments(self, parser):
    parser.add_argument(
      '--user', help='User running the command'
      )
    parser.add_argument(
      '--database', default=DEFAULT_DB_ALIAS,
      help='Nominates a specific database to load data from and export results into'
      )
    parser.add_argument(
      '--task', type=int,
      help='Task identifier (generated automatically if not provided)'
      )
    parser.add_argument(
      'file', nargs='+',
      help='workbook file name'
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
      logfile = 'importworkbook-%s.log' % timestamp
    else:
      logfile = 'importworkbook_%s-%s.log' % (self.database, timestamp)

    task = None
    try:
      setattr(_thread_locals, 'database', self.database)
      # Initialize the task
      if options['task']:
        try:
          task = Task.objects.all().using(self.database).get(pk=options['task'])
        except:
          raise CommandError("Task identifier not found")
        if task.started or task.finished or task.status != "Waiting" or task.name not in ('frepple_importworkbook', 'importworkbook'):
          raise CommandError("Invalid task identifier")
        task.status = '0%'
        task.started = now
      else:
        task = Task(name='importworkbook', submitted=now, started=now, status='0%', user=self.user)
      task.arguments = ' '.join(options['file'])
      task.save(using=self.database)

      all_models = [ (ct.model_class(), ct.pk) for ct in ContentType.objects.all() if ct.model_class() ]
      try:
        with transaction.atomic(using=self.database):
          # Find all models in the workbook
          for file in filename:
            wb = load_workbook(filename=file, read_only=True, data_only=True)
            models = []
            for ws_name in wb.sheetnames:
              # Find the model
              model = None
              contenttype_id = None
              for m, ct in all_models:
                if matchesModelName(ws_name, m):
                  model = m
                  contenttype_id = ct
                  break
              if not model or model in EXCLUDE_FROM_BULK_OPERATIONS:
                print(force_text(_("Ignoring data in worksheet: %s") % ws_name))
                # yield '<div class="alert alert-warning">' + force_text(_("Ignoring data in worksheet: %s") % ws_name) + '</div>'
              elif not self.user.has_perm('%s.%s' % (model._meta.app_label, get_permission_codename('add', model._meta))):
                # Check permissions
                print(force_text(_("You don't permissions to add: %s") % ws_name))
                # yield '<div class="alert alert-danger">' + force_text(_("You don't permissions to add: %s") % ws_name) + '</div>'
              else:
                deps = set([model])
                GridReport.dependent_models(model, deps)
                models.append( (ws_name, model, contenttype_id, deps) )

            # Sort the list of models, based on dependencies between models
            models = GridReport.sort_models(models)
            print('197----', models)
            # Process all rows in each worksheet
            for ws_name, model, contenttype_id, dependencies in models:
              print(force_text(_("Processing data in worksheet: %s") % ws_name))
              # yield '<strong>' + force_text(_("Processing data in worksheet: %s") % ws_name) + '</strong><br>'
              # yield ('<div class="table-responsive">'
                     # '<table class="table table-condensed" style="white-space: nowrap;"><tbody>')
              numerrors = 0
              numwarnings = 0
              firsterror = True
              ws = wb[ws_name]
              for error in parseExcelWorksheet(model, ws, user=self.user, database=self.database, ping=True):
                if error[0] == DEBUG:
                  # Yield some result so we can detect disconnect clients and interrupt the upload
                  # yield ' '
                  continue
                if firsterror and error[0] in (ERROR, WARNING):
                  print('%s %s %s %s %s%s%s' % (
                    capfirst(_("worksheet")), capfirst(_("row")),
                    capfirst(_("field")), capfirst(_("value")),
                    capfirst(_("error")), " / ", capfirst(_("warning"))
                    ))
                  # yield '<tr><th class="sr-only">%s</th><th>%s</th><th>%s</th><th>%s</th><th>%s%s%s</th></tr>' % (
                  #   capfirst(_("worksheet")), capfirst(_("row")),
                  #   capfirst(_("field")), capfirst(_("value")),
                  #   capfirst(_("error")), " / ", capfirst(_("warning"))
                  #   )
                  firsterror = False
                if error[0] == ERROR:
                  print('%s %s %s %s %s: %s' % (
                    ws_name,
                    error[1] if error[1] else '',
                    error[2] if error[2] else '',
                    error[3] if error[3] else '',
                    capfirst(_('error')),
                    error[4]
                    ))
                  # yield '<tr><td class="sr-only">%s</td><td>%s</td><td>%s</td><td>%s</td><td>%s: %s</td></tr>' % (
                  #   ws_name,
                  #   error[1] if error[1] else '',
                  #   error[2] if error[2] else '',
                  #   error[3] if error[3] else '',
                  #   capfirst(_('error')),
                  #   error[4]
                  #   )
                  numerrors += 1
                elif error[1] == WARNING:
                  print('%s %s %s %s %s: %s' % (
                    ws_name,
                    error[1] if error[1] else '',
                    error[2] if error[2] else '',
                    error[3] if error[3] else '',
                    capfirst(_('warning')),
                    error[4]
                    ))
                  # yield '<tr><td class="sr-only">%s</td><td>%s</td><td>%s</td><td>%s</td><td>%s: %s</td></tr>' % (
                  #   ws_name,
                  #   error[1] if error[1] else '',
                  #   error[2] if error[2] else '',
                  #   error[3] if error[3] else '',
                  #   capfirst(_('warning')),
                  #   error[4]
                  #   )
                  numwarnings += 1
                else:
                  print('%s %s %s %s %s %s' % (
                    "danger" if numerrors > 0 else 'success',
                    ws_name,
                    error[1] if error[1] else '',
                    error[2] if error[2] else '',
                    error[3] if error[3] else '',
                    error[4]
                    ))
              #     yield '<tr class=%s><td class="sr-only">%s</td><td>%s</td><td>%s</td><td>%s</td><td>%s</td></tr>' % (
              #       "danger" if numerrors > 0 else 'success',
              #       ws_name,
              #       error[1] if error[1] else '',
              #       error[2] if error[2] else '',
              #       error[3] if error[3] else '',
              #       error[4]
              #       )
              # yield '</tbody></table></div>'
            print('%s' % _("Done"))
            # yield '<div><strong>%s</strong></div>' % _("Done")
      except GeneratorExit:
        logger.warning('Connection Aborted')
    except Exception as e:
      if task:
        task.status = 'Failed'
        task.message = '%s' % e
        task.finished = datetime.now()
      raise e

    finally:
      setattr(_thread_locals, 'database', None)
      if task:
        task.save(using=self.database)

    return _("Done")

  # accordion template
  title = _('Import a spreadsheet')
  index = 1100
  help_url = 'user-guide/command-reference.html#importworkbook'

  @ staticmethod
  def getHTML(request):

    context = RequestContext(request, {})

    template = Template('''
      {% load i18n %}
      <table>
        <tr>
          <td style="vertical-align:top; padding: 15px">
            <button type="submit" class="btn btn-primary" id="import" onclick="import_show('{% trans "Import a spreadsheet" %}',null,false,uploadspreadsheetajax)" value="{% trans "import"|capfirst %}">{% trans "import"|capfirst %}</button>
          </td>
          <td style="padding: 15px 15px 0 15px">
            <p>{% trans "Import input data from a spreadsheet.</p><p>The spreadsheet must match the structure exported with the task above." %}</p>
          </td>
        </tr>
      </table>
      <script>
      var xhr = {abort: function () {}};

      var uploadspreadsheetajax = {
        url: '{{request.prefix}}/execute/launch/importworkbook/',
        success: function (data) {
          var el = $('#uploadResponse');
          el.html(data);
          if (el.attr('data-scrolled')!== "true") {
            el.scrollTop(el[0].scrollHeight - el.height());
          }
          $('#cancelbutton').html("{% trans 'Close' %}");
          $('#importbutton').hide();
          $("#animatedcog").css('visibility','hidden');
          $('#cancelimportbutton').hide();
          if (document.queryCommandSupported('copy')) {
            $('#copytoclipboard').show();
          }
          $("#grid").trigger("reloadGrid");
        },
        xhrFields: {
          onprogress: function (e) {
            var el = $('#uploadResponse');
            el.html(e.currentTarget.response);
            if (el.attr('data-scrolled')!== "true") {
              el.attr('data-scrolled', el[0].scrollHeight - el.height());
              el.scrollTop(el[0].scrollHeight - el.height());
            }
          }
        },
        error: function() {
          $('#cancelimportbutton').hide();
          $('#copytoclipboard').show();
          $("#animatedcog").css('visibility','hidden');
          $("#uploadResponse").scrollTop($("#uploadResponse")[0].scrollHeight);
        }
      };
      </script>
    ''')
    return template.render(context)
    # A list of translation strings from the above
    translated = (
      _("import"), _("Import a spreadsheet"),
      _("Import input data from a spreadsheet.</p><p>The spreadsheet must match the structure exported with the task above.")
      )
