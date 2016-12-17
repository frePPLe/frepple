#
# Copyright (C) 2007-2013 by frePPLe bvba
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

from decimal import Decimal
import json

from django.db import models
from django.contrib.admin.utils import unquote
from django.template import Library, Node, Variable, TemplateSyntaxError
from django.conf import settings
from django.utils.translation import ugettext as _
from django.utils.http import urlquote
from django.utils.encoding import iri_to_uri, force_text
from django.utils.html import escape
from django.utils.text import capfirst

from freppledb.common.models import User
from freppledb import VERSION

MAX_CRUMBS = 10

register = Library()
variable_title = Variable("title")
variable_request = Variable("request")
variable_popup = Variable("is_popup")


#
# A tag to create breadcrumbs on your site
#

class CrumbsNode(Node):
  r'''
  A generic breadcrumbs framework.

  Usage in your templates:
  {% crumbs %}

  The admin app already defines a block for crumbs, so the typical usage of the
  crumbs tag is as follows:
  {%block breadcrumbs%}<div class="breadcrumbs">{%crumbs%}</div>{%endblock%}
  '''

  def render(self, context):
    try:
      req = context['request']
    except:
      return ''  # No request found in the context: no crumbs...
    if not hasattr(req, 'session'):
      return  # No session found in the context: no crumbs...

    # Pick up the current crumbs from the session cookie
    try:
      cur = req.session['crumbs']
      try:
        cur = cur[req.prefix]
      except:
        cur = []
    except:
      req.session['crumbs'] = {}
      cur = []

    # Compute the new crumb node
    count = 0
    try:
      title = variable_title.resolve(context)
    except:
      title = req.get_full_path()
    if title != _('cockpit'):
      # Don't handle the cockpit screen in the crumbs
      try:
        # Check if the same title is already in the crumbs.
        title = str(title)
        exists = False
        for i in cur:
          if i[0] == title:
            # Current URL already exists in the list and we move it to the end
            node = i
            del cur[count]
            cur.append( (node[0], node[1], req.path) )
            exists = True
            break
          count += 1

        if not exists:
          # Add the current URL to the stack
          if 'tour' in req.GET:
            # Special case when the guided tour is used: we don't want to
            # include the tour argument in the breadcrumb. It makes the
            # breadcrumb link reenter the tour, which is not cool.
            params = req.GET.copy()
            params.pop('tour')
            cur.append( (
              title,
              '<li><a href="%s%s%s">%s</a></li>' % (
                req.prefix, urlquote(req.path),
                params and ('?' + iri_to_uri(params.urlencode())) or '',
                str(escape(capfirst(title)))
                ),
              req.path
              ))
          else:
            cur.append( (
              title,
              '<li><a href="%s%s%s">%s</a></li>' % (
                req.prefix, urlquote(req.path),
                req.GET and ('?' + iri_to_uri(req.GET.urlencode())) or '',
                str(escape(capfirst(title)))
                ),
              req.path
              ))
          count += 1

        # Limit the number of crumbs.
        while count > MAX_CRUMBS:
          count -= 1
          del cur[0]
      except:
        # Ignore errors to fail in a clean and graceful way
        pass

    # Update the current session
    req.session['crumbs'][req.prefix] = cur

    # Now create HTML code to return
    return ''.join([i[1] for i in cur])

  def __repr__(self):
    return "<Crumbs Node>"


def do_crumbs(parser, token):
    return CrumbsNode()

register.tag('crumbs', do_crumbs)


#
# A tag to update a context variable
#

class SetVariable(Node):
  def __init__(self, varname, value):
    self.varname = varname
    self.value = value

  def render(self, context):
    var = Variable(self.value).resolve(context)
    if var:
      context[self.varname] = var
    else:
      context[self.varname] = context[self.value]
    return ''

  def __repr__(self):
    return "<SetVariable Node>"


def set_var(parser, token):
  r'''
  Example:
  {% set category_list category.categories.all %}
  {% set dir_url "../" %}
  {% set type_list "table" %}
  '''
  from re import split
  bits = split(r'\s+', token.contents, 2)
  if len(bits) < 2:
    raise TemplateSyntaxError("'%s' tag requires two arguments" % bits[0])
  return SetVariable(bits[1], bits[2])

register.tag('set', set_var)



#
# A tag to include the tabs for a model
#

class ModelTabs(Node):
  def __init__(self, model):
    self.model = model

  def render(self, context):
    from django.db.models.options import Options
    from django.contrib.contenttypes.models import ContentType
    from freppledb.admin import data_site
    from django.core.urlresolvers import reverse
    try:
      # Look up the admin class to use
      model = Variable(self.model).resolve(context)
      if isinstance(model, Options):
        ct = ContentType.objects.get(app_label=model.app_label, model=model.object_name.lower())
      else:
        model = model.split(".")
        ct = ContentType.objects.get(app_label=model[0], model=model[1])
      admn = data_site._registry[ct.model_class()]
      if not hasattr(admn, 'tabs'):
        return ''

      # Render the admin class
      result = ['<div class="row"><div id="tabs" class="col-md-12 form-inline hor-align-right"><ul class="nav nav-tabs">']
      obj = context['object_id']
      active_tab = context.get('active_tab', 'edit')
      for tab in admn.tabs:
        if 'permissions' in tab:
          # A single permission is required
          if isinstance(tab['permissions'], str):
            if not context['request'].user.has_perm(tab['permissions']):
              continue
          else:
            # A list or tuple of permissions is given
            ok =  True
            for p in tab['permissions']:
              if not context['request'].user.has_perm(p):
                ok = False
                break
            if not ok:
              continue
        # Append to the results
        result.append(
          '<li %srole="presentation"><a class="ui-tabs-anchor" href="%s%s">%s</a></li>' % (
          'class="active" ' if active_tab == tab['name'] else '',
          context['request'].prefix,
          reverse(tab['view'], args=(obj,)),
          force_text(tab['label']).capitalize()
          ))
      result.append('</ul></div></div>')
      return '\n'.join(result)
    except:
      if settings.TEMPLATE_DEBUG:
        raise
      return ''


def get_modeltabs(parser, token):
  r'''
  {% tabs "customer" %}
  {% tabs myvariable %}
  '''
  from re import split
  bits = split(r'\s+', token.contents, 1)
  if len(bits) != 2:
    raise TemplateSyntaxError("'%s' tag requires 1 argument" % bits[0])
  return ModelTabs(bits[1])

get_modeltabs.is_safe = True
register.tag('tabs', get_modeltabs)


#
# A simple tag returning the frePPLe version
#

@register.simple_tag
def version():
  '''
  A simple tag returning the version of the frePPLe application.
  '''
  return VERSION

version.is_safe = True


@register.simple_tag
def version_short():
  '''
  A simple tag returning the version of the frePPLe application.
  '''
  versionnumber = VERSION.split('.', 2)
  return versionnumber[0]+"."+versionnumber[1]

version_short.is_safe = True


#
# A tag to mark whether the password of a user is correct.
#

@register.assignment_tag
def checkPassword(usr, pwd):
  try:
    return User.objects.get(username=usr).check_password(pwd)
  except:
    return False


#
# A filter to format a duration
#

def duration(value):
  try:
    if value is None:
      return ''
    value = Decimal(force_text(value))
    if value == 0:
      return '0 s'
    if value % 604800 == 0:
      return '%.2f w' % (value / Decimal('604800.0'))
    if value % 3600 != 0 and value < 86400:
      return '%.2f s' % value
    if value % 86400 != 0 and value < 604800:
      return '%.2f h' % (value / Decimal('3600'))
    return '%.2f d' % (value / Decimal('86400'))
  except Exception:
    return ''

duration.is_safe = True
register.filter('duration', duration)


#
# A filter to order a list
#

def sortList(inputList):
  return sorted(inputList)

register.filter('sortList', sortList)


#
# Filters to get metadata of a model
#

def verbose_name(obj):
  return obj._meta.verbose_name
register.filter(verbose_name)


def verbose_name_plural(obj):
  return obj._meta.verbose_name_plural
register.filter(verbose_name_plural)


def app_label(obj):
  return obj._meta.app_label
register.filter(app_label)


def object_name(obj):
  return obj._meta.object_name
register.filter(object_name)


def model_name(obj):
  return "%s.%s" % (obj._meta.app_label, obj._meta.model_name)
register.filter(model_name)


def short_model_name(obj):
  return obj._meta.model_name
register.filter(short_model_name)


def admin_unquote(obj):
  return unquote(obj)
register.filter(admin_unquote)


#
# Tag to display a menu
#

class MenuNode(Node):
  r'''
  A tag to return HTML code for the menu.
  '''
  def __init__(self, varname):
      self.varname = varname

  def render(self, context):
    from freppledb.menu import menu
    try:
      req = context['request']
    except:
      return ''  # No request found in the context
    o = []
    for i in menu.getMenu(req.LANGUAGE_CODE):
      group = [i[0], [] ]
      empty = True
      kept_back = None
      for j in i[1]:
        if j[2].has_permission(req.user):
          if j[2].separator:
            kept_back = (j[1], j[2], j[2].can_add(req.user) )
          else:
            if kept_back:
              group[1].append(kept_back)
              kept_back = None
            group[1].append( (j[1], j[2], j[2].can_add(req.user) ) )
            empty = False
      if not empty:
        # At least one item of the group is visible
        o.append(group)
    context[self.varname] = o
    return ''

  def __repr__(self):
    return "<getMenu Node>"


def getMenu(parser, token):
  tokens = token.contents.split()
  if len(tokens) < 3:
      raise TemplateSyntaxError("'%s' tag requires 3 arguments" % tokens[0])
  if tokens[1] != 'as':
      raise TemplateSyntaxError("First argument to '%s' tag must be 'as'" % tokens[0])
  return MenuNode(tokens[2])

register.tag('getMenu', getMenu)


#
# Tag to get a JSON string with all models and their child models
#
class ModelDependenciesNode(Node):
  r'''
  A tag to return JSON string with all models and their dependencies
  '''
  def render(self, context):
    res = {}
    for i in models.get_models(include_auto_created=True):
      deps = []
      i_name = "%s.%s" % (i._meta.app_label, i._meta.model_name)
      for j in i._meta.get_all_related_objects_with_model():
        if j[0].related_model == i:
          continue
        j_name = "%s.%s" % (j[0].related_model._meta.app_label, j[0].related_model._meta.model_name)
        # Some ugly (but unavoidable...) hard-codes related to the proxy models
        if j_name == 'input.operationplan':
          if i_name in ('input.supplier', 'item.itemsupplier', 'input.location', 'input.item'):
            deps.append('input.purchaseorder')
          if i_name in ('input.itemdistribution', 'input.location'):
            deps.append('input.distributionorder')
          if i_name in ('input.operation', 'input.location'):
            deps.append('input.manufacturingorder')
        elif not j_name in ('input.purchaseorder', 'input.manufacturingorder', 'input.distributionorder'):
          deps.append(j_name)
      res[i_name] = deps
    return json.dumps(res)

  def __repr__(self):
    return "<getModelDependencies Node>"


def getModelDependencies(parser, token):
  return ModelDependenciesNode()

register.tag('getModelDependencies', getModelDependencies)


#
# Tag to display a dashboard
#
class DashboardNode(Node):
  r'''
  A tag to return HTML code for the dashboard.
  '''
  def __init__(self, varname):
      self.varname = varname

  def render(self, context):
    from freppledb.common.dashboard import Dashboard
    try:
      req = context['request']
    except:
      return ''  # No request found in the context

    reg = Dashboard.buildList()
    context[self.varname] = [
      { 'rowname': rown['rowname'], 'cols': [
          {'width': i['width'], 'widgets': [ reg[j[0]](**j[1]) for j in i['widgets'] if j[0] in reg and reg[j[0]].has_permission(req.user)]} for i in rown['cols']
        ]
      } for rown in settings.DEFAULT_DASHBOARD
      ]
    return ''


  def __repr__(self):
    return "<getDashboard Node>"


def getDashboard(parser, token):
  tokens = token.contents.split()
  if len(tokens) < 3:
      raise TemplateSyntaxError("'%s' tag requires 3 arguments" % tokens[0])
  if tokens[1] != 'as':
      raise TemplateSyntaxError("First argument to '%s' tag must be 'as'" % tokens[0])
  return DashboardNode(tokens[2])

register.tag('getDashboard', getDashboard)
