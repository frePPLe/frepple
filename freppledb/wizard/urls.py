#
# Copyright (C) 2019 by frePPLe bv
#
# All information contained herein is, and remains the property of frePPLe.
# You are allowed to use and modify the source code, as long as the software is used
# within your company.
# You are not allowed to distribute the software, either in the form of source code
# or in the form of compiled binaries.
#

from django.conf.urls import url
from django.urls import path

from .views import (
    Home,
    CheckSupplyPath,
    Odoo,
    SendUsDataset,
    WizardLoad,
    SendSurveyMail,
    QuickStartProduction,
)

# Automatically add these URLs when the application is installed
autodiscover = True

urlpatterns = [
    url(r"^$", Home),
    url(r"^wizard/quickstart/production/$", QuickStartProduction.as_view()),
    url(r"^wizard/supplypath/", CheckSupplyPath),
    path(r"wizard/load/<str:mode>/", WizardLoad),
    url(r"^wizard/sendsurveymail/$", SendSurveyMail.action),
]
