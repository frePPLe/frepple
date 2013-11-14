#
# Copyright (C) 2007-2012 by Johan De Taeye, frePPLe bvba
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

import warnings, types

from django.core.exceptions import PermissionDenied
from django.core.urlresolvers import reverse
from django.contrib import admin
from django.contrib import messages
from django.contrib.admin.models import LogEntry, CHANGE
from django.contrib.admin.util import unquote, get_deleted_objects
from django.contrib.admin.templatetags.admin_urls import add_preserved_filters
from django.contrib.contenttypes.models import ContentType
from django.db import transaction
from django.http import HttpResponse, HttpResponseRedirect, Http404
from django.shortcuts import get_object_or_404, render_to_response
from django.template.response import SimpleTemplateResponse, TemplateResponse
from django.utils.encoding import force_text, force_unicode, iri_to_uri
from django.utils.safestring import mark_safe
from django.utils.html import escape, escapejs
from django.utils.translation import ugettext_lazy as _
from django.utils.text import capfirst, get_text_list
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

  def save_form(self, request, form, change):
    # Execute the standard behavior
    obj = super(MultiDBModelAdmin, self).save_form(request, form, change)
    # FrePPLe specific addition
    if change:
      old_pk = unquote(request.path_info.rsplit("/",2)[1])
      if old_pk != (isinstance(obj.pk,basestring) and obj.pk or str(obj.pk)):
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
    return super(MultiDBModelAdmin, self).get_queryset(request).using(request.database)

  def formfield_for_foreignkey(self, db_field, request=None, **kwargs):
    # Tell Django to get objects from the 'other' database.
    return super(MultiDBModelAdmin, self).formfield_for_foreignkey(db_field, request=request, using=request.database, **kwargs)

  def formfield_for_manytomany(self, db_field, request=None, **kwargs):
    # Tell Django to get objects from the 'other' database.
    return super(MultiDBModelAdmin, self).formfield_for_manytomany(db_field, request=request, using=request.database, **kwargs)

  def log_addition(self, request, obj):
    """
    Log that an object has been successfully added.
    """
    from django.contrib.admin.models import ADDITION
    LogEntry(
        user_id         = request.user.pk,
        content_type_id = ContentType.objects.get_for_model(obj).pk,
        object_id       = smart_text(obj.pk),
        object_repr     = force_text(obj)[:200],
        action_flag     = ADDITION
    ).save(using=request.database)

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
      for related in obj._meta.get_all_related_objects():
        related.model._base_manager.using(request.database) \
          .filter(**{related.field.name: old_pk}) \
          .update(**{related.field.name: obj})
      # c) Move the comments and audit trail to the new key
      model_type = ContentType.objects.get_for_model(obj)
      Comment.objects.using(request.database). \
        filter(content_type__pk=model_type.id, object_pk=old_pk). \
        update(object_pk=obj.pk)
      LogEntry.objects.using(request.database). \
        filter(content_type__pk=model_type.id, object_id=old_pk). \
        update(object_id=obj.pk)
      # e) Delete the old record
      self.queryset(request).get(pk=old_pk).delete()
    LogEntry(
        user_id         = request.user.pk,
        content_type_id = ContentType.objects.get_for_model(obj).pk,
        object_id       = smart_text(obj.pk),
        object_repr     = force_text(obj)[:200],
        action_flag     = CHANGE,
        change_message  = message
    ).save(using=request.database)

  def log_deletion(self, request, obj, object_repr):
    """
        Log that an object will be deleted. Note that this method is called
        before the deletion.
    """
    from django.contrib.admin.models import DELETION
    LogEntry(
        user_id         = request.user.id,
        content_type_id = ContentType.objects.get_for_model(self.model).pk,
        object_id       = smart_text(obj.pk),
        object_repr     = force_text(object_repr)[:200],
        action_flag     = DELETION
    ).save(using=request.database)

  def history_view(self, request, object_id, extra_context=None):
    "The 'history' admin view for this model."
    # First check if the object exists and the user can see its history.
    model = self.model
    obj = get_object_or_404(model.objects.using(request.database), pk=unquote(object_id))
    if not self.has_change_permission(request, obj):
        raise PermissionDenied

    # Then get the history for this object.
    opts = model._meta
    app_label = opts.app_label
    action_list = LogEntry.objects.using(request.database).filter(
      object_id = unquote(object_id),
      content_type__id__exact = ContentType.objects.get_for_model(model).id
    ).select_related().order_by('action_time')
    context = {
      'title': capfirst(force_text(opts.verbose_name) + " " + object_id),
      'action_list': action_list,
      'module_name': capfirst(force_text(opts.verbose_name_plural)),
      'object': obj,
      'app_label': app_label,
      'opts': opts,
      'active_tab': 'history',
      'object_id': object_id,
      'model': ContentType.objects.get_for_model(model).model,
    }
    context.update(extra_context or {})
    return TemplateResponse(request, self.object_history_template or [
            "admin/%s/%s/object_history.html" % (app_label, opts.model_name),
            "admin/%s/object_history.html" % app_label,
            "admin/object_history.html"
        ], context, current_app=self.admin_site.name)

  def response_add(self, request, obj, post_url_continue=None):
    """
    Determines the HttpResponse for the add_view stage.
    """
    opts = obj._meta
    pk_value = obj._get_pk_val()
    preserved_filters = self.get_preserved_filters(request)

    msg_dict = {'name': force_text(opts.verbose_name), 'obj': force_text(obj)}
    # Here, we distinguish between different save types by checking for
    # the presence of keys in request.POST.
    if "_popup" in request.POST:
        return SimpleTemplateResponse('admin/popup_response.html', {
            'pk_value': escape(pk_value),
            'obj': escapejs(obj)
        })

    elif "_continue" in request.POST:
      msg = _('The %(name)s "%(obj)s" was added successfully. You may edit it again below.') % msg_dict
      self.message_user(request, msg, messages.SUCCESS)
      if post_url_continue is None:
        post_url_continue = request.prefix + reverse('admin:%s_%s_change' %
            (opts.app_label, opts.model_name),
            args=(pk_value,),
            current_app=self.admin_site.name)
      post_url_continue = add_preserved_filters({'preserved_filters': preserved_filters, 'opts': opts}, post_url_continue)
      return HttpResponseRedirect(post_url_continue)

    elif "_addanother" in request.POST:
      msg = _('The %(name)s "%(obj)s" was added successfully. You may add another %(name)s below.') % msg_dict
      self.message_user(request, msg, messages.SUCCESS)
      redirect_url = request.prefix + request.path
      redirect_url = add_preserved_filters({'preserved_filters': preserved_filters, 'opts': opts}, redirect_url)
      return HttpResponseRedirect(redirect_url)

    else:
      msg = _('The %(name)s "%(obj)s" was added successfully.') % msg_dict
      self.message_user(request, msg, messages.SUCCESS)
      # Redirect to previous crumb
      return HttpResponseRedirect(request.session['crumbs'][request.prefix][-2][2])

  def response_change(self, request, obj):
    """
    Determines the HttpResponse for the change_view stage.
    """
    opts = self.model._meta
    pk_value = obj._get_pk_val()
    preserved_filters = self.get_preserved_filters(request)

    msg_dict = {'name': force_text(opts.verbose_name), 'obj': force_text(obj)}
    if "_continue" in request.POST:
      msg = _('The %(name)s "%(obj)s" was changed successfully. You may edit it again below.') % msg_dict
      self.message_user(request, msg, messages.SUCCESS)
      redirect_url = request.prefix + request.path
      redirect_url = add_preserved_filters({'preserved_filters': preserved_filters, 'opts': opts}, redirect_url)
      return HttpResponseRedirect(redirect_url)

    elif "_saveasnew" in request.POST:
      msg = _('The %(name)s "%(obj)s" was added successfully. You may edit it again below.') % msg_dict
      self.message_user(request, msg, messages.SUCCESS)
      redirect_url = request.prefix + reverse('admin:%s_%s_change' %
                             (opts.app_label, opts.model_name),
                             args=(pk_value,),
                             current_app=self.admin_site.name)
      redirect_url = add_preserved_filters({'preserved_filters': preserved_filters, 'opts': opts}, redirect_url)
      return HttpResponseRedirect(redirect_url)

    elif "_addanother" in request.POST:
      msg = _('The %(name)s "%(obj)s" was changed successfully. You may add another %(name)s below.') % msg_dict
      self.message_user(request, msg, messages.SUCCESS)
      redirect_url = request.prefix + reverse('admin:%s_%s_add' %
                             (opts.app_label, opts.model_name),
                             current_app=self.admin_site.name)
      redirect_url = add_preserved_filters({'preserved_filters': preserved_filters, 'opts': opts}, redirect_url)
      return HttpResponseRedirect(redirect_url)

    else:
      msg = _('The %(name)s "%(obj)s" was changed successfully.') % msg_dict
      self.message_user(request, msg, messages.SUCCESS)
      # Redirect to previous crumb
      return HttpResponseRedirect(request.session['crumbs'][request.prefix][-2][2])


  @csrf_protect_m
  @transaction.atomic
  def change_view(self, request, object_id, form_url='', extra_context=None):
    new_extra_context = extra_context or {}
    new_extra_context['title'] = capfirst(force_unicode(self.model._meta.verbose_name) + ' ' + unquote(object_id))
    return super(MultiDBModelAdmin, self).change_view(request, object_id, form_url, new_extra_context)


  @csrf_protect_m
  @transaction.atomic
  def delete_view(self, request, object_id, extra_context=None):
    "The 'delete' admin view for this model."
    opts = self.model._meta
    app_label = opts.app_label

    obj = self.get_object(request, unquote(object_id))

    if not self.has_delete_permission(request, obj):
      raise PermissionDenied

    if obj is None:
      raise Http404(_('%(name)s object with primary key %(key)r does not exist.') % {'name': force_text(opts.verbose_name), 'key': escape(object_id)})

    # frePPLe specific selection of the database
    using = request.database

    # Populate deleted_objects, a data structure of all related objects that
    # will also be deleted.
    (deleted_objects, perms_needed, protected) = get_deleted_objects(
       [obj], opts, request.user, self.admin_site, using)

    # Update the links to the related objects. A bit of a hack...
    if request.prefix:
      def replace_url(a):
        if isinstance(a, types.ListType):
          return [ replace_url(i) for i in a ]
        else:
          return mark_safe(a.replace('href="','href="%s' % request.prefix))
      deleted_objects = [ replace_url(i) for i in deleted_objects ]
      protected = [ replace_url(i) for i in protected ]
    print deleted_objects

    if request.POST: # The user has already confirmed the deletion.
      if perms_needed:
        raise PermissionDenied
      obj_display = force_text(obj)
      self.log_deletion(request, obj, obj_display)
      self.delete_model(request, obj)

      self.message_user(request, _('The %(name)s "%(obj)s" was deleted successfully.') % {'name': force_text(opts.verbose_name), 'obj': force_text(obj_display)})

      # Redirect to previous crumb
      return HttpResponseRedirect(request.session['crumbs'][request.prefix][-3][2])

    object_name = force_text(opts.verbose_name)

    context = {
        "title": capfirst(object_name + ' ' + unquote(object_id)),
        "object_name": object_name,
        "object": obj,
        "deleted_objects": deleted_objects,
        "perms_lacking": perms_needed,
        "protected": protected,
        "opts": opts,
        "app_label": app_label,
    }
    context.update(extra_context or {})

    return TemplateResponse(request, self.delete_confirmation_template or [
            "admin/%s/%s/delete_confirmation.html" % (app_label, opts.model_name),
            "admin/%s/delete_confirmation.html" % app_label,
            "admin/delete_confirmation.html"
        ], context, current_app=self.admin_site.name)

  # TODO: allow permissions per schema
  # def has_add_permission(self, request):
  # def has_change_permission(self, request, obj=None):
  # def has_delete_permission(self, request, obj=None):


class MultiDBTabularInline(admin.TabularInline):

  def __init__(self, parent_model, admin_site):
    super(MultiDBTabularInline, self).__init__(parent_model, admin_site)

  def get_queryset(self, request):
    return super(MultiDBTabularInline, self).get_queryset(request).using(request.database)

  def formfield_for_foreignkey(self, db_field, request=None, **kwargs):
    return super(MultiDBTabularInline, self).formfield_for_foreignkey(db_field, request=request, using=request.database, **kwargs)

  def formfield_for_manytomany(self, db_field, request=None, **kwargs):
    return super(MultiDBTabularInline, self).formfield_for_manytomany(db_field, request=request, using=request.database, **kwargs)

