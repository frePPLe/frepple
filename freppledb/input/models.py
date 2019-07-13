#
# Copyright (C) 2007-2013 by frePPLe bvba
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

from datetime import datetime, time
from decimal import Decimal

from django.db import models, DEFAULT_DB_ALIAS
from django.utils.translation import ugettext_lazy as _
from django.utils.text import format_lazy

from freppledb.common.fields import JSONBField, AliasDateTimeField
from freppledb.common.models import HierarchyModel, AuditModel, MultiDBManager


searchmode = (
    ("PRIORITY", _("priority")),
    ("MINCOST", _("minimum cost")),
    ("MINPENALTY", _("minimum penalty")),
    ("MINCOSTPENALTY", _("minimum cost plus penalty")),
)


class Calendar(AuditModel):
    # Database fields
    # . Translators: Translation included with Django
    name = models.CharField(_("name"), max_length=300, primary_key=True)
    description = models.CharField(
        _("description"), max_length=500, null=True, blank=True
    )
    category = models.CharField(
        _("category"), max_length=300, null=True, blank=True, db_index=True
    )
    subcategory = models.CharField(
        _("subcategory"), max_length=300, null=True, blank=True, db_index=True
    )
    defaultvalue = models.DecimalField(
        _("default value"),
        max_digits=20,
        decimal_places=8,
        default="0.00",
        null=True,
        blank=True,
        help_text=_("Value to be used when no entry is effective"),
    )

    def __str__(self):
        return self.name

    class Meta(AuditModel.Meta):
        db_table = "calendar"
        verbose_name = _("calendar")
        verbose_name_plural = _("calendars")
        ordering = ["name"]


class CalendarBucket(AuditModel):

    # Database fields
    id = models.AutoField(_("identifier"), primary_key=True)
    # . Translators: Translation included with Django
    calendar = models.ForeignKey(
        Calendar,
        verbose_name=_("calendar"),
        related_name="buckets",
        on_delete=models.CASCADE,
    )
    startdate = models.DateTimeField(_("start date"), null=True, blank=True)
    enddate = models.DateTimeField(
        _("end date"), null=True, blank=True, default=datetime(2030, 12, 31)
    )
    value = models.DecimalField(
        _("value"), default="0.00", blank=True, max_digits=20, decimal_places=8
    )
    priority = models.IntegerField(_("priority"), default=0, blank=True, null=True)

    # . Translators: Translation included with Django
    monday = models.BooleanField(_("Monday"), blank=True, default=True)
    # . Translators: Translation included with Django
    tuesday = models.BooleanField(_("Tuesday"), blank=True, default=True)
    # . Translators: Translation included with Django
    wednesday = models.BooleanField(_("Wednesday"), blank=True, default=True)
    # . Translators: Translation included with Django
    thursday = models.BooleanField(_("Thursday"), blank=True, default=True)
    # . Translators: Translation included with Django
    friday = models.BooleanField(_("Friday"), blank=True, default=True)
    # . Translators: Translation included with Django
    saturday = models.BooleanField(_("Saturday"), blank=True, default=True)
    # . Translators: Translation included with Django
    sunday = models.BooleanField(_("Sunday"), blank=True, default=True)
    starttime = models.TimeField(
        _("start time"), blank=True, null=True, default=time(0, 0, 0)
    )
    endtime = models.TimeField(
        _("end time"), blank=True, null=True, default=time(23, 59, 59)
    )

    class Manager(MultiDBManager):
        def get_by_natural_key(self, calendar, startdate, enddate, priority):
            return self.get(
                calendar=calendar,
                startdate=startdate,
                enddate=enddate,
                priority=priority,
            )

    def natural_key(self):
        return (self.calendar, self.startdate, self.enddate, self.priority)

    objects = Manager()

    def __str__(self):
        return "%s" % self.id

    class Meta(AuditModel.Meta):
        ordering = ["calendar", "id"]
        db_table = "calendarbucket"
        verbose_name = _("calendar bucket")
        verbose_name_plural = _("calendar buckets")
        unique_together = (("calendar", "startdate", "enddate", "priority"),)


class Location(AuditModel, HierarchyModel):
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
    available = models.ForeignKey(
        Calendar,
        verbose_name=_("available"),
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        help_text=_("Calendar defining the working hours and holidays"),
    )

    def __str__(self):
        return self.name

    class Meta(AuditModel.Meta):
        db_table = "location"
        verbose_name = _("location")
        verbose_name_plural = _("locations")
        ordering = ["name"]


class Customer(AuditModel, HierarchyModel):
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

    def __str__(self):
        return self.name

    class Meta(AuditModel.Meta):
        db_table = "customer"
        verbose_name = _("customer")
        verbose_name_plural = _("customers")
        ordering = ["name"]


class Item(AuditModel, HierarchyModel):
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

    def __str__(self):
        return self.name

    class Meta(AuditModel.Meta):
        db_table = "item"
        verbose_name = _("item")
        verbose_name_plural = _("items")
        ordering = ["name"]


class Operation(AuditModel):
    # Types of operations
    types = (
        ("fixed_time", _("fixed_time")),
        ("time_per", _("time_per")),
        ("routing", _("routing")),
        ("alternate", _("alternate")),
        ("split", _("split")),
    )

    # Database fields
    # . Translators: Translation included with Django
    name = models.CharField(_("name"), max_length=300, primary_key=True)
    type = models.CharField(
        _("type"),
        max_length=20,
        null=True,
        blank=True,
        choices=types,
        default="fixed_time",
    )
    description = models.CharField(
        _("description"), max_length=500, null=True, blank=True
    )
    category = models.CharField(
        _("category"), max_length=300, null=True, blank=True, db_index=True
    )
    subcategory = models.CharField(
        _("subcategory"), max_length=300, null=True, blank=True, db_index=True
    )
    item = models.ForeignKey(
        Item,
        verbose_name=_("item"),
        null=True,
        blank=True,
        db_index=True,
        related_name="operations",
        on_delete=models.CASCADE,
    )
    location = models.ForeignKey(
        Location, verbose_name=_("location"), db_index=True, on_delete=models.CASCADE
    )
    priority = models.IntegerField(
        _("priority"),
        default=1,
        null=True,
        blank=True,
        help_text=_("Priority among all alternates"),
    )
    effective_start = models.DateTimeField(
        _("effective start"), null=True, blank=True, help_text=_("Validity start date")
    )
    effective_end = models.DateTimeField(
        _("effective end"), null=True, blank=True, help_text=_("Validity end date")
    )
    fence = models.DurationField(
        _("release fence"),
        null=True,
        blank=True,
        help_text=_(
            "Operationplans within this time window from the current day are expected to be released to production ERP"
        ),
    )
    posttime = models.DurationField(
        _("post-op time"),
        null=True,
        blank=True,
        help_text=_(
            "A delay time to be respected as a soft constraint after ending the operation"
        ),
    )
    sizeminimum = models.DecimalField(
        _("size minimum"),
        max_digits=20,
        decimal_places=8,
        null=True,
        blank=True,
        default="1.0",
        help_text=_("A minimum quantity for operationplans"),
    )
    sizemultiple = models.DecimalField(
        _("size multiple"),
        null=True,
        blank=True,
        max_digits=20,
        decimal_places=8,
        help_text=_("A multiple quantity for operationplans"),
    )
    sizemaximum = models.DecimalField(
        _("size maximum"),
        null=True,
        blank=True,
        max_digits=20,
        decimal_places=8,
        help_text=_("A maximum quantity for operationplans"),
    )
    cost = models.DecimalField(
        _("cost"),
        null=True,
        blank=True,
        max_digits=20,
        decimal_places=8,
        help_text=_("Cost per operationplan unit"),
    )
    duration = models.DurationField(
        _("duration"),
        null=True,
        blank=True,
        help_text=_("A fixed duration for the operation"),
    )
    duration_per = models.DurationField(
        _("duration per unit"),
        null=True,
        blank=True,
        help_text=_("A variable duration for the operation"),
    )
    search = models.CharField(
        _("search mode"),
        max_length=20,
        null=True,
        blank=True,
        choices=searchmode,
        help_text=_("Method to select preferred alternate"),
    )
    available = models.ForeignKey(
        Calendar,
        verbose_name=_("available"),
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        help_text=_("Calendar defining the working hours and holidays"),
    )

    def __str__(self):
        return self.name

    class Meta(AuditModel.Meta):
        db_table = "operation"
        verbose_name = _("operation")
        verbose_name_plural = _("operations")
        ordering = ["name"]


class SubOperation(AuditModel):
    # Database fields
    id = models.AutoField(_("identifier"), primary_key=True)
    operation = models.ForeignKey(
        Operation,
        verbose_name=_("operation"),
        related_name="suboperations",
        help_text=_("Parent operation"),
        on_delete=models.CASCADE,
    )
    priority = models.IntegerField(
        _("priority"),
        default=1,
        help_text=_(
            "Sequence of this operation among the suboperations. Negative values are ignored."
        ),
    )
    suboperation = models.ForeignKey(
        Operation,
        verbose_name=_("suboperation"),
        related_name="superoperations",
        help_text=_("Child operation"),
        on_delete=models.CASCADE,
    )
    effective_start = models.DateTimeField(
        _("effective start"), null=True, blank=True, help_text=_("Validity start date")
    )
    effective_end = models.DateTimeField(
        _("effective end"), null=True, blank=True, help_text=_("Validity end date")
    )

    class Manager(MultiDBManager):
        def get_by_natural_key(self, operation, suboperation, effective_start):
            return self.get(
                operation=operation,
                suboperation=suboperation,
                effective_start=effective_start,
            )

    def natural_key(self):
        return (self.operation, self.suboperation, self.effective_start)

    objects = Manager()

    def __str__(self):
        return "%s   %s   %s" % (
            self.operation.name if self.operation else None,
            self.priority,
            self.suboperation.name if self.suboperation else None,
        )

    class Meta(AuditModel.Meta):
        db_table = "suboperation"
        ordering = ["operation", "priority", "suboperation"]
        verbose_name = _("suboperation")
        verbose_name_plural = _("suboperations")
        unique_together = (("operation", "suboperation", "effective_start"),)


class Buffer(AuditModel):
    # Types of buffers
    types = (("default", _("default")), ("infinite", _("infinite")))

    # Fields common to all buffer types
    id = models.AutoField(_("identifier"), primary_key=True)
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
    location = models.ForeignKey(
        Location,
        verbose_name=_("location"),
        db_index=True,
        blank=False,
        null=False,
        on_delete=models.CASCADE,
    )
    item = models.ForeignKey(
        Item,
        verbose_name=_("item"),
        db_index=True,
        blank=False,
        null=False,
        on_delete=models.CASCADE,
    )
    onhand = models.DecimalField(
        _("onhand"),
        null=True,
        blank=True,
        max_digits=20,
        decimal_places=8,
        default="0.00",
        help_text=_("current inventory"),
    )
    minimum = models.DecimalField(
        _("minimum"),
        null=True,
        blank=True,
        max_digits=20,
        decimal_places=8,
        default="0.00",
        help_text=_("safety stock"),
    )
    minimum_calendar = models.ForeignKey(
        Calendar,
        verbose_name=_("minimum calendar"),
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        help_text=_("Calendar storing a time-dependent safety stock profile"),
    )
    min_interval = models.DurationField(
        _("min_interval"),
        null=True,
        blank=True,
        help_text=_("Batching window for grouping replenishments in batches"),
    )

    class Manager(MultiDBManager):
        def get_by_natural_key(self, item, location):
            return self.get(item=item, location=location)

    def natural_key(self):
        return (self.item, self.location)

    objects = Manager()

    def __str__(self):
        return "%s @ %s" % (self.item.name, self.location.name)

    class Meta(AuditModel.Meta):
        db_table = "buffer"
        verbose_name = _("buffer")
        verbose_name_plural = _("buffers")
        ordering = ["item", "location"]
        unique_together = (("item", "location"),)


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
        _("efficiency %"),
        null=True,
        blank=True,
        max_digits=20,
        decimal_places=8,
        help_text=_("Efficiency percentage of the resource"),
    )
    efficiency_calendar = models.ForeignKey(
        Calendar,
        verbose_name=_("efficiency %% calendar"),
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
        # . Translators: Translation included with Django
        _("name"),
        max_length=300,
        primary_key=True,
        help_text=_("Unique identifier"),
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


class OperationMaterial(AuditModel):
    # Types of flow
    types = (
        ("start", _("Start")),
        ("end", _("End")),
        ("transfer_batch", _("Batch transfer")),
    )

    # Database fields
    id = models.AutoField(_("identifier"), primary_key=True)
    operation = models.ForeignKey(
        Operation,
        verbose_name=_("operation"),
        db_index=True,
        related_name="operationmaterials",
        blank=False,
        null=False,
        on_delete=models.CASCADE,
    )
    item = models.ForeignKey(
        Item,
        verbose_name=_("item"),
        db_index=True,
        related_name="operationmaterials",
        blank=False,
        null=False,
        on_delete=models.CASCADE,
    )
    quantity = models.DecimalField(
        _("quantity"),
        default="1.00",
        blank=True,
        null=True,
        max_digits=20,
        decimal_places=8,
        help_text=_("Quantity to consume or produce per operationplan unit"),
    )
    quantity_fixed = models.DecimalField(
        _("fixed quantity"),
        blank=True,
        null=True,
        max_digits=20,
        decimal_places=8,
        help_text=_("Fixed quantity to consume or produce"),
    )
    type = models.CharField(
        _("type"),
        max_length=20,
        null=True,
        blank=True,
        choices=types,
        default="start",
        help_text=_(
            "Consume/produce material at the start or the end of the operationplan"
        ),
    )
    effective_start = models.DateTimeField(
        _("effective start"), null=True, blank=True, help_text=_("Validity start date")
    )
    effective_end = models.DateTimeField(
        _("effective end"), null=True, blank=True, help_text=_("Validity end date")
    )
    name = models.CharField(
        # . Translators: Translation included with Django
        _("name"),
        max_length=300,
        null=True,
        blank=True,
        help_text=_("Optional name of this operation material"),
    )
    priority = models.IntegerField(
        _("priority"),
        default=1,
        null=True,
        blank=True,
        help_text=_("Priority of this operation material in a group of alternates"),
    )
    search = models.CharField(
        _("search mode"),
        max_length=20,
        null=True,
        blank=True,
        choices=searchmode,
        help_text=_("Method to select preferred alternate"),
    )
    transferbatch = models.DecimalField(
        _("transfer batch quantity"),
        max_digits=20,
        decimal_places=8,
        null=True,
        blank=True,
        help_text=_("Batch size by in which material is produced or consumed"),
    )

    class Manager(MultiDBManager):
        def get_by_natural_key(self, operation, item, effective_start):
            return self.get(
                operation=operation, item=item, effective_start=effective_start
            )

    def natural_key(self):
        return (self.operation, self.item, self.effective_start)

    objects = Manager()

    def __str__(self):
        if self.effective_start:
            return "%s - %s - %s" % (
                self.operation.name if self.operation else None,
                self.item.name if self.item else None,
                self.effective_start,
            )
        else:
            return "%s - %s" % (
                self.operation.name if self.operation else None,
                self.item.name if self.item else None,
            )

    class Meta(AuditModel.Meta):
        db_table = "operationmaterial"
        unique_together = (("operation", "item", "effective_start"),)
        verbose_name = _("operation material")
        verbose_name_plural = _("operation materials")


class OperationResource(AuditModel):
    # Database fields
    id = models.AutoField(_("identifier"), primary_key=True)
    operation = models.ForeignKey(
        Operation,
        verbose_name=_("operation"),
        db_index=True,
        related_name="operationresources",
        blank=False,
        null=False,
        on_delete=models.CASCADE,
    )
    resource = models.ForeignKey(
        Resource,
        verbose_name=_("resource"),
        db_index=True,
        related_name="operationresources",
        blank=False,
        null=False,
        on_delete=models.CASCADE,
    )
    skill = models.ForeignKey(
        Skill,
        verbose_name=_("skill"),
        related_name="operationresources",
        null=True,
        blank=True,
        db_index=True,
        on_delete=models.SET_NULL,
    )
    quantity = models.DecimalField(
        _("quantity"),
        default="1.00",
        max_digits=20,
        decimal_places=8,
        help_text=_("Required quantity of the resource"),
    )
    quantity_fixed = models.DecimalField(
        _("quantity fixed"),
        null=True,
        blank=True,
        max_digits=20,
        decimal_places=8,
        help_text=_(
            "constant part of the capacity consumption (bucketized resources only)"
        ),
    )
    effective_start = models.DateTimeField(
        _("effective start"), null=True, blank=True, help_text=_("Validity start date")
    )
    effective_end = models.DateTimeField(
        _("effective end"), null=True, blank=True, help_text=_("Validity end date")
    )
    name = models.CharField(
        # . Translators: Translation included with Django
        _("name"),
        max_length=300,
        null=True,
        blank=True,
        help_text=_("Optional name of this load"),
    )
    priority = models.IntegerField(
        _("priority"),
        default=1,
        null=True,
        blank=True,
        help_text=_("Priority of this load in a group of alternates"),
    )
    setup = models.CharField(
        _("setup"),
        max_length=300,
        null=True,
        blank=True,
        help_text=_("Setup required on the resource for this operation"),
    )
    search = models.CharField(
        _("search mode"),
        max_length=20,
        null=True,
        blank=True,
        choices=searchmode,
        help_text=_("Method to select preferred alternate"),
    )

    class Manager(MultiDBManager):
        def get_by_natural_key(self, operation, resource, effective_start):
            return self.get(
                operation=operation, resource=resource, effective_start=effective_start
            )

    def natural_key(self):
        return (self.operation, self.resource, self.effective_start)

    objects = Manager()

    def __str__(self):
        if self.effective_start:
            return "%s - %s - %s" % (
                self.operation.name if self.operation else None,
                self.resource.name if self.resource else None,
                self.effective_start,
            )
        else:
            return "%s - %s" % (
                self.operation.name if self.operation else None,
                self.resource.name if self.resource else None,
            )

    class Meta(AuditModel.Meta):
        db_table = "operationresource"
        unique_together = (("operation", "resource", "effective_start"),)
        verbose_name = _("operation resource")
        verbose_name_plural = _("operation resources")


class Supplier(AuditModel, HierarchyModel):
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
    available = models.ForeignKey(
        Calendar,
        verbose_name=_("available"),
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        help_text=_("Calendar defining the working hours and holidays"),
    )

    def __str__(self):
        return self.name

    class Meta(AuditModel.Meta):
        db_table = "supplier"
        verbose_name = _("supplier")
        verbose_name_plural = _("suppliers")
        ordering = ["name"]


class ItemSupplier(AuditModel):
    # Database fields
    id = models.AutoField(_("identifier"), primary_key=True)
    item = models.ForeignKey(
        Item,
        verbose_name=_("item"),
        db_index=True,
        related_name="itemsuppliers",
        null=False,
        blank=False,
        on_delete=models.CASCADE,
    )
    location = models.ForeignKey(
        Location,
        verbose_name=_("location"),
        null=True,
        blank=True,
        db_index=True,
        related_name="itemsuppliers",
        on_delete=models.CASCADE,
    )
    supplier = models.ForeignKey(
        Supplier,
        verbose_name=_("supplier"),
        db_index=True,
        related_name="suppliers",
        null=False,
        blank=False,
        on_delete=models.CASCADE,
    )
    leadtime = models.DurationField(
        _("lead time"), null=True, blank=True, help_text=_("Purchasing lead time")
    )
    sizeminimum = models.DecimalField(
        _("size minimum"),
        max_digits=20,
        decimal_places=8,
        null=True,
        blank=True,
        default="1.0",
        help_text=_("A minimum purchasing quantity"),
    )
    sizemultiple = models.DecimalField(
        _("size multiple"),
        null=True,
        blank=True,
        max_digits=20,
        decimal_places=8,
        help_text=_("A multiple purchasing quantity"),
    )
    sizemaximum = models.DecimalField(
        _("size maximum"),
        null=True,
        blank=True,
        max_digits=20,
        decimal_places=8,
        help_text=_("A maximum purchasing quantity"),
    )
    cost = models.DecimalField(
        _("cost"),
        null=True,
        blank=True,
        max_digits=20,
        decimal_places=8,
        help_text=_("Purchasing cost per unit"),
    )
    priority = models.IntegerField(
        _("priority"),
        default=1,
        null=True,
        blank=True,
        help_text=_("Priority among all alternates"),
    )
    effective_start = models.DateTimeField(
        _("effective start"), null=True, blank=True, help_text=_("Validity start date")
    )
    effective_end = models.DateTimeField(
        _("effective end"), null=True, blank=True, help_text=_("Validity end date")
    )
    resource = models.ForeignKey(
        Resource,
        verbose_name=_("resource"),
        null=True,
        blank=True,
        db_index=True,
        related_name="itemsuppliers",
        on_delete=models.SET_NULL,
        help_text=_("Resource to model the supplier capacity"),
    )
    resource_qty = models.DecimalField(
        _("resource quantity"),
        null=True,
        blank=True,
        max_digits=20,
        decimal_places=8,
        default="1.0",
        help_text=_("Resource capacity consumed per purchased unit"),
    )
    fence = models.DurationField(
        _("fence"),
        null=True,
        blank=True,
        help_text=_("Frozen fence for creating new procurements"),
    )

    class Manager(MultiDBManager):
        def get_by_natural_key(self, item, location, supplier, effective_start):
            return self.get(
                item=item,
                location=location,
                supplier=supplier,
                effective_start=effective_start,
            )

    def natural_key(self):
        return (self.item, self.location, self.supplier, self.effective_start)

    objects = Manager()

    def __str__(self):
        return "%s - %s - %s" % (
            self.supplier.name if self.supplier else "No supplier",
            self.item.name if self.item else "No item",
            self.location.name if self.location else "Any location",
        )

    class Meta(AuditModel.Meta):
        db_table = "itemsupplier"
        unique_together = (("item", "location", "supplier", "effective_start"),)
        verbose_name = _("item supplier")
        verbose_name_plural = _("item suppliers")


class ItemDistribution(AuditModel):
    # Database fields
    id = models.AutoField(_("identifier"), primary_key=True)
    item = models.ForeignKey(
        Item,
        verbose_name=_("item"),
        db_index=True,
        related_name="distributions",
        null=False,
        blank=False,
        on_delete=models.CASCADE,
    )
    location = models.ForeignKey(
        Location,
        verbose_name=_("location"),
        null=True,
        blank=True,
        db_index=True,
        related_name="itemdistributions_destination",
        on_delete=models.CASCADE,
    )
    origin = models.ForeignKey(
        Location,
        verbose_name=_("origin"),
        on_delete=models.CASCADE,
        db_index=True,
        related_name="itemdistributions_origin",
    )
    leadtime = models.DurationField(
        _("lead time"), null=True, blank=True, help_text=_("lead time")
    )
    sizeminimum = models.DecimalField(
        _("size minimum"),
        max_digits=20,
        decimal_places=8,
        null=True,
        blank=True,
        default="1.0",
        help_text=_("A minimum shipping quantity"),
    )
    sizemultiple = models.DecimalField(
        _("size multiple"),
        null=True,
        blank=True,
        max_digits=20,
        decimal_places=8,
        help_text=_("A multiple shipping quantity"),
    )
    sizemaximum = models.DecimalField(
        _("size maximum"),
        null=True,
        blank=True,
        max_digits=20,
        decimal_places=8,
        help_text=_("A maximum shipping quantity"),
    )
    cost = models.DecimalField(
        _("cost"),
        null=True,
        blank=True,
        max_digits=20,
        decimal_places=8,
        help_text=_("Shipping cost per unit"),
    )
    priority = models.IntegerField(
        _("priority"),
        default=1,
        null=True,
        blank=True,
        help_text=_("Priority among all alternates"),
    )
    effective_start = models.DateTimeField(
        _("effective start"), null=True, blank=True, help_text=_("Validity start date")
    )
    effective_end = models.DateTimeField(
        _("effective end"), null=True, blank=True, help_text=_("Validity end date")
    )
    resource = models.ForeignKey(
        Resource,
        verbose_name=_("resource"),
        null=True,
        blank=True,
        db_index=True,
        related_name="itemdistributions",
        on_delete=models.SET_NULL,
        help_text=_("Resource to model the distribution capacity"),
    )
    resource_qty = models.DecimalField(
        _("resource quantity"),
        null=True,
        blank=True,
        max_digits=20,
        decimal_places=8,
        default="1.0",
        help_text=_("Resource capacity consumed per distributed unit"),
    )
    fence = models.DurationField(
        _("fence"),
        null=True,
        blank=True,
        help_text=_("Frozen fence for creating new shipments"),
    )

    class Manager(MultiDBManager):
        def get_by_natural_key(self, item, location, origin, effective_start):
            return self.get(
                item=item,
                location=location,
                origin=origin,
                effective_start=effective_start,
            )

    def natural_key(self):
        return (self.item, self.location, self.origin, self.effective_start)

    objects = Manager()

    def __str__(self):
        return "%s - %s - %s" % (
            self.location.name if self.location else "Any destination",
            self.item.name if self.item else "No item",
            self.origin.name if self.origin else "No origin",
        )

    class Meta(AuditModel.Meta):
        db_table = "itemdistribution"
        unique_together = (("item", "location", "origin", "effective_start"),)
        verbose_name = _("item distribution")
        verbose_name_plural = _("item distributions")


class Demand(AuditModel, HierarchyModel):
    # Status
    demandstatus = (
        ("inquiry", _("inquiry")),
        ("quote", _("quote")),
        ("open", _("open")),
        ("closed", _("closed")),
        ("canceled", _("canceled")),
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
    customer = models.ForeignKey(
        Customer, verbose_name=_("customer"), db_index=True, on_delete=models.CASCADE
    )
    item = models.ForeignKey(
        Item, verbose_name=_("item"), db_index=True, on_delete=models.CASCADE
    )
    location = models.ForeignKey(
        Location, verbose_name=_("location"), db_index=True, on_delete=models.CASCADE
    )
    due = models.DateTimeField(
        _("due"), help_text=_("Due date of the demand"), db_index=True
    )
    status = models.CharField(
        _("status"),
        max_length=10,
        null=True,
        blank=True,
        choices=demandstatus,
        default="open",
        help_text=_('Status of the demand. Only "open" demands are planned'),
    )
    operation = models.ForeignKey(
        Operation,
        verbose_name=_("delivery operation"),
        null=True,
        blank=True,
        related_name="used_demand",
        on_delete=models.SET_NULL,
        help_text=_("Operation used to satisfy this demand"),
    )
    quantity = models.DecimalField(
        _("quantity"), max_digits=20, decimal_places=8, default=1
    )
    priority = models.IntegerField(
        _("priority"),
        default=10,
        help_text=_(
            "Priority of the demand (lower numbers indicate more important demands)"
        ),
    )
    minshipment = models.DecimalField(
        _("minimum shipment"),
        null=True,
        blank=True,
        max_digits=20,
        decimal_places=8,
        help_text=_("Minimum shipment quantity when planning this demand"),
    )
    maxlateness = models.DurationField(
        _("maximum lateness"),
        null=True,
        blank=True,
        help_text=_("Maximum lateness allowed when planning this demand"),
    )
    delay = models.DurationField(_("delay"), null=True, blank=True, editable=False)
    plannedquantity = models.DecimalField(
        _("planned quantity"),
        max_digits=20,
        decimal_places=8,
        null=True,
        blank=True,
        editable=False,
        help_text=_("Quantity planned for delivery"),
    )
    deliverydate = models.DateTimeField(
        _("delivery date"),
        help_text=_("Delivery date of the demand"),
        null=True,
        blank=True,
        editable=False,
    )
    plan = JSONBField(default="{}", null=True, blank=True, editable=False)

    # Convenience methods
    def __str__(self):
        return self.name

    class Meta(AuditModel.Meta):
        db_table = "demand"
        verbose_name = _("sales order")
        verbose_name_plural = _("sales orders")
        ordering = ["name"]


class OperationPlan(AuditModel):
    # Possible types
    types = (
        ("STCK", _("inventory")),
        ("MO", _("manufacturing order")),
        ("PO", _("purchase order")),
        ("DO", _("distribution order")),
        ("DLVR", _("delivery order")),
    )

    # Possible status
    orderstatus = (
        ("proposed", _("proposed")),
        ("approved", _("approved")),
        ("confirmed", _("confirmed")),
        ("completed", _("completed")),
        ("closed", _("closed")),
    )

    # Database fields
    # Common fields
    reference = models.CharField(
        _("reference"),
        max_length=300,
        primary_key=True,
        help_text=_("Unique identifier"),
    )
    status = models.CharField(
        _("status"),
        null=True,
        blank=True,
        max_length=20,
        choices=orderstatus,
        help_text=_("Status of the order"),
    )
    type = models.CharField(
        _("type"),
        max_length=5,
        choices=types,
        default="MO",
        help_text=_("Order type"),
        db_index=True,
    )
    quantity = models.DecimalField(
        _("quantity"), max_digits=20, decimal_places=8, default="1.00"
    )
    color = models.DecimalField(
        _("color"),
        max_digits=20,
        null=True,
        blank=True,
        decimal_places=8,
        default="0.00",
    )
    startdate = models.DateTimeField(
        _("start date"), help_text=_("start date"), null=True, blank=True, db_index=True
    )
    enddate = models.DateTimeField(
        _("end date"), help_text=_("end date"), null=True, blank=True, db_index=True
    )
    criticality = models.DecimalField(
        _("criticality"),
        max_digits=20,
        decimal_places=8,
        null=True,
        blank=True,
        editable=False,
    )
    delay = models.DurationField(_("delay"), null=True, blank=True, editable=False)
    plan = JSONBField(default="{}", null=True, blank=True, editable=False)
    # Used only for manufacturing orders
    operation = models.ForeignKey(
        Operation,
        verbose_name=_("operation"),
        db_index=True,
        null=True,
        blank=True,
        on_delete=models.CASCADE,
    )
    owner = models.ForeignKey(
        "self",
        verbose_name=_("owner"),
        null=True,
        blank=True,
        related_name="xchildren",
        help_text=_("Hierarchical parent"),
        on_delete=models.CASCADE,
    )
    # Used for purchase orders and distribution orders
    item = models.ForeignKey(
        Item,
        verbose_name=_("item"),
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        db_index=True,
    )
    # Used only for distribution orders
    origin = models.ForeignKey(
        Location,
        verbose_name=_("origin"),
        null=True,
        blank=True,
        related_name="origins",
        db_index=True,
        on_delete=models.CASCADE,
    )
    destination = models.ForeignKey(
        Location,
        verbose_name=_("destination"),
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name="destinations",
        db_index=True,
    )
    # Used only for purchase orders
    supplier = models.ForeignKey(
        Supplier,
        verbose_name=_("supplier"),
        null=True,
        blank=True,
        db_index=True,
        on_delete=models.CASCADE,
    )
    location = models.ForeignKey(
        Location,
        verbose_name=_("location"),
        null=True,
        blank=True,
        db_index=True,
        on_delete=models.CASCADE,
    )
    # Used for delivery operationplans
    demand = models.ForeignKey(
        Demand,
        verbose_name=_("demand"),
        null=True,
        blank=True,
        db_index=True,
        on_delete=models.CASCADE,
    )
    due = models.DateTimeField(
        _("due"),
        help_text=_("Due date of the demand/forecast"),
        null=True,
        blank=True,
        editable=False,
    )
    name = models.CharField(
        _("name"), max_length=1000, null=True, blank=True, db_index=True
    )

    class Manager(MultiDBManager):
        pass

    def __str__(self):
        return str(self.reference)

    def propagateStatus(self):
        if self.type == "STCK":
            return
        state = getattr(self, "_state", None)
        db = state.db if state else DEFAULT_DB_ALIAS

        # Assure that all child operationplans also get the same status
        now = datetime.now()
        if self.type not in ("DO", "PO"):
            for subop in self.xchildren.all().using(db):
                if subop.status != self.status:
                    if subop.enddate > now:
                        subop.enddate = now
                    if subop.startdate > now:
                        subop.startdate = now
                    subop.status = self.status
                    subop.save(update_fields=["status", "startdate", "enddate"])

        if self.status not in ("completed", "closed"):
            return

        # Assure the start and end are in the past
        if self.enddate > now:
            self.enddate = now
        if self.startdate > now:
            self.startdate = now

        if self.type == "MO" and self.owner and self.owner.operation.type == "routing":
            # Assure that previous routing steps are also marked closed or completed
            subopplans = [i for i in self.owner.xchildren.all().using(db)]
            for subop in subopplans:
                if subop.reference == self.reference:
                    subop.status = self.status
            steps = {
                z.suboperation: z.priority
                for z in self.owner.operation.suboperations.all()
                .using(db)
                .only("suboperation", "priority")
            }
            myprio = steps.get(self.operation, 0)
            for subop in subopplans:
                if (
                    subop.status != self.status
                    and steps.get(subop.operation, 0) < myprio
                ):
                    subop.status = self.status
                    if subop.enddate > now:
                        subop.enddate = now
                    if subop.startdate > now:
                        subop.startdate = now
                    subop.save(update_fields=["status", "startdate", "enddate"])

            # Assure that the parent is at least approved
            all_steps_completed = True
            all_steps_closed = True
            for subop in subopplans:
                if subop.status not in ("closed", "completed"):
                    all_steps_completed = False
                if subop.status != "closed":
                    all_steps_closed = False
            if all_steps_closed and self.owner.status != "closed":
                self.owner.status = "closed"
                if self.owner.enddate > now:
                    self.owner.enddate = now
                if self.owner.startdate > now:
                    self.owner.startdate = now
                self.owner.save(
                    update_fields=["status", "startdate", "enddate"], using=db
                )
            elif all_steps_completed and self.owner.status != "completed":
                self.owner.status = "completed"
                if self.owner.enddate > now:
                    self.owner.enddate = now
                if self.owner.startdate > now:
                    self.owner.startdate = now
                self.owner.save(
                    update_fields=["status", "startdate", "enddate"], using=db
                )
            elif self.owner.status == "proposed":
                self.owner.status = "approved"
                if self.owner.startdate > now:
                    self.owner.startdate = now
                self.owner.save(update_fields=["status", "startdate"], using=db)

        # Remove all capacity consumption of closed and completed
        self.resources.all().using(db).delete()

        for opplanmat in self.materials.all().using(db):
            # Assure the material production and consumption are in the past
            # We are not correcting the expected onhand. The next plan generation will do that.
            if opplanmat.flowdate > now:
                opplanmat.flowdate = now
                opplanmat.save(using=db)
            # Check that upstream buffers have enough supply in the closed status
            if opplanmat.quantity < 0:
                # check the inventory + consumed
                flplns = [
                    i
                    for i in OperationPlanMaterial.objects.all()
                    .using(db)
                    .filter(item=opplanmat.item.name, location=opplanmat.location.name)
                    .order_by("flowdate", "-quantity")
                    .select_related("operationplan")
                ]
                closed_balance = Decimal(
                    0.00001
                )  # Leaving some room for rounding errors
                for f in flplns:
                    if (
                        f.operationplan.type == "STCK"
                        or f.operationplan.status in ["closed", "completed"]
                        or f.operationplan.reference == self.reference
                    ):
                        closed_balance += f.quantity
                if closed_balance < 0:
                    # Things don't add up here.
                    # We'll close some upstream supply to make things match up
                    # First, try changing the status of confirmed supply
                    for f in flplns:
                        if (
                            f.quantity > 0
                            and f.operationplan.status == "confirmed"
                            and f.operationplan.type != "STCK"
                        ):
                            f.operationplan.status = self.status
                            f.operationplan.save(update_fields=["status"])
                            closed_balance += f.quantity
                            if closed_balance >= 0:
                                break
                    if closed_balance < 0:
                        # Second, try changing the status of approved supply
                        for f in flplns:
                            if f.quantity > 0 and f.operationplan.status == "approved":
                                f.operationplan.status = self.status
                                f.operationplan.save(update_fields=["status"])
                                closed_balance += f.quantity
                                if closed_balance >= 0:
                                    break
                        if closed_balance < 0:
                            # Finally, try changing the status of proposed supply
                            for f in flplns:
                                if (
                                    f.quantity > 0
                                    and f.operationplan.status == "proposed"
                                ):
                                    f.operationplan.status = self.status
                                    f.operationplan.save(update_fields=["status"])
                                    closed_balance += f.quantity
                                    if closed_balance >= 0:
                                        break

    def save(self, *args, **kwargs):
        self.propagateStatus()
        # Call the real save() method
        super().save(*args, **kwargs)

    class Meta(AuditModel.Meta):
        db_table = "operationplan"
        verbose_name = _("operationplan")
        verbose_name_plural = _("operationplans")
        ordering = ["reference"]


class OperationPlanResource(AuditModel):
    # Possible status
    OPRstatus = (
        ("proposed", _("proposed")),
        ("confirmed", _("confirmed")),
        ("closed", _("closed")),
    )

    # Database fields
    id = models.AutoField(_("identifier"), primary_key=True)
    resource = models.ForeignKey(
        Resource,
        verbose_name=_("resource"),
        related_name="operationplanresources",
        on_delete=models.CASCADE,
    )
    operationplan = models.ForeignKey(
        OperationPlan,
        verbose_name=_("reference"),
        db_index=True,
        related_name="resources",
        on_delete=models.CASCADE,
    )
    quantity = models.DecimalField(
        _("quantity"),
        max_digits=20,
        decimal_places=8,
        default=1.0,
        blank=True,
        null=True,
    )
    startdate = models.DateTimeField(
        _("start date"), db_index=True, null=True, blank=True
    )
    enddate = models.DateTimeField(_("end date"), db_index=True, null=True, blank=True)
    setup = models.CharField(_("setup"), max_length=300, null=True, blank=True)
    status = models.CharField(
        _("load status"),
        null=True,
        blank=True,
        max_length=20,
        choices=OPRstatus,
        help_text=_("Status of the resource assignment"),
    )

    class Manager(MultiDBManager):
        def get_by_natural_key(self, resource, operationplan):
            # Note: we are not enforcing the uniqueness of this natural key in the database
            return self.get(operationplan=operationplan, resource=resource)

    def natural_key(self):
        return (self.resource, self.operationplan)

    objects = Manager()

    def __str__(self):
        return "%s %s %s %s" % (
            self.resource,
            self.startdate,
            self.enddate,
            self.status,
        )

    class Meta:
        db_table = "operationplanresource"
        unique_together = (("resource", "operationplan"),)
        ordering = ["resource", "startdate"]
        verbose_name = _("resource detail")
        verbose_name_plural = _("resource detail")


class OperationPlanMaterial(AuditModel):
    # Possible status
    OPMstatus = (
        ("proposed", _("proposed")),
        ("confirmed", _("confirmed")),
        ("closed", _("closed")),
    )

    # Database fields
    id = models.AutoField(_("identifier"), primary_key=True)
    item = models.ForeignKey(
        Item,
        verbose_name=_("item"),
        related_name="operationplanmaterials",
        db_index=True,
        on_delete=models.CASCADE,
    )
    location = models.ForeignKey(
        Location,
        verbose_name=_("location"),
        related_name="operationplanmaterials",
        db_index=True,
        on_delete=models.CASCADE,
    )
    operationplan = models.ForeignKey(
        OperationPlan,
        verbose_name=_("reference"),
        db_index=True,
        related_name="materials",
        on_delete=models.CASCADE,
    )
    quantity = models.DecimalField(_("quantity"), max_digits=20, decimal_places=8)
    flowdate = models.DateTimeField(_("date"), db_index=True)
    onhand = models.DecimalField(
        _("onhand"), max_digits=20, decimal_places=8, null=True, blank=True
    )
    minimum = models.DecimalField(
        _("minimum"), max_digits=20, decimal_places=8, null=True, blank=True
    )
    periodofcover = models.DecimalField(
        _("period of cover"), max_digits=20, decimal_places=8, null=True, blank=True
    )
    status = models.CharField(
        _("material status"),
        null=True,
        blank=True,
        max_length=20,
        choices=OPMstatus,
        help_text=_("status of the material production or consumption"),
    )

    class Manager(MultiDBManager):
        def get_by_natural_key(self, operationplan, item, location):
            # Note: we are not enforcing the uniqueness of this natural key in the database
            # (eg when using transfer batching there can be multiple records for the same key)
            return self.get(operationplan=operationplan, item=item, location=location)

    def natural_key(self):
        return (self.operationplan, self.item, self.location)

    objects = Manager()

    def __str__(self):
        return "%s @ %s %s %s %s" % (
            self.item_id,
            self.location_id,
            self.flowdate,
            self.quantity,
            self.status,
        )

    class Meta:
        db_table = "operationplanmaterial"
        ordering = ["item", "location", "flowdate"]
        verbose_name = _("inventory detail")
        verbose_name_plural = _("inventory detail")
        indexes = [models.Index(fields=["item", "location"], name="opplanmat_itemloc")]


class DistributionOrder(OperationPlan):

    shipping_date = AliasDateTimeField(
        db_column="startdate", verbose_name=_("shipping date"), null=True, blank=True
    )
    receipt_date = AliasDateTimeField(
        db_column="enddate", verbose_name=_("receipt date"), null=True, blank=True
    )

    def __init__(self, *args, **kwargs):
        if "startdate" in kwargs:
            kwargs["shipping_date"] = kwargs["startdate"]
        elif "shipping_date" in kwargs:
            kwargs["startdate"] = kwargs["shipping_date"]
        if "enddate" in kwargs:
            kwargs["receipt_date"] = kwargs["enddate"]
        elif "receipt_date" in kwargs:
            kwargs["enddate"] = kwargs["receipt_date"]
        return super().__init__(*args, **kwargs)

    class DistributionOrderManager(OperationPlan.Manager):
        def get_queryset(self):
            return super().get_queryset().filter(type="DO")
            # .defer("operation", "owner", "supplier", "location")

    objects = DistributionOrderManager()

    def save(self, *args, **kwargs):
        self.type = "DO"
        self.operation = self.owner = self.location = self.supplier = None
        super().save(*args, **kwargs)

    class Meta:
        proxy = True
        verbose_name = _("distribution order")
        verbose_name_plural = _("distribution orders")


class PurchaseOrder(OperationPlan):

    ordering_date = AliasDateTimeField(
        db_column="startdate", verbose_name=_("ordering date"), null=True, blank=True
    )
    receipt_date = AliasDateTimeField(
        db_column="enddate", verbose_name=_("receipt date"), null=True, blank=True
    )

    def __init__(self, *args, **kwargs):
        if "startdate" in kwargs:
            kwargs["ordering_date"] = kwargs["startdate"]
        elif "ordering_date" in kwargs:
            kwargs["startdate"] = kwargs["ordering_date"]
        if "enddate" in kwargs:
            kwargs["receipt_date"] = kwargs["enddate"]
        elif "receipt_date" in kwargs:
            kwargs["enddate"] = kwargs["receipt_date"]
        return super().__init__(*args, **kwargs)

    class PurchaseOrderManager(OperationPlan.Manager):
        def get_queryset(self):
            return super().get_queryset().filter(type="PO")
            # Note: defer screws up the model name when deleting a PO
            # .defer("operation", "owner", "origin", "destination")

    objects = PurchaseOrderManager()

    def save(self, *args, **kwargs):
        self.type = "PO"
        self.operation = self.owner = self.origin = self.destination = None
        super().save(*args, **kwargs)

    class Meta:
        proxy = True
        verbose_name = _("purchase order")
        verbose_name_plural = _("purchase orders")


class ManufacturingOrder(OperationPlan):
    class ManufacturingOrderManager(OperationPlan.Manager):
        def get_queryset(self):
            return super().get_queryset().filter(type="MO")
            # Note: defer screws up the model name when deleting a PO
            # .defer("supplier", "location", "origin", "destination")

    objects = ManufacturingOrderManager()

    def save(self, *args, **kwargs):
        self.type = "MO"
        self.supplier = self.origin = self.destination = None
        if self.operation:
            self.item = self.operation.item
            self.location = self.operation.location
        super().save(*args, **kwargs)

    class Meta:
        proxy = True
        verbose_name = _("manufacturing order")
        verbose_name_plural = _("manufacturing orders")


class DeliveryOrder(OperationPlan):
    class DeliveryOrderManager(OperationPlan.Manager):
        def get_queryset(self):
            return (
                super().get_queryset().filter(demand__isnull=False, owner__isnull=True)
            )
            # Note: defer screws up the model name when deleting a PO
            # .defer("operation", "owner", "supplier", "location", "origin", "destination")

    objects = DeliveryOrderManager()

    def save(self, *args, **kwargs):
        self.type = "DLVR"
        self.supplier = (
            self.origin
        ) = self.destination = self.operation = self.owner = None
        if self.demand:
            self.item = self.demand.item
            self.location = self.demand.location
        super().save(*args, **kwargs)

    class Meta:
        proxy = True
        verbose_name = _("delivery order")
        verbose_name_plural = _("delivery orders")
