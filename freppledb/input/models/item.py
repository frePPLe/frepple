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

from django.db import models
from django.utils.translation import gettext_lazy as _

from freppledb.common.models import HierarchyModel, AuditModel, Parameter


class Item(AuditModel, HierarchyModel):
    types = (
        ("make to stock", _("make to stock")),
        ("make to order", _("make to order")),
    )

    # Database fields
    description = models.CharField(_("description"), null=True, blank=True)
    category = models.CharField(_("category"), null=True, blank=True, db_index=True)
    subcategory = models.CharField(
        _("subcategory"), null=True, blank=True, db_index=True
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
        _("type"), null=True, blank=True, choices=types
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
        editable=False,
    )
    uom = models.CharField(_("unit of measure"), null=True, blank=True)

    extra_dependencies = [
        Parameter,
    ]

    def __str__(self):
        return self.name

    class Meta(AuditModel.Meta):
        db_table = "item"
        verbose_name = _("item")
        verbose_name_plural = _("items")
        ordering = ["name"]
