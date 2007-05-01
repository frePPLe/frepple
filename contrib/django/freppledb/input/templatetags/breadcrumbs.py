#
# Copyright (C) 2007 by Johan De Taeye
#
# This library is free software; you can redistribute it and/or modify it
# under the terms of the GNU Lesser General Public License as published
# by the Free Software Foundation; either version 2.1 of the License, or
# (at your option) any later version.
#
# This library is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU Lesser
# General Public License for more details.
#
# You should have received a copy of the GNU Lesser General Public
# License along with this library; if not, write to the Free Software
# Foundation Inc., 59 Temple Place, Suite 330, Boston, MA 02111-1307, USA
#

# file : $URL$
# revision : $LastChangedRevision$  $LastChangedBy$
# date : $LastChangedDate$
# email : jdetaeye@users.sourceforge.net

from django import template
from django.contrib.sessions.models import Session
from django.template import resolve_variable
import urllib

HOMECRUMB = '<a href="/">Site administration</a>'


class CrumbsNode(template.Node):
    '''
    A generic breadcrumbs framework.
    Usage in your templates:
        {% load breadcrumbs %}
        {% crumbs %}
    The admin app already defines a block for crumbs, so the typical usage of the
    crumbs tag is as follows:
      {%block breadcrumbs%}<div class="breadcrumbs">{%crumbs%}</div>{%endblock%}
    '''
    def render(self, context):
        global HOMECRUMB
        # Pick up the current crumbs from the session cookie
        req = context['request']
        try: cur = req.session['crumbs']
        except: cur = [HOMECRUMB]

        # Pop from the stack if the same url is already in the crumbs
        try: title = resolve_variable("title",context)
        except: title = req.get_full_path()
        key = '<a href="%s">%s</a>' % (req.get_full_path(), title)
        cnt = 0
        for i in cur:
           if i == key:
             cur = cur[0:cnt]   # Pop all remaining elements from the stack
             break
           cnt += 1

        # Push current url on the stack
        cur.append(key)

        # Update the current session
        req.session['crumbs'] = cur

        # Now create HTML code to return
        return '  >  '.join(cur)

def do_crumbs(parser, token):
    return CrumbsNode()


def superlink(value,type):
    '''
    This filter creates a link with a context menu for right-clicks.
    '''
    # Fail silently if we end up with an empty string
    if value is None: return ''
    # Convert the parameter into a string if it's not already
    if not isinstance(value,basestring): value = str(value)
    # Fail silently if we end up with an empty string
    if value == '': return ''
    # Final return value
    return '<a href="/admin/input/%s/%s" class="%s">%s</a>' % (type,urllib.quote(value),type,value)


register = template.Library()
register.tag('crumbs',do_crumbs)
register.filter('superlink',superlink)
