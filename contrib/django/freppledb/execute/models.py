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

from django.db import models

# This variable defines the number of records to show in the admin lists.
LIST_PER_PAGE = 100


class log(models.Model):
  # Database fields
  category = models.CharField(maxlength=10, db_index=True)
  message = models.TextField(maxlength=200)
  lastmodified = models.DateTimeField(auto_now=True, editable=False, db_index=True)

  def __str__(self):
    return self.lastmodified + ' - ' + self.category

  def getTime(self):
    return str(self.lastmodified)
  getTime.short_description = 'Date and time'

  class Admin:
      list_display = ('getTime', 'category', 'message')
      search_fields = ['message']
      list_filter = ['category', 'lastmodified']
      list_per_page = LIST_PER_PAGE
      date_hierarchy = 'lastmodified'

  class Meta:
      permissions = (
          ("run_frepple", "Can run frepple"),
          ("run_db","Can run database procedures"),
          ("upload_csv","Can upload csv data files"),
         )
      verbose_name_plural = 'Log'  # Multiple logs entries are still called "a log"
