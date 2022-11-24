#
# Copyright (C) 2007-2013 by frePPLe bv
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
from django.utils.translation import gettext_lazy as _

from freppledb.common.models import HierarchyModel, AuditModel


class Item(AuditModel, HierarchyModel):
    types = (
        ("make to stock", _("make to stock")),
        ("make to order", _("make to order")),
    )

    # Database fields
    description = models.CharField(
        _("description"), max_length=500, null=True, blank=True
    )
    category = models.CharField(
        _("category"), max_length=300, null=True, blank=True, db_index=True
    )
    subcategory = models.CharField(
        _("subcategory"), max_length=300, null=True, blank=True, db_index=True
    )
    cost = models.DecimalField(
        _("cost"),
        null=True,
        blank=True,
        max_digits=20,
        decimal_places=8,
        help_text=_("Cost of the item"),
    )
    type = models.CharField(
        _("type"), max_length=20, null=True, blank=True, choices=types
    )
    weight = models.DecimalField(
        _("weight"),
        null=True,
        blank=True,
        max_digits=20,
        decimal_places=8,
        help_text=_("Weight of the item"),
    )
    volume = models.DecimalField(
        _("volume"),
        null=True,
        blank=True,
        max_digits=20,
        decimal_places=8,
        help_text=_("Volume of the item"),
    )
    periodofcover = models.IntegerField(
        _("period of cover"),
        null=True,
        blank=True,
        help_text=_("Period of cover in days"),
    )
    uom = models.CharField(_("unit of measure"), max_length=20, null=True, blank=True)

    def __str__(self):
        return self.name

    class Meta(AuditModel.Meta):
        db_table = "item"
        verbose_name = _("item")
        verbose_name_plural = _("items")
        ordering = ["name"]
