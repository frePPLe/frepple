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


# Make our tags built-in, so we don't have to load them any more in our
# templates with a 'load' tag.
template.add_to_builtins('common.templatetags.base_utils')
 

class MultiDBModelAdmin(admin.ModelAdmin):

  def save_model(self, request, obj, form, change):
    # Tell Django to save objects to the 'other' database.
    obj.save(using=request.database)

  def queryset(self, request):
    return super(MultiDBModelAdmin, self).queryset(request).using(request.database)

  def formfield_for_foreignkey(self, db_field, request=None, **kwargs):
    return super(MultiDBModelAdmin, self).formfield_for_foreignkey(db_field, request=request, using=request.database, **kwargs)

  def formfield_for_manytomany(self, db_field, request=None, **kwargs):
    return super(MultiDBModelAdmin, self).formfield_for_manytomany(db_field, request=request, using=request.database, **kwargs)

  # TODO def response_add(self, request, obj, post_url_continue='../%s/'):
  # TODO def response_change(self, request, obj):
  # TODO log_addition
  # TODO log_change
  # TODO log_deletion
        

class MultiDBTabularInline(admin.TabularInline):

  def queryset(self, request):
    return super(MultiDBTabularInline, self).queryset(request).using(request.database)

  def formfield_for_foreignkey(self, db_field, request=None, **kwargs):
    return super(MultiDBTabularInline, self).formfield_for_foreignkey(db_field, request=request, using=request.database, **kwargs)

  def formfield_for_manytomany(self, db_field, request=None, **kwargs):
    return super(MultiDBTabularInline, self).formfield_for_manytomany(db_field, request=request, using=request.database, **kwargs)
  