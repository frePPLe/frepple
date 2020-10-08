"""
This file defines the business logic for reports.
"""

from django.utils.translation import gettext_lazy as _

from freppledb.common.report import (
    GridReport,
    GridFieldText,
    GridFieldNumber,
    GridFieldBoolNullable,
    GridFieldLastModified,
)

from .models import My_Model


class MyModelList(GridReport):
    """
    This report show an editable grid for your models.
    You can sort data, filter data, import excel files, export excel files.
    """

    title = _("My models")
    basequeryset = My_Model.objects.all()
    model = My_Model
    frozenColumns = 1
    rows = (
        GridFieldText(
            "name",
            title=_("name"),
            key=True,
            formatter="detail",
            extra='"role":"my_app/my_model"',
        ),
        GridFieldText("charfield", title=_("charfield")),
        GridFieldBoolNullable("booleanfield", title=_("category")),
        GridFieldNumber("decimalfield", title=_("decimalfield")),
        GridFieldText("source", title=_("source")),
        GridFieldLastModified("lastmodified"),
    )
