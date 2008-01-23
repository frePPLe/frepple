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


from django.db import models
from django.utils.translation import ugettext_lazy as _


class log(models.Model):
  # Database fields
  lastmodified = models.DateTimeField(_('last modified'), auto_now=True, editable=False, db_index=True)
  category = models.CharField(_('category'), max_length=10, db_index=True)
  message = models.TextField(_('message'), max_length=200, null=True)
  user = models.CharField(_('user'), max_length=30, null=True)

  def __unicode__(self):
    return self.lastmodified + ' - ' + self.category + ' - ' + self.user

  class Meta:
      permissions = (
          ("run_frepple", "Can run frepple"),
          ("run_db","Can run database procedures"),
          ("upload_csv","Can upload csv data files"),
         )
      verbose_name_plural = _('log entries')
      verbose_name = _('log entry')
