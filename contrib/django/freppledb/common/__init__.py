#
# Copyright (C) 2007-2010 by Johan De Taeye
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
# Foundation Inc., 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301, USA
#

# file : $URL$
# revision : $LastChangedRevision$  $LastChangedBy$
# date : $LastChangedDate$

r'''
An reusable application that contains common functionality of different
frePPLe data models.

The common functionality handles:
  - user preferences: reporting buckets, report start and end dates, language, csv delimiter
  - breadcrumbs
  - login using the e-mail address
  - generic report framework
  - database utility functions, mainly to handle SQL dates in a portable way
  - date and time bucket definition
  - middelware allowing users to set their preferred language
'''

from django import template
from django.contrib import admin
from django.contrib.contenttypes.models import ContentType
from django.utils.encoding import force_unicode
from django.shortcuts import get_object_or_404, render_to_response
from django.contrib.admin.util import unquote

# Make our tags built-in, so we don't have to load them any more in our
# templates with a 'load' tag.
template.add_to_builtins('common.templatetags.base_utils')
 

class MultiDBModelAdmin(admin.ModelAdmin):
  r'''
  This class is an enhanced version of the django regular admin model.
  See the standard code in the file django\contrib\admin\options.py
  It adds:
     - support for multiple databases
     - different logic to determine the next page to display
  ''' 
  
  def save_model(self, request, obj, form, change):
    # Tell Django to save objects to the 'other' database.
    obj.save(using=request.database)

  def queryset(self, request):
    return super(MultiDBModelAdmin, self).queryset(request).using(request.database)

  def formfield_for_foreignkey(self, db_field, request=None, **kwargs):
    return super(MultiDBModelAdmin, self).formfield_for_foreignkey(db_field, request=request, using=request.database, **kwargs)

  def formfield_for_manytomany(self, db_field, request=None, **kwargs):
    return super(MultiDBModelAdmin, self).formfield_for_manytomany(db_field, request=request, using=request.database, **kwargs)

  def log_addition(self, request, object):
    """
    Log that an object has been successfully added.
    """
    from django.contrib.admin.models import LogEntry, ADDITION
    LogEntry(
        user_id         = request.user.pk,
        content_type_id = ContentType.objects.get_for_model(object).pk,
        object_id       = force_unicode(object.pk),
        object_repr     = force_unicode(object)[:200],
        action_flag     = ADDITION
    ).save(using=request.database)

  def log_change(self, request, object, message):
    """
    Log that an object has been successfully changed.
    """
    from django.contrib.admin.models import LogEntry, CHANGE
    LogEntry(
        user_id         = request.user.pk,
        content_type_id = ContentType.objects.get_for_model(object).pk,
        object_id       = force_unicode(object.pk),
        object_repr     = force_unicode(object)[:200],
        action_flag     = CHANGE,
        change_message  = message
    ).save(using=request.database)

  def log_deletion(self, request, object, object_repr):
    """
    Log that an object has been successfully deleted. Note that since the
    object is deleted, it might no longer be safe to call *any* methods
    on the object, hence this method getting object_repr.
    """
    from django.contrib.admin.models import LogEntry, DELETION
    LogEntry(
        user_id         = request.user.id,
        content_type_id = ContentType.objects.get_for_model(self.model).pk,
        object_id       = force_unicode(object.pk),
        object_repr     = object_repr[:200],
        action_flag     = DELETION
    ).save(using=request.database)

  def history_view(self, request, object_id, extra_context=None):
    "The 'history' admin view for this model."
    from django.contrib.admin.models import LogEntry
    model = self.model
    opts = model._meta
    app_label = opts.app_label
    action_list = LogEntry.objects.using(request.database).filter(
      object_id = object_id,
      content_type__id__exact = ContentType.objects.get_for_model(model).id
    ).select_related().order_by('action_time')
    # If no history was found, see whether this object even exists.
    obj = get_object_or_404(model, pk=unquote(object_id))
    context = {
      'title': _('Change history: %s') % force_unicode(obj),
      'action_list': action_list,
      'module_name': capfirst(force_unicode(opts.verbose_name_plural)),
      'object': obj,
      'root_path': self.admin_site.root_path,
      'app_label': app_label,
    }
    context.update(extra_context or {})
    context_instance = template.RequestContext(request, current_app=self.admin_site.name)
    return render_to_response(self.object_history_template or [
      "admin/%s/%s/object_history.html" % (app_label, opts.object_name.lower()),
      "admin/%s/object_history.html" % app_label,
      "admin/object_history.html"
    ], context, context_instance=context_instance)
      
  # TODO def response_add(self, request, obj, post_url_continue='../%s/'):
  # TODO def response_change(self, request, obj):
        
  # TODO: allow permissions per schema
  # def has_add_permission(self, request):
  # def has_change_permission(self, request, obj=None):
  # def has_delete_permission(self, request, obj=None):


class MultiDBTabularInline(admin.TabularInline):

  def queryset(self, request):
    return super(MultiDBTabularInline, self).queryset(request).using(request.database)

  def formfield_for_foreignkey(self, db_field, request=None, **kwargs):
    return super(MultiDBTabularInline, self).formfield_for_foreignkey(db_field, request=request, using=request.database, **kwargs)

  def formfield_for_manytomany(self, db_field, request=None, **kwargs):
    return super(MultiDBTabularInline, self).formfield_for_manytomany(db_field, request=request, using=request.database, **kwargs)
  