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

from functools import update_wrapper
import json
from urllib.parse import quote as urllib_quote

from django.apps import apps
from django.core.exceptions import PermissionDenied
from django.contrib import admin
from django.contrib.admin.options import IS_POPUP_VAR, TO_FIELD_VAR
from django.contrib import messages
from django.contrib.admin.exceptions import DisallowedModelAdminToField
from django.contrib.admin.utils import quote, unquote
from django.contrib.admin.templatetags.admin_urls import add_preserved_filters
from django.contrib.auth.forms import UserCreationForm
from django.contrib.contenttypes.models import ContentType
from django.db import transaction, DEFAULT_DB_ALIAS
from django.db.models import Q
from django.db.models.fields import (
    DecimalField,
    DateField,
    DateTimeField,
    TimeField,
    CharField,
)
from django import forms
from django.http import HttpResponseRedirect, Http404
from django.shortcuts import render
from django.template.response import TemplateResponse
from django.urls import reverse
from django.utils.encoding import force_str
from django.utils.html import format_html
from django.utils.safestring import mark_safe
from django.utils.translation import gettext_lazy as _
from django.utils.text import format_lazy, get_text_list
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_protect

from .models import Comment, User, Scenario


csrf_protect_m = method_decorator(csrf_protect)


class DatePickerInput(forms.DateInput):
    input_type = "date"


class TimePickerInput(forms.TimeInput):
    input_type = "time"


class DateTimePickerInput(forms.DateTimeInput):
    input_type = "datetime-local"


class DateTimeLocalField(forms.DateTimeField):
    input_formats = [
        "%Y-%m-%dT%H:%M:%S",
        "%Y-%m-%dT%H:%M:%S.%f",
        "%Y-%m-%dT%H:%M",
    ]
    widget = DateTimePickerInput(format="%Y-%m-%dT%H:%M:%S")


class MultiDBModelAdmin(admin.ModelAdmin):
    """
    This class is an enhanced version of the django regular admin model.
    It adds:
     - support for multiple databases
          - store and load history information in the right database
          - assure prefix is maintained in the URLs
          - check for related objects in the right database
     - support for changing the primary key of an object
     - different logic to determine the next page to display

    See https://docs.djangoproject.com/en/2.2/topics/db/multi-db/#exposing-multiple-databases-in-django-s-admin-interface

    See the standard code in the file django/contrib/admin/options.py
    The level of customization is relatively high, and this code is a bit of a
    concern for future upgrades of Django...
    """

    formfield_overrides = {
        # Django by default uses the value of decimal_places to compute a step.
        # We prefer to stick to a default step of 1.
        DecimalField: {
            "widget": forms.NumberInput(attrs={"step": "1", "placeholder": ""})
        },
        DateField: {"widget": DatePickerInput(attrs={"placeholder": ""})},
        TimeField: {"widget": TimePickerInput(attrs={"placeholder": ""})},
        DateTimeField: {
            "form_class": DateTimeLocalField,
            "widget": DateTimePickerInput(
                format="%Y-%m-%dT%H:%M:%S", attrs={"placeholder": ""}
            ),
        },
        CharField: {"widget": forms.TextInput(attrs={"placeholder": ""})},
    }

    def get_urls(self):
        """
        Customized to:
        - remove list and history views
        - add comment view
        """
        from django.urls import path

        def wrap(view):
            def wrapper(*args, **kwargs):
                return self.admin_site.admin_view(view)(*args, **kwargs)

            wrapper.model_admin = self
            return update_wrapper(wrapper, view)

        info = self.model._meta.app_label, self.model._meta.model_name

        urlpatterns = [
            path("", wrap(self.changelist_view), name="%s_%s_changelist" % info),
            path("add/", wrap(self.add_view), name="%s_%s_add" % info),
            path(
                "<path:object_id>/comment/",
                wrap(self.comment_view),
                name="%s_%s_comment" % info,
            ),
            path(
                "<path:object_id>/delete/",
                wrap(self.delete_view),
                name="%s_%s_delete" % info,
            ),
            path(
                "<path:object_id>/change/",
                wrap(self.change_view),
                name="%s_%s_change" % info,
            ),
        ]
        return urlpatterns

    def save_form(self, request, form, change):
        # Execute the standard behavior
        obj = super().save_form(request, form, change)
        # FrePPLe specific addition
        if change:
            path = request.path_info.rsplit("/", 3)
            if path[-2] == "change":
                old_pk = unquote(path[1])
            else:
                old_pk = unquote(path[-2])
            if old_pk != (isinstance(obj.pk, str) and obj.pk or str(obj.pk)):
                # The object was renamed. We continue handling the updates on the
                # old object. Only at the very end we will rename whatever needs to
                # be renamed.
                obj.new_pk = obj.pk
                obj.pk = old_pk
        return obj

    def save_model(self, request, obj, form, change):
        # Tell Django to save objects to the 'other' database.
        obj.save(using=request.database)

    def get_queryset(self, request):
        # Tell Django to get objects from the 'other' database.
        return super().get_queryset(request).using(request.database)

    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        # Tell Django to get objects from the 'other' database.
        return super().formfield_for_foreignkey(
            db_field, request=request, using=request.database, **kwargs
        )

    def formfield_for_manytomany(self, db_field, request=None, **kwargs):
        # Tell Django to get objects from the 'other' database.
        return super().formfield_for_manytomany(
            db_field, request=request, using=request.database, **kwargs
        )

    def log_addition(self, request, obj, message):
        """
        Log that an object has been successfully added.
        """
        content_type = ContentType.objects.get_for_model(obj, for_concrete_model=False)
        entry = Comment(
            user_id=request.user.pk,
            content_type_id=content_type.pk,
            object_pk=str(obj.pk),
            object_repr=str(obj)[:200],
            type="add",
            comment="Added %s." % str(obj),
        )
        entry.save(using=request.database)

    def log_change(self, request, obj, message):
        """
        Log that an object has been successfully changed.
        """
        if not message:
            return
        content_type = ContentType.objects.get_for_model(obj, for_concrete_model=False)
        if hasattr(obj, "new_pk"):
            # We are renaming an existing object.
            # a) Save the new record in the right database
            old_pk = obj.pk
            obj.pk = obj.new_pk
            obj.save(using=request.database)
            # b) All linked fields need updating.
            for related in obj._meta.get_fields():
                if (
                    (related.one_to_many or related.one_to_one)
                    and related.auto_created
                    and not related.concrete
                ):
                    related.related_model._base_manager.using(request.database).filter(
                        **{related.field.name: old_pk}
                    ).update(**{related.field.name: obj})
            # c) Move the comments to the new key
            Comment.objects.using(request.database).filter(
                content_type__pk=content_type.pk, object_pk=old_pk
            ).update(object_pk=obj.pk)
            # d) Delete the old record
            obj.pk = old_pk
            obj.delete(using=request.database)
            obj.pk = obj.new_pk
        for m in message:
            if "changed" in m:
                if "object" in m["changed"] and "name" in m["changed"]:
                    # Changed one or more fields on related objects
                    # {'changed': {'name': 'calendar bucket', 'object': '40', 'fields': ['starttime']}}
                    for model in apps.get_models():
                        if str(model._meta.verbose_name) == m["changed"]["name"]:
                            Comment(
                                user_id=request.user.pk,
                                content_type_id=ContentType.objects.get_for_model(
                                    model
                                ).pk,
                                object_pk=m["changed"]["object"],
                                object_repr=m["changed"]["object"],
                                type="change",
                                comment=(
                                    message
                                    if isinstance(message, str)
                                    else "Changed %s."
                                    % get_text_list(m["changed"]["fields"], "and")
                                ),
                            ).save(using=request.database)
                            break
                else:
                    # Changed one or more fields
                    # {'changed': {'fields': ['defaultvalue']}}
                    Comment(
                        user_id=request.user.pk,
                        content_type_id=content_type.pk,
                        object_pk=str(obj.pk),
                        object_repr=str(obj)[:200],
                        type="change",
                        comment=(
                            message
                            if isinstance(message, str)
                            else "Changed %s."
                            % get_text_list(m["changed"]["fields"], "and")
                        ),
                    ).save(using=request.database)
            elif "added" in m:
                if "object" in m["added"] and "name" in m["added"]:
                    # Adding related object
                    # {"added": {"name": "calendar bucket", "object": "48"}}
                    for model in apps.get_models():
                        if str(model._meta.verbose_name) == m["added"]["name"]:
                            Comment(
                                user_id=request.user.pk,
                                content_type_id=ContentType.objects.get_for_model(
                                    model
                                ).pk,
                                object_pk=m["added"]["object"],
                                object_repr=m["added"]["object"],
                                type="add",
                                comment="Added %s." % m["added"]["object"],
                            ).save(using=request.database)
                            break

    def log_deletion(self, request, obj, object_repr):
        """
        Log that an object will be deleted. Note that this method is called
        before the deletion.
        """
        entry = Comment(
            user_id=request.user.id,
            content_type_id=ContentType.objects.get_for_model(
                self.model, for_concrete_model=False
            ).pk,
            object_pk=str(obj.pk),
            object_repr=object_repr[:200],
            type="delete",
            comment="Deleted %s." % object_repr,
        )
        entry.save(using=request.database)
        return entry

    def response_add(self, request, obj, post_url_continue=None):
        """
        Determines the HttpResponse for the add_view stage.
        """
        opts = obj._meta
        preserved_filters = self.get_preserved_filters(request)
        # frePPLe specific: prepend the url prefix
        obj_url = request.prefix + reverse(
            "admin:%s_%s_change" % (opts.app_label, opts.model_name),
            args=(quote(obj.pk),),
            current_app=self.admin_site.name,
        )
        # Add a link to the object's change form if the user can edit the obj.
        if self.has_change_permission(request, obj):
            obj_repr = format_html(
                '<a href="{}">{}</a>', urllib_quote(obj_url, safe="/"), obj
            )
        else:
            obj_repr = str(obj)
        msg_dict = {"name": opts.verbose_name, "obj": obj_repr}
        # Here, we distinguish between different save types by checking for
        # the presence of keys in request.POST.

        if IS_POPUP_VAR in request.POST:
            to_field = request.POST.get(TO_FIELD_VAR)
            if to_field:
                attr = str(to_field)
            else:
                attr = obj._meta.pk.attname
            value = obj.serializable_value(attr)
            popup_response_data = json.dumps({"value": str(value), "obj": str(obj)})
            return TemplateResponse(
                request,
                self.popup_response_template
                or [
                    "admin/%s/%s/popup_response.html"
                    % (opts.app_label, opts.model_name),
                    "admin/%s/popup_response.html" % opts.app_label,
                    "admin/popup_response.html",
                ],
                {"popup_response_data": popup_response_data},
            )

        elif "_continue" in request.POST or (
            # Redirecting after "Save as new".
            "_saveasnew" in request.POST
            and self.save_as_continue
            and self.has_change_permission(request, obj)
        ):
            msg = _('The {name} "{obj}" was added successfully.')
            if self.has_change_permission(request, obj):
                msg = format_lazy("{} {}", msg, _("You may edit it again below."))
            self.message_user(request, format_html(msg, **msg_dict), messages.SUCCESS)
            if post_url_continue is None:
                post_url_continue = obj_url
            post_url_continue = add_preserved_filters(
                {"preserved_filters": preserved_filters, "opts": opts},
                post_url_continue,
            )
            return HttpResponseRedirect(post_url_continue)

        elif "_addanother" in request.POST:
            msg = format_html(
                _(
                    'The {name} "{obj}" was added successfully. You may add another {name} below.'
                ),
                **msg_dict,
            )
            self.message_user(request, msg, messages.SUCCESS)
            # frePPLe specific: prepend the url prefix
            redirect_url = request.prefix + request.path
            redirect_url = add_preserved_filters(
                {"preserved_filters": preserved_filters, "opts": opts}, redirect_url
            )
            return HttpResponseRedirect(redirect_url)

        else:
            msg = format_html(
                _('The {name} "{obj}" was added successfully.'), **msg_dict
            )
            self.message_user(request, msg, messages.SUCCESS)
            return self.response_post_save_add(request, obj)

    def _response_post_save(self, request, obj):
        """
        Figure out where to redirect after the 'Save' button has been pressed
        when adding a new object.
        """
        opts = self.model._meta
        if self.has_view_or_change_permission(request):
            # frePPLe specific: prepend the url prefix
            post_url = request.prefix + reverse(
                "admin:%s_%s_changelist" % (opts.app_label, opts.model_name),
                current_app=self.admin_site.name,
            )
            preserved_filters = self.get_preserved_filters(request)
            post_url = add_preserved_filters(
                {"preserved_filters": preserved_filters, "opts": opts}, post_url
            )
        else:
            # frePPLe specific: prepend the url prefix
            post_url = request.prefix
        return HttpResponseRedirect(post_url)

    def response_post_save_add(self, request, obj):
        """
        Figure out where to redirect after the 'Save' button has been pressed
        when adding a new object.
        """
        return self._response_post_save(request, obj)

    def response_post_save_change(self, request, obj):
        """
        Figure out where to redirect after the 'Save' button has been pressed
        when editing an existing object.
        """
        return self._response_post_save(request, obj)

    def has_add_permission(self, request):
        return (
            super().has_add_permission(request)
            or "add" not in self.opts.model._meta.default_permissions
        )

    def has_change_permission(self, request, obj=None):
        return (
            super().has_change_permission(request, obj)
            or "change" not in self.opts.model._meta.default_permissions
        )

    def has_delete_permission(self, request, obj=None):
        return (
            super().has_change_permission(request, obj)
            or "delete" not in self.opts.model._meta.default_permissions
        )

    def has_view_permission(self, request, obj=None):
        return (
            super().has_view_permission(request, obj)
            or "view" not in self.opts.model._meta.default_permissions
        )

    def response_change(self, request, obj):
        """
        Determines the HttpResponse for the change_view stage.
        """
        if IS_POPUP_VAR in request.POST:
            opts = obj._meta
            to_field = request.POST.get(TO_FIELD_VAR)
            attr = str(to_field) if to_field else opts.pk.attname
            value = request.resolver_match.kwargs["object_id"]
            new_value = obj.serializable_value(attr)
            popup_response_data = json.dumps(
                {
                    "action": "change",
                    "value": str(value),
                    "obj": str(obj),
                    "new_value": str(new_value),
                }
            )
            return TemplateResponse(
                request,
                self.popup_response_template
                or [
                    "admin/%s/%s/popup_response.html"
                    % (opts.app_label, opts.model_name),
                    "admin/%s/popup_response.html" % opts.app_label,
                    "admin/popup_response.html",
                ],
                {"popup_response_data": popup_response_data},
            )

        opts = self.model._meta
        preserved_filters = self.get_preserved_filters(request)

        msg_dict = {
            "name": force_str(opts.verbose_name),
            "obj": format_html(
                '<a href="{}">{}</a>', urllib_quote(request.path, safe="/"), obj
            ),
        }
        if "_continue" in request.POST:
            msg = format_html(
                _(
                    'The {name} "{obj}" was changed successfully. You may edit it again below.'
                ),
                **msg_dict,
            )
            self.message_user(request, msg, messages.SUCCESS)
            # frePPLe specific: prepend the url prefix
            redirect_url = request.prefix + request.path
            redirect_url = add_preserved_filters(
                {"preserved_filters": preserved_filters, "opts": opts}, redirect_url
            )
            return HttpResponseRedirect(redirect_url)

        elif "_saveasnew" in request.POST:
            msg = format_html(
                _(
                    'The {name} "{obj}" was added successfully. You may edit it again below.'
                ),
                **msg_dict,
            )
            self.message_user(request, msg, messages.SUCCESS)
            # frePPLe specific: prepend the url prefix
            redirect_url = request.prefix + reverse(
                "admin:%s_%s_change" % (opts.app_label, opts.model_name),
                args=(obj.pk,),
                current_app=self.admin_site.name,
            )
            redirect_url = add_preserved_filters(
                {"preserved_filters": preserved_filters, "opts": opts}, redirect_url
            )
            return HttpResponseRedirect(redirect_url)

        elif "_addanother" in request.POST:
            msg = format_html(
                _(
                    'The {name} "{obj}" was changed successfully. You may add another {name} below.'
                ),
                **msg_dict,
            )
            self.message_user(request, msg, messages.SUCCESS)
            # frePPLe specific: prepend the url prefix
            redirect_url = request.prefix + reverse(
                "admin:%s_%s_add" % (opts.app_label, opts.model_name),
                current_app=self.admin_site.name,
            )
            redirect_url = add_preserved_filters(
                {"preserved_filters": preserved_filters, "opts": opts}, redirect_url
            )
            return HttpResponseRedirect(redirect_url)

        else:
            msg = format_html(
                _('The {name} "{obj}" was changed successfully.'), **msg_dict
            )
            self.message_user(request, msg, messages.SUCCESS)
            return self.response_post_save_change(request, obj)

    @transaction.atomic
    def add_view(self, request, form_url="", extra_context=None):
        new_extra_context = extra_context or {}
        new_extra_context["model"] = self.model
        return super().add_view(request, form_url, new_extra_context)

    @transaction.atomic
    def change_view(self, request, object_id, form_url="", extra_context=None):
        request.session["lasttab"] = "edit"
        new_extra_context = extra_context or {}
        new_extra_context["title"] = (
            force_str(self.model._meta.verbose_name) + " " + unquote(object_id)
        )
        new_extra_context["post_title"] = _("edit")
        new_extra_context["admin"] = self
        new_extra_context["model"] = self.model
        return super().change_view(request, object_id, form_url, new_extra_context)

    @csrf_protect_m
    @transaction.atomic
    def comment_view(self, request, object_id, extra_context=None):
        request.session["lasttab"] = "comments"
        try:
            model = self.model._meta.model_name
            modeltype = ContentType.objects.using(request.database).get(
                app_label=self.model._meta.app_label, model=model
            )
            modeltype._state.db = request.database
            object_id = unquote(object_id)
            # Special treatment for buffers
            if model == "buffer":
                from freppledb.input.models import Buffer

                if " @ " in object_id:
                    bufferName = object_id
                    index = object_id.find(" @ ")
                    b = Buffer.objects.get(
                        item=object_id[0:index], location=object_id[index + 3 :]
                    )
                    if b:
                        object_id = b.id
                else:
                    b = Buffer.objects.get(id=object_id)
                    bufferName = b.item.name + " @ " + b.location.name
            modelinstance = modeltype.get_object_for_this_type(pk=object_id)
            comments = (
                Comment.objects.using(request.database)
                .filter(content_type__pk=modeltype.id, object_pk=object_id)
                .order_by("-id")
            )
        except Exception:
            raise Http404("Object not found")
        if request.method == "POST":
            if request.user.has_perm("common.add_comment"):
                comment = request.POST["comment"]
                att = request.FILES.get("attachment", None)
                if comment or att:
                    c = Comment(
                        content_object=modelinstance,
                        object_repr=str(modelinstance)[:200],
                        user=request.user,
                        comment=comment,
                        type="comment",
                    )
                    if att:
                        c.attachment = att
                    c.save(using=request.database)
            return HttpResponseRedirect("%s%s" % (request.prefix, request.path))
        else:
            request.session["lasttab"] = "messages"
            return render(
                request,
                "common/comments.html",
                context={
                    "title": force_str(modelinstance._meta.verbose_name)
                    + " "
                    + (bufferName if "bufferName" in vars() else object_id),
                    "post_title": _("messages"),
                    "model": self.model,
                    "opts": self.model._meta,
                    "object_id": quote(object_id),
                    "active_tab": "comments",
                    "comments": comments,
                },
            )

    def response_delete(self, request, obj_display, obj_id):
        """
        Determines the HttpResponse for the delete_view stage.
        """
        opts = self.model._meta

        if IS_POPUP_VAR in request.POST:
            popup_response_data = json.dumps({"action": "delete", "value": str(obj_id)})
            return TemplateResponse(
                request,
                self.popup_response_template
                or [
                    "admin/%s/%s/popup_response.html"
                    % (opts.app_label, opts.model_name),
                    "admin/%s/popup_response.html" % opts.app_label,
                    "admin/popup_response.html",
                ],
                {"popup_response_data": popup_response_data},
            )

        self.message_user(
            request,
            _('The %(name)s "%(obj)s" was deleted successfully.')
            % {"name": opts.verbose_name, "obj": obj_display},
            messages.SUCCESS,
        )

        try:
            # frePPLe specific: Delete delete-confirmation and edit pages from the crumbs
            # Lastcrumb has a URL like /data/input/customer/B/delete/
            # Editing page of this object is /data/input/customer/B/change/
            # Detail page of this object is /detail/input/customer/B/
            lastcrumb = request.session["crumbs"][request.prefix][-1][2]
            lastcrumbcore = lastcrumb[6:-8]
            detailpages = [
                "/data/%s/change" % lastcrumbcore,
                "/detail/%s/" % lastcrumbcore,
            ]
            del request.session["crumbs"][request.prefix][-1]
            if request.session["crumbs"][request.prefix][-1][2] in detailpages:
                del request.session["crumbs"][request.prefix][-1]
        except Exception:
            pass

        # frePPLe specific: Redirect to previous url
        return HttpResponseRedirect(
            "%s%s" % (request.prefix, request.session["crumbs"][request.prefix][-1][2])
        )

    @csrf_protect_m
    def delete_view(self, request, object_id, extra_context=None):
        # frePPLe specific: use database specified on the request instead of the router
        with transaction.atomic(using=request.database):
            return self._delete_view(request, object_id, extra_context)

    def _delete_view(self, request, object_id, extra_context):
        """
        The 'delete' admin view for this model.
        """
        opts = self.model._meta
        app_label = opts.app_label

        to_field = request.POST.get(TO_FIELD_VAR, request.GET.get(TO_FIELD_VAR))
        if to_field and not self.to_field_allowed(request, to_field):
            raise DisallowedModelAdminToField(
                "The field %s cannot be referenced." % to_field
            )

        obj = self.get_object(request, unquote(object_id), to_field)

        if not self.has_delete_permission(request, obj):
            raise PermissionDenied

        if obj is None:
            return self._get_obj_does_not_exist_redirect(request, opts, object_id)

        # Populate deleted_objects, a data structure of all related objects that
        # will also be deleted.
        (
            deleted_objects,
            model_count,
            perms_needed,
            protected,
        ) = self.get_deleted_objects([obj], request)

        # frePPLe specific: Update the links to the related objects.
        if request.prefix:

            def replace_url(a):
                if isinstance(a, list):
                    return [replace_url(i) for i in a]
                else:
                    return mark_safe(a.replace('href="', 'href="%s' % request.prefix))

            deleted_objects = [replace_url(i) for i in deleted_objects]
            protected = [replace_url(i) for i in protected]

        if request.POST and not protected:  # The user has confirmed the deletion.
            if perms_needed:
                raise PermissionDenied
            obj_display = str(obj)
            attr = str(to_field) if to_field else opts.pk.attname
            obj_id = obj.serializable_value(attr)
            self.log_deletion(request, obj, obj_display)
            self.delete_model(request, obj)

            return self.response_delete(request, obj_display, obj_id)

        object_name = str(opts.verbose_name)

        title = format_lazy("{} {}", self.model._meta.verbose_name, unquote(object_id))

        context = {
            **self.admin_site.each_context(request),
            "title": title,
            "post_title": _("delete"),
            "object_name": object_name,
            "object": obj,
            "model": self.model,
            "object_id": obj,
            "deleted_objects": deleted_objects,
            "model_count": dict(model_count).items(),
            "perms_lacking": perms_needed,
            "protected": protected,
            "opts": opts,
            "app_label": app_label,
            "preserved_filters": self.get_preserved_filters(request),
            "is_popup": (IS_POPUP_VAR in request.POST or IS_POPUP_VAR in request.GET),
            "to_field": to_field,
            **(extra_context or {}),
        }

        return self.render_delete_form(request, context)


class MultiDBTabularInline(admin.TabularInline):
    """
    See https://docs.djangoproject.com/en/2.2/topics/db/multi-db/#exposing-multiple-databases-in-django-s-admin-interface
    """

    def get_queryset(self, request):
        return super().get_queryset(request).using(request.database)

    def formfield_for_foreignkey(self, db_field, request=None, **kwargs):
        return super().formfield_for_foreignkey(
            db_field, request=request, using=request.database, **kwargs
        )

    def formfield_for_manytomany(self, db_field, request=None, **kwargs):
        return super().formfield_for_manytomany(
            db_field, request=request, using=request.database, **kwargs
        )


class MultiDBUserCreationForm(UserCreationForm):
    email = forms.EmailField(required=True, help_text=_("Required."))
    first_name = forms.CharField(
        required=True, max_length=30, help_text=_("Required. Max 30 characters.")
    )
    last_name = forms.CharField(
        required=True, max_length=30, help_text=_("Required. Max 30 characters.")
    )
    scenarios = forms.MultipleChoiceField(
        required=False,
        label="What-if scenarios in use",
        widget=forms.CheckboxSelectMultiple,
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        sc = []
        for db in Scenario.objects.using(DEFAULT_DB_ALIAS).filter(
            Q(status="In use") & ~Q(name=DEFAULT_DB_ALIAS)
        ):
            sc.append((db.name, db.name))
        self.fields["scenarios"].choices = sc

    class Meta(UserCreationForm):
        model = User
        fields = UserCreationForm.Meta.fields + ("first_name", "last_name", "email")

    def save(self, commit=True):
        user = super().save(commit=False)
        user.set_password(self.cleaned_data["password1"])
        user.databases = self.cleaned_data["scenarios"] or []
        user.databases.append(DEFAULT_DB_ALIAS)
        user.save(using=DEFAULT_DB_ALIAS)
        return user
