#
# Copyright (C) 2019 by frePPLe bvba
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

from django.db import models
from django.utils.translation import gettext as _

from freppledb.common.models import AuditModel, User


class SQLReport(AuditModel):
    id = models.AutoField(_("identifier"), primary_key=True)
    name = models.CharField(_("name"), max_length=300, db_index=True)
    sql = models.TextField(_("SQL query"), null=True, blank=True)
    description = models.CharField(
        _("description"), max_length=1000, null=True, blank=True
    )
    user = models.ForeignKey(
        User,
        # Translators: Translation included with Django
        verbose_name=_("user"),
        blank=False,
        null=True,
        editable=False,
        related_name="reports",
        on_delete=models.CASCADE,
    )
    public = models.BooleanField(blank=True, default=False)
