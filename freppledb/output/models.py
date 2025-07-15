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

from django.utils.translation import gettext_lazy as _
from django.db import models


class Problem(models.Model):
    allow_report_manager_access = True

    # Database fields
    entity = models.CharField(_("entity"), max_length=15, db_index=True)
    owner = models.CharField(_("owner"), max_length=300, db_index=True)
    name = models.CharField(_("name"), max_length=20, db_index=True)
    description = models.CharField(_("description"), max_length=1000)
    startdate = models.DateTimeField(_("start date"), db_index=True)
    enddate = models.DateTimeField(_("end date"), db_index=True)
    weight = models.DecimalField(_("weight"), max_digits=20, decimal_places=8)

    def __str__(self):
        return str(self.description)

    class Meta:
        db_table = "out_problem"
        ordering = ["startdate"]
        verbose_name = _("problem")
        verbose_name_plural = _("problems")
        default_permissions = []


class Constraint(models.Model):
    allow_report_manager_access = True

    # Database fields
    demand = models.CharField(_("demand"), max_length=300, null=True, db_index=True)
    forecast = models.CharField(_("forecast"), max_length=300, null=True, db_index=True)
    item = models.CharField(_("item"), max_length=300, null=True, db_index=True)
    entity = models.CharField(_("entity"), max_length=15, db_index=True)
    owner = models.CharField(_("owner"), max_length=300, db_index=True)
    name = models.CharField(_("name"), max_length=20, db_index=True)
    description = models.CharField(_("description"), max_length=1000)
    startdate = models.DateTimeField(_("start date"), db_index=True)
    enddate = models.DateTimeField(_("end date"), db_index=True)
    weight = models.DecimalField(_("weight"), max_digits=20, decimal_places=8)

    def __str__(self):
        return str(self.demand) + " " + str(self.description)

    class Meta:
        db_table = "out_constraint"
        ordering = ["item", "startdate"]
        verbose_name = _("constraint")
        verbose_name_plural = _("constraints")
        default_permissions = []


class ResourceSummary(models.Model):
    allow_report_manager_access = True

    resource = models.CharField(_("resource"), max_length=300)
    startdate = models.DateTimeField(_("startdate"))
    available = models.DecimalField(
        _("available"), max_digits=20, decimal_places=8, null=True
    )
    unavailable = models.DecimalField(
        _("unavailable"), max_digits=20, decimal_places=8, null=True
    )
    setup = models.DecimalField(_("setup"), max_digits=20, decimal_places=8, null=True)
    load = models.DecimalField(_("load"), max_digits=20, decimal_places=8, null=True)
    free = models.DecimalField(_("free"), max_digits=20, decimal_places=8, null=True)
    load_confirmed = models.DecimalField(_("confirmed load"), max_digits=20, decimal_places=8, null=True)

    class Meta:
        db_table = "out_resourceplan"
        ordering = ["resource", "startdate"]
        unique_together = (("resource", "startdate"),)
        verbose_name = (
            "resource summary"  # No need to translate these since only used internally
        )
        verbose_name_plural = "resource summaries"
        default_permissions = []
