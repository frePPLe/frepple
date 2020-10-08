"""
This file defines a form to edit your models.
"""

from django.utils.translation import gettext_lazy as _

from freppledb.admin import data_site
from freppledb.common.adminforms import MultiDBModelAdmin

from .models import My_Model


class My_Model_Admin(MultiDBModelAdmin):
    model = My_Model
    fields = ("name", "charfield", "booleanfield", "decimalfield")
    save_on_top = True
    # Defines tabs shown on the edit form
    tabs = [
        {
            "name": "edit",
            "label": _("edit"),
            "view": "admin:my_app_my_model_change",
            "permissions": "my_app.change_my_model",
        },
        {
            "name": "comments",
            "label": _("comments"),
            "view": "admin:my_app_my_model_comment",
        },
        {
            "name": "history",
            "label": _("History"),
            "view": "admin:my_app_my_model_history",
        },
    ]


data_site.register(My_Model, My_Model_Admin)
