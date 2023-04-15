#
# Copyright (C) 2019 by frePPLe bv
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

from django.urls import path

from .views import (
    Home,
    CheckSupplyPath,
    FeatureDashboard,
    WizardLoad,
    SendSurveyMail,
    QuickStartProduction,
)


# Automatically add these URLs when the application is installed
autodiscover = True

urlpatterns = [
    path(r"", Home),
    path(r"wizard/quickstart/production/", QuickStartProduction.as_view()),
    path(r"wizard/supplypath/", CheckSupplyPath),
    path(r"wizard/load/<str:mode>/", WizardLoad),
    path(r"wizard/sendsurveymail/", SendSurveyMail.action),
    path(r"wizard/features/", FeatureDashboard.as_view()),
]
