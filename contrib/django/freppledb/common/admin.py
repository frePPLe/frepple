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

from django.contrib.auth.models import User, Group
from django.contrib.auth.admin import UserAdmin, GroupAdmin
from django.contrib import admin

from common.models import *
from freppledb.admin import site


# Register the models from the Auth application.
# The admin users can then create, change and delete users and user groups.
site.register(Group, GroupAdmin)
site.register(User, UserAdmin)


class Dates_admin(admin.ModelAdmin):
  model = Dates
  fieldsets = (
      (None, {'fields': (('day','day_start','day_end'),
                         'dayofweek',
                         ('week','week_start','week_end'),
                         ('month','month_start','month_end'),
                         ('quarter','quarter_start','quarter_end'),
                         ('year','year_start','year_end'),
                         ('standard','standard_start','standard_end'),
                         )}),
      )
site.register(Dates,Dates_admin)
