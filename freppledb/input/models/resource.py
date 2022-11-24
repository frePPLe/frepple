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
from django.utils.text import format_lazy
from django.utils.translation import gettext_lazy as _

from freppledb.common.models import HierarchyModel, AuditModel, MultiDBManager

from .calendar import Calendar
from .location import Location


class SetupMatrix(AuditModel):
    # Database fields
    name = models.CharField(_("name"), max_length=300, primary_key=True)

    # Methods
    def __str__(self):
        return self.name

    class Meta(AuditModel.Meta):
        db_table = "setupmatrix"
        verbose_name = _("setup matrix")
        verbose_name_plural = _("setup matrices")
        ordering = ["name"]


class Resource(AuditModel, HierarchyModel):
    # Types of resources.
    # The predefined buckets-size entries are unfortunately hardcoded. A database
    # query to read the allowed values would be better, but is a performance
    # killer during mass import.
    types = (
        ("default", _("default")),
        ("buckets", _("buckets")),
        ("buckets_day", format_lazy("{}_{}", _("buckets"), _("day"))),
        ("buckets_week", format_lazy("{}_{}", _("buckets"), _("week"))),
        ("buckets_month", format_lazy("{}_{}", _("buckets"), _("month"))),
        ("infinite", _("infinite")),
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
    type = models.CharField(
        _("type"),
        max_length=20,
        null=True,
        blank=True,
        choices=types,
        default="default",
    )
    constrained = models.BooleanField(
        _("constrained"),
        null=True,
        blank=True,
        help_text=_(
            "controls whether or not this resource is planned in finite capacity mode"
        ),
    )
    maximum = models.DecimalField(
        _("maximum"),
        default="1.00",
        null=True,
        blank=True,
        max_digits=20,
        decimal_places=8,
        help_text=_("Size of the resource"),
    )
    maximum_calendar = models.ForeignKey(
        Calendar,
        verbose_name=_("maximum calendar"),
        related_name="+",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        help_text=_("Calendar defining the resource size varying over time"),
    )
    available = models.ForeignKey(
        Calendar,
        verbose_name=_("available"),
        related_name="+",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        help_text=_("Calendar defining the working hours and holidays"),
    )
    location = models.ForeignKey(
        Location,
        verbose_name=_("location"),
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        db_index=True,
    )
    cost = models.DecimalField(
        _("cost"),
        null=True,
        blank=True,
        max_digits=20,
        decimal_places=8,
        help_text=_("Cost for using 1 unit of the resource for 1 hour"),
    )
    maxearly = models.DurationField(
        _("max early"),
        null=True,
        blank=True,
        help_text=_(
            "Time window before the ask date where we look for available capacity"
        ),
    )
    setupmatrix = models.ForeignKey(
        SetupMatrix,
        verbose_name=_("setup matrix"),
        null=True,
        blank=True,
        db_index=True,
        on_delete=models.CASCADE,
        help_text=_("Setup matrix defining the conversion time and cost"),
    )
    setup = models.CharField(
        _("setup"),
        max_length=300,
        null=True,
        blank=True,
        help_text=_("Setup of the resource at the start of the plan"),
    )
    efficiency = models.DecimalField(
        # Translator: xgettext:no-python-format
        _("efficiency %"),
        null=True,
        blank=True,
        max_digits=20,
        decimal_places=8,
        help_text=_("Efficiency percentage of the resource"),
    )
    efficiency_calendar = models.ForeignKey(
        Calendar,
        # Translator: xgettext:no-python-format
        verbose_name=_("efficiency % calendar"),
        related_name="+",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        help_text=_(
            "Calendar defining the efficiency percentage of the resource varying over time"
        ),
    )

    # Methods
    def __str__(self):
        return self.name

    class Meta(AuditModel.Meta):
        db_table = "resource"
        verbose_name = _("resource")
        verbose_name_plural = _("resources")
        ordering = ["name"]


class Skill(AuditModel):
    # Database fields
    name = models.CharField(
        _("name"), max_length=300, primary_key=True, help_text=_("Unique identifier")
    )

    # Methods
    def __str__(self):
        return self.name

    class Meta(AuditModel.Meta):
        db_table = "skill"
        verbose_name = _("skill")
        verbose_name_plural = _("skills")
        ordering = ["name"]


class ResourceSkill(AuditModel):
    # Database fields
    id = models.AutoField(_("identifier"), primary_key=True)
    resource = models.ForeignKey(
        Resource,
        verbose_name=_("resource"),
        db_index=True,
        related_name="skills",
        blank=False,
        null=False,
        on_delete=models.CASCADE,
    )
    skill = models.ForeignKey(
        Skill,
        verbose_name=_("skill"),
        db_index=True,
        related_name="resources",
        blank=False,
        null=False,
        on_delete=models.CASCADE,
    )
    effective_start = models.DateTimeField(
        _("effective start"), null=True, blank=True, help_text=_("Validity start date")
    )
    effective_end = models.DateTimeField(
        _("effective end"), null=True, blank=True, help_text=_("Validity end date")
    )
    priority = models.IntegerField(
        _("priority"),
        default=1,
        null=True,
        blank=True,
        help_text=_("Priority of this skill in a group of alternates"),
    )

    class Manager(MultiDBManager):
        def get_by_natural_key(self, resource, skill):
            return self.get(resource=resource, skill=skill)

    def natural_key(self):
        return (self.resource, self.skill)

    objects = Manager()

    class Meta(AuditModel.Meta):
        db_table = "resourceskill"
        unique_together = (("resource", "skill"),)
        verbose_name = _("resource skill")
        verbose_name_plural = _("resource skills")
        ordering = ["resource", "skill"]


class SetupRule(AuditModel):
    """
    A rule that is part of a setup matrix.
    """

    # Database fields
    id = models.AutoField(_("identifier"), primary_key=True)
    setupmatrix = models.ForeignKey(
        SetupMatrix,
        verbose_name=_("setup matrix"),
        related_name="rules",
        on_delete=models.CASCADE,
    )
    priority = models.IntegerField(_("priority"))
    fromsetup = models.CharField(
        _("from setup"),
        max_length=300,
        blank=True,
        null=True,
        help_text=_("Name of the old setup (wildcard characters are supported)"),
    )
    tosetup = models.CharField(
        _("to setup"),
        max_length=300,
        blank=True,
        null=True,
        help_text=_("Name of the new setup (wildcard characters are supported)"),
    )
    duration = models.DurationField(
        _("duration"), null=True, blank=True, help_text=_("Duration of the changeover")
    )
    cost = models.DecimalField(
        _("cost"),
        max_digits=20,
        decimal_places=8,
        null=True,
        blank=True,
        help_text=_("Cost of the conversion"),
    )
    resource = models.ForeignKey(
        Resource,
        verbose_name=_("resource"),
        db_index=True,
        related_name="setuprules",
        blank=True,
        null=True,
        on_delete=models.SET_NULL,
        help_text=_("Extra resource used during this changeover"),
    )

    class Manager(MultiDBManager):
        def get_by_natural_key(self, setupmatrix, priority):
            return self.get(setupmatrix=setupmatrix, priority=priority)

    def natural_key(self):
        return (self.setupmatrix, self.priority)

    objects = Manager()

    def __str__(self):
        return "%s - %s" % (
            self.setupmatrix.name if self.setupmatrix else None,
            self.priority,
        )

    class Meta(AuditModel.Meta):
        ordering = ["priority"]
        db_table = "setuprule"
        unique_together = (("setupmatrix", "priority"),)
        verbose_name = _("setup matrix rule")
        verbose_name_plural = _("setup matrix rules")
