#
# Copyright (C) 2014 by Johan De Taeye, frePPLe bvba
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

from django.contrib.auth.models import AnonymousUser
from django.contrib.admin.models import LogEntry
from django.db import DEFAULT_DB_ALIAS
from django.utils.translation import ugettext_lazy as _
from django.utils.text import capfirst
from django.utils.encoding import force_unicode

from freppledb.common.dashboard import Dashboard, Widget


class WelcomeWidget(Widget):
  name = "welcome"
  title = _("Welcome")
  async = False

  def render(self, request=None):
    return _('''Welcome to frePPLe, the world's leading open source production planning tool!<br/><br/>
How to get started?
<ol><li>Start the <span class="underline"><a href="javascript:void(0);" onclick="tour.start('0,0,0'); return false;">guided tour</a></span></li>
<li>Check out the <span class="underline"><a href="/static/doc/index.html" target="_blank">documentation</a></span></li>
<li>Visit and join the <span class="underline"><a href="http://groups.google.com/group/frepple-users" target="_blank">user community</a></span></li>
<li><span class="underline"><a href="http://frepple.com/contact/" target="_blank">Contact us</a></span></li>
</ol>
''')

Dashboard.register(WelcomeWidget)


class NewsWidget(Widget):
  name = "news"
  title = _("News")
  async = False

  def render(self, request=None):
    return '<iframe style="width:100%" frameborder="0" src="http://frepple.com/news-summary/"></iframe>'

Dashboard.register(NewsWidget)


class RecentActionsWidget(Widget):
  name = "recent_actions"
  title = _("My actions")
  async = False

  def render(self, request=None):
    # This code is a slightly modified version of a standard Django tag.
    # The only change is to look for the logentry records in the right database.
    # See the file django\contrib\admin\templatetags\log.py
    from freppledb.common.middleware import current_request
    try: db = current_request.database or DEFAULT_DB_ALIAS
    except: db = DEFAULT_DB_ALIAS
    if isinstance(current_request.user, AnonymousUser):
      q = LogEntry.objects.using(db).select_related('content_type', 'user')[:self.limit]
    else:
      q = LogEntry.objects.using(db).filter(user__id__exact=current_request.user.pk).select_related('content_type', 'user')[:self.limit]
    result = []
    for entry in q:
      if entry.is_change():
        result.append('<span style="display: inline-block;" class="ui-icon ui-icon-pencil"></span><a href="%s%s">%s</a>' % (current_request.prefix, entry.get_admin_url(), entry.object_repr))
      elif entry.is_addition():
        result.append('<span style="display: inline-block;" class="ui-icon ui-icon-plusthick"></span><a href="%s%s">%s</a>' % (current_request.prefix, entry.get_admin_url(), entry.object_repr))
      elif entry.is_deletion():
        result.append('<span style="display: inline-block;" class="ui-icon ui-icon-minusthick"></span>%s' % entry.object_repr)
      else:
        raise "Unexpected log entry type"
      if entry.content_type:
        result.append('<span class="mini">%s</span><br/>' % capfirst(force_unicode(_(entry.content_type.name))) )
      else:
        result.append('<span class="mini">%s</span><br/>' % force_unicode(_('Unknown content')))
    return result and '\n'.join(result) or force_unicode(_('None available'))

Dashboard.register(RecentActionsWidget)
