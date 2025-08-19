#
# Copyright (C) 2007-2013 by frePPLe bv
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

from datetime import time
from decimal import Decimal
import json
from pathlib import Path
from urllib.parse import quote

from bootstrap3 import renderers
from bootstrap3.utils import add_css_class
from bootstrap3.text import text_value


from django.apps import apps
from django.conf import settings
from django.contrib.admin.utils import unquote as django_unquote, quote as django_quote
from django.contrib.auth.forms import ReadOnlyPasswordHashWidget
from django.contrib.admin.widgets import (
    AdminDateWidget,
    AdminTimeWidget,
    AdminSplitDateTime,
    RelatedFieldWidgetWrapper,
)
from django.db import models, connections
from django.forms import FileInput, CheckboxInput, RadioSelect, CheckboxSelectMultiple
from django.template import Library, Node, Variable, TemplateSyntaxError
from django.utils.translation import gettext_lazy as _
from django.utils.encoding import iri_to_uri, force_str
from django.utils.html import escape
from django.utils.safestring import mark_safe
from django.utils.text import capfirst

from freppledb.common.models import User, NotificationFactory
from freppledb import __version__

MAX_CRUMBS = 10

register = Library()
variable_title = Variable("title")
variable_request = Variable("request")
variable_popup = Variable("is_popup")


#
# A tag to create breadcrumbs on your site
#


class CrumbsNode(Node):
    """
    A generic breadcrumbs framework.

    Usage in your templates:
    {% crumbs %}

    The admin app already defines a block for crumbs, so the typical usage of the
    crumbs tag is as follows:
    {%block breadcrumbs%}<div class="breadcrumbs">{%crumbs%}</div>{%endblock%}
    """

    def render(self, context):
        try:
            req = context["request"]
        except Exception:
            return ""  # No request found in the context: no crumbs...
        if not hasattr(req, "session"):
            return  # No session found in the context: no crumbs...

        # Pick up the current crumbs from the session cookie
        try:
            cur = req.session["crumbs"]
            try:
                cur = cur[req.prefix]
            except Exception:
                cur = []
        except Exception:
            req.session["crumbs"] = {}
            cur = []

        # Compute the new crumb node
        count = 0
        try:
            title = variable_title.resolve(context)
        except Exception:
            title = req.get_full_path()
        if title != _("home"):
            # Don't handle the home screen in the crumbs
            try:
                # Check if the same title is already in the crumbs.
                title = str(title)
                exists = False
                for i in cur:
                    if i[0] == title:
                        # Current URL already exists in the list and we move it to the end
                        node = i
                        del cur[count]
                        cur.append((node[0], node[1], req.path))
                        exists = True
                        break
                    count += 1

                if not exists:
                    # Add the current URL to the stack
                    if not req.GET or (
                        "noautofilter" in req.GET
                        and "parentreference"
                        not in req.GET  # Special case for MO search
                    ):
                        args = ""
                    else:
                        args = "?%s" % iri_to_uri(req.GET.urlencode())
                    cur.append(
                        (
                            title,
                            '<li class="breadcrumb-item"><a href="%s%s%s">%s</a></li>'
                            % (
                                req.prefix,
                                quote(req.path, safe="/"),
                                args,
                                str(escape(capfirst(title))),
                            ),
                            req.path,
                        )
                    )
                    count += 1

                # Limit the number of crumbs.
                while count > MAX_CRUMBS:
                    count -= 1
                    del cur[0]
            except Exception:
                # Ignore errors to fail in a clean and graceful way
                pass

        # Update the current session
        req.session["crumbs"][req.prefix] = cur

        # Now create HTML code to return
        return "".join([i[1] for i in cur])

    def __repr__(self):
        return "<Crumbs Node>"


def do_crumbs(parser, token):
    return CrumbsNode()


register.tag("crumbs", do_crumbs)


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
        return ""

    def __repr__(self):
        return "<SetVariable Node>"


def set_var(parser, token):
    """
    Example:
    {% set category_list category.categories.all %}
    {% set dir_url "../" %}
    {% set type_list "table" %}
    """
    from re import split

    bits = split(r"\s+", token.contents, 2)
    if len(bits) < 2:
        raise TemplateSyntaxError("'%s' tag requires two arguments" % bits[0])
    return SetVariable(bits[1], bits[2])


register.tag("set", set_var)


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
        from django.urls import reverse

        try:
            # Look up the admin class to use
            model = Variable(self.model).resolve(context)
            if not model:
                return mark_safe("")
            if isinstance(model, Options):
                ct = ContentType.objects.get(
                    app_label=model.app_label, model=model.object_name.lower()
                )
            elif isinstance(model, models.Model):
                ct = ContentType.objects.get(
                    app_label=model._meta.app_label,
                    model=model._meta.object_name.lower(),
                )
            else:
                model = model.split(".")
                ct = ContentType.objects.get(app_label=model[0], model=model[1])
            admn = data_site._registry[ct.model_class()]
            if not hasattr(admn, "tabs"):
                return mark_safe("")

            # Render the admin class
            result = [
                '<div class="row"><div id="tabs" class="col-auto form-inline ms-auto mb-1"><ul class="nav nav-tabs">'
            ]
            obj = context["object_id"]
            active_tab = context.get("active_tab", "edit")
            for tab in admn.tabs:
                if "permissions" in tab:
                    # A single permission is required
                    if isinstance(tab["permissions"], str):
                        if not context["request"].user.has_perm(tab["permissions"]):
                            continue
                    else:
                        # A list or tuple of permissions is given
                        ok = True
                        for p in tab["permissions"]:
                            if not context["request"].user.has_perm(p):
                                ok = False
                                break
                        if not ok:
                            continue
                # Append to the results
                result.append(
                    '<li class="nav-item"><a class="nav-link text-reset%s" href="%s%s?noautofilter" target="_self">%s</a></li>'
                    % (
                        " active" if active_tab == tab["name"] else "",
                        context["request"].prefix,
                        reverse(tab["view"], args=(obj,)),
                        force_str(tab["label"]).capitalize(),
                    )
                )
            result.append("</ul></div></div>")
            return mark_safe("\n".join(result))
        except Exception:
            raise


def get_modeltabs(parser, token):
    """
    {% tabs "customer" %}
    {% tabs myvariable %}
    """
    from re import split

    bits = split(r"\s+", token.contents, 1)
    if len(bits) != 2:
        raise TemplateSyntaxError("'%s' tag requires 1 argument" % bits[0])
    return ModelTabs(bits[1])


register.tag("tabs", get_modeltabs)

#
# A tag to get information on the follower status of an object
#


class Following(Node):
    def __init__(self, model, pk, var):
        self.model = model
        self.pk = pk
        self.var = var

    def render(self, context):
        from django.db.models.options import Options
        from django.contrib.contenttypes.models import ContentType

        try:
            # Look up the admin class to use
            model = Variable(self.model).resolve(context)
            pk = Variable(self.pk).resolve(context)
            request = Variable("request").resolve(context)
            if not model or not pk:
                context[self.var] = None
                return mark_safe("")
            if isinstance(model, Options):
                ct = ContentType.objects.get(
                    app_label=model.app_label, model=model.object_name.lower()
                )
            elif isinstance(model, models.Model):
                ct = ContentType.objects.get_for_model(model)
            else:
                model = model.split(".")
                ct = ContentType.objects.get(app_label=model[0], model=model[1])
            context[self.var] = NotificationFactory.getFollower(
                object_pk=pk,
                content_type=ct,
                user=request.user,
                database=request.database,
            )
        except Exception:
            context[self.var] = None
        return mark_safe("")

    def __repr__(self):
        return "<Following Node>"


def get_following(parser, token):
    """
    {% following "customer" "custname" as f %}
    """
    try:
        a, b, c, d, e = token.split_contents()
    except ValueError:
        raise TemplateSyntaxError(
            "%s tag requires a single argument" % token.contents.split()[0]
        )
    if d != "as":
        raise TemplateSyntaxError("Third argument to '%s' tag must be 'as'" % a)
    return Following(b, c, e)


register.tag("following", get_following)

#
# A simple tag returning the frePPLe version
#


@register.simple_tag
def version():
    """
    A simple tag returning the version of the frePPLe application.
    """
    return __version__


@register.simple_tag
def version_short():
    """
    A simple tag returning the version of the frePPLe application.
    """
    try:
        versionnumber = __version__.split(".", 2)
        return "%s.%s" % (versionnumber[0], versionnumber[1])
    except Exception:
        return "current"


#
# A tag to mark whether the password of a user is correct.
#


@register.simple_tag
def checkPassword(usr, pwd):
    try:
        return User.objects.get(username=usr).check_password(pwd)
    except Exception:
        return False


#
# A filter to format a duration
#


def duration(value):
    try:
        if value is None:
            return ""
        value = Decimal(force_str(value))
        if value == 0:
            return "0 s"
        if value % 604800 == 0:
            return "%.2f w" % (value / Decimal("604800.0"))
        if value % 3600 != 0 and value < 86400:
            return "%.2f s" % value
        if value % 86400 != 0 and value < 604800:
            return "%.2f h" % (value / Decimal("3600"))
        return "%.2f d" % (value / Decimal("86400"))
    except Exception:
        return ""


register.filter("duration", duration, is_safe=True)


#
# A filter to order a list
#


def sortList(inputList):
    return sorted(inputList)


register.filter("sortList", sortList)


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


def label_lower(obj):
    return obj._meta.label_lower


register.filter(label_lower)


def admin_unquote(obj):
    return django_unquote(obj)


register.filter(admin_unquote)


def admin_quote(obj):
    return django_quote(obj)


register.filter(admin_quote)


#
# Tag to display a menu
#


class MenuNode(Node):
    r"""
    A tag to return HTML code for the menu.
    """

    def __init__(self, varname):
        self.varname = varname

    def render(self, context):
        from freppledb.menu import menu

        try:
            req = context["request"]
        except Exception:
            return ""  # No request found in the context
        o = []

        # Find all tables with data
        with connections[req.database].cursor() as cursor:
            cursor.execute(
                """
                select tablename from (
                  select tablename,
                    query_to_xml(
                      format('select 1 as cnt from %I.%I limit 1', schemaname, tablename),
                      false, true, ''
                      ) as xml_count
                  from pg_catalog.pg_tables
                  where schemaname = 'public'
                  ) s
                where xml_count is document;
                """
            )
            present = set([i[0] for i in cursor])

        def generator(i):
            for j in i[1]:
                if callable(j[2].callback):
                    # Dynamic definition of menu items with a callback function
                    for x in j[2].callback(req):
                        yield x
                else:
                    # Static definition of the menu
                    yield j

        for i in menu.getMenu(req.LANGUAGE_CODE):
            group = [i[0], [], False]
            empty = True
            kept_back = None
            for j in generator(i):
                if j[2].has_permission(req.user):
                    ok = True
                    if j[2].dependencies:
                        for dep in j[2].dependencies:
                            if not isinstance(dep, type) and callable(dep):
                                ok = dep(req)
                                if not ok:
                                    break
                            elif dep._meta.db_table not in present:
                                ok = False
                                break
                    emptytable = not j[2].model or j[2].model._meta.db_table in present
                    if j[2].separator:
                        if group[2]:
                            kept_back = (
                                j[1],
                                j[2],
                                j[2].can_add(req.user),
                                emptytable,
                                ok,
                            )
                    else:
                        if kept_back:
                            group[1].append(kept_back)
                            kept_back = None
                        group[1].append(
                            (j[1], j[2], j[2].can_add(req.user), emptytable, ok)
                        )
                        if not group[2] and ok:
                            group[2] = True
                        empty = False
            if not empty:
                # At least one item of the group is visible
                o.append(group)
        context[self.varname] = o
        return ""

    def __repr__(self):
        return "<getMenu Node>"


def getMenu(parser, token):
    tokens = token.contents.split()
    if len(tokens) < 3:
        raise TemplateSyntaxError("'%s' tag requires 3 arguments" % tokens[0])
    if tokens[1] != "as":
        raise TemplateSyntaxError("First argument to '%s' tag must be 'as'" % tokens[0])
    return MenuNode(tokens[2])


register.tag("getMenu", getMenu)


#
# Tag to get a JSON string with all models and their child models
#
class ModelDependenciesNode(Node):
    r"""
    A tag to return JSON string with all models and their dependencies
    """

    def render(self, context):
        res = {}
        for a in apps.app_configs:
            for i in apps.get_app_config(a).get_models():
                deps = []
                i_name = "%s.%s" % (i._meta.app_label, i._meta.model_name)
                for f in i._meta.get_fields():
                    if (
                        (f.one_to_many or f.one_to_one)
                        and f.auto_created
                        and not f.concrete
                    ):
                        if f.related_model == i:
                            continue
                        j_name = "%s.%s" % (
                            f.related_model._meta.app_label,
                            f.related_model._meta.model_name,
                        )
                        # Some ugly (but unavoidable...) hard-codes related to the proxy models
                        if j_name == "input.operationplan":
                            if i_name in (
                                "input.supplier",
                                "item.itemsupplier",
                                "input.location",
                                "input.item",
                            ):
                                deps.append("input.purchaseorder")
                            if i_name in ("input.itemdistribution", "input.location"):
                                deps.append("input.distributionorder")
                            if i_name in ("input.operation", "input.location"):
                                deps.append("input.manufacturingorder")
                            if i_name in ("input.demand"):
                                deps.append("input.deliveryorder")
                        elif not j_name in (
                            "input.purchaseorder",
                            "input.manufacturingorder",
                            "input.distributionorder",
                        ):
                            deps.append(j_name)
                res[i_name] = deps
        return json.dumps(res)

    def __repr__(self):
        return "<getModelDependencies Node>"


def getModelDependencies(parser, token):
    return ModelDependenciesNode()


register.tag("getModelDependencies", getModelDependencies)


#
# Tag to display a dashboard
#
class DashboardNode(Node):
    r"""
    A tag to return HTML code for the dashboard.
    """

    def __init__(self, varname, hiddenvarname):
        self.varname = varname
        self.hiddenvarname = hiddenvarname

    def render(self, context):
        from freppledb.common.dashboard import Dashboard

        try:
            req = context["request"]
        except Exception:
            return ""  # No request found in the context
        reg = Dashboard.buildList()
        mydashboard = req.user.getPreference(
            "freppledb.common.cockpit", database=req.database
        )
        if not mydashboard:
            mydashboard = settings.DEFAULT_DASHBOARD
        context[self.hiddenvarname] = dict(
            sorted(
                {i: j for i, j in reg.items()}.items(),
                key=lambda k: capfirst(k[1].title),
            )
        )
        context[self.varname] = []
        for i in mydashboard:
            cols = []
            width = 0
            for j in i["cols"]:
                widgets = []
                for k in j["widgets"]:
                    if k[0] in reg and reg[k[0]].has_permission(req.user, req.database):
                        w = reg[k[0]](**k[1])
                        width += {"xl": 12, "lg": 6, "md": 4, "sm": 3}[w.size]
                        if width > 12:
                            width -= 12
                            w.linebreak = True
                        widgets.append(w)
                        context[self.hiddenvarname].pop(k[0], None)
                cols.append({"width": j["width"], "widgets": widgets})
            context[self.varname].append({"rowname": i["rowname"], "cols": cols})
        return ""

    def __repr__(self):
        return "<getDashboard Node>"


def getDashboard(parser, token):
    tokens = token.contents.split()
    if len(tokens) < 4:
        raise TemplateSyntaxError("'%s' tag requires 4 arguments" % tokens[0])
    if tokens[1] != "as":
        raise TemplateSyntaxError("First argument to '%s' tag must be 'as'" % tokens[0])
    return DashboardNode(tokens[2], tokens[3])


register.tag("getDashboard", getDashboard)


@register.simple_tag(takes_context=True)
def renderDashboardWidget(context, obj):
    return mark_safe(obj.render(context.request))


@register.simple_tag
def google_analytics():
    """
    A tag to add google analytics tracking code to the site.
    """
    if settings.GOOGLE_ANALYTICS and not settings.DEBUG:
        return mark_safe(
            "<script async src='https://www.googletagmanager.com/gtag/js?id=%s'></script>\n"
            "<script>\n"
            "window.dataLayer = window.dataLayer || [];\n"
            "function gtag(){dataLayer.push(arguments);}\n"
            "gtag('js', new Date())\n;"
            "gtag('config', '%s')\n;"
            "</script>\n" % (settings.GOOGLE_ANALYTICS, settings.GOOGLE_ANALYTICS)
        )
    else:
        return mark_safe("")


google_analytics.is_safe = True


#
# A tag to return a setting.
#


@register.simple_tag
def setting(key, default=None):
    return getattr(settings, key, default)


@register.simple_tag
def call_method(obj, method_name, *args):
    method = getattr(obj, method_name)
    return method(*args) if method else None


@register.filter(name="json")
def jsonfilter(a):
    json_str = json.dumps(a)
    # Escape all the XML/HTML special characters.
    escapes = ["<", ">", "&", "'"]
    for c in escapes:
        json_str = json_str.replace(c, r"\u%04x" % ord(c))

    # now it's safe to use mark_safe
    return mark_safe(json_str)


jsonfilter.is_safe = True


@register.filter(name="timeformat")
def timeformatfilter(a):
    if a:
        t = time(
            hour=int(a / 3600),
            minute=int(int(a % 3600) / 60),
            second=a % 60,
            microsecond=0,
        )
        return mark_safe(t.isoformat(timespec="seconds"))
    else:
        return mark_safe("00:00:00")


timeformatfilter.is_safe = True


@register.filter(name="extension")
def extensionfilter(val):
    return Path(val).suffix[1:].lower()


#
# A filter to order a dictionary by key
#
@register.filter(name="sort_dictionary_by_key")
def sort_dictionary_by_key(input_dictionary):
    return dict(sorted(input_dictionary.items()))


sort_dictionary_by_key.is_safe = True


@register.simple_tag(name="render_field_bootstrap")
def render_field_bootstrap(field, **kwargs):
    class BootstrapFieldRenderer(renderers.FieldRenderer):
        """
        A django-bootstrap3 field renderer that renders just the field
        """

        def render(self):
            # Hidden input requires no special treatment
            if self.field.is_hidden:
                return text_value(self.field)
            # Render the widget
            self.add_widget_attrs()
            html = self.field.as_widget(attrs=self.widget.attrs)
            return html

        def add_class_attrs(self, widget=None):
            if not widget:
                widget = self.widget

            # for multiwidgets we recursively update classes for each sub-widget
            if isinstance(widget, AdminSplitDateTime):
                for w in widget.widgets:
                    self.add_class_attrs(w)
                return

            classes = widget.attrs.get("class", "")
            if isinstance(widget, ReadOnlyPasswordHashWidget):
                classes = add_css_class(classes, "form-control-static", prepend=True)
            elif isinstance(
                widget, (AdminDateWidget, AdminTimeWidget, RelatedFieldWidgetWrapper)
            ):
                # for some admin widgets we don't want the input to take full horizontal space
                classes = add_css_class(
                    classes, "form-control form-control-inline", prepend=True
                )
            elif not isinstance(
                widget, (CheckboxInput, RadioSelect, CheckboxSelectMultiple, FileInput)
            ):
                classes = add_css_class(classes, "form-control", prepend=True)
                # For these widget types, add the size class here
                classes = add_css_class(classes, self.get_size_class())
            widget.attrs["class"] = classes

    return BootstrapFieldRenderer(field, **kwargs).render()
