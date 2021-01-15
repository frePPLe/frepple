#
# Copyright (C) 2016 by frePPLe bv
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

from django.conf import settings
from django.db import DEFAULT_DB_ALIAS
from django.utils import formats
from django.utils.encoding import force_text
from django.utils.html import escape
from django.utils.text import capfirst
from django.utils.timesince import timesince
from django.utils.translation import gettext_lazy as _

from freppledb import __version__
from freppledb.common.dashboard import Dashboard, Widget
from freppledb.common.models import Notification


class WelcomeWidget(Widget):
    name = "welcome"
    title = _("Welcome")
    tooltip = _("Some links to get started")
    asynchronous = False

    def render(self, request=None):
        from freppledb.common.middleware import _thread_locals

        try:
            versionnumber = __version__.split(".", 2)
            docurl = "%s/docs/%s.%s/index.html" % (
                settings.DOCUMENTATION_URL,
                versionnumber[0],
                versionnumber[1],
            )
        except:
            docurl = "%s/docs/current/index.html" % (settings.DOCUMENTATION_URL,)

        try:
            db = _thread_locals.request.database
            if not db or db == DEFAULT_DB_ALIAS:
                prefix = ""
            else:
                prefix = "/%s" % _thread_locals.request.database
        except Exception:
            prefix = ""
        return (
            _(
                """Welcome to the world's leading open source production planning tool!<br><br>
How to get started?
<ol>
<li>Check out the <span class="underline"><a href="%(docurl)s" target="_blank" rel="noopener">documentation</a></span></li>
<li>Visit and join the <span class="underline"><a href="http://groups.google.com/group/frepple-users" target="_blank" rel="noopener">user community</a></span></li>
<li><span class="underline"><a href="https://frepple.com/company/#contact" target="_blank" rel="noopener">Contact us</a></span></li>
</ol>
"""
            )
            % {"docurl": docurl, "prefix": prefix}
        )


Dashboard.register(WelcomeWidget)


class NewsWidget(Widget):
    name = "news"
    title = _("News")
    tooltip = _("Show the latest news items from the frePPLe website")
    asynchronous = False

    def render(self, request=None):
        return '<iframe style="width:100%; border:none;" src="https://frepple.com/news-summary/"></iframe>'


Dashboard.register(NewsWidget)


class InboxWidget(Widget):
    name = "inbox"
    title = _("inbox")
    tooltip = _("Unread messages from your inbox")
    url = "/inbox/"
    asynchronous = False
    limit = 10

    def render(self, request=None):
        from freppledb.common.middleware import _thread_locals

        try:
            db = _thread_locals.request.database or DEFAULT_DB_ALIAS
        except Exception:
            db = DEFAULT_DB_ALIAS
        notifs = list(
            Notification.objects.using(db)
            .filter(user=_thread_locals.request.user)
            .order_by("-id")
            .select_related("comment", "user")[: self.limit]
        )
        if not notifs:
            return """
              <div class="pull-left"><i class="fa fa-5x fa-trophy" style="color: gold"></i>&nbsp;&nbsp;</div>
              <h2>Congrats!</h2>
              Your inbox is empty.
              """
        result = []
        result.append(
            '<div class="table-responsive"><table class="table table-condensed table-hover"><tbody>'
        )
        for notif in notifs:
            result.append(
                """<tr><td>
                <a class="underline" href="%s%s">%s</a>&nbsp;<span class="small">%s</span>
                <div class="small pull-right" data-toggle="tooltip" data-original-title="%s %s">%s%s&nbsp;&nbsp;%s</div>
                <br><p style="padding-left: 10px; display: inline-block">%s</p>"""
                % (
                    _thread_locals.request.prefix,
                    notif.comment.getURL(),
                    notif.comment.object_repr,
                    escape(
                        capfirst(force_text(_(notif.comment.content_type.name)))
                        if notif.comment.content_type
                        else ""
                    ),
                    escape(notif.comment.user.get_full_name()),
                    formats.date_format(notif.comment.lastmodified, "DATETIME_FORMAT"),
                    '<img class="avatar-sm" src="/uploads/%s">&nbsp;'
                    % notif.comment.user.avatar
                    if notif.comment.user.avatar
                    else "",
                    escape(notif.comment.user.username),
                    timesince(notif.comment.lastmodified),
                    notif.comment.comment
                    if notif.comment.safe()
                    else escape(notif.comment.comment),
                )
                + "</td></tr>"
            )
        result.append("</tbody></table></div>")
        return "\n".join(result)

    javascript = """
    var hasForecast = %s;
    var hasIP = %s;
    """ % (
        "true" if "freppledb.forecast" in settings.INSTALLED_APPS else "false",
        "true" if "freppledb.inventoryplanning" in settings.INSTALLED_APPS else "false",
    )


Dashboard.register(InboxWidget)
