#
# Copyright (C) 2018 by frePPLe bvba
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

import datetime
import os

from django.apps import apps
from django.conf import settings
from django.core.management.base import CommandError
from django.core.management.commands import loaddata
from django.db import connections, transaction
from django.template import Template, RequestContext
from django.utils.translation import ugettext_lazy as _


class Command(loaddata.Command):

  @staticmethod
  def getHTML(request):
    #  here is the code for the accordion menu

    # Loop over all fixtures of all apps and directories
    fixtures = set()
    folders = list(settings.FIXTURE_DIRS)
    for app in apps.get_app_configs():
      if not app.name.startswith('django'):
        folders.append(os.path.join(os.path.dirname(app.path), app.label, 'fixtures'))
    for f in folders:
      try:
        for root, dirs, files in os.walk(f):
          for i in files:
            if i.endswith('.json'):
              fixtures.add(i.split('.')[0])
      except:
        pass  # Silently ignore failures
    fixtures = sorted(fixtures)

    javascript = '''
          $("#entityul li a").click(function(){
            $("#entity").html($(this).text() + ' <span class="caret"></span>');
            $("#loaddatafile").val($(this).text());
          });
          function checkbox_changed(checkbox) {
            $("#regeneratevar").val(checkbox.checked);
          };
    '''
    context = RequestContext(request, {'fixtures': fixtures, 'javascript': javascript})

    template = Template('''
      {% load i18n %}
      {% if perms.auth.run_db %}
      <form class="form" role="form" method="post"
        onsubmit="return $('#loaddatafile').val() != ''"
        action="{{request.prefix}}/execute/launch/loaddata/">{% csrf_token %}
      <table>
        <tr>
          <td style="padding:15px; vertical-align:top">
            <button  class="btn btn-primary" id="load" type="submit" value="{% trans "launch"|capfirst %}">
              {% trans "launch"|capfirst %}
            </button>
          </td>
          <td style="padding:15px">
            <div class="dropdown dropdown-submit-input">
              <p>{% trans "Load one of the available datasets." %}</p>
              <button class="btn btn-default dropdown-toggle form-control" id="entity" type="button" data-toggle="dropdown">-&nbsp;&nbsp;<span class="caret"></span>
              </button>
              <ul class="dropdown-menu col-xs-12" aria-labelledby="entity" id="entityul">
                {% for i in fixtures %}<li><a>{{i}}</a></li>{% endfor %}
              </ul>
            </div>
          </td>
          <td style="padding:15px">
            <div>
              <ul class="checkbox">
                <li><input type="checkbox" id="cb1" onclick="checkbox_changed(this)" checked />
                <label for="cb1">{% trans "Execute plan after loading is done" %}</label></li>
              </ul>
            </div>
          </td>
        </tr>
      </table>
      <input type="hidden" name="fixture" id="loaddatafile" value="">
      <input type="hidden" name="regenerateplan" id="regeneratevar" value="true">
      </form>
      <script>{{ javascript|safe }}</script>
      {% else %}
        {% trans "Sorry, You don't have any execute permissions..." %}
      {% endif %}
    ''')
    return template.render(context)
    # A list of translation strings from the above
    translated = (
      _("launch"), _("Load one of the available datasets."),
      _("Sorry, You don't have any execute permissions..."),
      _("Execute plan after loading is done")
      )

  title = _('Load a dataset')
  index = 1800
  help_url = 'user-guide/command-reference.html#loaddata'

  def handle(self, *args, **options):
    super(Command, self).handle(*args, **options)

    # if the fixture doesn't contain the 'demo' word, let's not apply loaddata post-treatments
    if '_demo' not in (args[0]).lower():
      return

    # get the database object
    database = options['database']
    if database not in settings.DATABASES:
      raise CommandError("No database settings known for '%s'" % database )

    with transaction.atomic(using=database, savepoint=False):
      print('updating fixture to current date')

      cursor = connections[database].cursor()
      cursor.execute('''
        select to_timestamp(value,'YYYY-MM-DD hh24:mi:ss') from common_parameter where name = 'currentdate'
      ''')
      currentDate = cursor.fetchone()[0]
      now = datetime.datetime.now()
      offset = (now - currentDate).days

      #update currentdate to now
      cursor.execute('''
        update common_parameter set value = 'now' where name = 'currentdate'
      ''')

      #update demand due dates
      cursor.execute('''
        update demand set due = due + %s * interval '1 day'
      ''', (offset,))

      #update PO/DO/MO due dates
      cursor.execute('''
        update operationplan set startdate = startdate + %s * interval '1 day', enddate = enddate + %s * interval '1 day'
      ''', 2 * (offset,))
