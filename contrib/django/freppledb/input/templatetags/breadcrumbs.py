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

register = template.Library()

class CrumbsNode(template.Node):
    ''' 
    Partial attempt to create a more generic breadcrumbs framework
    Missing:
      - 'popping' from the crumb stack, only pushing
      - behavior across sessions not as desired
    Not happy with it...
    Usage in your templates:
        {% load breadcrumbs %}
        {% crumbs any_url name %}
    '''
    def __init__(self, url, name):
        self.url = url
        self.name = name
    def render(self, context):
        # Pick up the current crumbs from the session cookie
        cur = context.get('request').session.get('crumbs', [])
        cur.append((self.url,self.name))
        context.get('request').session['crumbs'] = cur
        # Now create HTML code to return
        return ' '.join([ ('<a href="%s">%s</a>' % (i,j))  for i,j in cur])

def do_crumbs(parser, token):
    try:
        tagname, url, name = token.split_contents()
    except ValueError:
        raise template.TemplateSyntaxError, "%r tag requires 2 arguments" % token.contents[0]
    return CrumbsNode(url,name)

register.tag('crumbs', do_crumbs)
