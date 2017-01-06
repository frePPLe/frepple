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

from django.contrib.auth.models import AnonymousUser
from django.contrib.admin.models import LogEntry
from django.db import DEFAULT_DB_ALIAS, connections
from django.utils import formats
from django.utils.html import escape
from django.utils.translation import ugettext_lazy as _
from django.utils.text import capfirst
from django.utils.encoding import force_text

from freppledb import VERSION
from freppledb.common.dashboard import Dashboard, Widget
from freppledb.common.models import Comment, Wizard


class WelcomeWidget(Widget):
  name = "welcome"
  title = _("Welcome")
  tooltip = _("Some links to get started")
  asynchronous = False

  def render(self, request=None):
    versionnumber = VERSION.split('.', 2)
    return _('''Welcome to frePPLe, the world's leading open source production planning tool!<br/><br/>
How to get started?
<ol><li>Start the <span class="underline"><a href="javascript:void(0);" onclick="tour.start('0,0,0'); return false;">guided tour</a></span></li>
<li>Check out the <span class="underline"><a href="%(docurl)s" target="_blank">documentation</a></span></li>
<li>Visit and join the <span class="underline"><a href="http://groups.google.com/group/frepple-users" target="_blank">user community</a></span></li>
<li><span class="underline"><a href="https://frepple.com/contact/" target="_blank">Contact us</a></span></li>
</ol>
''') % {'docurl': "https://frepple.com/docs/%s.%s/" % (versionnumber[0], versionnumber[1])}

Dashboard.register(WelcomeWidget)


class WizardWidget(Widget):
  name = "wizard"
  title = _("Wizard to load your data")
  tooltip = _("Get started quick and easy to fill out the data tables")
  asynchronous = False
  url = '/wizard/'

  def render(self, request=None):
    from freppledb.common.middleware import _thread_locals
    try:
      db = _thread_locals.request.database or DEFAULT_DB_ALIAS
    except:
      db = DEFAULT_DB_ALIAS
    cursor = connections[db].cursor()
    cursor.execute('''
      with summary as (
      select owner_id as grp,
        sum(case when status then 1 else 0 end) steps_complete,
        count(*) steps_total
      from common_wizard
      where owner_id is not null
      group by owner_id
      )
      select 'Overall progress',
        coalesce(sum(steps_complete),0),
        coalesce(sum(greatest(steps_total,1)),1)
      from summary
      union all
      (
      select name, steps_complete, steps_total
      from summary
      inner join common_wizard
      on summary.grp = common_wizard.name
      order by common_wizard.sequenceorder
      )
      ''')

    result = ['<div class="table-reponsive"><table style="width: 100%"><thead>']
    first = True
    for label, complete, total in cursor.fetchall():
      progress = int(complete / total * 100)
      if first:
        first = False
        result.append('<tr id="overall"><th style="vertical-align: top; text-align: left; width: 150px; padding-right: 10px;">')
        result.append('<span>%s</span>' % capfirst(force_text(_('overall progress'))) )
        result.append('</th><th style="min-width: 50px"><div class="progress">')
        result.append('<div class="progress-bar progress-bar-success" role="progressbar" data-valuemin="0" data-valuemax="%s" data-valuenow="%s" style="width: %s%%; min-width: 0px;">' % (complete, total, progress) )
        result.append('<span style="color: black">%s%%</span>' % progress )
        result.append('</div>')
        result.append('</div></th></tr></thead><tbody>')
      else:
        result.append('<tr style="vertical-align: top"><td class="underline"><a href="/wizard/" target="_blank">%s</a></td>' % label)
        result.append('<td><div class="progress">')
        result.append('<div class="progress-bar progress-bar-success" role="progressbar" data-valuemin="0" data-valuemax="%s" data-valuenow="%s" style="width: %s%%; min-width: 0px;">' % (complete, total, progress) )
        result.append('<span style="color: black">%s%%</span>' % progress )
        result.append('</div></div></td></tr>')
    result.append('</tbody></table></div>')

    return '\n'.join(result)
Dashboard.register(WizardWidget)


class NewsWidget(Widget):
  name = "news"
  title = _("News")
  tooltip = _("Show the latest news items from the frePPLe website")
  asynchronous = False

  def render(self, request=None):
    return '<iframe style="width:100%; border:none;" src="https://frepple.com/news-summary/"></iframe>'

Dashboard.register(NewsWidget)


class RecentActionsWidget(Widget):
  name = "recent_actions"
  #. Translators: Translation included with Django
  title = _("My Actions")
  tooltip = _("Display a list of the entities you recently changed")
  asynchronous = False
  limit = 10

  def render(self, request=None):
    # This code is a slightly modified version of a standard Django tag.
    # The only change is to look for the logentry records in the right database.
    # See the file django\contrib\admin\templatetags\log.py
    from freppledb.common.middleware import _thread_locals
    try:
      db = _thread_locals.request.database or DEFAULT_DB_ALIAS
    except:
      db = DEFAULT_DB_ALIAS
    if isinstance(_thread_locals.request.user, AnonymousUser):
      q = LogEntry.objects.using(db).select_related('content_type', 'user')[:self.limit]
    else:
      q = LogEntry.objects.using(db).filter(user__id__exact=_thread_locals.request.user.pk).select_related('content_type', 'user')[:self.limit]
    result = []
    for entry in q:
      if entry.is_change():
        result.append('<span style="display: inline-block;" class="fa fa-pencil"></span><a href="%s%s">&nbsp;%s</a>' % (_thread_locals.request.prefix, entry.get_admin_url(), escape(entry.object_repr)))
      elif entry.is_addition():
        result.append('<span style="display: inline-block;" class="fa fa-plus"></span><a href="%s%s">&nbsp;%s</a>' % (_thread_locals.request.prefix, entry.get_admin_url(), escape(entry.object_repr)))
      elif entry.is_deletion():
        result.append('<span style="display: inline-block;" class="fa fa-minus"></span>&nbsp;%s' % escape(entry.object_repr))
      else:
        raise "Unexpected log entry type"
      if entry.content_type:
        result.append('<span class="small">%s</span><br/>' % capfirst(force_text(_(entry.content_type.name))) )
      else:
        result.append('<span class="small">%s</span><br/>' % force_text(_('Unknown content')))
    #. Translators: Translation included with Django
    return result and '\n'.join(result) or force_text(_('None available'))

Dashboard.register(RecentActionsWidget)


class RecentCommentsWidget(Widget):
  name = "recent_comments"
  title = _("comments")
  tooltip = _("Display a list of recent comments")
  url = '/data/common/comment/?sord=desc&sidx=lastmodified'
  asynchronous = False
  limit = 10

  def render(self, request=None):
    from freppledb.common.middleware import _thread_locals
    try:
      db = _thread_locals.request.database or DEFAULT_DB_ALIAS
    except:
      db = DEFAULT_DB_ALIAS
    cmts = Comment.objects.using(db).order_by('-lastmodified').select_related('content_type', 'user')[:self.limit]
    result = []
    result.append('<div class="table-responsive"><table class="table table-condensed"><tbody>');
    for c in cmts:
      result.append('<tr><td><a href="%s%s">%s</a>&nbsp;<span class="small">%s</span><div class="small" style="float: right;">%s&nbsp;&nbsp;%s</div></br><p style="padding-left: 10px; display: inline-block;">%s</p>' % (
        _thread_locals.request.prefix, c.get_admin_url(), escape(c.object_pk),
        escape(capfirst(force_text(_(c.content_type.name))) if c.content_type else force_text(_('Unknown content'))),
        escape(c.user.username if c.user else ''),
        formats.date_format(c.lastmodified, 'SHORT_DATETIME_FORMAT'),
        escape(c.comment)
        )+'</td></tr>')
    result.append('</tbody></table></div>')
    #. Translators: Translation included with Django
    return '\n'.join(result) if result else force_text(_('None available'))

Dashboard.register(RecentCommentsWidget)
