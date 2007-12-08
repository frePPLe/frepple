#
# Copyright (C) 2007 by Johan De Taeye
#
# This library is free software; you can redistribute it and/or modify it
# under the terms of the GNU Lesser General Public License as published
# by the Free Software Foundation; either version 2.1 of the License, or
# (at your option) any later version.
#
# This library is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU Lesser
# General Public License for more details.
#
# You should have received a copy of the GNU Lesser General Public
# License along with this library; if not, write to the Free Software
# Foundation Inc., 59 Temple Place, Suite 330, Boston, MA 02111-1307, USA
#

# file : $URL$
# revision : $LastChangedRevision$  $LastChangedBy$
# date : $LastChangedDate$

from django.conf.urls.defaults import *
import os.path
import input.views
import output.views
import user.views
from django.conf import settings


urlpatterns = patterns('',

    # frePPLe execution application
    (r'^execute/', include('execute.urls')),

    # Main index page
    (r'^$', 'django.views.generic.simple.redirect_to', {'url': '/admin/'}),

    # Admin pages
    # This includes also the Javascript i18n library
    (r'^admin/', include('django.contrib.admin.urls')),

    # Output reports
    (r'^buffer/([^/]+)/$', 'utils.report.view_report',
      {'report': output.views.BufferReport,}),
    (r'^buffer/$', 'utils.report.view_report',
      {'report': output.views.BufferReport,}),
    (r'^demand/([^/]+)/$', 'utils.report.view_report',
      {'report': output.views.DemandReport,}),
    (r'^demand/$', 'utils.report.view_report',
      {'report': output.views.DemandReport,}),
    (r'^resource/([^/]+)/$', 'utils.report.view_report',
      {'report': output.views.ResourceReport,}),
    (r'^resource/$', 'utils.report.view_report',
      {'report': output.views.ResourceReport,}),
    (r'^operation/([^/]+)/$', 'utils.report.view_report',
      {'report': output.views.OperationReport,}),
    (r'^operation/$', 'utils.report.view_report',
      {'report': output.views.OperationReport,}),
    (r'^forecast/([^/]+)/$', 'utils.report.view_report',
      {'report': output.views.ForecastReport,}),
    (r'^forecast/$', 'utils.report.view_report',
      {'report': output.views.ForecastReport,}),
    (r'^pegging/$', 'utils.report.view_report',
      {'report': output.views.PeggingReport,}),
    (r'^flowplan/$', 'utils.report.view_report',
      {'report': output.views.FlowPlanReport,}),
    (r'^problem/$', 'utils.report.view_report',
      {'report': output.views.ProblemReport,}),
    (r'^operationplan/$', 'utils.report.view_report',
      {'report': output.views.OperationPlanReport,}),
    (r'^loadplan/$', 'utils.report.view_report',
      {'report': output.views.LoadPlanReport,}),
    (r'^demandplan/$', 'utils.report.view_report',
      {'report': output.views.DemandPlanReport,}),

    # Input reports
    (r'^supplypath/([^/]+)/([^/]+)/$', input.views.pathreport.viewupstream),
    (r'^whereused/([^/]+)/([^/]+)/$', input.views.pathreport.viewdownstream),
    (r'^edit/$', input.views.uploadjson.post),

    # User preferences
    (r'^preferences/$', user.views.preferences),
)

# Allows the standalone development server (and the py2exe executable) to serve
# the static pages.
# In a production environment you need to configure your web server to take care of
# these pages.
if settings.STANDALONE == True:
  urlpatterns += patterns('',(r'^static/(?P<path>.*)$', 'django.views.static.serve',
       {'document_root': os.path.join(settings.FREPPLE_APP,'static'),
        'show_indexes': False}),
    )
