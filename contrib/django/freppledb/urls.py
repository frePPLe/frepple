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
# email : jdetaeye@users.sourceforge.net

from django.conf.urls.defaults import *
import sys, os.path
import freppledb.input.views
import freppledb.output.views
import freppledb.execute.views
import freppledb.user.views
from django.conf import settings

urlpatterns = patterns('',

    # Frepple execution
    (r'^execute/logfrepple/$', 'django.views.generic.simple.direct_to_template',
       {'template': 'execute/logfrepple.html',
        'extra_context': {'title': 'Frepple log file'},
       }),
    (r'^execute/log/$', 'freppledb.report.view_report', {'report': freppledb.execute.views.LogReport,}),
    (r'^execute/runfrepple/$', 'freppledb.execute.views.runfrepple'),
    (r'^execute/erase/$', 'freppledb.execute.views.erase'),
    (r'^execute/create/$', 'freppledb.execute.views.create'),
    (r'^execute/upload/$', 'freppledb.execute.views.upload'),
    (r'^execute/fixture/$', 'freppledb.execute.views.fixture'),
    (r'^execute/', 'freppledb.execute.views.main'),

    # Main index page
    (r'^$', 'django.views.generic.simple.redirect_to', {'url': '/admin/'}),

    # Admin pages
    (r'^admin/', include('django.contrib.admin.urls')),

    # Frepple reports
    (r'^buffer/([^/]+)/$', 'freppledb.report.view_report', {'report': freppledb.output.views.BufferReport,}),
    (r'^buffer/$', 'freppledb.report.view_report', {'report': freppledb.output.views.BufferReport,}),
    (r'^demand/([^/]+)/$', 'freppledb.report.view_report', {'report': freppledb.output.views.DemandReport,}),
    (r'^demand/$', 'freppledb.report.view_report', {'report': freppledb.output.views.DemandReport,}),
    (r'^resource/([^/]+)/$', 'freppledb.report.view_report', {'report': freppledb.output.views.ResourceReport,}),
    (r'^resource/$', 'freppledb.report.view_report', {'report': freppledb.output.views.ResourceReport,}),
    (r'^operation/([^/]+)/$', 'freppledb.report.view_report', {'report': freppledb.output.views.OperationReport,}),
    (r'^operation/$', 'freppledb.report.view_report', {'report': freppledb.output.views.OperationReport,}),
    (r'^forecast/([^/]+)/$', 'freppledb.report.view_report', {'report': freppledb.output.views.ForecastReport,}),
    (r'^forecast/$', 'freppledb.report.view_report', {'report': freppledb.output.views.ForecastReport,}),
    (r'^supplypath/([^/]+)/([^/]+)/$', freppledb.output.views.pathreport.viewupstream),
    (r'^whereused/([^/]+)/([^/]+)/$', freppledb.output.views.pathreport.viewdownstream),
    (r'^pegging/$', 'freppledb.report.view_report', {'report': freppledb.output.views.PeggingReport,}),
    (r'^flowplan/$', 'freppledb.report.view_report', {'report': freppledb.output.views.FlowPlanReport,}),
    (r'^problem/$', 'freppledb.report.view_report', {'report': freppledb.output.views.ProblemReport,}),
    (r'^operationplan/$', 'freppledb.report.view_report', {'report': freppledb.output.views.OperationPlanReport,}),
    (r'^loadplan/$', 'freppledb.report.view_report', {'report': freppledb.output.views.LoadPlanReport,}),
    (r'^demandplan/$', 'freppledb.report.view_report', {'report': freppledb.output.views.DemandPlanReport,}),

    # Posting special edits
    (r'^edit/$', freppledb.input.views.uploadjson.post),

    # User preferences
    (r'^preferences/$', freppledb.user.views.preferences),
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
