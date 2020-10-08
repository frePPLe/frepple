"""
This file is used to add customized entries to the menu.
"""

from django.utils.translation import ugettext as _

from freppledb.menu import menu

from .models import My_Model
from .views import MyModelList

menu.addGroup("my_menu", label=_("My App"), index=1)
menu.addItem(
    "my_menu",
    "my_model",
    url="/data/my_app/my_model/",
    report=MyModelList,
    index=100,
    model=My_Model,
)
menu.addItem(
    "my_menu",
    "google",
    url="http://google.com",
    window=True,
    label=_("link to my company"),
    prefix=False,
    index=300,
)
