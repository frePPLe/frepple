#
# Copyright (C) 2019 by frePPLe bv
#
# This library is free software; you can redistribute it and/or modify it
# under the terms of the GNU Affero General Public License as published
# by the Free Software Foundation; either version 3 of the License, or
#
# This library is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU Affero
# General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public
# License along with this program.  If not, see <http://www.gnu.org/licenses/>.
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
