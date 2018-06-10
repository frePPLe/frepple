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

from functools import update_wrapper
import json

from django.conf.urls import url
from django.core.exceptions import PermissionDenied
from django.contrib import admin
from django.contrib.admin.options import get_content_type_for_model
from django.contrib import messages
from django.contrib.admin.exceptions import DisallowedModelAdminToField
from django.contrib.admin.models import LogEntry, CHANGE
from django.contrib.admin.utils import quote, unquote, get_deleted_objects
from django.contrib.admin.templatetags.admin_urls import add_preserved_filters
from django.contrib.contenttypes.models import ContentType
from django.db import transaction
from django.db.models.fields import DecimalField
from django.forms.widgets import NumberInput
from django.http import HttpResponseRedirect, Http404
from django.shortcuts import render
from django.template.response import TemplateResponse
from django.urls import reverse
from django.utils import six
from django.utils.encoding import force_text
from django.utils.html import escape, escapejs, format_html
from django.utils.http import urlquote
from django.utils.safestring import mark_safe
from django.utils.translation import ugettext_lazy as _
from django.utils.text import capfirst
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_protect
from django.utils.encoding import smart_text

from freppledb.common.models import Comment


csrf_protect_m = method_decorator(csrf_protect)


class MultiDBModelAdmin(admin.ModelAdmin):
  r'''
  This class is an enhanced version of the django regular admin model.
  It adds:
     - support for multiple databases
          - store and load history information in the right database
          - assure prefix is maintained in the URLs
          - check for related objects in the right database
     - support for changing the primary key of an object
     - different logic to determine the next page to display

  See the standard code in the file django\contrib\admin\options.py
  The level of customization is relatively high, and this code is a bit of a
  concern for future upgrades of Django...
  '''

  formfield_overrides = {
    # Django by default uses the value of decimal_places to compute a step.
    # We prefer to stick to a default step of 1.
    DecimalField: {'widget': NumberInput(attrs={'step': '1'})}
    }

  def get_urls(self):
    def wrap(view):
      def wrapper(*args, **kwargs):
        return self.admin_site.admin_view(view)(*args, **kwargs)
      return update_wrapper(wrapper, view)

    urls = super().get_urls()
    my_urls = [
      url(r'^(.+)/comment/$', wrap(self.comment_view), name='%s_%s_comment' % (self.model._meta.app_label, self.model._meta.model_name)),
      ]
    return my_urls + urls


  def save_form(self, request, form, change):
    # Execute the standard behavior
    obj = super().save_form(request, form, change)
    # FrePPLe specific addition
    if change:
      path = request.path_info.rsplit("/", 3)
      if path[-2] == 'change':
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
    return super().formfield_for_foreignkey(db_field, request=request, using=request.database, **kwargs)


  def formfield_for_manytomany(self, db_field, request=None, **kwargs):
    # Tell Django to get objects from the 'other' database.
    return super().formfield_for_manytomany(db_field, request=request, using=request.database, **kwargs)


  def log_addition(self, request, obj, message):
    """
    Log that an object has been successfully added.
    """
    from django.contrib.admin.models import ADDITION
    entry = LogEntry(
      user_id=request.user.pk,
      content_type_id=ContentType.objects.get_for_model(obj).pk,
      object_id=obj.pk,
      object_repr=force_text(obj)[:200],
      action_flag=ADDITION,
      change_message=message if isinstance(message, str) else json.dumps(message)
    )
    entry.save(using=request.database)
    return entry


  def log_change(self, request, obj, message):
    """
    Log that an object has been successfully changed.
    """
    if hasattr(obj, 'new_pk'):
      # We are renaming an existing object.
      # a) Save the new record in the right database
      old_pk = obj.pk
      obj.pk = obj.new_pk
      obj.save(using=request.database)
      # b) All linked fields need updating.
      for related in obj._meta.get_fields():
        if (related.one_to_many or related.one_to_one) and related.auto_created and not related.concrete:
          related.related_model._base_manager.using(request.database) \
            .filter(**{related.field.name: old_pk}) \
            .update(**{related.field.name: obj})
      # c) Move the comments and audit trail to the new key
      model_type = ContentType.objects.get_for_model(obj)
      Comment.objects.using(request.database) \
        .filter(content_type__pk=model_type.id, object_pk=old_pk) \
        .update(object_pk=obj.pk)
      LogEntry.objects.using(request.database) \
        .filter(content_type__pk=model_type.id, object_id=old_pk) \
        .update(object_id=obj.pk)
      # d) Delete the old record
      obj.pk = old_pk
      obj.delete(using=request.database)
      obj.pk = obj.new_pk
    entry = LogEntry(
      user_id=request.user.pk,
      content_type_id=ContentType.objects.get_for_model(obj).pk,
      object_id=smart_text(obj.pk),
      object_repr=force_text(obj)[:200],
      action_flag=CHANGE,
      change_message=message if isinstance(message, str) else json.dumps(message)
      )
    entry.save(using=request.database)
    return entry


  def log_deletion(self, request, obj, object_repr):
    """
        Log that an object will be deleted. Note that this method is called
        before the deletion.
    """
    from django.contrib.admin.models import DELETION
    entry = LogEntry(
      user_id=request.user.id,
      content_type_id=ContentType.objects.get_for_model(self.model).pk,
      object_id=smart_text(obj.pk),
      object_repr=force_text(object_repr)[:200],
      action_flag=DELETION
    )
    entry.save(using=request.database)
    return entry


  def history_view(self, request, object_id, extra_context=None):
    "The 'history' admin view for this model."
    # First check if the user can see this history.
    model = self.model
    obj = self.get_object(request, unquote(object_id))
    if obj is None:
        return self._get_obj_does_not_exist_redirect(request, model._meta, object_id)

    if not self.has_change_permission(request, obj):
        raise PermissionDenied

    # Then get the history for this object.
    opts = model._meta
    app_label = opts.app_label
    action_list = LogEntry.objects.using(request.database).filter(
        object_id=unquote(object_id),
        content_type=get_content_type_for_model(model)
    ).select_related().order_by('action_time')

    context = dict(
        self.admin_site.each_context(request),
        # Translators: Translation included with Django
        title=force_text(opts.verbose_name) + " " + unquote(object_id),
        post_title=_('Change history'),
        action_list=action_list,
        module_name=capfirst(force_text(opts.verbose_name_plural)),
        object=obj,
        object_id=object_id,
        opts=opts,
        active_tab='history',
        preserved_filters=self.get_preserved_filters(request),
    )
    context.update(extra_context or {})

    request.current_app = self.admin_site.name

    return TemplateResponse(request, self.object_history_template or [
        "admin/%s/%s/object_history.html" % (app_label, opts.model_name),
        "admin/%s/object_history.html" % app_label,
        "admin/object_history.html"
    ], context)


  def response_add(self, request, obj, post_url_continue=None):
    """
    Determines the HttpResponse for the add_view stage.
    """
    opts = obj._meta
    pk_value = obj._get_pk_val()
    preserved_filters = self.get_preserved_filters(request)
    obj_url = request.prefix + reverse(
        'admin:%s_%s_change' % (opts.app_label, opts.model_name),
        args=(quote(pk_value),),
        current_app=self.admin_site.name,
    )
    # Add a link to the object's change form if the user can edit the obj.
    if self.has_change_permission(request, obj):
        obj_repr = format_html('<a href="{}">{}</a>', urlquote(obj_url), obj)
    else:
        obj_repr = force_text(obj)
    msg_dict = {
        'name': force_text(opts.verbose_name),
        'obj': obj_repr,
    }
    # Here, we distinguish between different save types by checking for
    # the presence of keys in request.POST.

    if '_popup' in request.POST:
        to_field = request.POST.get('_to_field')
        if to_field:
            attr = str(to_field)
        else:
            attr = obj._meta.pk.attname
        value = obj.serializable_value(attr)
        popup_response_data = json.dumps({
            'value': six.text_type(value),
            'obj': six.text_type(obj),
        })
        return TemplateResponse(request, self.popup_response_template or [
            'admin/%s/%s/popup_response.html' % (opts.app_label, opts.model_name),
            'admin/%s/popup_response.html' % opts.app_label,
            'admin/popup_response.html',
        ], {
            'popup_response_data': popup_response_data,
        })

    elif "_continue" in request.POST or (
            # Redirecting after "Save as new".
            "_saveasnew" in request.POST and self.save_as_continue and
            self.has_change_permission(request, obj)
    ):
        msg = format_html(
          # Translators: Translation included with Django
          _('The {name} "{obj}" was added successfully. You may edit it again below.'),
          **msg_dict
        )
        self.message_user(request, msg, messages.SUCCESS)
        if post_url_continue is None:
            post_url_continue = obj_url
        post_url_continue = add_preserved_filters(
            {'preserved_filters': preserved_filters, 'opts': opts},
            post_url_continue
        )
        return HttpResponseRedirect(post_url_continue)

    elif "_addanother" in request.POST:
        msg = format_html(
          # Translators: Translation included with Django
          _('The {name} "{obj}" was added successfully. You may add another {name} below.'),
          **msg_dict
        )
        self.message_user(request, msg, messages.SUCCESS)
        redirect_url = request.prefix + request.path
        redirect_url = add_preserved_filters({'preserved_filters': preserved_filters, 'opts': opts}, redirect_url)
        return HttpResponseRedirect(redirect_url)

    else:
        msg = format_html(
            # Translators: Translation included with Django
            _('The {name} "{obj}" was added successfully.'),
            **msg_dict
        )
        self.message_user(request, msg, messages.SUCCESS)
        return self.response_post_save_add(request, obj)


  def response_post_save_add(self, request, obj):
    """
    Figure out where to redirect after the 'Save' button has been pressed
    when adding a new object.
    """
    opts = self.model._meta
    if self.has_change_permission(request, None):
        post_url = request.prefix + reverse('admin:%s_%s_changelist' %
                           (opts.app_label, opts.model_name),
                           current_app=self.admin_site.name)
        preserved_filters = self.get_preserved_filters(request)
        post_url = add_preserved_filters({'preserved_filters': preserved_filters, 'opts': opts}, post_url)
    else:
        post_url = request.prefix
    return HttpResponseRedirect(post_url)


  def response_change(self, request, obj):
    """
    Determines the HttpResponse for the change_view stage.
    """

    if '_popup' in request.POST:
        opts = obj._meta
        to_field = request.POST.get('_to_field')
        attr = str(to_field) if to_field else opts.pk.attname
        # Retrieve the `object_id` from the resolved pattern arguments.
        value = request.resolver_match.args[0]
        new_value = obj.serializable_value(attr)
        popup_response_data = json.dumps({
            'action': 'change',
            'value': six.text_type(value),
            'obj': six.text_type(obj),
            'new_value': six.text_type(new_value),
        })
        return TemplateResponse(request, self.popup_response_template or [
            'admin/%s/%s/popup_response.html' % (opts.app_label, opts.model_name),
            'admin/%s/popup_response.html' % opts.app_label,
            'admin/popup_response.html',
        ], {
            'popup_response_data': popup_response_data,
        })

    opts = self.model._meta
    pk_value = obj._get_pk_val()
    preserved_filters = self.get_preserved_filters(request)

    msg_dict = {
        'name': force_text(opts.verbose_name),
        'obj': format_html('<a href="{}">{}</a>', urlquote(request.path), obj),
    }
    if "_continue" in request.POST:
        msg = format_html(
            # Translators: Translation included with Django
            _('The {name} "{obj}" was changed successfully. You may edit it again below.'),
            **msg_dict
        )
        self.message_user(request, msg, messages.SUCCESS)
        redirect_url = request.prefix + request.path
        redirect_url = add_preserved_filters({'preserved_filters': preserved_filters, 'opts': opts}, redirect_url)
        return HttpResponseRedirect(redirect_url)

    elif "_saveasnew" in request.POST:
        msg = format_html(
            # Translators: Translation included with Django
            _('The {name} "{obj}" was added successfully. You may edit it again below.'),
            **msg_dict
        )
        self.message_user(request, msg, messages.SUCCESS)
        redirect_url = request.prefix + reverse('admin:%s_%s_change' %
                               (opts.app_label, opts.model_name),
                               args=(pk_value,),
                               current_app=self.admin_site.name)
        redirect_url = add_preserved_filters({'preserved_filters': preserved_filters, 'opts': opts}, redirect_url)
        return HttpResponseRedirect(redirect_url)

    elif "_addanother" in request.POST:
        msg = format_html(
            # Translators: Translation included with Django
            _('The {name} "{obj}" was changed successfully. You may add another {name} below.'),
            **msg_dict
        )
        self.message_user(request, msg, messages.SUCCESS)
        redirect_url = request.prefix + reverse('admin:%s_%s_add' %
                               (opts.app_label, opts.model_name),
                               current_app=self.admin_site.name)
        redirect_url = add_preserved_filters({'preserved_filters': preserved_filters, 'opts': opts}, redirect_url)
        return HttpResponseRedirect(redirect_url)

    else:
        msg = format_html(
            # Translators: Translation included with Django
            _('The {name} "{obj}" was changed successfully.'),
            **msg_dict
        )
        self.message_user(request, msg, messages.SUCCESS)
        return self.response_post_save_change(request, obj)


  def response_post_save_change(self, request, obj):
    """
    Figure out where to redirect after the 'Save' button has been pressed
    when editing an existing object.
    """
    opts = self.model._meta

    if self.has_change_permission(request, None):
        post_url = request.prefix + reverse('admin:%s_%s_changelist' %
                           (opts.app_label, opts.model_name),
                           current_app=self.admin_site.name)
        preserved_filters = self.get_preserved_filters(request)
        post_url = add_preserved_filters({'preserved_filters': preserved_filters, 'opts': opts}, post_url)
    else:
        post_url = request.prefix
    return HttpResponseRedirect(post_url)


  @csrf_protect_m
  @transaction.atomic
  def change_view(self, request, object_id, form_url='', extra_context=None):
    request.session['lasttab'] = 'edit'
    new_extra_context = extra_context or {}
    new_extra_context['title'] = force_text(self.model._meta.verbose_name) + ' ' + unquote(object_id)
    # Translators: Translation included with Django
    new_extra_context['post_title'] = _('edit')
    return super().change_view(request, object_id, form_url, new_extra_context)


  @csrf_protect_m
  @transaction.atomic
  def comment_view(self, request, object_id, extra_context=None):
    "The 'comment' view for this model."
    request.session['lasttab'] = 'comments'
    try:
      modeltype = ContentType.objects.using(request.database).get(
        app_label=self.model._meta.app_label,
        model=self.model._meta.model_name
        )
      modeltype._state.db = request.database
      object_id = unquote(object_id)
      modelinstance = modeltype.get_object_for_this_type(pk=object_id)
      comments = Comment.objects.using(request.database) \
        .filter(content_type__pk=modeltype.id, object_pk=object_id) \
        .order_by('-id')
    except:
      raise Http404('Object not found')
    if request.method == 'POST':
      if request.user.has_perm("common.add_comment"):
        comment = request.POST['comment']
        if comment:
          Comment(
               content_object=modelinstance,
               user=request.user,
               comment=comment
               ).save(using=request.database)
      return HttpResponseRedirect('%s%s' % (
        request.prefix, request.path
        ))
    else:
      return render(request, 'common/comments.html',
        context = {
          'title': force_text(modelinstance._meta.verbose_name) + " " + object_id,
          'post_title': _('comments'),
          'model': self.model._meta.model_name,
          'opts': self.model._meta,
          'object_id': quote(object_id),
          'active_tab': 'comments',
          'comments': comments
          }
        )


  def response_delete(self, request, obj_display, obj_id):
    """
    Determines the HttpResponse for the delete_view stage.
    """

    opts = self.model._meta

    if '_popup' in request.POST:
        popup_response_data = json.dumps({
            'action': 'delete',
            'value': str(obj_id),
        })
        return TemplateResponse(request, self.popup_response_template or [
            'admin/%s/%s/popup_response.html' % (opts.app_label, opts.model_name),
            'admin/%s/popup_response.html' % opts.app_label,
            'admin/popup_response.html',
        ], {
            'popup_response_data': popup_response_data,
        })

    self.message_user(
        request,
        # Translators: Translation included with Django
        _('The %(name)s "%(obj)s" was deleted successfully.') % {
            'name': force_text(opts.verbose_name),
            'obj': force_text(obj_display),
        },
        messages.SUCCESS,
    )

    # Delete this entity page from the crumbs
    del request.session['crumbs'][request.prefix][-1]

    # Redirect to previous url
    return HttpResponseRedirect("%s%s" % (request.prefix, request.session['crumbs'][request.prefix][-1][2]))



  @csrf_protect_m
  def delete_view(self, request, object_id, extra_context=None):
    with transaction.atomic(using=request.database):
      return self._delete_view(request, object_id, extra_context)


  def _delete_view(self, request, object_id, extra_context):
    """
    The 'delete' admin view for this model.
    """
    opts = self.model._meta
    app_label = opts.app_label

    to_field = request.POST.get('_to_field', request.GET.get('_to_field'))
    if to_field and not self.to_field_allowed(request, to_field):
        raise DisallowedModelAdminToField("The field %s cannot be referenced." % to_field)

    obj = self.get_object(request, unquote(object_id))

    if not self.has_delete_permission(request, obj):
      raise PermissionDenied

    if obj is None:
      return self._get_obj_does_not_exist_redirect(request, opts, object_id)

    # frePPLe specific selection of the database
    using = request.database

    # Populate deleted_objects, a data structure of all related objects that
    # will also be deleted.
    (deleted_objects, model_count, perms_needed, protected) = get_deleted_objects(
      [obj], opts, request.user, self.admin_site, using
      )

    # Update the links to the related objects.  frePPLe specific.
    if request.prefix:
      def replace_url(a):
        if isinstance(a, list):
          return [ replace_url(i) for i in a ]
        else:
          return mark_safe(a.replace('href="', 'href="%s' % request.prefix))
      deleted_objects = [ replace_url(i) for i in deleted_objects ]
      protected = [ replace_url(i) for i in protected ]

    if request.POST and not protected:  # The user has confirmed the deletion.
      if perms_needed:
        raise PermissionDenied
      obj_display = force_text(obj)
      attr = str(to_field) if to_field else opts.pk.attname
      obj_id = obj.serializable_value(attr)
      self.log_deletion(request, obj, obj_display)
      self.delete_model(request, obj)

      return self.response_delete(request, obj_display, obj_id)

    object_name = force_text(opts.verbose_name)

    context = dict(
      self.admin_site.each_context(request),
      title=capfirst(object_name + ' ' + unquote(object_id)),
      object_name=object_name,
      object=obj,
      object_id=obj,
      deleted_objects=deleted_objects,
      model_count=dict(model_count).items(),
      perms_lacking=perms_needed,
      protected=protected,
      opts=opts,
      app_label=app_label,
      preserved_filters=self.get_preserved_filters(request),
      is_popup=('_popup' in request.POST or
                '_popup' in request.GET),
      to_field=to_field,
      )
    context.update(extra_context or {})

    return self.render_delete_form(request, context)


class MultiDBTabularInline(admin.TabularInline):

  def __init__(self, parent_model, admin_site):
    super(MultiDBTabularInline, self).__init__(parent_model, admin_site)

  def get_queryset(self, request):
    return super(MultiDBTabularInline, self).get_queryset(request).using(request.database)

  def formfield_for_foreignkey(self, db_field, request=None, **kwargs):
    return super(MultiDBTabularInline, self).formfield_for_foreignkey(db_field, request=request, using=request.database, **kwargs)

  def formfield_for_manytomany(self, db_field, request=None, **kwargs):
    return super(MultiDBTabularInline, self).formfield_for_manytomany(db_field, request=request, using=request.database, **kwargs)
