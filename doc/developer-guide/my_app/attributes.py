"""
This file demonstrates how you can extend an existing frePPLe model with
custom attributes.
"""

from freppledb.boot import registerAttribute

# Use the function "_" for all strings that can be translated.
from django.utils.translation import gettext_lazy as _

registerAttribute(
    "freppledb.input.models.Item",  # Class we are extending
    [
        (
            "attribute_1",  # Field name in the database
            _("first attribute"),  # Human readable label of the field
            "number",  # Type of the field.
            True,  # Is the field editable?
            True,  # Should the field be visible by default?
        )
    ],
)
