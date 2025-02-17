#
# Copyright (C) 2016 by frePPLe bv
#
# Permission is hereby granted, free of charge, to any person obtaining
# a copy of this software and associated documentation files (the
# "Software"), to deal in the Software without restriction, including
# without limitation the rights to use, copy, modify, merge, publish,
# distribute, sublicense, and/or sell copies of the Software, and to
# permit persons to whom the Software is furnished to do so, subject to
# the following conditions:
#
# The above copyright notice and this permission notice shall be
# included in all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND,
# EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF
# MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND
# NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE
# LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION
# OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION
# WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.
#

from django.conf import settings
from django.db import DEFAULT_DB_ALIAS
from django.utils import formats
from django.utils.encoding import force_str
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

    @staticmethod
    def render(request):
        try:
            versionnumber = __version__.split(".", 2)
            docurl = "%s/docs/%s.%s/index.html" % (
                settings.DOCUMENTATION_URL,
                versionnumber[0],
                versionnumber[1],
            )
        except Exception:
            docurl = "%s/docs/current/index.html" % (settings.DOCUMENTATION_URL,)

        try:
            db = request.database
            if not db or db == DEFAULT_DB_ALIAS:
                prefix = ""
            else:
                prefix = "/%s" % db
        except Exception:
            prefix = ""
        return (
            _(
                """Welcome to the world's leading open source production planning tool!<br><br>
How to get started?
<ol>
<li>Check out the <span class="text-decoration-underline"><a href="%(docurl)s" target="_blank" rel="noopener">documentation</a></span></li>
<li>Visit and join the <span class="text-decoration-underline"><a href="https://github.com/frePPLe/frepple/discussions" target="_blank" rel="noopener">user community</a></span></li>
<li><span class="text-decoration-underline"><a href="https://frepple.com/company/#contact" target="_blank" rel="noopener">Contact us</a></span></li>
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

    @staticmethod
    def render(request):
        return '<iframe style="width:100%; border:none;" src="https://frepple.com/news-summary/"></iframe>'


Dashboard.register(NewsWidget)


class InboxWidget(Widget):
    name = "inbox"
    title = _("inbox")
    tooltip = _("Unread messages from your inbox")
    url = "/inbox/"
    asynchronous = False
    limit = 10

    @classmethod
    def render(cls, request):
        notifs = list(
            Notification.objects.using(request.database)
            .filter(user=request.user)
            .order_by("-id")
            .select_related("comment", "user")[: cls.limit]
        )
        if not notifs:
            return """
              <div class="pull-left"><i class="fa fa-5x fa-trophy" style="color: gold"></i>&nbsp;&nbsp;</div>
              <h2>Congrats!</h2>
              Your inbox is empty.
              """
        result = []
        result.append(
            '<div class="table-responsive"><table class="table table-sm table-hover"><tbody>'
        )
        for notif in notifs:
            result.append(
                """<tr><td>
                <a class="text-decoration-underline" href="%s%s">%s</a>&nbsp;<span class="small">%s</span>
                <div class="small pull-right" data-bs-toggle="tooltip" data-bs-title="%s %s">%s%s&nbsp;&nbsp;%s</div>
                <br><p style="padding-left: 10px; display: inline-block">%s</p>"""
                % (
                    request.prefix,
                    notif.comment.getURL(),
                    notif.comment.object_repr,
                    escape(
                        capfirst(force_str(_(notif.comment.content_type.name)))
                        if notif.comment.content_type
                        else ""
                    ),
                    escape(notif.comment.user.get_full_name()),
                    formats.date_format(notif.comment.lastmodified, "DATETIME_FORMAT"),
                    (
                        '<img class="avatar-sm" src="/uploads/%s">&nbsp;'
                        % notif.comment.user.avatar
                        if notif.comment.user.avatar
                        else ""
                    ),
                    escape(notif.comment.user.username),
                    timesince(notif.comment.lastmodified),
                    (
                        notif.comment.comment
                        if notif.comment.safe()
                        else escape(notif.comment.comment)
                    ),
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
