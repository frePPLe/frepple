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

from importlib import import_module
import json
from mimetypes import guess_type
import multiprocessing
import os.path
from pathlib import Path
import re

from django.db.models import Case, When, Value, IntegerField
from django.db.models.functions import Cast, Substr, Length
from django.conf import settings
from django.core import management
from django.core.paginator import Paginator
from django.http import (
    JsonResponse,
    HttpResponseNotAllowed,
    HttpResponseForbidden,
    HttpResponseNotFound,
    Http404,
    HttpResponseRedirect,
    HttpResponse,
    HttpResponseServerError,
)
from django.shortcuts import render
from django.contrib import messages
from django.contrib.auth import update_session_auth_hash
from django.contrib.auth.password_validation import (
    validate_password,
    get_password_validators,
    password_validators_help_text_html,
)
from django.contrib.auth.decorators import login_required
from django.contrib.admin.views.decorators import staff_member_required
from django.contrib.contenttypes.models import ContentType
from django.db import DEFAULT_DB_ALIAS
from django.db.models.expressions import RawSQL
from django.urls import reverse, resolve
from django import forms
from django.template import Template
from django.utils.decorators import method_decorator
from django.utils.encoding import force_str
from django.utils.translation import gettext_lazy as _
from django.utils.text import capfirst
from django.contrib.auth.models import Group
from django.utils import translation

from django.shortcuts import render
from django.views import static
from django.views.decorators.csrf import csrf_protect
from django.views.decorators.debug import sensitive_variables
from django.views.generic.base import View

from .models import (
    Attribute,
    User,
    Parameter,
    Scenario,
    Comment,
    Bucket,
    BucketDetail,
    Notification,
    Follower,
)
from .report import (
    GridReport,
    GridFieldLastModified,
    GridFieldText,
    GridFieldBool,
    sizeof_fmt,
)
from .report import (
    GridFieldDateTime,
    GridFieldInteger,
    getCurrency,
    GridFieldChoice,
    GridFieldJSON,
)
from .utils import getStorageUsage, forceWsgiReload

from freppledb.admin import data_site
from freppledb.common.models import Scenario
from freppledb.common.utils import get_databases
from freppledb import edition, __version__, runCommand

import logging
from freppledb.common.models import NotificationFactory

logger = logging.getLogger(__name__)


@staff_member_required
def AboutView(request):
    from freppledb.input.utils import countItemLocations

    maxstorage = getattr(settings, "MAXSTORAGE", 0) or 0
    usedstorage = getStorageUsage()
    apps = []
    for i in settings.INSTALLED_APPS:
        if i in settings.INSTALLABLE_APPS:
            apps.append(i)
        else:
            try:
                m = getattr(import_module(i), "frepple_app", None)
                if m and m.get("display_in_list", False):
                    apps.append(i)
            except Exception as e:
                pass
    return JsonResponse(
        {
            "version": __version__,
            "edition": edition,
            "storage_used": sizeof_fmt(usedstorage),
            "storage_allocation": (
                sizeof_fmt(maxstorage * 1024 * 1024) if maxstorage else None
            ),
            "storage_exceeded": maxstorage and usedstorage > maxstorage,
            "itemlocations": {
                sc.name: countItemLocations(sc.name)
                for sc in Scenario.objects.using(DEFAULT_DB_ALIAS)
                .filter(status="In use")
                .annotate(
                    sort_key=Case(
                        When(name="default", then=Value(0)),
                        When(
                            name__startswith="scenario",
                            then=Cast(
                                Substr("name", 9, Length("name")), IntegerField()
                            ),
                        ),
                        default=Value(9999),
                        output_field=IntegerField(),
                    )
                )
                .order_by("sort_key", "name")
            },
            "apps": apps,
            "website": settings.DOCUMENTATION_URL,
        }
    )


class AppsView(View):
    template = "common/apps.html"
    reportkey = "common.apps"

    @classmethod
    @method_decorator(staff_member_required)
    def get(cls, request, *args, **kwargs):
        if not request.user.is_superuser:
            return HttpResponseForbidden("<h1>%s</h1>" % _("Permission denied"))
        request.prefs = request.user.getPreference(
            cls.reportkey, database=request.database
        )
        apps = {}
        for a in getattr(settings, "INSTALLABLE_APPS", []):
            try:
                if isinstance(a, Path):
                    for d in a.iterdir():
                        if d.is_dir():
                            try:
                                appname = d.parts[-1]
                                m = getattr(import_module(appname), "frepple_app", None)
                                if m:
                                    apps[appname] = {
                                        "name": appname,
                                        "installed": appname in settings.INSTALLED_APPS,
                                        "summary": m.get("summary", appname),
                                        "version": m.get("version", None),
                                        "description": m.get("description", None),
                                        "documentation_url": m.get(
                                            "documentation_url", None
                                        ),
                                    }
                            except Exception:
                                pass
                else:
                    m = getattr(import_module(a), "frepple_app", None)
                    if m:
                        apps[a] = {
                            "name": a,
                            "installed": a in settings.INSTALLED_APPS,
                            "summary": m.get("summary", a),
                            "version": m.get("version", None),
                            "description": m.get("description", None),
                            "documentation_url": m.get("documentation_url", None),
                        }
            except Exception:
                pass
        return render(
            request,
            cls.template,
            {
                "title": _("apps"),
                "edition": "%s %s" % (edition, __version__),
                "reportkey": cls.reportkey,
                "apps": apps.values(),
                "superuser": request.user.is_superuser,
            },
        )

    @classmethod
    @method_decorator(staff_member_required)
    def post(reportclass, request, *args, **kwargs):
        if request.headers.get("x-requested-with") != "XMLHttpRequest":
            return HttpResponseNotFound("Only ajax post requests allowed")
        if request.database != DEFAULT_DB_ALIAS:
            return HttpResponseForbidden(
                "Apps are global and can only be updated in the main database"
            )
        if not request.user.is_superuser:
            return HttpResponseForbidden("Only superusers can update apps")
        try:
            data = json.loads(
                request.body.decode(request.encoding or settings.DEFAULT_CHARSET)
            )
            reportclass.updateApp(**data)
            return HttpResponse(content="OK")
        except Exception as e:
            logger.error("Error updating app: %s" % e)
            return HttpResponseServerError("Error updating app")

    @classmethod
    def updateApp(reportclass, app=None, action=None, **kwargs):
        if not app or action not in ("install", "uninstall"):
            raise Exception("Missing action or app")

        metadata = None
        try:
            metadata = getattr(import_module(app), "frepple_app", None)
        except Exception:
            pass
        if not metadata:
            raise Exception("Can't install or uninstall this app")

        appname = app.rsplit(".", 1)[-1]
        djangosettingsname = os.path.join(
            settings.FREPPLE_CONFIGDIR, "djangosettings.py"
        )

        # Read djangosettings
        djangosettings = ""
        with open(djangosettingsname, "rt") as f:
            djangosettings = f.read()

        if action == "install":
            # Validate
            if app in settings.INSTALLED_APPS:
                raise Exception("This app is already installed")

            # Update djangosettings
            with open("%s" % djangosettingsname, "wt+") as f:
                status = 0
                new_file = []
                found = False
                for l in djangosettings.splitlines():
                    if status == 0 and "INSTALLED_APPS" in l:
                        status = 1
                    elif status == 1 and app in l:
                        i = re.search(r"\S", l).start()
                        l = '%s"%s",' % (l[:i], app)
                        status = 2
                        found = True
                    elif status == 1 and (
                        "END UPDATED BLOCK" in l or "INSTALLABLE_APPS" in l
                    ):
                        status = 3
                    new_file.append(l)
                if not found:
                    idx = 0
                    for l in new_file:
                        if "freppledb.boot" in l:
                            i = re.search(r"\S", l).start()
                            l = '%s"%s",' % (l[:i], app)
                            new_file.insert(idx + 1, l)
                            break
                        idx += 1
                for l in new_file:
                    print(l, file=f)

            # Migrate (after updating djangosettings)
            child = multiprocessing.get_context("spawn").Process(
                target=runCommand,
                args=("migrate", appname),
            )
            child.start()

        elif action == "uninstall":
            # Validate
            if app not in settings.INSTALLED_APPS:
                raise Exception("This app isn't installed")

            # Unmigrate (before updating djangosettings)
            management.call_command("migrate", appname, "zero")

            # Update djangosettings
            with open("%s" % djangosettingsname, "wt+") as f:
                status = 0
                for l in djangosettings.splitlines():
                    if status == 0 and "INSTALLED_APPS" in l:
                        status = 1
                    elif status == 1 and app in l:
                        i = re.search(r"\S", l).start()
                        l = '%s# "%s",' % (l[:i], app)
                        status = 2
                    print(l, file=f)

        # Trigger reloading of the WSGI app
        forceWsgiReload()


@login_required
def ScenarioView(request):
    if request.method != "GET":
        raise Http404("Only get requests allowed")
    return JsonResponse(
        [
            sc
            for sc in Scenario.objects.all()
            .using(DEFAULT_DB_ALIAS)
            .values("name", "status", "description")
        ],
        safe=False,
    )


@staff_member_required
def cockpit(request):
    return render(
        request,
        "index.html",
        context={
            "title": _("home"),
            "bucketnames": Bucket.objects.order_by("-level").values_list(
                "name", flat=True
            ),
            "currency": getCurrency(),
        },
    )


def handler404(request, exception):
    """
    Custom error handler which redirects to the main page rather than displaying the 404 page.
    """
    messages.add_message(
        request,
        messages.ERROR,
        force_str(
            _("Page not found") + ": " + request.prefix + request.get_full_path()
        ),
    )
    return HttpResponseRedirect(request.prefix + "/")


def handler500(request):
    """
    Custom handler for "HTTP 500 - server error"
    """
    try:
        response = render(request, "500.html", content_type="text/html")
        response.status_code = 500
        return response
    except Exception as e:
        logger.error("Error generating 500 page: %s" % e)
        return HttpResponseServerError(
            "<h1>Server Error (500)</h1>", content_type="text/html"
        )


class PreferencesForm(forms.Form):
    language = forms.ChoiceField(
        label=_("language"), initial="auto", choices=User.languageList
    )
    pagesize = forms.IntegerField(label=_("Page size"), required=False, initial=100)
    theme = forms.ChoiceField(
        label=_("Theme"),
        required=False,
        choices=[(i, capfirst(i)) for i in settings.THEMES],
    )
    default_scenario = forms.ChoiceField(
        label=_("default scenario"),
        required=False,
        choices=[(i, i) for i in get_databases().keys()] + [(None, None)],
    )
    cur_password = forms.CharField(
        label=_("Change password"),
        required=False,
        help_text=_("Old password"),
        widget=forms.PasswordInput(),
    )
    new_password1 = forms.CharField(
        label="",
        required=False,
        help_text=password_validators_help_text_html(
            get_password_validators(settings.AUTH_PASSWORD_VALIDATORS)
        ),
        widget=forms.PasswordInput(),
    )
    new_password2 = forms.CharField(
        label="",
        required=False,
        help_text=_("New password confirmation"),
        widget=forms.PasswordInput(),
    )
    avatar = forms.ImageField(label="", required=False)
    personalization = forms.CharField(required=False)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if len(settings.THEMES) == 1:
            # If there is only one theme make this choice unavailable
            self.fields.pop("theme")

    def clean(self):
        newdata = super().clean()
        if newdata.get("pagesize", 0) > 10000:
            raise forms.ValidationError("Maximum page size is 10000.")
        if newdata.get("pagesize", 25) < 25:
            raise forms.ValidationError("Minimum page size is 25.")
        if newdata.get("avatar", None) and newdata["avatar"].size > 102400:
            raise forms.ValidationError("Avatars are limited to 100kB")
        if newdata["cur_password"]:
            if not self.user.check_password(newdata["cur_password"]):
                raise forms.ValidationError(
                    _(
                        "Your old password was entered incorrectly. Please enter it again."
                    )
                )
            # Validate_password raises a ValidationError
            validate_password(
                newdata["new_password1"],
                self.user,
                get_password_validators(settings.AUTH_PASSWORD_VALIDATORS),
            )
            if newdata["new_password1"] != newdata["new_password2"]:
                raise forms.ValidationError("The two password fields didn't match.")
        if newdata["personalization"]:
            tmp = newdata["personalization"].split("-", 1)
            if tmp[0] == "scenario":
                if (
                    not Scenario.objects.using(DEFAULT_DB_ALIAS)
                    .filter(name=tmp[1], status="In use")
                    .exists()
                ):
                    raise forms.ValidationError("Invalid personalization argument")
            elif tmp[0] == "user":
                if (
                    not User.objects.using(DEFAULT_DB_ALIAS)
                    .filter(username=tmp[1])
                    .exists()
                ):
                    raise forms.ValidationError("Invalid personalization argument")
            elif tmp[0] not in ("nochange", "resetall"):
                raise forms.ValidationError("Invalid personalization argument")


@sensitive_variables("newdata")
@login_required
@csrf_protect
def preferences(request):
    if request.method == "POST":
        form = PreferencesForm(request.POST, request.FILES)
        form.user = request.user
        if form.is_valid():
            try:
                newdata = form.cleaned_data
                request.user.language = newdata["language"]
                if "theme" in newdata:
                    request.user.theme = newdata["theme"]
                request.user.pagesize = newdata["pagesize"]
                if newdata["avatar"]:
                    request.user.avatar = newdata["avatar"]
                if (
                    newdata["default_scenario"]
                    and newdata["default_scenario"] != "None"
                ):
                    request.user.default_scenario = newdata["default_scenario"]
                if newdata["cur_password"]:
                    request.user.set_password(newdata["new_password1"])
                    # Updating the password logs out all other sessions for the user
                    # except the current one if
                    # django.contrib.auth.middleware.SessionAuthenticationMiddleware
                    # is enabled.
                    update_session_auth_hash(request, form.user)
                request.user.save()
                # Switch to the new theme and language immediately
                if "theme" in newdata:
                    request.theme = (
                        request.user.scenario_themes.get(
                            request.database, newdata["theme"]
                        )
                        if request.user.scenario_themes
                        else newdata["theme"]
                    )
                if newdata["language"] == "auto":
                    newdata["language"] = translation.get_language_from_request(request)
                if translation.get_language() != newdata["language"]:
                    translation.activate(newdata["language"])
                    request.LANGUAGE_CODE = translation.get_language()
                messages.add_message(
                    request,
                    messages.INFO,
                    force_str(_("Successfully updated preferences")),
                )
                # Update the personalization
                if newdata["personalization"]:
                    tmp = newdata["personalization"].split("-", 1)
                    request.user.intializePersonalization(tmp[0], tmp[1])
            except Exception as e:
                logger.error("Failure updating preferences: %s" % e)
                messages.add_message(
                    request,
                    messages.ERROR,
                    force_str(_("Failure updating preferences")),
                )
    else:
        form = PreferencesForm(
            {
                "language": request.user.language,
                "theme": request.user.theme,
                "pagesize": request.user.pagesize,
                "avatar": request.user.avatar,
                "default_scenario": request.user.default_scenario,
            }
        )
    LANGUAGE = User.languageList[0][1]
    for l in User.languageList:
        if l[0] == request.user.language:
            LANGUAGE = l[1]
    return render(
        request,
        "common/preferences.html",
        context={
            "title": _("My preferences"),
            "form": form,
            "theme_is_overriden": (
                request.database in request.user.scenario_themes
                if request.user.scenario_themes
                else False
            ),
            "THEMES": settings.THEMES,
            "LANGUAGE": LANGUAGE,
            "SCENARIOS": Scenario.objects.using(DEFAULT_DB_ALIAS)
            .filter(status="In use")
            .order_by("name"),
            "USERS": User.objects.using(DEFAULT_DB_ALIAS)
            .order_by("username")
            .exclude(username=request.user.username)
            .only("username"),
        },
    )


class HorizonForm(forms.Form):
    horizonbuckets = forms.ModelChoiceField(
        queryset=Bucket.objects.all().values_list("name", flat=True)
    )
    horizonstart = forms.DateField(required=False, input_formats=["%Y-%m-%d"])
    horizonend = forms.DateField(required=False, input_formats=["%Y-%m-%d"])
    horizontype = forms.ChoiceField(choices=(("1", "1"), ("0", "0")))
    horizonbefore = forms.IntegerField(required=False, min_value=0)
    horizonlength = forms.IntegerField(required=False, min_value=1)
    horizonunit = forms.ChoiceField(
        choices=(("day", "day"), ("week", "week"), ("month", "month"))
    )


@login_required
@csrf_protect
def horizon(request):
    if request.method != "POST":
        return HttpResponseServerError("Only post requests allowed")
    form = HorizonForm(request.POST)
    if not form.is_valid():
        return HttpResponseServerError("Invalid form data")
    try:
        request.user.horizonbuckets = form.cleaned_data["horizonbuckets"]
        request.user.horizonstart = form.cleaned_data["horizonstart"]
        request.user.horizonend = form.cleaned_data["horizonend"]
        request.user.horizontype = form.cleaned_data["horizontype"] == "1"
        request.user.horizonbefore = form.cleaned_data["horizonbefore"]
        request.user.horizonlength = form.cleaned_data["horizonlength"]
        request.user.horizonunit = form.cleaned_data["horizonunit"]
        request.user.save(
            update_fields=[
                "horizonbuckets",
                "horizonstart",
                "horizonend",
                "horizontype",
                "horizonbefore",
                "horizonlength",
                "horizonunit",
            ]
        )
        return HttpResponse(content="OK")
    except Exception as e:
        logger.error("Error saving horizon settings: %s" % e)
        raise Http404("Error saving horizon settings")


@login_required
@csrf_protect
def saveSettings(request):
    if (
        request.method != "POST"
        or request.headers.get("x-requested-with") != "XMLHttpRequest"
    ):
        raise Http404("Only ajax post requests allowed")
    try:
        data = json.loads(
            request.body.decode(request.encoding or settings.DEFAULT_CHARSET)
        )
        for key, value in data.items():
            request.user.setPreference(key, value, database=request.database)
        return HttpResponse(content="OK")
    except Exception as e:
        logger.error("Error saving report settings: %s" % e)
        return HttpResponseServerError("Error saving report settings")


def login(request, extra_context=None):
    response = data_site.login(request, extra_context)
    if "remember_me" in request.POST and settings.SESSION_COOKIE_AGE:
        request.session.set_expiry(settings.SESSION_COOKIE_AGE)
    if (
        request.path == "/data/login/"
        and isinstance(response, HttpResponseRedirect)
        and response.url in ("/", "/data/")
    ):
        sc = getattr(request.user, "default_scenario", None)
        if sc not in get_databases() or (
            request.user.databases and sc not in request.user.databases
        ):
            sc = None
        if not sc and request.user.databases:
            sc = sorted(request.user.databases)[0]
        if sc:
            # Automatically switch to a non-default scenario
            return HttpResponseRedirect(f"/{sc}/" if sc != DEFAULT_DB_ALIAS else "/")
    return response


class UserList(GridReport):
    title = _("users")
    template = "common/userlist.html"
    basequeryset = User.objects.all().annotate(
        group_dict=RawSQL(
            "select json_agg(json_build_array(auth_group.id::text, auth_group.name)) "
            "from common_user_groups "
            "inner join auth_group on common_user_groups.group_id = auth_group.id "
            "where common_user_groups.user_id = common_user.id",
            (),
        )
    )
    model = User
    frozenColumns = 2
    permissions = (("change_user", "Can change user"),)
    help_url = "user-interface/getting-around/user-permissions-and-roles.html"
    canDuplicate = False

    @classmethod
    def initialize(reportclass, request):
        if request.database != DEFAULT_DB_ALIAS:
            User.synchronize(database=request.database)

    rows = (
        GridFieldInteger(
            "id",
            title=_("id"),
            key=True,
            formatter="admin",
            extra='"role":"common/user"',
        ),
        GridFieldText(
            "avatar",
            width=50,
            editable=False,
            field_name="avatar",
            title=_("avatar"),
            formatter="image",
        ),
        GridFieldText("username", title=_("username")),
        GridFieldText("email", title=_("email address"), formatter="email", width=200),
        GridFieldText("first_name", title=_("first name")),
        GridFieldText("last_name", title=_("last name")),
        GridFieldBool("is_active", title=_("active")),
        GridFieldBool("is_superuser", title=_("superuser status"), width=120),
        GridFieldChoice("language", title=_("language"), choices=User.languageList),
        GridFieldJSON(
            "group_dict",
            title=_("groups"),
            formatter="listdetail",
            extra='"formatter": grouplistformatter',
            width=120,
            editable=False,
            sortable=False,
        ),
        GridFieldDateTime("date_joined", title=_("date joined"), editable=False),
        GridFieldDateTime("last_login", title=_("last login"), editable=False),
    )


class GroupList(GridReport):
    title = _("groups")
    basequeryset = Group.objects.all()
    model = Group
    frozenColumns = 1
    permissions = (("change_group", "Can change group"),)
    help_url = "user-interface/getting-around/user-permissions-and-roles.html"
    canDuplicate = False

    rows = (
        GridFieldInteger(
            "id",
            title=_("identifier"),
            key=True,
            formatter="detail",
            extra='"role":"auth/group"',
        ),
        GridFieldText("name", title=_("name"), width=200),
    )


class ParameterList(GridReport):
    title = _("parameters")
    basequeryset = Parameter.objects.all()
    model = Parameter
    adminsite = "admin"
    frozenColumns = 1
    help_url = "model-reference/parameters.html"

    rows = (
        GridFieldText(
            "name",
            title=_("name"),
            key=True,
            formatter="detail",
            extra='"role":"common/parameter"',
        ),
        GridFieldText("value", title=_("value")),
        GridFieldText("description", title=_("description"), formatter="longstring"),
        GridFieldText("source", title=_("source"), initially_hidden=True),
        GridFieldLastModified("lastmodified"),
    )


class CommentList(GridReport):
    template = "common/commentlist.html"
    title = _("messages")
    basequeryset = Comment.objects.all()
    model = Comment
    editable = False
    multiselect = False
    frozenColumns = 0
    default_sort = (0, "desc")
    help_url = "user-interface/getting-around/messages.html"

    rows = (
        GridFieldInteger("id", title=_("identifier"), key=True),
        GridFieldLastModified("lastmodified"),
        GridFieldText(
            "user",
            title=_("user"),
            field_name="user__username",
            editable=False,
            align="center",
            width=80,
        ),
        GridFieldChoice("type", title=_("type"), choices=Comment.type_list),
        GridFieldText(
            "model",
            title=_("model"),
            field_name="content_type__model",
            editable=False,
            align="center",
        ),
        GridFieldText(
            "object_pk",
            title=_("object id"),
            field_name="object_pk",
            editable=False,
            align="center",
            extra='"formatter": objectfmt',
        ),
        GridFieldText(
            "attachment",
            title=_("attachment"),
            width=50,
            editable=False,
            align="center",
            extra='"formatter": attachment',
        ),
        GridFieldText("comment", title=_("comment"), width=400, editable=False),
        GridFieldText(
            "app", title="app", hidden=True, field_name="content_type__app_label"
        ),
    )


class FollowerList(GridReport):
    title = _("following")
    model = Follower
    frozenColumns = 0
    template = "common/follower.html"
    message_when_empty = Template(
        """
        <h3>You are not following any objects yet</h3>
        <br>
        All reports where you edit or review an object have a follow button in the upper right corner.<br>
        <br>
        You will get messages in your inbox when there is any activity on objects you follow.<br>
        <br>
        <img style="border-radius: 10px; max-width: 180px" src="/static/img/inbox_and_following.png">
        <br>
        """
    )

    @classmethod
    def basequeryset(reportclass, request, *args, **kwargs):
        return (
            Follower.objects.all()
            .filter(user=request.user)
            .annotate(
                following=RawSQL(
                    "select string_agg(value#>>'{}', ', ') from jsonb_array_elements(common_follower.args->'sub')",
                    [],
                )
            )
        )

    @classmethod
    def query(reportclass, request, basequery, sortsql="1 asc"):
        for row in basequery:
            sub = []
            if row.following:
                for x in row.following.split(","):
                    app_label, model = x.split(".", 2)
                    try:
                        sub.append(
                            force_str(
                                ContentType.objects.get_by_natural_key(
                                    app_label.strip(), model.strip()
                                )
                                .model_class()
                                ._meta.verbose_name
                            )
                        )
                    except Exception:
                        pass
            yield {
                "id": row.id,
                "content_type__model": force_str(
                    row.content_type.model_class()._meta.verbose_name
                ),
                "object_pk": row.object_pk,
                "type": row.type,
                "following": ", ".join(sub),
                "model": row.content_type.model,
                "app": row.content_type.app_label,
            }

    @classmethod
    def rows(request, *args, **kwargs):
        return (
            GridFieldInteger(
                "id",
                title=_("identifier"),
                key=True,
                formatter="detail",
                extra='"role":"common/follower"',
                initially_hidden=True,
            ),
            GridFieldChoice(
                "content_type",
                field_name="content_type__model",
                title=_("model name"),
                choices=[(str(x.id), x.name) for x in ContentType.objects.all()],
            ),
            GridFieldText(
                "object_pk",
                field_name="object_pk",
                title=_("object name"),
                extra='"formatter": objectfmt',
            ),
            GridFieldChoice("type", title=_("type"), choices=Follower.type_list),
            GridFieldChoice("following", title=_("following"), editable=False),
            GridFieldText("model", title="model", hidden=True, field_name="model"),
            GridFieldText("app", title="app", hidden=True, field_name="app"),
        )


class BucketList(GridReport):
    title = _("buckets")
    basequeryset = Bucket.objects.all()
    model = Bucket
    frozenColumns = 1
    help_url = "model-reference/buckets.html"
    rows = (
        GridFieldText(
            "name",
            title=_("name"),
            key=True,
            formatter="detail",
            extra='"role":"common/bucket"',
        ),
        GridFieldText("description", title=_("description")),
        GridFieldInteger("level", title=_("level")),
        GridFieldText("source", title=_("source"), initially_hidden=True),
        GridFieldLastModified("lastmodified"),
    )


class BucketDetailList(GridReport):
    title = _("bucket dates")
    basequeryset = BucketDetail.objects.all()
    model = BucketDetail
    frozenColumns = 2
    help_url = "model-reference/bucket-dates.html"
    default_sort = (2, "asc", 1, "asc")
    rows = (
        GridFieldInteger(
            "id",
            title=_("identifier"),
            key=True,
            formatter="detail",
            extra='"role":"common/bucketdetail"',
            initially_hidden=True,
        ),
        GridFieldText(
            "bucket",
            title=_("bucket"),
            field_name="bucket__name",
            formatter="detail",
            extra='"role":"common/bucket"',
        ),
        GridFieldDateTime("startdate", title=_("start date")),
        GridFieldDateTime("enddate", title=_("end date")),
        GridFieldText("name", title=_("name")),
        GridFieldText("source", title=_("source"), initially_hidden=True),
        GridFieldLastModified("lastmodified"),
    )


class AttributeList(GridReport):
    title = _("attributes")
    basequeryset = Attribute.objects.all()
    model = Attribute
    frozenColumns = 1
    help_url = "model-reference/attributes.html"
    message_when_empty = Template(
        """
        <h3>Extend frePPLe with your own attributes</h3>
        <br>
        Every business uses specific attributes on items, sales orders, suppliers...<br>
        You can edit, filter, sort, import and export your attribute fields like all other fields.<br>
        <br><br>
        <a href="{{request.prefix}}/data/common/attribute/add/" class="btn btn-primary">Add attribute</a>
        <br>
        """
    )

    rows = (
        GridFieldInteger(
            "id",
            title=_("identifier"),
            key=True,
            formatter="detail",
            extra='"role":"common/attribute"',
            initially_hidden=True,
        ),
        GridFieldChoice(
            "model",
            title=_("model"),
            field_name="model",
            choices=Attribute._getContentTypeChoices(),
        ),
        GridFieldText(
            "name",
            title=_("name"),
        ),
        GridFieldText(
            "label",
            title=_("label"),
        ),
        GridFieldChoice("type", title=_("type"), choices=Attribute.types),
        GridFieldBool(
            "editable",
            title=_("editable"),
        ),
        GridFieldBool(
            "initially_hidden",
            title=_("initially hidden"),
        ),
        GridFieldText("source", title=_("source"), initially_hidden=True),
        GridFieldLastModified("lastmodified"),
    )


@staff_member_required
def detail(request, app, model, object_id):
    # Find the object type
    ct = ContentType.objects.get(app_label=app, model=model)
    admn = data_site._registry[ct.model_class()]
    if not hasattr(admn, "tabs"):
        url = reverse("admin:%s_%s_change" % (ct.app_label, ct.model), args=("dummy",))
        return resolve(url).func(request, object_id)

    # Find the tab we need to open
    lasttab = request.session.get("lasttab")
    newtab = None
    for tab in admn.tabs:
        if lasttab == tab["name"] or not lasttab:
            perms = tab.get("permissions")
            if perms:
                if isinstance(perms, str):
                    # A single permission is given
                    if not request.user.has_perm(perms):
                        continue
                else:
                    # A list or tuple of permissions is given
                    ok = True
                    for p in perms:
                        if not request.user.has_perm(p):
                            ok = False
                            break
                    if not ok:
                        continue
            newtab = tab
            break
    if not newtab:
        newtab = admn.tabs[0]

    # Convert a view name into a function when accessed the first time
    viewfunc = newtab.get("viewfunc", None)
    if not viewfunc:
        url = reverse(newtab["view"], args=("dummy",))
        newtab["viewfunc"] = resolve(url).func

    # Open the tab, enforcing the noautofilter behavior
    request.GET = request.GET.copy()
    request.GET["noautofilter"] = True
    return newtab["viewfunc"](request, object_id)


def csrf_failure(request, reason):
    # Redirect to login page
    logger.error("CSRF failure detected")
    return HttpResponseRedirect(request.prefix + "/")


def sendStaticFile(request, *args, headers=None):
    """
    Serving log and data files can be handled either:
    - by Django's Python code
    - by the apache or nginx web server if the module xsendfile is installed
    """
    if getattr(settings, "APACHE_XSENDFILE", False):
        # Forward to Apache
        # Code inspired on https://github.com/johnsensible/django-sendfile/
        response = HttpResponse()
        guessed_mimetype = guess_type(args[-1], strict=False)[0]
        if guessed_mimetype:
            response["Content-Type"] = guessed_mimetype
        else:
            response["Content-Type"] = "application/octet-stream"
        # For apache:
        response["X-Sendfile"] = os.path.join(*args)
        # For nginx:
        # response["X-Accel-Redirect"]= os.path.join(*args)
    else:
        # Django's static file server
        response = static.serve(
            request, args[-1], document_root=os.path.join(*args[:-1])
        )
    if response.headers.get("Content-Encoding", None) == "gzip":
        # Avoid that gzipped files are decompressed automatically by browsers
        del response.headers["Content-Encoding"]
        response.headers["Content-Type"] = "application/gzip"
    if headers:
        for k, v in headers.items():
            response[k] = v
    return response


@login_required
def uploads(request, filename):
    return sendStaticFile(
        request,
        settings.FREPPLE_LOGDIR,
        "uploads",
        filename,
        headers={"Cache-Control": "max-age=%s" % settings.MEDIA_MAX_AGE},
    )


@login_required
def inbox(request):
    if request.headers.get("x-requested-with") == "XMLHttpRequest":
        if request.method == "GET":
            # Return summary json to ajax requests
            return JsonResponse(
                {
                    "unread": Notification.objects.using(request.database)
                    .filter(user_id=request.user.id, status="U")
                    .count()
                }
            )
        else:
            # Updating messages posted in the format
            # [{"id": 123, "action": "read / delete"},...]
            response = {"errors": 0}
            try:
                for rec in json.JSONDecoder().decode(
                    request.read().decode(request.encoding or settings.DEFAULT_CHARSET)
                ):
                    try:
                        pk = rec.get("id", None)
                        status = rec.get("status", None)
                        if id and status:
                            notif = Notification.objects.using(request.database).get(
                                pk=pk, user=request.user
                            )
                            if status == "D":
                                notif.delete(using=request.database)
                            else:
                                notif.status = status
                                notif.save(using=request.database)
                    except Exception as e:
                        logger.error("Error processing notification %s: %s" % (pk, e))
                        response["errors"] += 1
            except Exception as e:
                logger.error("Error parsing notifcation update: %s" % e)
                response["errors"] += 1
            return JsonResponse(response)
    else:
        # Return inbox page for normal requests
        msgs = (
            Notification.objects.using(request.database)
            .filter(user=request.user)
            .order_by("-id")
            .select_related("comment", "user")
        )
        empty = not msgs.exists()
        if empty:
            if (
                Follower.objects.using(request.database)
                .filter(user=request.user)
                .exists()
            ):
                empty = False
        unread = request.GET.get("unread", "false")
        if unread != "false":
            msgs = msgs.filter(status="U")
        inbox = Paginator(msgs, request.user.pagesize)
        return render(
            request,
            "common/inbox.html",
            context={
                "title": _("inbox"),
                "inbox": inbox.get_page(request.GET.get("page", 1)),
                "unread": unread != "false",
                "empty": empty,
            },
        )


@login_required
def follow(request):
    if (
        request.headers.get("x-requested-with") == "XMLHttpRequest"
        and request.method == "POST"
    ):
        # Updating followers posted in the format:
        # [{
        #  'object_pk': "my product", 'model': 'input.item',
        #  'users': ['me', 'you'],
        #  'models': ['input.item', 'input.distributionorder', 'input.itemdistribution']
        # }]
        errors = False
        for rec in json.JSONDecoder().decode(
            request.body.decode(request.encoding or settings.DEFAULT_CHARSET)
        ):
            try:
                object_pk = rec.get("object_pk", None)
                model = rec.get("model", None)
                if not object_pk or not model:
                    continue
                app_and_model = model.split(".")
                ct = ContentType.objects.get(
                    app_label=app_and_model[0], model=app_and_model[1]
                )
                followers = {
                    f.user.username: f
                    for f in Follower.objects.using(request.database).filter(
                        content_type=ct.pk, object_pk=object_pk
                    )
                }
                for username, type in rec.get("users", {}).items():
                    user = User.objects.using(request.database).get(username=username)
                    if username not in followers:
                        # New follower
                        Follower(
                            content_type_id=ct.pk,
                            object_pk=object_pk,
                            user=user,
                            type="M" if type == "email" else "O",
                        ).save(using=request.database)
                        Comment(
                            user_id=request.user.id,
                            content_type_id=ct.pk,
                            object_pk=object_pk,
                            object_repr=object_pk,
                            type="follower",
                            comment="Added follower %s" % username,
                        ).save(using=request.database)
                    else:
                        # Update follower
                        followers[username].type = "M" if type == "email" else "O"
                        followers[username].save(using=request.database)
                for username, flw in followers.items():
                    if (
                        username not in rec.get("users", {})
                        and username != request.user.username
                    ):
                        # Delete a follower
                        flw.delete(using=request.database)
                        Comment(
                            user_id=request.user.id,
                            content_type_id=ct.pk,
                            object_pk=object_pk,
                            object_repr=object_pk,
                            type="follower",
                            comment="Deleted follower %s" % username,
                        ).save(using=request.database)
                myfollow = followers.get(request.user.username)
                models = rec.get("models", None)
                if myfollow:
                    if models:
                        # Update existing follower
                        myfollow.args["sub"] = models
                        if "type" in rec:
                            myfollow.type = "M" if rec.get("type") == "email" else "O"
                        myfollow.save(using=request.database)
                    else:
                        # Delete follower
                        myfollow.delete(using=request.database)
                elif models:
                    # New follower
                    Follower(
                        content_type_id=ct.pk,
                        object_pk=object_pk,
                        user=request.user,
                        type="M" if rec.get("type") == "email" else "O",
                        args={"sub": models},
                    ).save(using=request.database)
            except Exception as e:
                logger.error("Error processing follower POST %s: %s" % (rec, e))
                errors = True
        if errors:
            return HttpResponse(content="NOT OK", status=400)
        else:
            return HttpResponse(content="OK")
    elif (
        request.headers.get("x-requested-with") == "XMLHttpRequest"
        and request.method == "GET"
    ):
        # Return follower information for an object
        try:
            object_pk = request.GET.get("object_pk", None)
            model = request.GET.get("model", None)
            if object_pk and model:
                app_and_model = model.split(".")
                ct = ContentType.objects.get(
                    app_label=app_and_model[0], model=app_and_model[1]
                )
                return JsonResponse(
                    NotificationFactory.getAllFollowers(
                        content_type=ct,
                        object_pk=object_pk,
                        user=request.user,
                        database=request.database,
                    )
                )
        except Exception as e:
            logger.error("Error processing follower GET: %s" % e)
            return HttpResponse(content="NOT OK", status=400)
    else:
        return HttpResponseNotAllowed(
            ["post", "get"], content="Only ajax GET and POST requests are allowed"
        )
