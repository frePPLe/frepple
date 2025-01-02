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

from datetime import datetime

from django.db import models
from django import forms
from django.utils.translation import gettext_lazy as _

from freppledb.common.models import AuditModel, MultiDBManager

from ..models.calendar import Calendar
from ..models.item import Item
from ..models.location import Location
from ..models.resource import Resource, Skill


searchmode = (
    ("PRIORITY", _("priority")),
    ("MINCOST", _("minimum cost")),
    ("MINPENALTY", _("minimum penalty")),
    ("MINCOSTPENALTY", _("minimum cost plus penalty")),
)


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
        help_text=_("Item produced by this operation"),
    )
    location = models.ForeignKey(
        Location, verbose_name=_("location"), db_index=True, on_delete=models.CASCADE
    )
    owner = models.ForeignKey(
        "self",
        verbose_name=_("owner"),
        null=True,
        blank=True,
        related_name="childoperations",
        on_delete=models.SET_NULL,
        help_text=_(
            "Parent operation (which must be of type routing, alternate or split)"
        ),
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
        help_text=_("Minimum production quantity"),
    )
    sizemultiple = models.DecimalField(
        _("size multiple"),
        null=True,
        blank=True,
        max_digits=20,
        decimal_places=8,
        help_text=_("Multiple production quantity"),
    )
    sizemaximum = models.DecimalField(
        _("size maximum"),
        null=True,
        blank=True,
        max_digits=20,
        decimal_places=8,
        help_text=_("Maximum production quantity"),
    )
    cost = models.DecimalField(
        _("cost"),
        null=True,
        blank=True,
        max_digits=20,
        decimal_places=8,
        help_text=_("Cost per produced unit"),
    )
    duration = models.DurationField(
        _("duration"),
        null=True,
        blank=True,
        help_text=_("Fixed production time for setup and overhead"),
    )
    duration_per = models.DurationField(
        _("duration per unit"),
        null=True,
        blank=True,
        help_text=_("Production time per produced piece"),
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

    # Make sure owner type is correct
    def clean_fields(self, exclude=None):
        super().clean_fields(exclude=exclude)
        if self.owner is not None:
            owner = Operation.objects.get(name=self.owner)

            if owner.type in ["time_per", "fixed_time"]:
                raise forms.ValidationError(
                    "Invalid owner: Owner cannot be of type time per or fixed time."
                )
            if owner.type == "routing" and self.type not in ["time_per", "fixed_time"]:
                raise forms.ValidationError(
                    "Invalid owner: Only time per or fixed time operations can have an owner of type routing."
                )
            if owner.name == self.name:
                raise forms.ValidationError(
                    "Invalid owner: Operation name and owner must be different."
                )
            if self.type in ["alternate", "split"] and owner.type in [
                "alternate",
                "split",
            ]:
                raise forms.ValidationError(
                    "Invalid owner: alternate and split operations cannot have an owner of type alternate or split."
                )


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
    location = models.ForeignKey(
        Location,
        verbose_name=_("location"),
        db_index=True,
        related_name="operationmaterials",
        blank=True,
        null=True,
        on_delete=models.SET_NULL,
    )
    quantity = models.DecimalField(
        _("quantity"),
        default="1.00",
        blank=True,
        null=True,
        max_digits=20,
        decimal_places=8,
        help_text=_("Quantity to consume or produce per piece"),
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
        _("effective start"),
        null=True,
        blank=True,
        help_text=_("Validity start date"),
        default=datetime(1971, 1, 1),
    )
    effective_end = models.DateTimeField(
        _("effective end"),
        null=True,
        blank=True,
        help_text=_("Validity end date"),
        default=datetime(2030, 12, 31),
    )
    name = models.CharField(
        _("name"),
        max_length=300,
        null=True,
        blank=True,
        help_text=_("Name of this operation material to identify alternates"),
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
    offset = models.DurationField(
        _("offset"),
        null=True,
        blank=True,
        help_text=_("Time offset from the start or end to consume or produce material"),
    )

    class Manager(MultiDBManager):
        def get_by_natural_key(self, operation, item, effective_start):
            return self.get(
                operation=operation,
                item=item,
                effective_start=effective_start or datetime(1971, 1, 1),
            )

    def natural_key(self):
        return (self.operation, self.item, self.effective_start or datetime(1971, 1, 1))

    def validate_unique(self, exclude=None):
        if self.effective_start is None:
            self.effective_start = datetime(1971, 1, 1)
        super().validate_unique(exclude=exclude)

    objects = Manager()

    def __str__(self):
        if self.effective_start and self.effective_start != datetime(1971, 1, 1):
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
        help_text=_("Required skill to perform the operation"),
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
            "Constant part of the capacity consumption (bucketized resources only)"
        ),
    )
    effective_start = models.DateTimeField(
        _("effective start"),
        null=True,
        blank=True,
        help_text=_("Validity start date"),
        default=datetime(1971, 1, 1),
    )
    effective_end = models.DateTimeField(
        _("effective end"),
        null=True,
        blank=True,
        help_text=_("Validity end date"),
        default=datetime(2030, 12, 31),
    )
    name = models.CharField(
        _("name"),
        max_length=300,
        null=True,
        blank=True,
        help_text=_("Name of this operation resource to identify alternates"),
    )
    priority = models.IntegerField(
        _("priority"),
        default=1,
        null=True,
        blank=True,
        help_text=_("Priority of this operation resource in a group of alternates"),
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
                operation=operation,
                resource=resource,
                effective_start=effective_start or datetime(1971, 1, 1),
            )

    def natural_key(self):
        return (
            self.operation,
            self.resource,
            self.effective_start or datetime(1971, 1, 1),
        )

    def validate_unique(self, exclude=None):
        if self.effective_start is None:
            self.effective_start = datetime(1971, 1, 1)
        super().validate_unique(exclude=exclude)

    objects = Manager()

    def __str__(self):
        if self.effective_start and self.effective_start != datetime(1971, 1, 1):
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

    def getPreferredResource(self):
        # TODO for approved & confirmed MOs the C++ engine also considers the utilization of the resource
        Resource.rebuildHierarchy(self._state.db)
        if not self.resource or self.resource.rght == self.resource.lft + 1:
            # Not an aggregate resource
            return self.resource

        # Find the most efficient child resource that has the required skill
        q = Resource.objects.using(self._state.db).filter(
            rght=models.F("lft") + 1,
            lft__gt=self.resource.lft,
            rght__lt=self.resource.rght,
        )
        if self.skill:
            return (
                q.filter(skills__skill=self.skill)
                .order_by("skills__priority", "-efficiency", "name")
                .first()
            )
        else:
            return q.order_by("-efficiency", "name").first()


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
        _("effective start"),
        null=True,
        blank=True,
        help_text=_("Validity start date"),
        default=datetime(1971, 1, 1),
    )
    effective_end = models.DateTimeField(
        _("effective end"),
        null=True,
        blank=True,
        help_text=_("Validity end date"),
        default=datetime(2030, 12, 31),
    )

    class Manager(MultiDBManager):
        def get_by_natural_key(self, operation, suboperation, effective_start):
            return self.get(
                operation=operation,
                suboperation=suboperation,
                effective_start=effective_start or datetime(1971, 1, 1),
            )

    def natural_key(self):
        return (
            self.operation,
            self.suboperation,
            self.effective_start or datetime(1971, 1, 1),
        )

    def validate_unique(self, exclude=None):
        if self.effective_start is None:
            self.effective_start = datetime(1971, 1, 1)
        super().validate_unique(exclude=exclude)

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

    def save(self, *args, **kwargs):
        # Call the real save() method
        super().save(*args, **kwargs)

        # Merge the same info immediately in the operation table
        self.suboperation.owner = self.operation
        self.suboperation.priority = self.priority
        self.suboperation.effective_start = self.effective_start
        self.suboperation.effective_end = self.effective_end
        self.suboperation.item = None
        self.suboperation.save(
            update_fields=[
                "owner",
                "priority",
                "effective_start",
                "effective_end",
                "item",
            ]
        )


class OperationDependency(AuditModel):
    # Database fields
    id = models.AutoField(_("identifier"), primary_key=True)
    operation = models.ForeignKey(
        Operation,
        verbose_name=_("operation"),
        related_name="dependencies",
        help_text=_("operation"),
        on_delete=models.CASCADE,
    )
    blockedby = models.ForeignKey(
        Operation,
        verbose_name=_("blocked by operation"),
        related_name="dependents",
        help_text=_("blocked by operation"),
        on_delete=models.CASCADE,
    )
    quantity = models.DecimalField(
        _("quantity"),
        max_digits=20,
        decimal_places=8,
        null=True,
        blank=True,
        default="1.0",
        help_text=_("Quantity relation between the operations"),
    )
    safety_leadtime = models.DurationField(
        _("soft safety lead time"),
        null=True,
        blank=True,
        help_text=_("soft safety lead time"),
    )
    hard_safety_leadtime = models.DurationField(
        _("hard safety lead time"),
        null=True,
        blank=True,
        help_text=_("hard safety lead time"),
    )

    class Manager(MultiDBManager):
        def get_by_natural_key(self, operation, blockedby):
            return self.get(operation=operation, blockedby=blockedby)

    def natural_key(self):
        return (self.operation, self.blockedby)

    objects = Manager()

    def __str__(self):
        return "%s   %s" % (
            self.operation.name if self.operation else None,
            self.blockedby.name if self.blockedby else None,
        )

    class Meta(AuditModel.Meta):
        db_table = "operation_dependency"
        ordering = ["operation", "blockedby"]
        verbose_name = _("operation dependency")
        verbose_name_plural = _("operation dependencies")
        unique_together = (("operation", "blockedby"),)
