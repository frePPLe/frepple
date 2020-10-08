"""
This file demonstrates how you can define an new entity in the database.
"""

from django.db import models

# Use the function "_" for all strings that can be translated.
from django.utils.translation import ugettext_lazy as _

# A subclass of AuditModel will inherit an field "last_modified" and "source".
from freppledb.common.models import AuditModel


class My_Model(AuditModel):
    # Database fields
    name = models.CharField(_("name"), max_length=300, primary_key=True)
    charfield = models.CharField(
        _("charfield"),
        max_length=300,
        null=True,
        blank=True,
        help_text=_("A sample character field"),
    )
    booleanfield = models.BooleanField(
        _("booleanfield"),
        blank=True,
        default=True,
        help_text=_("A sample boolean field"),
    )
    decimalfield = models.DecimalField(
        _("decimalfield"),
        max_digits=20,
        decimal_places=8,
        default="0.00",
        help_text=_("A sample decimal field"),
    )

    class Meta(AuditModel.Meta):
        db_table = "my_model"  # Name of the database table
        verbose_name = _("my model")  # A translatable name for the entity
        verbose_name_plural = _("my models")  # Plural name
        ordering = ["name"]
