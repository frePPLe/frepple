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

from django.template import Library, Node, resolve_variable, TemplateSyntaxError
from django.contrib.sessions.models import Session
from django.conf import settings
from django.contrib.admin.views.main import quote
from django.utils.translation import ugettext as _
from django.utils.http import urlquote
from django.utils.encoding import iri_to_uri
from django.utils.encoding import smart_unicode
from django.utils.html import escape

HOMECRUMB = '<a href="/admin/">%s</a>'

register = Library()


#
# A tag to find all models a user is allowed to see
#

class ModelsNode(Node):
    def __init__(self, appname, varname):
        self.varname = varname
        self.appname = appname

    def render(self, context):
        from django.db import models
        from django.utils.text import capfirst
        user = context['user']
        model_list = []
        if user.has_module_perms(self.appname):
          for m in models.get_models(models.get_app(self.appname)):
             # Verify if the model is allowed to be displayed in the admin ui and
             # check the user has appropriate permissions to access it
             if m._meta.admin and user.has_perm("%s.%s" % (self.appname, m._meta.get_change_permission())):
                 model_list.append({
                   'name': capfirst(m._meta.verbose_name_plural),
                   'admin_url': '/admin/%s/%s/' % (self.appname, m.__name__.lower()),
                   })
          model_list.sort()
        context[self.varname] = model_list
        return ''


def get_models(parser, token):
    """
    Returns a list of output models to which the user has permissions.

    Syntax::

        {% get_models from [application_name] as [context_var_containing_app_list] %}

    Example usage::

        {% get_models from output as modelsOut %}
    """
    tokens = token.contents.split()
    if len(tokens) < 5:
        raise TemplateSyntaxError, "'%s' tag requires two arguments" % tokens[0]
    if tokens[1] != 'from':
        raise TemplateSyntaxError, "First argument to '%s' tag must be 'from'" % tokens[0]
    if tokens[3] != 'as':
        raise TemplateSyntaxError, "Third argument to '%s' tag must be 'as'" % tokens[0]
    return ModelsNode(tokens[2],tokens[4])

register.tag('get_models', get_models)


#
# A tag to create breadcrumbs on your site
#

class CrumbsNode(Node):
    '''
    A generic breadcrumbs framework.
    Usage in your templates:
        {% crumbs %}

    The admin app already defines a block for crumbs, so the typical usage of the
    crumbs tag is as follows:
        {%block breadcrumbs%}<div class="breadcrumbs">{%crumbs%}</div>{%endblock%}

    When the context variable 'reset_crumbs' is defined and set to True, the trail of
    breadcrumbs is truncated and restarted.
    The variable can be set either as an extra context variable in the view
    code, or with the 'set' template tag in the template:
        {% set reset_crumbs "True" %}
    '''
    def render(self, context):
        global HOMECRUMB
        try: req = context['request']
        except: return ''  # No request found in the context: no crumbs...
        # Pick up the current crumbs from the session cookie
        try: cur = req.session['crumbs']
        except: cur = [(_('Home'),HOMECRUMB % _('Home'))]

        # Check if we need to reset the crumbs
        try:
          if context['reset_crumbs']: cur = [(_('Home'),HOMECRUMB % _('Home'))]
        except: pass

        # Pop from the stack if the same url is already in the crumbs
        try: title = resolve_variable("title",context)
        except: title = req.get_full_path()
        # A special case to work around the hardcoded title of the main admin page
        if title == _('Site administration'): title = _('Home')
        cnt = 0
        for i in cur:
           if i[0] == title:
             cur = cur[0:cnt]   # Pop all remaining elements from the stack
             break
           cnt += 1

        # Push current url on the stack
        cur.append( (title,'<a href="%s">%s</a>' % (escape(req.get_full_path()), escape(title))) )

        # Update the current session
        req.session['crumbs'] = cur

        # Now create HTML code to return
        return '  >  '.join([i[1] for i in cur])

def do_crumbs(parser, token):
    return CrumbsNode()

register.tag('crumbs', do_crumbs)


#
# A tag to create a superlink, which is a hyperlink plus a rightclick context menu
#

def superlink(value,type):
    '''
    This filter creates a link with a context menu for right-clicks.
    '''
    # Fail silently if we end up with an empty string
    if value is None: return ''
    # Convert the parameter into a string if it's not already
    if not isinstance(value,basestring): value = unicode(value)
    # Fail silently if we end up with an empty string
    if value == '': return ''
    # Final return value
    return '<a href="/admin/input/%s/%s/" class="%s">%s</a>' % \
      (type, iri_to_uri(urlquote(value)), type, escape(value))

register.filter('superlink', superlink)


#
# A tag to update a context variable
#

class SetVariable(Node):
  def __init__(self, varname, value):
    self.varname = varname
    self.value = value

  def render(self, context):
    var = resolve_variable(self.value,context)
    if var:
      context[self.varname] = var
    else:
      context[self.varname] = context[self.value]
    return ''


def set_var(parser, token):
  '''
  Example:
    {% set category_list category.categories.all %}
    {% set dir_url "../" %}
    {% set type_list "table" %}
  '''
  from re import split
  bits = split(r'\s+', token.contents, 2)
  if len(bits) < 2:
      raise TemplateSyntaxError, "'%s' tag requires two arguments" % bits[0]
  return SetVariable(bits[1],bits[2])

register.tag('set', set_var)


#
# A simple tag returning the frePPLe version
#

@register.simple_tag
def version():
  '''
  A simple tag returning the version of the frepple application.
  '''
  return settings.FREPPLE_VERSION


#
# A tag to add a parameter to the current url
#

class AddParameter(Node):
  def __init__(self, varname, value):
    self.varname = varname
    self.value = value

  def render(self, context):
    req = resolve_variable('request',context)
    params = req.GET.copy()
    params[self.varname] = self.value
    return escape('%s?%s' % (req.path, params.urlencode()))

def addurlparameter(parser, token):
  '''
  Example:
    {% addurlparameter type csv %}
  If the current page url is "/mypage/?p=1" the tag will return the
  url "/mypage/?p=1&amp;type=csv"
  '''
  from re import split
  bits = split(r'\s+', token.contents, 2)
  if len(bits) < 2:
      raise TemplateSyntaxError, "'%s' tag requires two arguments" % bits[0]
  return AddParameter(bits[1],bits[2])

register.tag('addurlparameter', addurlparameter)
