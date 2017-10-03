# Copyright (C) 2014 by frePPLe bvba
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
from django.db import DEFAULT_DB_ALIAS
from django.db.models import signals
from django.contrib.auth.models import Permission
from django.contrib.contenttypes.models import ContentType
from django.core.management.commands import loaddata
from django.utils.translation import ugettext_lazy as _
from django.template import Template, RequestContext

from freppledb.common.management import removeModelPermissions

from django.apps import apps
from django.conf import settings


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
  '''
  context = RequestContext(request, {'fixtures': fixtures, 'javascript': javascript})

  template = Template('''
    {% load i18n %}
    {% if perms.auth.run_db %}
    <form class="form" role="form" method="post" action="{{request.prefix}}/execute/launch/loaddata/">{% csrf_token %}
    <table>
      <tr>
        <td  style="padding: 0px 15px;">
          <button  class="btn btn-primary" id="load" type="submit" value="{% trans "launch"|capfirst %}">
            {% trans "launch"|capfirst %}
          </button>
        </td>
        <td>
          <div class="dropdown dropdown-submit-input">
            {% trans "Load one of the available datasets to the current database." %}
            <button class="btn btn-default dropdown-toggle form-control" id="entity" type="button" data-toggle="dropdown">-&nbsp;&nbsp;<span class="caret"></span>
            </button>
            <ul class="dropdown-menu col-xs-12" aria-labelledby="entity" id="entityul">
              {% for i in fixtures %}<li><a>{{i}}</a></li>{% endfor %}
            </ul>
          </div>
        </td>
      </tr>
    </table>
    <input type="hidden" name="fixture" id="loaddatafile" value="">
    </form>
    <script>{{ javascript|safe }}</script>
    {% endif %}
  ''')
  return template.render(context)


loaddata.Command.getHTML = getHTML
loaddata.Command.title = _('Load a dataset')
loaddata.Command.index = 1800


def updatePermissions(using=DEFAULT_DB_ALIAS, **kwargs):
  removeModelPermissions("execute", "task", using)
  p = Permission.objects.get_or_create(
    codename='run_db',
    content_type=ContentType.objects.get(model="permission", app_label="auth")
    )[0]
  p.name = 'Run database operations'
  p.save()


signals.post_migrate.connect(updatePermissions)
